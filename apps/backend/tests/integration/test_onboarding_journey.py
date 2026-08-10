"""SQLite owner-fact, preference and completion integration evidence."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.contracts.adaptive import VersionedRef
from app.contracts.onboarding import OnboardingPreferenceCommandV1
from app.core.database import Base
from app.core.exceptions import BusinessError
from app.models.book_learning import BookLearningTranscriptTurnRecord
from app.models.document import ModerationStatus, ProcessingStatus, UserDocument
from app.models.planning import (
    LearningActivityRecord,
    LearningActivityStateRecord,
    LearningGoalRecord,
    LearningPlanRecord,
)
from app.models.user import User
from app.queries.onboarding import (
    DataControlObservation,
    ModelConfigurationObservation,
    OnboardingJourneyQueryService,
    StaticDataControlQuery,
    StaticModelConfigurationQuery,
)
from app.services.onboarding import OnboardingPreferenceService
from app.services.owner.canonical_identity import canonical_user_id

NOW = datetime(2026, 8, 9, 13, 0, tzinfo=timezone.utc)


@pytest.fixture
async def sqlite_factory(tmp_path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'onboarding.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


def _user() -> User:
    return User(
        id=str(uuid4()),
        pseudonym_id=uuid4().hex,
    )


def _query(session) -> OnboardingJourneyQueryService:
    return OnboardingJourneyQueryService(
        session,
        model_configuration=StaticModelConfigurationQuery(
            ModelConfigurationObservation(
                availability="AVAILABLE",
                state="ACTIVE",
                revision=3,
                runtime_ready=True,
                runtime_revision=3,
                verified_at=NOW,
                source_ref="ModelRouteProfile:3",
            )
        ),
        data_control=StaticDataControlQuery(
            DataControlObservation(
                availability="AVAILABLE",
                route="/settings/data",
                source_ref="DataControlCapability:1",
            )
        ),
        clock=lambda: NOW,
    )


@pytest.mark.asyncio
async def test_new_user_journey_uses_owner_facts_and_single_next_action(sqlite_factory) -> None:
    async with sqlite_factory() as session:
        user = _user()
        session.add(user)
        await session.flush()
        view = await _query(session).get_journey(user, correlation_id="journey-1")
        assert view.preference.visibility == "ACTIVE"
        assert view.steps[0].state == "COMPLETE"
        assert view.steps[1].state == "NOT_STARTED"
        assert view.next_action.action_code == "ACKNOWLEDGE_BOUNDARIES"
        assert view.should_enter_welcome is True

        command = OnboardingPreferenceCommandV1(
            expected_preference_version=1,
            action="ACKNOWLEDGE_BOUNDARIES",
            notice_version="privacy-and-model-v1",
            idempotency_key="ack-1",
        )
        service = OnboardingPreferenceService(session, journey_query=_query(session))
        acknowledged = await service.apply(user=user, command=command, correlation_id="journey-2")
        replay = await service.apply(user=user, command=command, correlation_id="journey-3")
        assert acknowledged.preference.preference_version == 2
        assert replay.preference.preference_version == 2
        assert replay.next_action.action_code == "OPEN_LIBRARY"


@pytest.mark.asyncio
async def test_first_activity_requires_latest_completed_state_and_transcript_ref(
    sqlite_factory,
) -> None:
    async with sqlite_factory() as session:
        user = _user()
        document_id, goal_id, plan_id, activity_id = uuid4(), uuid4(), uuid4(), uuid4()
        owner_id = canonical_user_id(user.id)
        session.add(user)
        await session.flush()
        session.add_all(
            [
                UserDocument(
                    id=str(document_id),
                    pseudonym_id=user.pseudonym_id,
                    original_filename="private.epub",
                    file_extension=".epub",
                    file_size_bytes=100,
                    storage_path="managed/private.epub",
                    processing_status=ProcessingStatus.COMPLETED,
                    moderation_status=ModerationStatus.APPROVED,
                ),
                LearningGoalRecord(
                    id=f"{goal_id}:1",
                    goal_id=str(goal_id),
                    user_id=str(owner_id),
                    version=1,
                    status="active",
                    idempotency_key="goal-1",
                    payload={
                        "goal_id": str(goal_id),
                        "version": 1,
                        "user_id": str(owner_id),
                        "title": "理解资料",
                        "topic": "资料",
                        "target_capabilities": ["理解"],
                        "success_criteria": ["完成第一节"],
                        "source_document_ids": [str(document_id)],
                        "status": "active",
                        "confirmed_by_user": True,
                        "created_at": NOW.isoformat(),
                        "confirmed_at": NOW.isoformat(),
                        "reason_codes": ["TEST"],
                    },
                ),
                LearningPlanRecord(
                    id=f"{plan_id}:1",
                    plan_id=str(plan_id),
                    learning_goal_id=str(goal_id),
                    idempotency_key="plan-1",
                    version=1,
                    status="active",
                    payload={},
                ),
                LearningActivityRecord(
                    id=str(activity_id),
                    plan_id=str(plan_id),
                    plan_version=1,
                    priority=1,
                    payload={"title": "第一节", "type": "learn_new"},
                ),
                LearningActivityStateRecord(
                    id=f"{activity_id}:1",
                    activity_id=str(activity_id),
                    version=1,
                    plan_id=str(plan_id),
                    plan_version=1,
                    status="completed",
                    previous_status="active",
                    transition_reason="INVALID_TEST_TRANSITION",
                    source_refs=[
                        VersionedRef(
                            entity_type="BookLearningTranscriptTurn",
                            entity_id="turn-1",
                            version=1,
                        ).model_dump(mode="json")
                    ],
                    actor_type="learner",
                    completed_at=NOW,
                    correlation_id=str(uuid4()),
                    created_at=NOW,
                ),
                BookLearningTranscriptTurnRecord(
                    turn_record_id=str(uuid4()),
                    user_id=str(owner_id),
                    goal_id=str(goal_id),
                    plan_id=str(plan_id),
                    plan_version=1,
                    activity_id=str(activity_id),
                    session_id=str(uuid4()),
                    turn_id="turn-1",
                    turn_number=1,
                    turn_kind="learner",
                    idempotency_key="turn-1",
                    learner_text="我的理解",
                    response_payload={},
                    created_at=NOW,
                ),
            ]
        )
        await session.flush()

        invalid = await _query(session).get_journey(user, correlation_id="invalid-source")
        assert invalid.steps[3].state != "COMPLETE"

        transcript_ref = VersionedRef(
            entity_type="BookLearningTranscriptTurn",
            entity_id="turn-1",
            version=1,
        )
        session.add_all(
            [
                LearningActivityStateRecord(
                    id=f"{activity_id}:2",
                    activity_id=str(activity_id),
                    version=2,
                    plan_id=str(plan_id),
                    plan_version=1,
                    status="completed",
                    previous_status="active",
                    transition_reason="LEARNER_FINISHED_TRANSCRIPT_BACKED_ACTIVITY",
                    source_refs=[transcript_ref.model_dump(mode="json")],
                    actor_type="learner",
                    completed_at=NOW,
                    correlation_id=str(uuid4()),
                    created_at=NOW,
                ),
            ]
        )
        await session.flush()
        complete = await _query(session).get_journey(user, correlation_id="valid-source")
        assert complete.steps[3].state == "COMPLETE"
        assert complete.next_action.action_code == "ACKNOWLEDGE_BOUNDARIES"


@pytest.mark.asyncio
async def test_goal_without_current_eligible_material_mapping_is_stale(
    sqlite_factory,
) -> None:
    async with sqlite_factory() as session:
        user = _user()
        eligible_document_id = str(uuid4())
        goal_id = str(uuid4())
        session.add(user)
        await session.flush()
        session.add_all(
            [
                UserDocument(
                    id=eligible_document_id,
                    pseudonym_id=user.pseudonym_id,
                    original_filename="eligible.epub",
                    file_extension=".epub",
                    file_size_bytes=100,
                    storage_path="managed/eligible.epub",
                    processing_status=ProcessingStatus.COMPLETED,
                    moderation_status=ModerationStatus.APPROVED,
                ),
                LearningGoalRecord(
                    id=f"{goal_id}:1",
                    goal_id=goal_id,
                    user_id=str(canonical_user_id(user.id)),
                    version=1,
                    status="active",
                    idempotency_key="stale-goal-mapping",
                    payload={
                        "confirmed_by_user": True,
                        "source_document_ids": [str(uuid4())],
                    },
                ),
            ]
        )
        await session.flush()
        view = await _query(session).get_journey(user, correlation_id="stale-goal-mapping")
        assert view.steps[1].state == "COMPLETE"
        assert view.steps[2].state == "STALE"
        assert view.steps[2].source_status[0].reason_codes == ("GOAL_SOURCE_MAPPING_UNAVAILABLE",)


@pytest.mark.asyncio
async def test_dismiss_is_presentation_only_and_reopen_requeries_facts(sqlite_factory) -> None:
    async with sqlite_factory() as session:
        user = _user()
        session.add(user)
        await session.flush()
        query = _query(session)
        first = await query.get_journey(user, correlation_id="first")
        service = OnboardingPreferenceService(session, journey_query=query)
        dismissed = await service.apply(
            user=user,
            command=OnboardingPreferenceCommandV1(
                expected_preference_version=first.preference.preference_version,
                action="DISMISS",
                idempotency_key="dismiss-1",
            ),
            correlation_id="dismiss",
        )
        assert dismissed.preference.visibility == "DISMISSED"
        assert dismissed.should_enter_welcome is False
        assert dismissed.steps[1].state == "NOT_STARTED"
        reopened = await service.apply(
            user=user,
            command=OnboardingPreferenceCommandV1(
                expected_preference_version=dismissed.preference.preference_version,
                action="REOPEN",
                idempotency_key="reopen-1",
            ),
            correlation_id="reopen",
        )
        assert reopened.preference.visibility == "ACTIVE"
        assert reopened.steps[1].state == "NOT_STARTED"


@pytest.mark.asyncio
async def test_concurrent_preference_commands_conflict_instead_of_last_write_wins(
    sqlite_factory,
) -> None:
    async with sqlite_factory() as setup:
        user = _user()
        setup.add(user)
        await setup.commit()
        await _query(setup).get_journey(user, correlation_id="seed")
        await setup.commit()
        user_id = user.id

    async def apply(command: OnboardingPreferenceCommandV1) -> tuple[str, int | str]:
        async with sqlite_factory() as session:
            current_user = await session.get(User, user_id)
            assert current_user is not None
            try:
                view = await OnboardingPreferenceService(
                    session, journey_query=_query(session)
                ).apply(
                    user=current_user,
                    command=command,
                    correlation_id=command.idempotency_key,
                )
                await session.commit()
                return ("ok", view.preference.preference_version)
            except BusinessError as exc:
                await session.rollback()
                return ("error", exc.error_code)

    results = await asyncio.gather(
        apply(
            OnboardingPreferenceCommandV1(
                expected_preference_version=1,
                action="DISMISS",
                idempotency_key="concurrent-dismiss",
            )
        ),
        apply(
            OnboardingPreferenceCommandV1(
                expected_preference_version=1,
                action="ACKNOWLEDGE_BOUNDARIES",
                notice_version="privacy-and-model-v1",
                idempotency_key="concurrent-ack",
            )
        ),
    )
    assert sorted(results) == [
        ("error", "ONBOARDING_PREFERENCE_VERSION_CONFLICT"),
        ("ok", 2),
    ]


@pytest.mark.asyncio
async def test_idempotency_receipt_survives_session_restart_and_rejects_new_payload(
    sqlite_factory,
) -> None:
    user = _user()
    command = OnboardingPreferenceCommandV1(
        expected_preference_version=1,
        action="DISMISS",
        idempotency_key="restart-dismiss",
    )
    async with sqlite_factory() as first_session:
        first_session.add(user)
        await first_session.flush()
        first = await OnboardingPreferenceService(
            first_session, journey_query=_query(first_session)
        ).apply(user=user, command=command, correlation_id="first-process")
        assert first.preference.preference_version == 2
        await first_session.commit()
        user_id = user.id

    async with sqlite_factory() as restarted_session:
        restarted_user = await restarted_session.get(User, user_id)
        assert restarted_user is not None
        service = OnboardingPreferenceService(
            restarted_session, journey_query=_query(restarted_session)
        )
        replay = await service.apply(
            user=restarted_user,
            command=command,
            correlation_id="restarted-process",
        )
        assert replay.preference.preference_version == 2
        with pytest.raises(BusinessError) as error:
            await service.apply(
                user=restarted_user,
                command=OnboardingPreferenceCommandV1(
                    expected_preference_version=2,
                    action="REOPEN",
                    idempotency_key="restart-dismiss",
                ),
                correlation_id="different-payload",
            )
        assert error.value.error_code == "ONBOARDING_PREFERENCE_VERSION_CONFLICT"


@pytest.mark.asyncio
async def test_journey_does_not_expose_another_users_material(sqlite_factory) -> None:
    async with sqlite_factory() as session:
        current_user = _user()
        other_user = _user()
        foreign_document_id = str(uuid4())
        session.add_all([current_user, other_user])
        await session.flush()
        session.add_all(
            [
                UserDocument(
                    id=foreign_document_id,
                    pseudonym_id=other_user.pseudonym_id,
                    original_filename="other.epub",
                    file_extension=".epub",
                    file_size_bytes=100,
                    storage_path="managed/other.epub",
                    processing_status=ProcessingStatus.COMPLETED,
                    moderation_status=ModerationStatus.APPROVED,
                ),
            ]
        )
        await session.flush()
        view = await _query(session).get_journey(current_user, correlation_id="cross-user")
        assert view.steps[1].state == "NOT_STARTED"
        assert foreign_document_id not in view.model_dump_json()


@pytest.mark.asyncio
async def test_unavailable_owner_ports_are_partial_and_do_not_force_welcome(
    sqlite_factory,
) -> None:
    async with sqlite_factory() as session:
        user = _user()
        session.add(user)
        await session.flush()
        view = await OnboardingJourneyQueryService(session, clock=lambda: NOW).get_journey(
            user, correlation_id="dependency-partial"
        )
        assert view.journey_state == "PARTIAL"
        assert view.should_enter_welcome is False
        assert view.steps[0].source_status[0].reason_codes == (
            "MODEL_CONFIGURATION_QUERY_UNAVAILABLE",
        )


@pytest.mark.asyncio
async def test_stale_model_projection_is_not_reported_ready(sqlite_factory) -> None:
    async with sqlite_factory() as session:
        user = _user()
        session.add(user)
        await session.flush()
        query = OnboardingJourneyQueryService(
            session,
            model_configuration=StaticModelConfigurationQuery(
                ModelConfigurationObservation(
                    availability="STALE",
                    state="ACTIVE",
                    revision=3,
                    runtime_ready=True,
                    runtime_revision=3,
                    verified_at=NOW,
                    source_ref="ModelRouteProfile:3",
                    reason_codes=("MODEL_RUNTIME_VERIFICATION_STALE",),
                )
            ),
            data_control=StaticDataControlQuery(
                DataControlObservation(
                    availability="AVAILABLE",
                    route="/settings/data",
                    source_ref="DataControlCapability:1",
                )
            ),
            clock=lambda: NOW,
        )
        view = await query.get_journey(user, correlation_id="stale-model")
        assert view.journey_state == "STALE"
        assert view.steps[0].state == "STALE"
        assert view.next_action.action_code == "ACKNOWLEDGE_BOUNDARIES"


@pytest.mark.asyncio
async def test_concurrent_first_query_creates_one_active_preference(sqlite_factory) -> None:
    async with sqlite_factory() as setup:
        user = _user()
        setup.add(user)
        await setup.commit()
        user_id = user.id

    async def read() -> tuple[int, str]:
        async with sqlite_factory() as session:
            current_user = await session.get(User, user_id)
            assert current_user is not None
            view = await _query(session).get_journey(current_user, correlation_id=uuid4().hex)
            await session.commit()
            return view.preference.preference_version, view.preference.visibility

    assert await asyncio.gather(read(), read()) == [(1, "ACTIVE"), (1, "ACTIVE")]
    async with sqlite_factory() as verify:
        from sqlalchemy import func, select

        from app.models.onboarding import OnboardingPreferenceRecord

        count = await verify.scalar(
            select(func.count(OnboardingPreferenceRecord.preference_id)).where(
                OnboardingPreferenceRecord.user_id == user_id
            )
        )
        assert count == 1
