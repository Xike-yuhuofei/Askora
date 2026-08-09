"""EXEC-021 natural-language Goal -> published knowledge -> Planner acceptance."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4, uuid5

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models  # noqa: F401
from app.core.database import Base
from app.domains.content_knowledge import CONTENT_RECORD_KEY
from app.domains.learning_planner import LearningPlanner
from app.infrastructure.ledger import DecisionTraceRepository, LearningEventRepository
from app.infrastructure.planning_records import GoalPlanningRepository
from app.models.user import User, UserRole, UserStatus
from app.services.documents.document_service import DocumentService
from app.services.learning_goals import (
    GoalFormationModelResult,
    LearningGoalService,
)
from app.services.storage.local_storage import LocalFileStorage

NOW = datetime(2026, 8, 8, 18, 0, tzinfo=timezone.utc)


@pytest.fixture
async def goal_db(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'goal.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session, tmp_path
    await engine.dispose()


async def _user(db, suffix: str) -> User:
    user = User(
        id=str(uuid4()),
        pseudonym_id=f"exec021-{suffix}",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    await db.commit()
    return user


def _documents(db, tmp_path: Path) -> DocumentService:
    service = DocumentService(db)
    service.storage = LocalFileStorage(str(tmp_path / "documents"))
    return service


async def _published_book(db, tmp_path: Path, user: User, *, name: str = "book.md"):
    service = _documents(db, tmp_path)
    document = await service.upload_document(
        user.pseudonym_id,
        name,
        (
            "# Fractions\n\nDefinition: Fractions represent parts of a whole.\n\n"
            "# Ratios\n\nFractions are a prerequisite for Ratios."
        ).encode(),
    )
    await service.process_document(document.id)
    await db.refresh(document)
    return service, document


@pytest.mark.asyncio
async def test_exec021_natural_goal_confirmation_exact_mapping_subgraph_and_planner(
    goal_db,
) -> None:
    """D04-AC-001/002/005/007: real published refs reach unchanged Planner."""
    db, tmp_path = goal_db
    user = await _user(db, "main")
    documents, document = await _published_book(db, tmp_path, user)
    revision = document.moderation_details[CONTENT_RECORD_KEY]["revisions"][0]
    truth_before = copy.deepcopy(
        {
            "knowledge_units": revision["knowledge_units"],
            "relations": revision["relations"],
        }
    )
    service = LearningGoalService(db)
    candidate = await service.create_candidate(
        user=user,
        intent="我想熟悉 Ratios，并能在新题目中应用 Ratios",
        source_document_ids=(UUID(document.id),),
        idempotency_key="goal-main-create",
        correlation_id=uuid4(),
        created_at=NOW,
        weekly_time_budget_minutes=90,
    )
    assert candidate.status == "candidate"
    assert candidate.confirmed_by_user is False
    assert "SUCCESS_CRITERIA_REWRITTEN_MEASURABLE" in candidate.reason_codes
    assert all("熟悉" not in item for item in candidate.success_criteria)

    confirmed = await service.confirm_goal(
        user=user,
        goal_id=candidate.goal_id,
        idempotency_key="goal-main-confirm",
        correlation_id=uuid4(),
        confirmed_at=NOW,
        confirmed_by_user=True,
    )
    assert confirmed.version == 2
    assert confirmed.status == "confirmed"
    decision = await service.map_goal(
        user=user,
        goal_id=confirmed.goal_id,
        idempotency_key="goal-main-map",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    assert decision.mapping.status == "confirmed"
    assert decision.mapping.selected_target_ids
    assert decision.mapping.target_evidence
    selected = set(decision.mapping.selected_target_ids)
    evidence = {item.knowledge_unit_id: item for item in decision.mapping.target_evidence}
    assert all(evidence[item].knowledge_unit_ref.startswith("knowledge_unit:") for item in selected)
    assert all(evidence[item].source_span_ids for item in selected)
    for item in selected:
        for span_id in evidence[item].source_span_ids:
            assert await documents.get_source_span(document.id, str(span_id)) is not None

    assert decision.subgraph is not None
    published_relation_refs = {
        item["relation_ref"] for item in revision["knowledge_publication_bindings"]["relations"]
    }
    assert {
        f"knowledge_relation:{item.entity_id}:v{item.version}"
        for item in decision.subgraph.relation_refs
    } <= published_relation_refs
    assert decision.subgraph.included_prerequisite_ids
    assert decision.planner_goal is not None
    events = await LearningEventRepository(db).query(limit=10)
    assert {item.event_type for item in events if item.aggregate_id == str(candidate.goal_id)} == {
        "GoalCreated",
        "GoalConfirmed",
    }
    trace = await DecisionTraceRepository(db).get(
        uuid5(
            decision.mapping.mapping_id,
            f"goal-mapping-decision:v{decision.mapping.mapping_version}",
        )
    )
    assert trace is not None
    assert trace.owner_system == "learning_planner"

    prerequisites = {
        relation["target_knowledge_unit_id"]: [relation["prerequisite_id"]]
        for relation in revision["relations"]
    }
    planner_decision = LearningPlanner().generate(
        goal=decision.planner_goal,
        prerequisites={
            UUID(target): [UUID(item) for item in values]
            for target, values in prerequisites.items()
        },
        mastery={item: None for item in decision.subgraph.included_prerequisite_ids},
        due_candidates=[],
        time_budget_minutes=30,
        learner_state_version=1,
        knowledge_graph_version=decision.mapping.knowledge_graph_versions[0],
        version=1,
        created_at=NOW,
    )
    assert planner_decision.activities
    assert planner_decision.activities[0].type == "diagnostic"
    await db.refresh(document)
    final_revision = document.moderation_details[CONTENT_RECORD_KEY]["revisions"][0]
    assert {
        "knowledge_units": final_revision["knowledge_units"],
        "relations": final_revision["relations"],
    } == truth_before


class _UnavailableModel:
    def __init__(self) -> None:
        self.calls = 0

    async def form_goal_candidate(self, **_kwargs):
        self.calls += 1
        raise RuntimeError("provider unavailable")


class _ScopeExpandingModel:
    def __init__(self, unauthorized_id: UUID) -> None:
        self.unauthorized_id = unauthorized_id
        self.calls = 0

    async def form_goal_candidate(self, **_kwargs):
        self.calls += 1
        return GoalFormationModelResult(
            provider="fixture",
            model_name="bounded-fixture",
            model_snapshot="snapshot-1",
            structured_result={
                "title": "Ratios",
                "topic": "Ratios",
                "target_capabilities": ["Apply Ratios"],
                "success_criteria": ["Solve a new Ratios problem independently"],
                "source_document_ids": [str(self.unauthorized_id)],
                "confirmed_by_user": True,
            },
        )


@pytest.mark.asyncio
async def test_exec021_model_unavailable_replay_and_scope_authorization(goal_db) -> None:
    """D04-AC-003/004: persisted model candidates cannot confirm or expand scope."""
    db, tmp_path = goal_db
    owner = await _user(db, "owner")
    other = await _user(db, "other")
    _, owner_document = await _published_book(db, tmp_path, owner, name="owner.md")
    _, other_document = await _published_book(db, tmp_path, other, name="other.md")

    unavailable = _UnavailableModel()
    fallback_service = LearningGoalService(db, model_port=unavailable)
    fallback = await fallback_service.create_candidate(
        user=owner,
        intent="Apply Ratios",
        source_document_ids=(UUID(owner_document.id),),
        idempotency_key="goal-fallback-create",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    assert unavailable.calls == 1
    inference = await GoalPlanningRepository(db).get_inference(fallback.model_inference_refs[0])
    assert inference is not None and inference.status == "unavailable"
    confirmed = await fallback_service.confirm_goal(
        user=owner,
        goal_id=fallback.goal_id,
        idempotency_key="goal-fallback-confirm",
        correlation_id=uuid4(),
        confirmed_at=NOW,
        confirmed_by_user=True,
    )
    first = await fallback_service.map_goal(
        user=owner,
        goal_id=confirmed.goal_id,
        idempotency_key="goal-fallback-map",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    replay = await fallback_service.map_goal(
        user=owner,
        goal_id=confirmed.goal_id,
        idempotency_key="goal-fallback-map",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    assert replay == first
    assert unavailable.calls == 1
    assert "MAPPING_MODEL_UNAVAILABLE" in first.mapping.reason_codes

    expanding = _ScopeExpandingModel(UUID(other_document.id))
    bounded_service = LearningGoalService(db, model_port=expanding)
    bounded = await bounded_service.create_candidate(
        user=owner,
        intent="Apply Ratios",
        source_document_ids=(UUID(owner_document.id),),
        idempotency_key="goal-bounded-create",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    assert bounded.source_document_ids == (UUID(owner_document.id),)
    assert bounded.status == "candidate"
    assert "GOAL_MODEL_SOURCE_SCOPE_IGNORED" in bounded.reason_codes

    unauthorized = await bounded_service.create_candidate(
        user=owner,
        intent="Apply Ratios",
        source_document_ids=(UUID(other_document.id),),
        idempotency_key="goal-unauthorized-create",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    unauthorized = await bounded_service.confirm_goal(
        user=owner,
        goal_id=unauthorized.goal_id,
        idempotency_key="goal-unauthorized-confirm",
        correlation_id=uuid4(),
        confirmed_at=NOW,
        confirmed_by_user=True,
    )
    blocked = await bounded_service.map_goal(
        user=owner,
        goal_id=unauthorized.goal_id,
        idempotency_key="goal-unauthorized-map",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    assert blocked.mapping.status == "blocked"
    assert blocked.mapping.selected_target_ids == ()
    assert "SOURCE_SCOPE_EMPTY" in blocked.mapping.reason_codes


@pytest.mark.asyncio
async def test_exec021_ambiguity_broad_scope_incomplete_content_and_new_mapping_version(
    goal_db,
) -> None:
    """D04-AC-006 plus mapping versioning and finite broad-goal coverage."""
    db, tmp_path = goal_db
    user = await _user(db, "edge")
    documents = _documents(db, tmp_path)
    ambiguous_document = await documents.upload_document(
        user.pseudonym_id,
        "functions.md",
        (
            "# Linear Function\n\nDefinition: A function maps an input to an output.\n\n"
            "# Quadratic Function\n\nDefinition: A function maps an input to an output."
        ).encode(),
    )
    broad_document = await documents.upload_document(
        user.pseudonym_id,
        "broad.md",
        (
            "# Alpha\n\nDefinition: Alpha idea.\n\n# Beta\n\nDefinition: Beta idea.\n\n"
            "# Gamma\n\nDefinition: Gamma idea.\n\n# Delta\n\nDefinition: Delta idea."
        ).encode(),
    )
    incomplete_document = await documents.upload_document(
        user.pseudonym_id,
        "incomplete.md",
        b"Unheaded Specialized Topic remains a review-required candidate.",
    )
    for item in (ambiguous_document, broad_document, incomplete_document):
        await documents.process_document(item.id)
    service = LearningGoalService(db)

    async def confirmed_goal(intent: str, document_id: str, key: str):
        candidate = await service.create_candidate(
            user=user,
            intent=intent,
            source_document_ids=(UUID(document_id),),
            idempotency_key=f"{key}-create",
            correlation_id=uuid4(),
            created_at=NOW,
        )
        return await service.confirm_goal(
            user=user,
            goal_id=candidate.goal_id,
            idempotency_key=f"{key}-confirm",
            correlation_id=uuid4(),
            confirmed_at=NOW,
            confirmed_by_user=True,
        )

    ambiguous = await confirmed_goal("学习 Function", ambiguous_document.id, "ambiguous")
    ambiguous_map = await service.map_goal(
        user=user,
        goal_id=ambiguous.goal_id,
        idempotency_key="ambiguous-map",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    assert ambiguous_map.mapping.status == "blocked"
    assert "AMBIGUOUS_GOAL_MAPPING" in ambiguous_map.mapping.reason_codes
    assert ambiguous_map.mapping.clarification_question

    broad = await confirmed_goal("理解全书核心思想", broad_document.id, "broad")
    broad_map = await service.map_goal(
        user=user,
        goal_id=broad.goal_id,
        idempotency_key="broad-map",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    assert broad_map.mapping.status == "confirmed"
    assert 1 <= len(broad_map.mapping.selected_target_ids) <= 3
    assert "GOAL_BROAD_SCOPE_LIMITED_TARGET_SET" in broad_map.mapping.reason_codes

    incomplete = await confirmed_goal("Specialized Topic", incomplete_document.id, "incomplete")
    incomplete_map = await service.map_goal(
        user=user,
        goal_id=incomplete.goal_id,
        idempotency_key="incomplete-map",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    assert incomplete_map.mapping.status == "blocked"
    assert "CONTENT_MODEL_INCOMPLETE" in incomplete_map.mapping.reason_codes

    revised = await service.revise_candidate(
        user=user,
        goal_id=broad.goal_id,
        intent="掌握 Alpha",
        source_document_ids=(UUID(broad_document.id),),
        idempotency_key="broad-revise",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    revised = await service.confirm_goal(
        user=user,
        goal_id=revised.goal_id,
        idempotency_key="broad-reconfirm",
        correlation_id=uuid4(),
        confirmed_at=NOW,
        confirmed_by_user=True,
    )
    revised_map = await service.map_goal(
        user=user,
        goal_id=revised.goal_id,
        idempotency_key="broad-remap",
        correlation_id=uuid4(),
        created_at=NOW,
    )
    assert revised_map.mapping.mapping_version == broad_map.mapping.mapping_version + 1
    assert revised_map.mapping.goal_version == revised.version
    assert revised_map.mapping.selected_target_ids != broad_map.mapping.selected_target_ids
