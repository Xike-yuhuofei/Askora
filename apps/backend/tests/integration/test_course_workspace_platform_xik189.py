"""XIK-189 real-SQLite integration coverage for ADR-0023 / CWSP-* contracts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.contracts.activity_lifecycle import LearningActivityStateV1
from app.contracts.learning import LearningActivity, LearningPlan
from app.contracts.workspace import (
    CreateWorkspaceV1,
    SwitchWorkspaceV1,
    WorkspaceTransitionGuardV1,
)
from app.core.exceptions import BusinessError
from app.infrastructure.activity_lifecycle import ActivityLifecycleRepository
from app.models.dialog import DialogSession
from app.models.planning import LearningActivityRecord, LearningGoalRecord, LearningPlanRecord
from app.models.workspace import (
    LearningSession,
    Workspace,
    WorkspaceCommandReceipt,
    WorkspaceSelection,
)
from app.queries.workspace import CourseActivityIndexQueryService
from app.services.local_identity import ensure_local_owner
from app.services.workspace.bootstrap import WorkspaceBootstrapService
from app.services.workspace.repository import (
    CrossWorkspaceReferenceError,
    WorkspaceNotFoundError,
)
from app.services.workspace.selection import WorkspaceSelectionService
from app.services.workspace.service import WorkspaceService

NOW = datetime(2026, 8, 11, 14, 0, tzinfo=timezone.utc)


def _guard(**changes: str) -> WorkspaceTransitionGuardV1:
    values = {
        "composer_draft": "CLEAR",
        "stream": "CLEAR",
        "user_note": "CLEAR",
        "material_position": "PRESERVED",
    }
    values.update(changes)
    return WorkspaceTransitionGuardV1.model_validate(values)


async def _owner(session) -> UUID:
    context = await ensure_local_owner(session)
    await session.commit()
    return context.owner_id


def _create_command(
    name: str,
    *,
    expected: int | None,
    key: str,
    guard: WorkspaceTransitionGuardV1 | None = None,
) -> CreateWorkspaceV1:
    return CreateWorkspaceV1(
        display_name=name,
        expected_selection_version=expected,
        transition_guard=guard or _guard(),
        idempotency_key=key,
    )


async def test_cwsp_ac001_fresh_list_is_empty_and_zero_write(sqlite_factory) -> None:
    """CWSP-AC-001/006: fresh read truth is EMPTY and creates no business row."""
    async with sqlite_factory() as session:
        owner_id = await _owner(session)
        service = WorkspaceSelectionService(session, clock=lambda: NOW)

        first = await service.list(owner_id=owner_id, correlation_id=uuid4())
        second = await service.list(owner_id=owner_id, correlation_id=uuid4())

        assert first.data.view_state == second.data.view_state == "EMPTY"
        assert first.data.workspaces == ()
        assert await session.scalar(select(func.count(Workspace.workspace_id))) == 0
        assert await session.scalar(select(func.count(WorkspaceSelection.owner_id))) == 0
        assert await session.scalar(select(func.count(WorkspaceCommandReceipt.receipt_id))) == 0


async def test_cwsp_ac002_runtime_reconciliation_distinguishes_fresh_and_legacy(
    sqlite_factory,
) -> None:
    """CWSP-070: fresh stays empty; real legacy business data gets one default+selection."""
    async with sqlite_factory() as session:
        context = await ensure_local_owner(session)
        await session.commit()
        bootstrap = WorkspaceBootstrapService(session)

        fresh = await bootstrap.reconcile_course_workspace(context.canonical_owner_id)
        assert fresh.workspace_id is None
        assert await session.scalar(select(func.count(Workspace.workspace_id))) == 0

        from app.models.user import User

        compatibility_user = await session.get(User, context.canonical_owner_id)
        assert compatibility_user is not None
        legacy = DialogSession(
            id=str(uuid4()),
            user_id=context.canonical_owner_id,
            pseudonym_id=compatibility_user.pseudonym_id,
            workspace_id=None,
            title="legacy",
        )
        session.add(legacy)
        await session.commit()

        migrated = await bootstrap.reconcile_course_workspace(context.canonical_owner_id)
        await session.commit()
        await session.refresh(legacy)
        assert migrated.workspace_id is not None
        assert legacy.workspace_id == migrated.workspace_id
        selection = await session.get(WorkspaceSelection, context.canonical_owner_id)
        assert selection is not None
        assert selection.current_workspace_id == migrated.workspace_id

        rerun = await bootstrap.reconcile_course_workspace(context.canonical_owner_id)
        await session.commit()
        assert rerun.workspace_id == migrated.workspace_id
        assert await session.scalar(select(func.count(Workspace.workspace_id))) == 1
        assert await session.scalar(select(func.count(WorkspaceSelection.owner_id))) == 1


async def test_cwsp_create_select_cas_idempotency_and_no_orphan(sqlite_factory) -> None:
    """CWSP-AC-004: first/subsequent create are atomic, versioned and idempotent."""
    async with sqlite_factory() as session:
        owner_id = await _owner(session)
        service = WorkspaceSelectionService(session, clock=lambda: NOW)

        first_command = _create_command("课程 A", expected=None, key="create-a")
        first = await service.create(
            owner_id=owner_id, command=first_command, correlation_id=uuid4()
        )
        await session.commit()
        assert first.outcome == "CREATED_AND_SELECTED"
        assert first.selection_version == 1
        assert first.workspace is not None and first.workspace.is_default is True

        replay = await service.create(
            owner_id=owner_id, command=first_command, correlation_id=uuid4()
        )
        assert replay == first
        assert await session.scalar(select(func.count(Workspace.workspace_id))) == 1

        with pytest.raises(BusinessError) as different_digest:
            await service.create(
                owner_id=owner_id,
                command=_create_command("不同课程", expected=None, key="create-a"),
                correlation_id=uuid4(),
            )
        assert different_digest.value.error_code == "WORKSPACE_IDEMPOTENCY_CONFLICT"

        second = await service.create(
            owner_id=owner_id,
            command=_create_command("课程 B", expected=1, key="create-b"),
            correlation_id=uuid4(),
        )
        await session.commit()
        assert second.selection_version == 2
        assert second.workspace is not None and second.workspace.is_default is False

        count_before = await session.scalar(select(func.count(Workspace.workspace_id)))
        with pytest.raises(BusinessError) as stale:
            await service.create(
                owner_id=owner_id,
                command=_create_command("不应创建", expected=1, key="create-stale"),
                correlation_id=uuid4(),
            )
        assert stale.value.error_code == "WORKSPACE_SELECTION_VERSION_CONFLICT"
        assert await session.scalar(select(func.count(Workspace.workspace_id))) == count_before

        listing = await service.list(owner_id=owner_id, correlation_id=uuid4())
        assert [item.display_name for item in listing.data.workspaces] == ["课程 B", "课程 A"]
        assert listing.data.selection_version == 2


@pytest.mark.parametrize(
    ("field", "kind"),
    [
        ("composer_draft", "COMPOSER_DRAFT"),
        ("stream", "STREAM"),
        ("user_note", "USER_NOTE"),
        ("material_position", "MATERIAL_POSITION"),
    ],
)
async def test_cwsp_ac005_every_unresolved_guard_is_zero_write(
    sqlite_factory, field: str, kind: str
) -> None:
    """CWSP-023/030: every unresolved client work kind blocks before persistence."""
    async with sqlite_factory() as session:
        owner_id = await _owner(session)
        service = WorkspaceSelectionService(session)
        result = await service.create(
            owner_id=owner_id,
            command=_create_command(
                "Blocked",
                expected=None,
                key=f"blocked-{field}",
                guard=_guard(**{field: "UNRESOLVED"}),
            ),
            correlation_id=uuid4(),
        )
        assert result.outcome == "RECOVERY_REQUIRED"
        assert [blocker.kind for blocker in result.blockers] == [kind]
        assert await session.scalar(select(func.count(Workspace.workspace_id))) == 0
        assert await session.scalar(select(func.count(WorkspaceSelection.owner_id))) == 0
        assert await session.scalar(select(func.count(WorkspaceCommandReceipt.receipt_id))) == 0


async def test_cwsp_switch_preserves_session_and_foreign_ids_do_not_leak(sqlite_factory) -> None:
    """CWSP-AC-005/007: switch preserves source work; foreign owner gets same 404 code."""
    async with sqlite_factory() as session:
        owner_id = await _owner(session)
        selection_service = WorkspaceSelectionService(session)
        first = await selection_service.create(
            owner_id=owner_id,
            command=_create_command("A", expected=None, key="a"),
            correlation_id=uuid4(),
        )
        second = await selection_service.create(
            owner_id=owner_id,
            command=_create_command("B", expected=1, key="b"),
            correlation_id=uuid4(),
        )
        assert first.workspace is not None and second.workspace is not None
        source_session = await WorkspaceService(session).create_session(
            workspace_id=str(second.workspace.workspace_id)
        )
        await session.commit()

        switched = await selection_service.switch(
            owner_id=owner_id,
            command=SwitchWorkspaceV1(
                target_workspace_id=first.workspace.workspace_id,
                expected_selection_version=2,
                transition_guard=_guard(),
                idempotency_key="switch-a",
            ),
            correlation_id=uuid4(),
        )
        await session.commit()
        assert switched.outcome == "SWITCHED"
        assert switched.selection_version == 3
        assert f"learning_session:{source_session.session_id}" in (
            switched.preserved.learning_session_refs
        )
        persisted = await session.get(LearningSession, source_session.session_id)
        assert persisted is not None and persisted.status == "active"

        already = await selection_service.switch(
            owner_id=owner_id,
            command=SwitchWorkspaceV1(
                target_workspace_id=first.workspace.workspace_id,
                expected_selection_version=3,
                transition_guard=_guard(),
                idempotency_key="already-a",
            ),
            correlation_id=uuid4(),
        )
        assert already.outcome == "ALREADY_CURRENT"
        assert already.selection_version == 3

        with pytest.raises(BusinessError) as foreign:
            await selection_service.get(
                owner_id=uuid4(),
                workspace_id=first.workspace.workspace_id,
                correlation_id=uuid4(),
            )
        assert foreign.value.error_code == "WORKSPACE_NOT_FOUND_OR_INACCESSIBLE"
        assert first.workspace.display_name not in foreign.value.message


async def test_cwsp_canonical_http_surface_has_no_hidden_get_writes(sqlite_factory) -> None:
    """API-320/CWSP-034: real ASGI requests prove create/switch and read purity."""
    from httpx import ASGITransport, AsyncClient

    from app.core.database import get_db
    from app.main import app as fastapi_app

    async with sqlite_factory() as session:
        await _owner(session)

        async def override_db():
            yield session

        fastapi_app.dependency_overrides[get_db] = override_db
        try:
            transport = ASGITransport(app=fastapi_app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                empty = await client.get("/api/v1/workspaces")
                assert empty.status_code == 200
                assert empty.json()["data"]["view_state"] == "EMPTY"

                first = await client.post(
                    "/api/v1/workspaces",
                    json=_create_command("HTTP A", expected=None, key="http-a").model_dump(
                        mode="json"
                    ),
                )
                assert first.status_code == 200, first.text
                first_id = first.json()["workspace"]["workspace_id"]
                second = await client.post(
                    "/api/v1/workspaces",
                    json=_create_command("HTTP B", expected=1, key="http-b").model_dump(
                        mode="json"
                    ),
                )
                assert second.status_code == 200, second.text

                version_before = await session.scalar(select(WorkspaceSelection.version).limit(1))
                receipts_before = await session.scalar(
                    select(func.count(WorkspaceCommandReceipt.receipt_id))
                )
                for path in (
                    "/api/v1/workspaces",
                    "/api/v1/workspaces/current",
                    f"/api/v1/workspaces/{first_id}",
                    f"/api/v1/workspaces/{first_id}/activities",
                ):
                    response = await client.get(path)
                    assert response.status_code == 200, response.text
                    assert response.headers["cache-control"] == "private, no-store"
                assert await session.scalar(select(WorkspaceSelection.version).limit(1)) == (
                    version_before
                )
                assert (
                    await session.scalar(select(func.count(WorkspaceCommandReceipt.receipt_id)))
                    == receipts_before
                )

                switched = await client.post(
                    f"/api/v1/workspaces/{first_id}/switch",
                    json=SwitchWorkspaceV1(
                        target_workspace_id=UUID(first_id),
                        expected_selection_version=2,
                        transition_guard=_guard(),
                        idempotency_key="http-switch-a",
                    ).model_dump(mode="json"),
                )
                assert switched.status_code == 200, switched.text
                assert switched.json()["outcome"] == "SWITCHED"
                assert switched.json()["selection_version"] == 3

                foreign = await client.get(f"/api/v1/workspaces/{uuid4()}")
                assert foreign.status_code == 404
                assert foreign.json()["error"]["code"] == ("WORKSPACE_NOT_FOUND_OR_INACCESSIBLE")
        finally:
            fastapi_app.dependency_overrides.clear()


async def _seed_activity_plan(session, workspace_id: str):
    goal_id = uuid4()
    plan_id = uuid4()
    objective_id = uuid4()
    activity_ids = (uuid4(), uuid4(), uuid4())
    session.add(
        LearningGoalRecord(
            id=f"{goal_id}:1",
            goal_id=str(goal_id),
            user_id=str(uuid4()),
            workspace_id=workspace_id,
            version=1,
            status="active",
            idempotency_key=f"goal-{goal_id}",
            payload={},
            created_at=NOW,
        )
    )
    plan = LearningPlan(
        plan_id=plan_id,
        version=1,
        learning_goal_id=goal_id,
        planning_horizon={},
        objective_ids=[objective_id],
        activity_ids=list(activity_ids),
        constraints={},
        assumptions={},
        created_from_learner_state_version=0,
        knowledge_graph_version="kg-1",
        reason_codes=["TEST_FIXTURE"],
        status="active",
    )
    session.add(
        LearningPlanRecord(
            id=f"{plan_id}:1",
            plan_id=str(plan_id),
            learning_goal_id=str(goal_id),
            idempotency_key=f"plan-{plan_id}",
            version=1,
            status="active",
            payload=plan.model_dump(mode="json"),
            created_at=NOW,
        )
    )
    activity_types = ("practice", "diagnostic", "delayed_review")
    for order, (activity_id, activity_type) in enumerate(
        zip(activity_ids, activity_types, strict=True)
    ):
        activity = LearningActivity(
            activity_id=activity_id,
            plan_id=plan_id,
            plan_version=1,
            objective_id=objective_id,
            type=activity_type,
            knowledge_unit_ids=[uuid4()],
            estimated_duration_minutes=10,
            priority=float(3 - order),
            reason_codes=["TEST_FIXTURE"],
            status="available",
        )
        session.add(
            LearningActivityRecord(
                id=str(activity_id),
                plan_id=str(plan_id),
                plan_version=1,
                priority=activity.priority,
                payload=activity.model_dump(mode="json"),
                created_at=NOW + timedelta(minutes=order),
            )
        )
    await session.flush()
    lifecycle = ActivityLifecycleRepository(session)
    states = []
    for order, (activity_id, status) in enumerate(
        zip(activity_ids, ("active", "available", "completed"), strict=True)
    ):
        states.append(
            await lifecycle.append(
                LearningActivityStateV1(
                    activity_id=activity_id,
                    version=1,
                    plan_id=plan_id,
                    plan_version=1,
                    status=status,
                    transition_reason="TEST_FIXTURE",
                    actor_type="system",
                    started_at=NOW + timedelta(minutes=order) if status == "active" else None,
                    completed_at=NOW + timedelta(minutes=order) if status == "completed" else None,
                    correlation_id=uuid4(),
                    created_at=NOW + timedelta(minutes=order),
                )
            )
        )
    return goal_id, plan_id, activity_ids, states


async def test_cwsp_activity_index_exact_order_and_session_scope(sqlite_factory) -> None:
    """CWSP-AC-008..010: exact SYS06 projection and Activity-scoped Session binding."""
    async with sqlite_factory() as session:
        owner_id = await _owner(session)
        created = await WorkspaceSelectionService(session).create(
            owner_id=owner_id,
            command=_create_command("学习课程", expected=None, key="course"),
            correlation_id=uuid4(),
        )
        assert created.workspace is not None
        workspace_id = str(created.workspace.workspace_id)
        goal_id, plan_id, activity_ids, states = await _seed_activity_plan(session, workspace_id)
        learning_session = await WorkspaceService(session).create_session(
            workspace_id=workspace_id,
            learning_activity_id=str(activity_ids[0]),
            learning_goal_id=str(goal_id),
        )
        await session.commit()

        workspace = await session.get(Workspace, workspace_id)
        assert workspace is not None
        query = CourseActivityIndexQueryService(session, clock=lambda: NOW)
        first = await query.get(workspace=workspace, correlation_id=uuid4())
        second = await query.get(workspace=workspace, correlation_id=uuid4())
        assert first.data.view_state == "READY"
        assert [item.status for item in first.data.activities] == [
            "active",
            "available",
            "completed",
        ]
        assert first.data.resumable_activity_ref == first.data.activities[0].activity_ref
        assert first.data.activities[1].launch_state == "REQUIRES_START_COMMAND"
        assert first.data.activities[0].title_source_ref.endswith("course-activity-title/1.0")
        assert f"learning_session:{learning_session.session_id}" in (
            first.data.activities[0].learning_session_refs
        )
        assert first.data.activities == second.data.activities

        other = await WorkspaceSelectionService(session).create(
            owner_id=owner_id,
            command=_create_command("另一课程", expected=1, key="other-course"),
            correlation_id=uuid4(),
        )
        assert other.workspace is not None
        with pytest.raises(CrossWorkspaceReferenceError):
            await WorkspaceService(session).create_session(
                workspace_id=str(other.workspace.workspace_id),
                learning_activity_id=str(activity_ids[0]),
            )
        with pytest.raises(WorkspaceNotFoundError):
            await WorkspaceService(session).create_session(
                workspace_id=workspace_id,
                learning_activity_id=str(uuid4()),
            )

        await ActivityLifecycleRepository(session).append(
            LearningActivityStateV1(
                activity_id=activity_ids[1],
                version=2,
                plan_id=plan_id,
                plan_version=1,
                status="active",
                previous_status=states[1].status,
                transition_reason="TEST_MULTIPLE_ACTIVE",
                actor_type="system",
                started_at=NOW + timedelta(hours=1),
                correlation_id=uuid4(),
                created_at=NOW + timedelta(hours=1),
            )
        )
        partial = await query.get(workspace=workspace, correlation_id=uuid4())
        assert partial.data.view_state == "PARTIAL"
        assert "MULTIPLE_ACTIVE_ACTIVITIES" in partial.data.reason_codes
        assert partial.data.resumable_activity_ref is None
