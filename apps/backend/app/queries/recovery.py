"""Owner-scoped recovery issue projection; no business-state writes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.recovery import (
    RecoveryActionV1,
    RecoveryCategory,
    RecoveryIssueListResponseV1,
    RecoveryIssueViewV1,
)
from app.domains.content_knowledge import SAFETY_REINSPECTION_KEY, SAFETY_SCANNER_VERSION
from app.infrastructure.recovery import RecoveryLedgerRepository
from app.models.document import ProcessingStatus, UserDocument
from app.models.ledger import OutboxTaskRecord, RecoveryEventRecord
from app.models.user import User
from app.services.documents.document_service import (
    DOCUMENT_PROCESS_TASK_TYPE,
    DOCUMENT_REINSPECTION_TASK_TYPE,
    DocumentService,
)
from app.services.storage.local_storage import get_local_storage


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def row_version(value: datetime) -> int:
    return max(1, int(aware(value).timestamp() * 1_000_000))


def command_action(
    code: Literal["retry_owner_command", "reinspect_document"],
    label: str,
    *,
    enabled: bool = True,
    disabled_reason_code: str | None = None,
) -> RecoveryActionV1:
    return RecoveryActionV1(
        action_code=code,
        label=label,
        kind="command",
        enabled=enabled,
        disabled_reason_code=disabled_reason_code,
        endpoint="/api/v1/recovery/actions",
        method="POST",
        requires_idempotency_key=True,
    )


def diagnostic_action() -> RecoveryActionV1:
    return RecoveryActionV1(
        action_code="copy_diagnostics",
        label="复制脱敏诊断",
        kind="client",
        enabled=True,
    )


def wait_action(label: str) -> RecoveryActionV1:
    return RecoveryActionV1(
        action_code="wait_until",
        label=label,
        kind="wait",
        enabled=True,
    )


class RecoveryQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_issues(
        self, user: User, *, correlation_id: str
    ) -> RecoveryIssueListResponseV1:
        issues = [
            *await self._document_issues(user),
            *await self._outbox_issues(user),
            *await self._operational_issues(user),
        ]
        severity_rank = {"blocking": 0, "warning": 1, "info": 2}
        issues.sort(key=lambda issue: (severity_rank[issue.severity], -issue.updated_at.timestamp()))
        now = utc_now()
        return RecoveryIssueListResponseV1(
            generated_at=now,
            issues=tuple(issues),
            active_count=sum(issue.status != "resolved" for issue in issues),
            correlation_id=correlation_id,
        )

    async def _document_issues(self, user: User) -> list[RecoveryIssueViewV1]:
        documents = list(
            (
                await self._session.scalars(
                    select(UserDocument).where(
                        UserDocument.pseudonym_id == user.pseudonym_id,
                        UserDocument.is_deleted.is_(False),
                    )
                )
            ).all()
        )
        storage = get_local_storage()
        document_tasks = list(
            (
                await self._session.scalars(
                    select(OutboxTaskRecord).where(
                        OutboxTaskRecord.type.in_(
                            (DOCUMENT_PROCESS_TASK_TYPE, DOCUMENT_REINSPECTION_TASK_TYPE)
                        )
                    )
                )
            ).all()
        )
        issues: list[RecoveryIssueViewV1] = []
        for document in documents:
            created = aware(document.created_at)
            updated = aware(document.updated_at)
            if storage.get_file_size(document.storage_path) <= 0:
                issues.append(
                    RecoveryIssueViewV1(
                        issue_ref=f"document:{document.id}:file",
                        issue_version=row_version(updated),
                        code="CONTENT_FILE_MISSING",
                        category=RecoveryCategory.DATA_INTEGRITY,
                        severity="blocking",
                        status="active",
                        title="资料原文件不可用",
                        summary="资料记录仍在，但 Askora 无法读取对应原文件。",
                        data_safety="preserved_but_unavailable",
                        duplicate_risk="not_applicable",
                        source_system="SYS01",
                        resource_ref=f"document:{document.id}",
                        actions=(
                            RecoveryActionV1(
                                action_code="open_data_recovery",
                                label="打开数据恢复",
                                kind="navigate",
                                enabled=True,
                                route="/settings/data",
                            ),
                            RecoveryActionV1(
                                action_code="reselect_file",
                                label="重新选择原文件",
                                kind="navigate",
                                enabled=True,
                                route=f"/library?reselect={document.id}",
                            ),
                        ),
                        opened_at=created,
                        updated_at=updated,
                    )
                )
                continue
            if document.processing_status == ProcessingStatus.FAILED:
                manual_attempts = sum(
                    1
                    for task in document_tasks
                    if task.payload.get("document_id") == document.id
                    and isinstance(task.payload.get("recovery_of"), str)
                )
                retry_budget = 3
                actions = (
                    (command_action("retry_owner_command", "重新处理"),)
                    if manual_attempts < retry_budget
                    else (diagnostic_action(),)
                )
                issues.append(
                    RecoveryIssueViewV1(
                        issue_ref=f"document:{document.id}:processing",
                        issue_version=row_version(updated),
                        code="CONTENT_PROCESSING_FAILED",
                        category=RecoveryCategory.TRANSIENT,
                        severity="blocking",
                        status="active",
                        title="资料处理没有完成",
                        summary="原文件仍保留，可安全重新提交一次处理任务。",
                        data_safety="preserved",
                        duplicate_risk="prevented_by_idempotency",
                        source_system="SYS01",
                        resource_ref=f"document:{document.id}",
                        attempt_count=manual_attempts,
                        retry_budget=retry_budget,
                        actions=actions,
                        opened_at=created,
                        updated_at=updated,
                    )
                )
            elif document.processing_status == ProcessingStatus.QUARANTINED:
                details = document.moderation_details or {}
                control = details.get(SAFETY_REINSPECTION_KEY, {})
                current_version = DocumentService.last_scanner_version(details)
                if (
                    isinstance(control, dict)
                    and control.get("target_scanner_version") == SAFETY_SCANNER_VERSION
                    and control.get("status") in {"pending", "processing"}
                ):
                    actions = (wait_action("安全复检正在进行"),)
                    status: Literal["active", "waiting"] = "waiting"
                elif (
                    isinstance(control, dict)
                    and control.get("target_scanner_version") == SAFETY_SCANNER_VERSION
                    and control.get("status") == "failed"
                ):
                    actions = (diagnostic_action(),)
                    status = "active"
                elif current_version == SAFETY_SCANNER_VERSION:
                    actions = (
                        command_action(
                            "reinspect_document",
                            "暂无更新的安全策略",
                            enabled=False,
                            disabled_reason_code="CONTENT_REINSPECTION_POLICY_UNCHANGED",
                        ),
                    )
                    status = "active"
                else:
                    actions = (command_action("reinspect_document", "使用新策略复检"),)
                    status = "active"
                issues.append(
                    RecoveryIssueViewV1(
                        issue_ref=f"document:{document.id}:quarantine",
                        issue_version=row_version(updated),
                        code="CONTENT_QUARANTINED",
                        category=RecoveryCategory.SECURITY,
                        severity="blocking",
                        status=status,
                        title="资料仍在安全隔离中",
                        summary="隔离期间不会进入检索或学习；只有更新的安全策略才能复检。",
                        data_safety="preserved_but_unavailable",
                        duplicate_risk="prevented_by_idempotency",
                        source_system="SYS01",
                        resource_ref=f"document:{document.id}",
                        retry_budget=1,
                        actions=actions,
                        opened_at=created,
                        updated_at=updated,
                    )
                )
        return issues

    async def _outbox_issues(self, user: User) -> list[RecoveryIssueViewV1]:
        all_records = list(
            (
                await self._session.scalars(
                    select(OutboxTaskRecord)
                )
            ).all()
        )
        records = [
            record for record in all_records if record.status in {"retry", "dead_letter"}
        ]
        recovery_origins = {
            origin
            for record in all_records
            if isinstance((origin := record.payload.get("recovery_of")), str)
        }
        issues: list[RecoveryIssueViewV1] = []
        for record in records:
            payload = record.payload or {}
            document_id = payload.get("document_id")
            scoped = payload.get("pseudonym_id") == user.pseudonym_id
            if isinstance(document_id, str):
                scoped = bool(
                    await self._session.scalar(
                        select(UserDocument.id).where(
                            UserDocument.id == document_id,
                            UserDocument.pseudonym_id == user.pseudonym_id,
                            UserDocument.is_deleted.is_(False),
                        )
                    )
                )
            if not scoped:
                continue
            if f"outbox:{record.id}" in recovery_origins or (
                isinstance(document_id, str)
                and f"document:{document_id}:failed" in recovery_origins
            ):
                continue
            retryable_type = record.type in {
                DOCUMENT_PROCESS_TASK_TYPE,
                DOCUMENT_REINSPECTION_TASK_TYPE,
            }
            waiting = record.status == "retry"
            actions: tuple[RecoveryActionV1, ...] = ()
            if waiting:
                actions = (wait_action("等待自动重试"),)
            elif retryable_type:
                actions = (command_action("retry_owner_command", "创建安全重试"),)
            else:
                actions = (diagnostic_action(),)
            code = (
                "OUTBOX_RETRY_WAITING"
                if waiting
                else "OUTBOX_RETRY_EXHAUSTED"
                if retryable_type
                else "OUTBOX_HANDLER_UNAVAILABLE"
            )
            issues.append(
                RecoveryIssueViewV1(
                    issue_ref=f"outbox:{record.id}",
                    issue_version=row_version(record.updated_at),
                    code=code,
                    category=(
                        RecoveryCategory.TRANSIENT
                        if retryable_type or waiting
                        else RecoveryCategory.INTERNAL
                    ),
                    severity="warning" if waiting else "blocking",
                    status="waiting" if waiting else "active",
                    title="后台任务正在等待重试" if waiting else "后台任务重试已耗尽",
                    summary=(
                        "任务会在预算内自动重试，不需要重复提交。"
                        if waiting
                        else (
                            "可创建保留原失败历史的新任务。"
                            if retryable_type
                            else "该任务没有可证明安全的重放处理器，只提供诊断。"
                        )
                    ),
                    data_safety="preserved",
                    duplicate_risk=(
                        "prevented_by_idempotency" if retryable_type else "requires_confirmation"
                    ),
                    source_system="SYS08",
                    resource_ref=f"outbox:{record.id}",
                    attempt_count=record.attempt_count,
                    retry_budget=5,
                    next_eligible_at=aware(record.next_attempt_at) if waiting else None,
                    actions=actions,
                    opened_at=aware(record.created_at),
                    updated_at=aware(record.updated_at),
                )
            )
        return issues

    async def _operational_issues(self, user: User) -> list[RecoveryIssueViewV1]:
        events = await RecoveryLedgerRepository(self._session).list_events(
            pseudonym_id=user.pseudonym_id
        )
        latest: dict[str, RecoveryEventRecord] = {}
        for event in events:
            if event.issue_key.startswith("audit:"):
                continue
            latest[event.issue_key] = event
        issues: list[RecoveryIssueViewV1] = []
        for event in latest.values():
            if event.status == "resolved":
                continue
            actions = self._operational_actions(event)
            issues.append(
                RecoveryIssueViewV1(
                    issue_ref=event.issue_key,
                    issue_version=event.issue_version,
                    code=event.code,
                    category=RecoveryCategory(event.category),
                    severity=cast(Literal["info", "warning", "blocking"], event.severity),
                    status=cast(
                        Literal["active", "waiting", "action_running", "resolved"],
                        event.status,
                    ),
                    title=event.title,
                    summary=event.summary,
                    data_safety=cast(
                        Literal[
                            "preserved", "preserved_but_unavailable", "at_risk", "unknown"
                        ],
                        event.data_safety,
                    ),
                    duplicate_risk=cast(
                        Literal[
                            "none",
                            "prevented_by_idempotency",
                            "requires_confirmation",
                            "not_applicable",
                        ],
                        event.duplicate_risk,
                    ),
                    source_system=cast(
                        Literal["SYS01", "SYS08", "BOOTSTRAP", "DATA_CONTROL"],
                        event.source_system,
                    ),
                    resource_ref=event.resource_ref,
                    correlation_id=event.correlation_id,
                    attempt_count=event.attempt_count,
                    retry_budget=event.retry_budget,
                    next_eligible_at=(
                        aware(event.next_eligible_at) if event.next_eligible_at else None
                    ),
                    actions=actions,
                    opened_at=aware(event.created_at),
                    updated_at=aware(event.created_at),
                )
            )
        return issues

    @staticmethod
    def _operational_actions(event: RecoveryEventRecord) -> tuple[RecoveryActionV1, ...]:
        if event.code in {"AI_PROVIDER_KEY_INVALID", "AI_PROVIDER_KEY_MISSING"}:
            return (
                RecoveryActionV1(
                    action_code="open_model_settings",
                    label="打开模型设置",
                    kind="navigate",
                    enabled=True,
                    route="/settings/models",
                ),
            )
        if event.code == "AI_MODEL_UNAVAILABLE":
            return (
                RecoveryActionV1(
                    action_code="open_model_settings",
                    label="检查模型设置",
                    kind="navigate",
                    enabled=True,
                    route="/settings/models",
                ),
            )
        if event.retry_budget is not None and event.attempt_count >= event.retry_budget:
            return (diagnostic_action(),)
        if event.next_eligible_at is not None:
            return (wait_action("等待后再试"),)
        return (diagnostic_action(),)
