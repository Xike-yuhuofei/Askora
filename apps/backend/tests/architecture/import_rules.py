"""Standard-library AST import rules for EXEC-001 T6."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImportViolation:
    rule: str
    path: str
    module: str
    line: int

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.rule, self.path, self.module)


@dataclass(frozen=True)
class LegacyAllowance:
    rule: str
    path: str
    module: str
    todo_owner: str
    removal_exec: str

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.rule, self.path, self.module)


# 每项均为一个精确 import；禁止 glob。后续 EXEC 必须删除对应 allowance。
LEGACY_ALLOWLIST = (
    LegacyAllowance(
        rule="API_NO_LEARNER_PERSISTENCE",
        path="app/api/v1/users.py",
        module="app.models.profile",
        todo_owner="SYS03 learner-model migration",
        removal_exec="EXEC-004",
    ),
    LegacyAllowance(
        rule="ORCHESTRATION_NO_OWNED_STATE_WRITE",
        path="app/engines/socratic_adapter.py",
        module="app.services.kt",
        todo_owner="SYS08 canonical teaching entry migration",
        removal_exec="EXEC-002",
    ),
)


def _imported_modules(tree: ast.AST) -> list[tuple[str, int]]:
    modules: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append((node.module, node.lineno))
    return modules


def _is_learner_persistence(module: str) -> bool:
    return module == "app.models.profile" or module.startswith(
        (
            "app.domains.learner_model.persistence",
            "app.domains.learner_model.repository",
            "app.infrastructure.learner",
            "app.infrastructure.mastery",
        )
    )


def _violations_for_import(relative_path: str, module: str, line: int) -> list[ImportViolation]:
    violations: list[ImportViolation] = []
    if relative_path.startswith("app/api/") and _is_learner_persistence(module):
        violations.append(
            ImportViolation("API_NO_LEARNER_PERSISTENCE", relative_path, module, line)
        )

    if relative_path.startswith("app/services/assessment/") and module.startswith(
        (
            "app.services.kt",
            "app.services.dkt",
            "app.domains.learner_model.persistence",
            "app.domains.learner_model.repository",
            "app.infrastructure.learner",
            "app.infrastructure.mastery",
        )
    ):
        violations.append(
            ImportViolation("ASSESSMENT_NO_LEARNER_WRITE", relative_path, module, line)
        )

    orchestration_path = relative_path.startswith(
        ("app/engines/", "app/orchestration/", "app/services/llm/")
    )
    if orchestration_path and module.startswith(
        (
            "app.services.kt",
            "app.services.dkt",
            "app.domains.learner_model.persistence",
            "app.domains.learner_model.repository",
            "app.domains.learning_planner.persistence",
            "app.domains.learning_planner.repository",
            "app.domains.review_scheduler.persistence",
            "app.domains.review_scheduler.repository",
            "app.infrastructure.learner",
            "app.infrastructure.mastery",
            "app.infrastructure.plan",
            "app.infrastructure.review",
        )
    ):
        violations.append(
            ImportViolation("ORCHESTRATION_NO_OWNED_STATE_WRITE", relative_path, module, line)
        )

    contract_or_domain = relative_path.startswith(("app/contracts/", "app/domains/"))
    forbidden_root = module.split(".", maxsplit=1)[0]
    if contract_or_domain and forbidden_root in {
        "fastapi",
        "redis",
        "aiokafka",
        "kafka",
        "openai",
        "anthropic",
        "dashscope",
    }:
        violations.append(
            ImportViolation("DOMAIN_CONTRACTS_NO_ADAPTER_SDK", relative_path, module, line)
        )
    return violations


def inspect_imports(app_root: Path) -> list[ImportViolation]:
    violations: list[ImportViolation] = []
    for path in sorted(app_root.rglob("*.py")):
        relative_path = path.relative_to(app_root.parent).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for module, line in _imported_modules(tree):
            violations.extend(_violations_for_import(relative_path, module, line))
    return violations


def partition_allowlisted(
    violations: list[ImportViolation],
    allowlist: tuple[LegacyAllowance, ...] = LEGACY_ALLOWLIST,
) -> tuple[list[ImportViolation], list[ImportViolation]]:
    allowed_keys = {item.key for item in allowlist}
    allowed = [item for item in violations if item.key in allowed_keys]
    unexpected = [item for item in violations if item.key not in allowed_keys]
    return unexpected, allowed
