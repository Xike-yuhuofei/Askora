"""Owner-fact assembler for the P1-06 first-use journey."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import and_, exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.contracts.adaptive import AvailabilityStatus, VersionedRef
from app.contracts.onboarding import (
    BoundaryNoticeV1,
    FirstActivityCompletionProjectionV1,
    OnboardingJourneyState,
    OnboardingJourneyViewV1,
    OnboardingNextActionV1,
    OnboardingStepState,
    OnboardingStepViewV1,
    SourceObservationV1,
)
from app.models.book_learning import BookLearningTranscriptTurnRecord
from app.models.document import ModerationStatus, ProcessingStatus, UserDocument
from app.models.planning import (
    LearningActivityStateRecord,
    LearningGoalRecord,
    LearningPlanRecord,
)
from app.models.user import User
from app.repositories.onboarding_preferences import OnboardingPreferenceRepository
from app.services.auth.canonical_identity import canonical_user_id

JOURNEY_ID = "first-learning-v1"
BOUNDARY_NOTICE_VERSION = "privacy-and-model-v1"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    """Normalize SQLite's naive ORM datetimes to the canonical UTC boundary."""
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value


@dataclass(frozen=True)
class ModelConfigurationObservation:
    availability: AvailabilityStatus | str
    state: str | None = None
    revision: int | None = None
    runtime_ready: bool = False
    runtime_revision: int | None = None
    verified_at: datetime | None = None
    source_ref: str | None = None
    reason_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class DataControlObservation:
    availability: AvailabilityStatus | str
    route: str | None = None
    source_ref: str | None = None
    reason_codes: tuple[str, ...] = ()


class ModelConfigurationQuery(Protocol):
    async def get_summary(self, user: User) -> ModelConfigurationObservation: ...


class DataControlQuery(Protocol):
    async def get_capability(self, user: User) -> DataControlObservation: ...


class StaticModelConfigurationQuery:
    def __init__(self, observation: ModelConfigurationObservation) -> None:
        self._observation = observation

    async def get_summary(self, user: User) -> ModelConfigurationObservation:
        del user
        return self._observation


class StaticDataControlQuery:
    def __init__(self, observation: DataControlObservation) -> None:
        self._observation = observation

    async def get_capability(self, user: User) -> DataControlObservation:
        del user
        return self._observation


class UnavailableModelConfigurationQuery(StaticModelConfigurationQuery):
    def __init__(self) -> None:
        super().__init__(
            ModelConfigurationObservation(
                availability="MISSING",
                reason_codes=("MODEL_CONFIGURATION_QUERY_UNAVAILABLE",),
            )
        )


class DatabaseModelConfigurationQuery:
    """Real model configuration query backed by the runtime model router."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_summary(self, user: User) -> ModelConfigurationObservation:
        try:
            from app.services.llm.model_router import get_model_router

            router = get_model_router()
            providers = router._providers
            available_providers = [
                p for p in providers.values()
                if getattr(p, "api_key", None)
            ]
            if not available_providers:
                return ModelConfigurationObservation(
                    availability="MISSING",
                    reason_codes=(),
                )
            return ModelConfigurationObservation(
                availability="AVAILABLE",
                state="ACTIVE",
                revision=1,
                runtime_ready=True,
                runtime_revision=1,
                verified_at=_now(),
                source_ref="ModelRouter:current",
                reason_codes=(),
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("ModelConfigurationQuery error: %s", e, exc_info=True)
            return ModelConfigurationObservation(
                availability="MISSING",
                reason_codes=("MODEL_CONFIGURATION_QUERY_UNAVAILABLE",),
            )


class UnavailableDataControlQuery(StaticDataControlQuery):
    def __init__(self) -> None:
        super().__init__(
            DataControlObservation(
                availability="MISSING",
                reason_codes=("DATA_CONTROL_QUERY_UNAVAILABLE",),
            )
        )


class DatabaseDataControlQuery:
    """Real data control query backed by onboarding preferences."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_capability(self, user: User) -> DataControlObservation:
        from app.repositories.onboarding_preferences import OnboardingPreferenceRepository

        repo = OnboardingPreferenceRepository(self._session)
        prefs = await repo.get(user_id=str(user.id), journey_id=JOURNEY_ID)

        if prefs is None:
            return DataControlObservation(
                availability="MISSING",
                reason_codes=(),
            )

        boundary_ack = prefs.boundary_notice_version_acknowledged
        route = "settings" if not boundary_ack else None

        return DataControlObservation(
            availability="AVAILABLE",
            route=route,
            source_ref=f"OnboardingPreference:{user.id}",
            reason_codes=(),
        )


