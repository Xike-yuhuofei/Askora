#!/usr/bin/env python3
"""Validate local documentation links and guard known stale project-state claims."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
INVENTORY_ROW = re.compile(r"^\| `([^`]+)` \|", re.MULTILINE)
SCHEMES = ("http:", "https:", "mailto:", "tel:", "data:")
EXCLUDED_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "release",
}

STALE_PATTERNS = {
    "README.md": (
        "docs/architecture/当前项目架构.md",
        "本仓库当前尚无正式提交",
    ),
    "docs/exec-plans/README.md": (
        "active/EXEC-007-v0.3-governance-preconditions.md",
        "当前 active contracts",
    ),
    "docs/specs/README.md": ("下一阶段：正式生成 `EXEC-007`",),
    "docs/specs/vertical-slices/v0.3-adaptive-teaching-loop.md": (
        "下一阶段为生成 `EXEC-007`",
    ),
    "docs/design/个人AI辅助学习平台设计方案.md": (
        "进入实现前依次完成",
        "本阶段不修改 `docs/specs/**`",
    ),
    "docs/design/AI学习系统算法与教学内核设计.md": (
        "当前阶段完成的是 Canonical Design，不是 Spec 或实现",
        "后续流程必须先进入 ADR Resolution",
    ),
    "docs/design/research/README.md": ("研究完成前不得直接生成 v0.3 EXEC",),
}


def documentation_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(
            part in EXCLUDED_DIRECTORIES or part.endswith(".egg-info")
            for part in relative.parts
        ):
            continue
        if path.is_file() and path.suffix.lower() in {".md", ".mdx", ".rst"}:
            files.append(path)
    return sorted(files)


def link_target(raw: str) -> str:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        value = value[1 : value.index(">")]
    else:
        value = value.split(maxsplit=1)[0]
    return unquote(value.split("#", 1)[0])


def check_links(files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in files:
        content = path.read_text(encoding="utf-8", errors="replace")
        for match in MARKDOWN_LINK.finditer(content):
            target = link_target(match.group(1))
            if not target or target.lower().startswith(SCHEMES):
                continue
            destination = (path.parent / target).resolve()
            if not destination.exists():
                line = content.count("\n", 0, match.start()) + 1
                relative = path.relative_to(ROOT)
                errors.append(f"{relative}:{line}: missing local link target: {target}")
    return errors


def check_stale_claims() -> list[str]:
    errors: list[str] = []
    for name, patterns in STALE_PATTERNS.items():
        path = ROOT / name
        content = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern in content:
                errors.append(f"{name}: stale project-state claim remains: {pattern}")

    active = ROOT / "docs/exec-plans/active"
    if active.exists() and any(active.glob("*.md")):
        errors.append("docs/exec-plans/active: active EXEC files require index review")
    return errors


def check_inventory(files: list[Path]) -> list[str]:
    inventory = ROOT / "docs/document-inventory.md"
    listed = set(INVENTORY_ROW.findall(inventory.read_text(encoding="utf-8")))
    actual = {str(path.relative_to(ROOT)) for path in files}
    return [
        f"docs/document-inventory.md: missing disposition for {name}"
        for name in sorted(actual - listed)
    ]


def main() -> int:
    files = documentation_files()
    errors = [*check_links(files), *check_stale_claims(), *check_inventory(files)]
    if errors:
        print("Documentation check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Documentation check passed: {len(files)} files, 0 broken local links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
