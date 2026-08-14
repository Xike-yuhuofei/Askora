"""ADR-0023/CWSP Platform Workspace selection application service."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Literal, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.workspace import (
    CreateWorkspaceV1,
    RenameWorkspaceV1,
    SwitchWorkspaceV1,
    WorkspaceGetResponseV1,
    WorkspaceItemV1,
    WorkspaceListDataV1,
    WorkspaceListResponseV1,
    WorkspaceMutationResultV1,
    WorkspacePreservedRefsV1,
    WorkspaceSwitchBlockerV1,
    WorkspaceTransitionGuardV1,
)
from app.core.exceptions import BusinessError
from app.models.planning import LearningActivityRecord
from app.models.workspace import (
    LearningSession,
    LearningSessionStatus,
    Workspace,
    WorkspaceSelection,
)
from app.services.workspace.repository import (
    WorkspaceError,
    WorkspaceIdempotencyConflictError,
    WorkspaceRepository,
    WorkspaceSelectionRepository,
    WorkspaceSelectionVersionConflictError,
)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _digest(command: CreateWorkspaceV1 | SwitchWorkspaceV1 | RenameWorkspaceV1) -> str:
    payload = command.model_dump(mode="json", exclude={"idempotency_key"})
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class WorkspaceSelectionService:
    """Single Platform writer for Workspace create/current/switch."""

    def __init__(self, db: AsyncSession, *, clock=None) -> None:
        self.db = db
        self.workspaces = WorkspaceRepository(db)
        self.selections = WorkspaceSelectionRepository(db)
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    async def list(self, *, owner_id: UUID, correlation_id: UUID) -> WorkspaceListResponseV1:
        owner = str(owner_id)
        workspaces = await self.workspaces.list_active_for_owner(owner)
        selection = await self.selections.get(owner)
        current_id = selection.current_workspace_id if selection else None
        valid_current = current_id is None or any(w.workspace_id == current_id for w in workspaces)
        items = tuple(
            self._item(workspace, current_id=current_id)
            for workspace in sorted(
                workspaces,
                key=lambda item: (
                    item.workspace_id != current_id,
                    -_aware(item.updated_at).timestamp(),
                    _aware(item.created_at).timestamp(),
                    item.workspace_id,
                ),
            )
        )
        view_state: Literal["EMPTY", "READY", "STALE"] = (
            "EMPTY"
            if not workspaces and selection is None
            else "READY" if valid_current and selection is not None else "STALE"
        )
        return WorkspaceListResponseV1(
            generated_at=self.clock(),
            correlation_id=correlation_id,
            data=WorkspaceListDataV1(
                view_state=view_state,
                selection_version=selection.version if selection else None,
                current_workspace_id=UUID(current_id) if current_id and valid_current else None,
                workspaces=items,
            ),
        )

    async def count_active(self, *, owner_id: UUID) -> int:
        """Side-effect-free compatibility capability query."""
        return await self.workspaces.count_active_for_owner(str(owner_id))

    async def get(
        self, *, owner_id: UUID, workspace_id: UUID, correlation_id: UUID
    ) -> WorkspaceGetResponseV1:
        owner = str(owner_id)
        workspace = await self.workspaces.get_for_owner(owner, str(workspace_id))
        if workspace is None or workspace.lifecycle != "active":
            self._not_found()
            raise AssertionError("unreachable")
        selection = await self.selections.get(owner)
        return WorkspaceGetResponseV1(
            generated_at=self.clock(),
            correlation_id=correlation_id,
            data=self._item(
                workspace,
                current_id=selection.current_workspace_id if selection else None,
            ),
        )

    async def current(self, *, owner_id: UUID, correlation_id: UUID) -> WorkspaceGetResponseV1:
        selection = await self.selections.get(str(owner_id))
        if selection is None:
            raise BusinessError(
                message="当前课程尚未选择",
                error_code="WORKSPACE_SELECTION_MISSING",
                status_code=404,
                category="not_found",
            )
        return await self.get(
            owner_id=owner_id,
            workspace_id=UUID(selection.current_workspace_id),
            correlation_id=correlation_id,
        )

    async def create(
        self, *, owner_id: UUID, command: CreateWorkspaceV1, correlation_id: UUID
    ) -> WorkspaceMutationResultV1:
        owner = str(owner_id)
        digest = _digest(command)
        replay = await self._replay(
            owner_id=owner,
            command_type="CREATE_WORKSPACE",
            idempotency_key=command.idempotency_key,
            digest=digest,
        )
        if replay is not None:
            return replay
        blockers = self._blockers(command.transition_guard)
        if blockers:
            return WorkspaceMutationResultV1(
                outcome="RECOVERY_REQUIRED",
                blockers=blockers,
                correlation_id=correlation_id,
            )
        active = await self.workspaces.list_active_for_owner(owner)
        selection = await self.selections.get(owner, for_update=True)
        actual = selection.version if selection else None
        if actual != command.expected_selection_version:
            self._version_conflict(actual, selection)
        try:
            async with self.db.begin_nested():
                workspace = await self.workspaces.create(
                    owner_id=owner,
                    display_name=command.display_name,
                    is_default=not active,
                )
        except IntegrityError as exc:
            replay_after_race = await self._replay(
                owner_id=owner,
                command_type="CREATE_WORKSPACE",
                idempotency_key=command.idempotency_key,
                digest=digest,
            )
            if replay_after_race is not None:
                return replay_after_race
            raise BusinessError(
                message="课程创建未能满足持久化完整性约束",
                error_code="WORKSPACE_INTEGRITY_FAILED",
                status_code=500,
                category="internal",
            ) from exc
        try:
            selected = await self.selections.set(
                owner_id=owner,
                current_workspace_id=workspace.workspace_id,
                reason="FIRST_CREATE" if not active else "EXPLICIT_SWITCH",
                correlation_id=str(correlation_id),
                expected_version=actual,
            )
        except WorkspaceSelectionVersionConflictError:
            replay_after_race = await self._replay(
                owner_id=owner,
                command_type="CREATE_WORKSPACE",
                idempotency_key=command.idempotency_key,
                digest=digest,
            )
            if replay_after_race is not None:
                return replay_after_race
            latest = await self.selections.get(owner)
            self._version_conflict(latest.version if latest else None, latest)
            raise AssertionError("unreachable")
        result = WorkspaceMutationResultV1(
            outcome="CREATED_AND_SELECTED",
            workspace=self._item(workspace, current_id=workspace.workspace_id),
            selection_ref=self._selection_ref(selected),
            selection_version=selected.version,
            correlation_id=correlation_id,
        )
        return await self._append_or_replay(
            owner_id=owner,
            command_type="CREATE_WORKSPACE",
            idempotency_key=command.idempotency_key,
            digest=digest,
            result=result,
        )

    async def switch(
        self, *, owner_id: UUID, command: SwitchWorkspaceV1, correlation_id: UUID
    ) -> WorkspaceMutationResultV1:
        owner = str(owner_id)
        digest = _digest(command)
        replay = await self._replay(
            owner_id=owner,
            command_type="SWITCH_WORKSPACE",
            idempotency_key=command.idempotency_key,
            digest=digest,
        )
        if replay is not None:
            return replay
        selection = await self.selections.get(owner, for_update=True)
        if selection is None:
            raise BusinessError(
                message="当前课程尚未选择",
                error_code="WORKSPACE_SELECTION_MISSING",
                status_code=404,
                category="not_found",
            )
        if selection.version != command.expected_selection_version:
            self._version_conflict(selection.version, selection)
        target = await self.workspaces.get_for_owner(owner, str(command.target_workspace_id))
        if target is None or target.lifecycle != "active":
            self._not_found()
            raise AssertionError("unreachable")
        blockers = self._blockers(command.transition_guard)
        if blockers:
            return WorkspaceMutationResultV1(
                outcome="RECOVERY_REQUIRED",
                selection_ref=self._selection_ref(selection),
                selection_version=selection.version,
                blockers=blockers,
                correlation_id=correlation_id,
            )
        preserved = await self._preserved(selection.current_workspace_id)
        if selection.current_workspace_id == target.workspace_id:
            result = WorkspaceMutationResultV1(
                outcome="ALREADY_CURRENT",
                workspace=self._item(target, current_id=target.workspace_id),
                selection_ref=self._selection_ref(selection),
                selection_version=selection.version,
                preserved=preserved,
                correlation_id=correlation_id,
            )
        else:
            try:
                selection = await self.selections.set(
                    owner_id=owner,
                    current_workspace_id=target.workspace_id,
                    reason="EXPLICIT_SWITCH",
                    correlation_id=str(correlation_id),
                    expected_version=command.expected_selection_version,
                )
            except WorkspaceSelectionVersionConflictError:
                replay_after_race = await self._replay(
                    owner_id=owner,
                    command_type="SWITCH_WORKSPACE",
                    idempotency_key=command.idempotency_key,
                    digest=digest,
                )
                if replay_after_race is not None:
                    return replay_after_race
                latest = await self.selections.get(owner)
                self._version_conflict(latest.version if latest else None, latest)
                raise AssertionError("unreachable")
            result = WorkspaceMutationResultV1(
                outcome="SWITCHED",
                workspace=self._item(target, current_id=target.workspace_id),
                selection_ref=self._selection_ref(selection),
                selection_version=selection.version,
                preserved=preserved,
                correlation_id=correlation_id,
            )
        return await self._append_or_replay(
            owner_id=owner,
            command_type="SWITCH_WORKSPACE",
            idempotency_key=command.idempotency_key,
            digest=digest,
            result=result,
        )

    async def rename(
        self, *, owner_id: UUID, workspace_id: UUID, command: RenameWorkspaceV1, correlation_id: UUID
    ) -> WorkspaceMutationResultV1:
        owner = str(owner_id)
        digest = _digest(command)
        replay = await self._replay(
            owner_id=owner,
            command_type="RENAME_WORKSPACE",
            idempotency_key=command.idempotency_key,
            digest=digest,
        )
        if replay is not None:
            return replay

        target = await self.workspaces.get_for_owner(owner, str(workspace_id))
        if target is None or target.lifecycle != "active":
            self._not_found()
            raise AssertionError("unreachable")

        try:
            async with self.db.begin_nested():
                workspace = await self.workspaces.rename(
                    workspace_id=str(workspace_id),
                    display_name=command.display_name,
                )
        except WorkspaceError:
            replay_after_race = await self._replay(
                owner_id=owner,
                command_type="RENAME_WORKSPACE",
                idempotency_key=command.idempotency_key,
                digest=digest,
            )
            if replay_after_race is not None:
                return replay_after_race
            raise

        selection = await self.selections.get(owner)
        result = WorkspaceMutationResultV1(
            outcome="SWITCHED",
            workspace=self._item(workspace, current_id=selection.current_workspace_id if selection else None),
            selection_ref=self._selection_ref(selection) if selection else None,
            selection_version=selection.version if selection else None,
            correlation_id=correlation_id,
        )
        return await self._append_or_replay(
            owner_id=owner,
            command_type="RENAME_WORKSPACE",
            idempotency_key=command.idempotency_key,
            digest=digest,
            result=result,
        )

    async def _append_or_replay(
        self,
        *,
        owner_id: str,
        command_type: str,
        idempotency_key: str,
        digest: str,
        result: WorkspaceMutationResultV1,
    ) -> WorkspaceMutationResultV1:
        try:
            receipt = await self.selections.append_receipt(
                owner_id=owner_id,
                command_type=command_type,
                idempotency_key=idempotency_key,
                command_digest=digest,
                response_payload=result.model_dump(mode="json"),
            )
        except WorkspaceIdempotencyConflictError as exc:
            raise BusinessError(
                message="幂等键已用于不同的课程操作",
                error_code="WORKSPACE_IDEMPOTENCY_CONFLICT",
                status_code=409,
                category="conflict",
            ) from exc
        return WorkspaceMutationResultV1.model_validate(receipt.response_payload)

    async def _replay(
        self, *, owner_id: str, command_type: str, idempotency_key: str, digest: str
    ) -> WorkspaceMutationResultV1 | None:
        receipt = await self.selections.get_receipt(
            owner_id=owner_id,
            command_type=command_type,
            idempotency_key=idempotency_key,
        )
        if receipt is None:
            return None
        if receipt.command_digest != digest:
            raise BusinessError(
                message="幂等键已用于不同的课程操作",
                error_code="WORKSPACE_IDEMPOTENCY_CONFLICT",
                status_code=409,
                category="conflict",
            )
        return WorkspaceMutationResultV1.model_validate(receipt.response_payload)

    async def _preserved(self, workspace_id: str) -> WorkspacePreservedRefsV1:
        sessions = (
            await self.db.scalars(
                select(LearningSession).where(
                    LearningSession.workspace_id == workspace_id,
                    LearningSession.status == LearningSessionStatus.ACTIVE,
                )
            )
        ).all()
        activity_ids = tuple(
            sorted(
                {
                    item.learning_activity_id
                    for item in sessions
                    if item.learning_activity_id is not None
                }
            )
        )
        activity_records = (
            (
                await self.db.scalars(
                    select(LearningActivityRecord).where(
                        LearningActivityRecord.id.in_(activity_ids)
                    )
                )
            ).all()
            if activity_ids
            else ()
        )
        by_id = {item.id: item for item in activity_records}
        return WorkspacePreservedRefsV1(
            activity_refs=tuple(
                f"learning_activity:{activity_id}:v{by_id[activity_id].plan_version}"
                for activity_id in activity_ids
                if activity_id in by_id
            ),
            learning_session_refs=tuple(f"learning_session:{item.session_id}" for item in sessions),
        )

    @staticmethod
    def _blockers(guard: WorkspaceTransitionGuardV1) -> tuple[WorkspaceSwitchBlockerV1, ...]:
        mapping: tuple[
            tuple[
                str,
                Literal["COMPOSER_DRAFT", "STREAM", "USER_NOTE", "MATERIAL_POSITION"],
                Literal["FRONTEND_PRESENTATION", "SYS08", "USER_NOTE_OWNER"],
            ],
            ...,
        ] = (
            (guard.composer_draft, "COMPOSER_DRAFT", "FRONTEND_PRESENTATION"),
            (guard.stream, "STREAM", "SYS08"),
            (guard.user_note, "USER_NOTE", "USER_NOTE_OWNER"),
            (guard.material_position, "MATERIAL_POSITION", "FRONTEND_PRESENTATION"),
        )
        return tuple(
            WorkspaceSwitchBlockerV1(
                kind=kind,
                owner=owner,
                allowed_actions=("PRESERVE", "SAVE", "BACKGROUND", "CANCEL", "DISCARD", "RETURN"),
                reason_code=f"{kind}_UNRESOLVED",
            )
            for value, kind, owner in mapping
            if value == "UNRESOLVED"
        )

    @staticmethod
    def _item(workspace: Workspace, *, current_id: str | None) -> WorkspaceItemV1:
        return WorkspaceItemV1(
            workspace_id=UUID(workspace.workspace_id),
            workspace_ref=f"workspace:{workspace.workspace_id}:v{workspace.version}",
            display_name=workspace.display_name,
            version=workspace.version,
            lifecycle=cast(Literal["active", "trash"], workspace.lifecycle),
            is_default=workspace.is_default,
            is_current=workspace.workspace_id == current_id,
            created_at=_aware(workspace.created_at),
            updated_at=_aware(workspace.updated_at),
        )

    @staticmethod
    def _selection_ref(selection: WorkspaceSelection) -> str:
        return f"workspace_selection:{selection.owner_id}:v{selection.version}"

    @staticmethod
    def _not_found() -> None:
        raise BusinessError(
            message="课程不存在或不可访问",
            error_code="WORKSPACE_NOT_FOUND_OR_INACCESSIBLE",
            status_code=404,
            category="not_found",
        )

    @classmethod
    def _version_conflict(cls, actual: int | None, selection: WorkspaceSelection | None) -> None:
        raise BusinessError(
            message="课程选择已更新，请刷新后重试",
            error_code="WORKSPACE_SELECTION_VERSION_CONFLICT",
            status_code=409,
            category="conflict",
            detail={
                "current_selection_version": actual,
                "current_selection_ref": cls._selection_ref(selection) if selection else None,
            },
        )
