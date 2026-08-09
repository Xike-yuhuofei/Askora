"""Recovery command router that delegates side effects to original owners."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.recovery import (
    RecoveryCommandV1,
    RecoveryIssueViewV1,
    RecoveryResultV1,
    recovery_catalog_entry,
)
from app.core.exceptions import (
    RecoveryActionNotAllowedError,
    RecoveryIssueNotFoundError,
    RecoveryVersionConflictError,
)
from app.infrastructure.outbox import OutboxRepository
from app.infrastructure.recovery import RecoveryLedgerRepository
from app.models.user import User
from app.queries.recovery import RecoveryQueryService
from app.services.documents.document_service import (
    DOCUMENT_PROCESS_TASK_TYPE,
    DOCUMENT_REINSPECTION_TASK_TYPE,
    DocumentService,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


class RecoveryActionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._ledger = RecoveryLedgerRepository(session)

    async def execute(
        self,
        user: User,
        command: RecoveryCommandV1,
        *,
        correlation_id: str,
    ) -> RecoveryResultV1:
        prior = await self._ledger.find_action_result(
            pseudonym_id=user.pseudonym_id,
            idempotency_key=command.idempotency_key,
        )
        if prior is not None:
            details = prior.safe_details or {}
            return RecoveryResultV1(
                result_ref=prior.result_ref or prior.id,
                issue_ref=str(details.get("issue_ref", command.issue_ref)),
                status=details.get("result_status", "accepted"),
                issue_version=prior.issue_version,
                owner_command_ref=details.get("owner_command_ref"),
                replacement_task_ref=details.get("replacement_task_ref"),
                message=prior.summary,
                correlation_id=prior.correlation_id or correlation_id,
                completed_at=aware(prior.created_at),
            )

        listing = await RecoveryQueryService(self._session).list_issues(
            user, correlation_id=correlation_id
        )
        issue = next((item for item in listing.issues if item.issue_ref == command.issue_ref), None)
        if issue is None:
            raise RecoveryIssueNotFoundError()
        if issue.issue_version != command.expected_issue_version:
            raise RecoveryVersionConflictError()
        action = next(
            (item for item in issue.actions if item.action_code == command.action_code), None
        )
        if action is None or not action.enabled or action.kind != "command":
            raise RecoveryActionNotAllowedError(
                (action.disabled_reason_code or "ACTION_DISABLED")
                if action is not None
                else "ACTION_NOT_IN_ISSUE_ALLOWLIST"
            )

        audit_key = f"audit:{issue.issue_ref}"
        await self._ledger.append(
            pseudonym_id=user.pseudonym_id,
            issue_key=audit_key,
            event_type="action_requested",
            code=issue.code,
            category=issue.category.value,
            severity=issue.severity,
            status="action_running",
            source_system="SYS08",
            data_safety=issue.data_safety,
            duplicate_risk=issue.duplicate_risk,
            title=issue.title,
            summary="恢复动作已提交给原状态 owner。",
            resource_ref=issue.resource_ref,
            correlation_id=correlation_id,
            action_code=command.action_code,
            idempotency_key=command.idempotency_key,
            safe_details={"issue_ref": issue.issue_ref},
        )
        await self._session.commit()

        try:
            owner_ref, task_ref, message = await self._dispatch_owner_action(user, issue, command)
        except Exception:
            await self._session.rollback()
            await self._ledger.append(
                pseudonym_id=user.pseudonym_id,
                issue_key=audit_key,
                event_type="action_failed",
                code=issue.code,
                category=issue.category.value,
                severity=issue.severity,
                status="active",
                source_system="SYS08",
                data_safety=issue.data_safety,
                duplicate_risk=issue.duplicate_risk,
                title=issue.title,
                summary="恢复动作未完成，原状态保持不变。",
                resource_ref=issue.resource_ref,
                correlation_id=correlation_id,
                action_code=command.action_code,
                idempotency_key=command.idempotency_key,
                result_ref=f"recovery-result:{uuid4()}",
                safe_details={
                    "issue_ref": issue.issue_ref,
                    "result_status": "failed",
                },
            )
            await self._session.commit()
            raise
        result_ref = f"recovery-result:{uuid4()}"
        completed_at = utc_now()
        result_event = await self._ledger.append(
            pseudonym_id=user.pseudonym_id,
            issue_key=audit_key,
            event_type="action_succeeded",
            code=issue.code,
            category=issue.category.value,
            severity=issue.severity,
            status="resolved",
            source_system="SYS08",
            data_safety=issue.data_safety,
            duplicate_risk=issue.duplicate_risk,
            title=issue.title,
            summary=message,
            resource_ref=issue.resource_ref,
            correlation_id=correlation_id,
            action_code=command.action_code,
            idempotency_key=command.idempotency_key,
            result_ref=result_ref,
            safe_details={
                "issue_ref": issue.issue_ref,
                "result_status": "accepted",
                "owner_command_ref": owner_ref,
                "replacement_task_ref": task_ref,
            },
            created_at=completed_at,
        )
        await self._session.commit()
        return RecoveryResultV1(
            result_ref=result_ref,
            issue_ref=issue.issue_ref,
            status="accepted",
            issue_version=result_event.issue_version,
            owner_command_ref=owner_ref,
            replacement_task_ref=task_ref,
            message=message,
            correlation_id=correlation_id,
            completed_at=completed_at,
        )

    async def _dispatch_owner_action(
        self, user: User, issue: RecoveryIssueViewV1, command: RecoveryCommandV1
    ) -> tuple[str | None, str | None, str]:
        parts = issue.issue_ref.split(":")
        documents = DocumentService(self._session)
        if len(parts) == 3 and parts[0] == "document":
            document_id, kind = parts[1], parts[2]
            if kind == "processing" and command.action_code == "retry_owner_command":
                _, replacement_task = await documents.retry_failed_document(
                    document_id=document_id,
                    pseudonym_id=user.pseudonym_id,
                    recovery_idempotency_key=command.idempotency_key,
                )
                return (
                    f"document:{document_id}",
                    f"outbox:{replacement_task.id}",
                    "已创建安全的资料处理任务",
                )
            if kind == "quarantine" and command.action_code == "reinspect_document":
                document, _ = await documents.request_reinspection(
                    document_id=document_id,
                    pseudonym_id=user.pseudonym_id,
                )
                return f"document:{document.id}", None, "已提交新版安全策略复检"
        if len(parts) == 2 and parts[0] == "outbox":
            original_task = await OutboxRepository(self._session).get(parts[1])
            if original_task is None:
                raise RecoveryIssueNotFoundError()
            original_document_id = original_task.payload.get("document_id")
            if not isinstance(original_document_id, str):
                raise RecoveryActionNotAllowedError("OUTBOX_OWNER_SCOPE_UNKNOWN")
            if original_task.type == DOCUMENT_PROCESS_TASK_TYPE:
                _, replacement = await documents.retry_failed_document(
                    document_id=original_document_id,
                    pseudonym_id=user.pseudonym_id,
                    recovery_idempotency_key=command.idempotency_key,
                    recovery_of=f"outbox:{original_task.id}",
                )
                return (
                    f"document:{original_document_id}",
                    f"outbox:{replacement.id}",
                    "已保留原失败历史并创建替代任务",
                )
            if original_task.type == DOCUMENT_REINSPECTION_TASK_TYPE:
                document, _ = await documents.request_reinspection(
                    document_id=original_document_id,
                    pseudonym_id=user.pseudonym_id,
                )
                return f"document:{document.id}", None, "已重新提交安全复检"
        raise RecoveryActionNotAllowedError("NO_OWNER_COMMAND_HANDLER")


class RecoveryIncidentService:
    """Publish SYS08 operational incidents without creating learner evidence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._ledger = RecoveryLedgerRepository(session)

    async def record_model_failure(
        self,
        user: User,
        *,
        activity_id: str,
        code: str,
        retryable: bool,
        retry_after_seconds: int | None,
        correlation_id: str,
    ) -> None:
        title, summary = {
            "AI_PROVIDER_TIMEOUT": ("模型响应超时", "本轮未被接纳，可在等待后安全重试。"),
            "AI_PROVIDER_RATE_LIMITED": ("模型请求达到限额", "本轮未被接纳，请按等待时间重试。"),
            "AI_PROVIDER_KEY_INVALID": ("模型密钥无效", "请在模型设置中更新并验证密钥。"),
            "AI_PROVIDER_KEY_MISSING": ("尚未配置模型密钥", "请先完成模型设置和连接验证。"),
            "AI_MODEL_UNAVAILABLE": ("所选模型暂不可用", "本轮未被接纳，可检查模型设置后重试。"),
            "AI_OUTPUT_VALIDATION_FAILED": (
                "模型输出未通过验证",
                "不可信输出已丢弃，没有写入学习记录。",
            ),
        }.get(code, ("模型执行未完成", "本轮未被接纳，没有写入学习记录。"))
        now = utc_now()
        issue_key = f"provider:{activity_id}"
        existing_events = await self._ledger.list_events(pseudonym_id=user.pseudonym_id)
        latest = next(
            (event for event in reversed(existing_events) if event.issue_key == issue_key),
            None,
        )
        attempt_count = (latest.attempt_count if latest is not None else 0) + 1
        retry_budget = 3 if retryable else 0
        budget_available = retryable and attempt_count < retry_budget
        entry = recovery_catalog_entry(code)
        await self._ledger.append(
            pseudonym_id=user.pseudonym_id,
            issue_key=issue_key,
            event_type="opened",
            code=code,
            category=entry.category.value,
            severity="blocking",
            status=(
                "waiting" if budget_available and retry_after_seconds is not None else "active"
            ),
            source_system="SYS08",
            data_safety=entry.data_safety,
            duplicate_risk="prevented_by_idempotency",
            title=title,
            summary=summary,
            resource_ref=f"activity:{activity_id}",
            correlation_id=correlation_id,
            attempt_count=attempt_count,
            retry_budget=retry_budget,
            next_eligible_at=(
                now + timedelta(seconds=retry_after_seconds)
                if budget_available and retry_after_seconds is not None
                else None
            ),
            created_at=now,
        )
        await self._session.commit()

    async def resolve_model_issue(
        self,
        user: User,
        *,
        activity_id: str,
        correlation_id: str,
    ) -> None:
        issue_key = f"provider:{activity_id}"
        events = await self._ledger.list_events(pseudonym_id=user.pseudonym_id)
        latest = next((event for event in reversed(events) if event.issue_key == issue_key), None)
        if latest is None or latest.status == "resolved":
            return
        await self._ledger.append(
            pseudonym_id=user.pseudonym_id,
            issue_key=issue_key,
            event_type="resolved",
            code=latest.code,
            category=latest.category,
            severity=latest.severity,
            status="resolved",
            source_system="SYS08",
            data_safety=latest.data_safety,
            duplicate_risk=latest.duplicate_risk,
            title=latest.title,
            summary="后续模型执行成功；原失败事件已保留。",
            resource_ref=latest.resource_ref,
            correlation_id=correlation_id,
        )