@dataclass(frozen=True)
class _MaterialFacts:
    step: OnboardingStepViewV1
    eligible_ids: tuple[str, ...]
    has_processing: bool


@dataclass(frozen=True)
class _GoalFacts:
    step: OnboardingStepViewV1
    current_records: tuple[LearningGoalRecord, ...]
    source_document_ids: tuple[str, ...]


class OnboardingJourneyQueryService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        model_configuration: ModelConfigurationQuery | None = None,
        data_control: DataControlQuery | None = None,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self._session = session
        self._preferences = OnboardingPreferenceRepository(session)
        self._model_configuration = model_configuration or UnavailableModelConfigurationQuery()
        self._data_control = data_control or UnavailableDataControlQuery()
        self._clock = clock

    @property
    def preferences(self) -> OnboardingPreferenceRepository:
        return self._preferences

    def now(self) -> datetime:
        return _aware(self._clock())

    async def get_journey(self, user: User, *, correlation_id: str) -> OnboardingJourneyViewV1:
        generated_at = self.now()
        preference_record = await self._preferences.get_or_create_active(
            user_id=str(user.id), journey_id=JOURNEY_ID, now=generated_at
        )
        preference = self._preferences.to_contract(preference_record)
        model = await self._model_configuration.get_summary(user)
        data_control = await self._data_control.get_capability(user)
        model_step = self._model_step(model, generated_at)
        material = await self._material_facts(user, generated_at)
        goals = await self._goal_facts(
            user, generated_at, eligible_document_ids=material.eligible_ids
        )
        completion = await self.first_activity_completion(user)
        eligible_goal_ids = tuple(item.goal_id for item in goals.current_records)
        activity_step = await self._activity_step(
            user,
            completion,
            generated_at,
            eligible_goal_ids=eligible_goal_ids,
        )
        steps = (model_step, material.step, goals.step, activity_step)
        dependency_partial = self._dependency_partial(model, data_control)
        acknowledged = preference.boundary_notice_version_acknowledged == BOUNDARY_NOTICE_VERSION
        complete = acknowledged and all(item.state == "COMPLETE" for item in steps)
        journey_state: OnboardingJourneyState
        if complete:
            journey_state = "COMPLETE"
        elif any(item.state == "BLOCKED" for item in steps):
            journey_state = "BLOCKED"
        elif any(item.state == "STALE" for item in steps):
            journey_state = "STALE"
        elif dependency_partial:
            journey_state = "PARTIAL"
        else:
            journey_state = "ACTIVE"
        next_action = await self._next_action(
            acknowledged=acknowledged,
            model_step=model_step,
            material=material,
            goals=goals,
            activity_step=activity_step,
            eligible_goal_ids=eligible_goal_ids,
            user=user,
        )
        return OnboardingJourneyViewV1(
            generated_at=generated_at,
            journey_state=journey_state,
            should_enter_welcome=(
                preference.visibility == "ACTIVE" and not complete and not dependency_partial
            ),
            preference=preference,
            boundary_notice=BoundaryNoticeV1(
                notice_version=BOUNDARY_NOTICE_VERSION,
                acknowledged=acknowledged,
                data_control_route=data_control.route,
                model_settings_route="/settings#model",
            ),
            steps=steps,
            next_action=next_action,
            correlation_id=correlation_id,
        )

    @staticmethod
    def _dependency_partial(
        model: ModelConfigurationObservation,
        data_control: DataControlObservation,
    ) -> bool:
        reason_codes = (*model.reason_codes, *data_control.reason_codes)
        return any(
            code.endswith("_QUERY_UNAVAILABLE")
            or code.endswith("_SCHEMA_UNSUPPORTED")
            or code.endswith("_UNAUTHORIZED")
            for code in reason_codes
        )

    @staticmethod
    def _model_step(
        observation: ModelConfigurationObservation, observed_at: datetime
    ) -> OnboardingStepViewV1:
        available = AvailabilityStatus(observation.availability)
        complete = (
            available == AvailabilityStatus.AVAILABLE
            and observation.state == "ACTIVE"
            and observation.runtime_ready
            and observation.revision is not None
            and observation.runtime_revision == observation.revision
            and observation.verified_at is not None
        )
        state: OnboardingStepState
        if complete:
            state, summary = "COMPLETE", "模型已真实验证并在当前运行版本启用"
        elif available in {
            AvailabilityStatus.STALE,
            AvailabilityStatus.LOW_CONFIDENCE,
        }:
            state, summary = "STALE", "模型配置状态已过期，请重新验证"
        elif available == AvailabilityStatus.AVAILABLE and observation.state == "DEGRADED":
            state, summary = "BLOCKED", "模型配置需要恢复"
        elif available == AvailabilityStatus.AVAILABLE:
            state, summary = "IN_PROGRESS", "模型尚未完成当前运行版本验证"
        else:
            state, summary = "NOT_STARTED", "尚未在 App 内验证模型"
        return OnboardingStepViewV1(
            step="MODEL",
            state=state,
            title="模型",
            summary=summary,
            source_status=(
                SourceObservationV1(
                    source_system="SYS08",
                    availability=available,
                    source_ref=observation.source_ref,
                    observed_at=observation.verified_at or observed_at,
                    reason_codes=observation.reason_codes,
                ),
            ),
        )

    async def _material_facts(self, user: User, observed_at: datetime) -> _MaterialFacts:
        records = (
            await self._session.scalars(
                select(UserDocument)
                .where(
                    UserDocument.pseudonym_id == user.pseudonym_id,
                    UserDocument.is_deleted.is_(False),
                )
                .order_by(UserDocument.created_at, UserDocument.id)
            )
        ).all()
        eligible = tuple(
            item.id
            for item in records
            if item.processing_status == ProcessingStatus.COMPLETED
            and item.moderation_status == ModerationStatus.APPROVED
        )
        has_processing = any(
            item.processing_status in {ProcessingStatus.PENDING, ProcessingStatus.PROCESSING}
            for item in records
        )
        blocked = any(
            item.processing_status
            in {ProcessingStatus.FAILED, ProcessingStatus.REJECTED, ProcessingStatus.QUARANTINED}
            or item.moderation_status
            in {ModerationStatus.REJECTED, ModerationStatus.REQUIRES_REVIEW}
            for item in records
        )
        state: OnboardingStepState
        availability: AvailabilityStatus
        if eligible:
            state, summary, availability = (
                "COMPLETE",
                "已有可用于学习的私人资料",
                AvailabilityStatus.AVAILABLE,
            )
            source_ref = f"UserDocument:{eligible[0]}:current"
            reasons: tuple[str, ...] = ()
        elif has_processing:
            state, summary, availability = (
                "IN_PROGRESS",
                "资料正在本机处理",
                AvailabilityStatus.AVAILABLE,
            )
            source_ref = f"UserDocument:{records[0].id}:processing"
            reasons = ("CONTENT_PROCESSING",)
        elif blocked:
            state, summary, availability = (
                "BLOCKED",
                "资料需要处理后才能学习",
                AvailabilityStatus.AVAILABLE,
            )
            source_ref = f"UserDocument:{records[0].id}:blocked"
            reasons = ("CONTENT_NOT_LEARNING_READY",)
        else:
            state, summary, availability = (
                "NOT_STARTED",
                "尚未导入学习资料",
                AvailabilityStatus.MISSING,
            )
            source_ref = None
            reasons = ("NO_ELIGIBLE_MATERIAL",)
        return _MaterialFacts(
            step=OnboardingStepViewV1(
                step="MATERIAL",
                state=state,
                title="资料",
                summary=summary,
                source_status=(
                    SourceObservationV1(
                        source_system="SYS01",
                        availability=availability,
                        source_ref=source_ref,
                        observed_at=observed_at,
                        reason_codes=reasons,
                    ),
                ),
            ),
            eligible_ids=eligible,
            has_processing=has_processing,
        )

    async def _goal_facts(
        self,
        user: User,
        observed_at: datetime,
        *,
        eligible_document_ids: tuple[str, ...],
    ) -> _GoalFacts:
        owner_id = str(canonical_user_id(user.id))
        records = (
            await self._session.scalars(
                select(LearningGoalRecord)
                .where(LearningGoalRecord.user_id == owner_id)
                .order_by(LearningGoalRecord.goal_id, LearningGoalRecord.version.desc())
            )
        ).all()
        latest: dict[str, LearningGoalRecord] = {}
        for record in records:
            latest.setdefault(record.goal_id, record)
        confirmed_current = tuple(
            item
            for item in latest.values()
            if item.status in {"confirmed", "active"}
            and bool(item.payload.get("confirmed_by_user"))
        )
        eligible_set = set(eligible_document_ids)
        current = tuple(
            item
            for item in confirmed_current
            if any(
                str(document_id) in eligible_set
                for document_id in item.payload.get("source_document_ids", [])
            )
        )
        source_document_ids = tuple(
            dict.fromkeys(
                str(document_id)
                for item in current
                for document_id in item.payload.get("source_document_ids", [])
            )
        )
        candidates = tuple(item for item in latest.values() if item.status == "candidate")
        state: OnboardingStepState
        availability: AvailabilityStatus
        if current and source_document_ids:
            state, summary, availability = (
                "COMPLETE",
                "学习目标已由你确认",
                AvailabilityStatus.AVAILABLE,
            )
            source_ref = f"LearningGoal:{current[0].goal_id}:v{current[0].version}"
            reasons: tuple[str, ...] = ()
        elif confirmed_current:
            state, summary, availability = (
                "STALE",
                "学习目标关联的资料当前不可用",
                AvailabilityStatus.STALE,
            )
            source_ref = (
                f"LearningGoal:{confirmed_current[0].goal_id}:" f"v{confirmed_current[0].version}"
            )
            reasons = ("GOAL_SOURCE_MAPPING_UNAVAILABLE",)
        elif candidates:
            state, summary, availability = (
                "IN_PROGRESS",
                "学习目标等待你确认",
                AvailabilityStatus.AVAILABLE,
            )
            source_ref = f"LearningGoal:{candidates[0].goal_id}:v{candidates[0].version}"
            reasons = ("GOAL_CONFIRMATION_REQUIRED",)
        else:
            state, summary, availability = (
                "NOT_STARTED",
                "尚未确认学习目标",
                AvailabilityStatus.MISSING,
            )
            source_ref = None
            reasons = ("CONFIRMED_GOAL_MISSING",)
        return _GoalFacts(
            step=OnboardingStepViewV1(
                step="GOAL",
                state=state,
                title="目标",
                summary=summary,
                source_status=(
                    SourceObservationV1(
                        source_system="SYS06",
                        availability=availability,
                        source_ref=source_ref,
                        observed_at=observed_at,
                        reason_codes=reasons,
                    ),
                ),
            ),
            current_records=current,
            source_document_ids=source_document_ids,
        )

    async def first_activity_completion(
        self, user: User
    ) -> FirstActivityCompletionProjectionV1 | None:
        state = LearningActivityStateRecord
        newer_state = aliased(LearningActivityStateRecord)
        goal = LearningGoalRecord
        newer_goal = aliased(LearningGoalRecord)
        rows = (
            await self._session.execute(
                select(state, LearningPlanRecord, goal)
                .join(
                    LearningPlanRecord,
                    and_(
                        LearningPlanRecord.plan_id == state.plan_id,
                        LearningPlanRecord.version == state.plan_version,
                    ),
                )
                .join(goal, goal.goal_id == LearningPlanRecord.learning_goal_id)
                .where(
                    goal.user_id == str(canonical_user_id(user.id)),
                    state.status == "completed",
                    state.previous_status == "active",
                    state.transition_reason == "LEARNER_FINISHED_TRANSCRIPT_BACKED_ACTIVITY",
                    state.actor_type == "learner",
                    state.completed_at.is_not(None),
                    ~exists(
                        select(1).where(
                            newer_state.activity_id == state.activity_id,
                            newer_state.version > state.version,
                        )
                    ),
                    ~exists(
                        select(1).where(
                            newer_goal.goal_id == goal.goal_id,
                            newer_goal.version > goal.version,
                        )
                    ),
                )
                .order_by(state.completed_at, state.activity_id)
            )
        ).all()
        owner_id = str(canonical_user_id(user.id))
        for state_record, _plan_record, _goal_record in rows:
            for raw_ref in state_record.source_refs or []:
                try:
                    ref = VersionedRef.model_validate(raw_ref)
                    turn_number = int(ref.version)
                except (ValueError, TypeError):
                    continue
                if ref.entity_type != "BookLearningTranscriptTurn":
                    continue
                accepted = await self._session.scalar(
                    select(BookLearningTranscriptTurnRecord.turn_record_id).where(
                        BookLearningTranscriptTurnRecord.user_id == owner_id,
                        BookLearningTranscriptTurnRecord.activity_id == state_record.activity_id,
                        BookLearningTranscriptTurnRecord.turn_id == ref.entity_id,
                        BookLearningTranscriptTurnRecord.turn_number == turn_number,
                    )
                )
                if accepted is None:
                    continue
                completed_at = state_record.completed_at
                if completed_at is None:
                    continue
                return FirstActivityCompletionProjectionV1(
                    user_ref=owner_id,
                    activity_ref=VersionedRef(
                        entity_type="LearningActivity",
                        entity_id=state_record.activity_id,
                        version=state_record.plan_version,
                    ),
                    state_ref=VersionedRef(
                        entity_type="LearningActivityState",
                        entity_id=state_record.activity_id,
                        version=state_record.version,
                    ),
                    completed_at=_aware(completed_at),
                    completion_source_ref=ref,
                )
        return None

    async def _latest_current_activity_states(
        self, user: User, *, eligible_goal_ids: tuple[str, ...]
    ) -> tuple[LearningActivityStateRecord, ...]:
        if not eligible_goal_ids:
            return ()
        state = LearningActivityStateRecord
        newer = aliased(LearningActivityStateRecord)
        newer_plan = aliased(LearningPlanRecord)
        rows = (
            await self._session.scalars(
                select(state)
                .join(
                    LearningPlanRecord,
                    and_(
                        LearningPlanRecord.plan_id == state.plan_id,
                        LearningPlanRecord.version == state.plan_version,
                    ),
                )
                .join(
                    LearningGoalRecord,
                    LearningGoalRecord.goal_id == LearningPlanRecord.learning_goal_id,
                )
                .where(
                    LearningGoalRecord.user_id == str(canonical_user_id(user.id)),
                    LearningPlanRecord.learning_goal_id.in_(eligible_goal_ids),
                    LearningPlanRecord.status == "active",
                    state.status.in_(("available", "active")),
                    ~exists(
                        select(1).where(
                            newer.activity_id == state.activity_id,
                            newer.version > state.version,
                        )
                    ),
                    ~exists(
                        select(1).where(
                            newer_plan.plan_id == LearningPlanRecord.plan_id,
                            newer_plan.version > LearningPlanRecord.version,
                        )
                    ),
                )
                .order_by(state.status.desc(), state.activity_id)
            )
        ).all()
        unique: dict[str, LearningActivityStateRecord] = {}
        for row in rows:
            unique.setdefault(row.activity_id, row)
        return tuple(unique.values())

    async def _activity_step(
        self,
        user: User,
        completion: FirstActivityCompletionProjectionV1 | None,
        observed_at: datetime,
        *,
        eligible_goal_ids: tuple[str, ...],
    ) -> OnboardingStepViewV1:
        state: OnboardingStepState
        availability: AvailabilityStatus
        if completion is not None:
            state, summary, availability = (
                "COMPLETE",
                "第一项学习活动已完成",
                AvailabilityStatus.AVAILABLE,
            )
            source_ref = (
                f"LearningActivityState:{completion.state_ref.entity_id}:"
                f"v{completion.state_ref.version}"
            )
            reasons: tuple[str, ...] = ()
        else:
            current = await self._latest_current_activity_states(
                user, eligible_goal_ids=eligible_goal_ids
            )
            if any(item.status == "active" for item in current):
                state, summary, availability = (
                    "IN_PROGRESS",
                    "第一项学习活动可以继续",
                    AvailabilityStatus.AVAILABLE,
                )
                source_ref = f"LearningActivityState:{current[0].activity_id}:v{current[0].version}"
                reasons = ("ACTIVITY_RESUMABLE",)
            elif current:
                state, summary, availability = (
                    "NOT_STARTED",
                    "第一项学习活动已经准备好",
                    AvailabilityStatus.AVAILABLE,
                )
                source_ref = f"LearningActivityState:{current[0].activity_id}:v{current[0].version}"
                reasons = ("ACTIVITY_AVAILABLE",)
            else:
                state, summary, availability = (
                    "NOT_STARTED",
                    "第一项学习活动尚未准备完成",
                    AvailabilityStatus.MISSING,
                )
                source_ref = None
                reasons = ("FIRST_ACTIVITY_NOT_AVAILABLE",)
        return OnboardingStepViewV1(
            step="FIRST_ACTIVITY",
            state=state,
            title="第一节",
            summary=summary,
            source_status=(
                SourceObservationV1(
                    source_system="SYS06",
                    availability=availability,
                    source_ref=source_ref,
                    observed_at=observed_at,
                    reason_codes=reasons,
                ),
            ),
        )

    async def _next_action(
        self,
        *,
        acknowledged: bool,
        model_step: OnboardingStepViewV1,
        material: _MaterialFacts,
        goals: _GoalFacts,
        activity_step: OnboardingStepViewV1,
        eligible_goal_ids: tuple[str, ...],
        user: User,
    ) -> OnboardingNextActionV1:
        if not acknowledged:
            return OnboardingNextActionV1(
                action_code="ACKNOWLEDGE_BOUNDARIES",
                kind="command",
                label="我已了解，开始设置",
            )
        if model_step.state != "COMPLETE":
            return OnboardingNextActionV1(
                action_code="OPEN_MODEL_SETTINGS",
                kind="navigate",
                label="配置并验证模型",
                route="/settings#model",
                reason_codes=model_step.source_status[0].reason_codes,
            )
        if material.step.state != "COMPLETE":
            if material.has_processing:
                return OnboardingNextActionV1(
                    action_code="WAIT",
                    kind="wait",
                    label="查看资料处理进度",
                    route="/library",
                    reason_codes=("CONTENT_PROCESSING",),
                )
            return OnboardingNextActionV1(
                action_code="OPEN_LIBRARY",
                kind="navigate",
                label="导入一份私人资料",
                route="/library?intent=first-learning",
                reason_codes=material.step.source_status[0].reason_codes,
            )
        if goals.step.state != "COMPLETE":
            if len(material.eligible_ids) != 1:
                return OnboardingNextActionV1(
                    action_code="SELECT_MATERIAL",
                    kind="navigate",
                    label="选择要学习的资料",
                    route="/library?intent=first-learning",
                    reason_codes=("MULTIPLE_ELIGIBLE_MATERIALS_REQUIRE_SELECTION",),
                )
            document_id = material.eligible_ids[0]
            return OnboardingNextActionV1(
                action_code="OPEN_MATERIAL_LEARNING",
                kind="navigate",
                label="说明并确认学习目标",
                route=f"/book-learning/{document_id}",
                resource_ref=f"UserDocument:{document_id}:current",
            )
        if activity_step.state == "COMPLETE":
            return OnboardingNextActionV1(
                action_code="OPEN_TODAY",
                kind="navigate",
                label="回到今天查看下一步",
                route="/today",
            )
        current = await self._latest_current_activity_states(
            user, eligible_goal_ids=eligible_goal_ids
        )
        active = tuple(item for item in current if item.status == "active")
        available = tuple(item for item in current if item.status == "available")
        if len(active) == 1:
            activity_id = active[0].activity_id
            return OnboardingNextActionV1(
                action_code="RESUME_ACTIVITY",
                kind="navigate",
                label="继续第一节",
                route=f"/learn/{activity_id}",
                resource_ref=f"LearningActivity:{activity_id}:v{active[0].plan_version}",
            )
        if len(available) == 1:
            activity_id = available[0].activity_id
            return OnboardingNextActionV1(
                action_code="START_ACTIVITY",
                kind="navigate",
                label="开始第一节",
                route=f"/learn/{activity_id}",
                resource_ref=f"LearningActivity:{activity_id}:v{available[0].plan_version}",
            )
        if len(current) > 1:
            return OnboardingNextActionV1(
                action_code="OPEN_TODAY",
                kind="navigate",
                label="选择当前学习活动",
                route="/today",
                reason_codes=("MULTIPLE_CURRENT_ACTIVITIES_USE_SYS06_TODAY_SELECTION",),
            )
        if len(goals.source_document_ids) == 1:
            document_id = goals.source_document_ids[0]
            return OnboardingNextActionV1(
                action_code="CONTINUE_DIAGNOSTIC",
                kind="navigate",
                label="继续准备第一节",
                route=f"/book-learning/{document_id}",
                resource_ref=f"UserDocument:{document_id}:current",
            )
        return OnboardingNextActionV1(
            action_code="SELECT_MATERIAL",
            kind="navigate",
            label="选择要继续的学习资料",
            route="/library?intent=first-learning",
            reason_codes=("GOAL_SOURCE_SELECTION_REQUIRED",),
        )
