#!/usr/bin/env python3
"""Validate local documentation links and guard known stale project-state claims."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
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
    "ui",
}

STALE_PATTERNS = {
    "README.md": (
        "docs/architecture/当前项目架构.md",
        "本仓库当前尚无正式提交",
    ),
    "docs/specs/README.md": ("下一阶段：正式生成 `EXEC-007`",),
    "docs/research/learning-core/README.md": (
        "研究完成前不得直接生成 v0.3 EXEC",
    ),
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
        # docs/archive 是历史快照，不参与 current 链接校验
        if relative.parts[:2] == ("docs", "archive"):
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


def active_exec_files() -> list[Path]:
    active = ROOT / "docs/planning/execs"
    if not active.exists():
        return []
    return sorted(path for path in active.glob("EXEC-*.md") if path.is_file())


def check_active_exec_index() -> list[str]:
    active_files = active_exec_files()
    if not active_files:
        return []

    index = ROOT / "docs/planning/README.md"
    content = index.read_text(encoding="utf-8")
    errors: list[str] = []

    for path in active_files:
        relative_target = f"execs/{path.name}"
        if relative_target not in content:
            errors.append(
                f"docs/planning/execs: {path.name} is active but missing from docs/planning/README.md"
            )

    exec_numbers = []
    for path in active_files:
        match = re.match(r"EXEC-(\d+)-", path.name)
        if match:
            exec_numbers.append(int(match.group(1)))
    if len(exec_numbers) != len(set(exec_numbers)):
        errors.append("docs/planning/execs: duplicate EXEC number detected")

    return errors


def check_stale_claims() -> list[str]:
    errors: list[str] = []
    for name, patterns in STALE_PATTERNS.items():
        path = ROOT / name
        content = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern in content:
                errors.append(f"{name}: stale project-state claim remains: {pattern}")
    errors.extend(check_active_exec_index())
    return errors


INVENTORY_PATH_RE = re.compile(r"`((?:product|design|decisions|specs)/[^`]+)`")
CURRENT_CONTRACT_ROOTS = ("product", "design", "decisions", "specs")


def extract_heading_section(content: str, heading_needle: str) -> str:
    lines = content.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.startswith("## ") and heading_needle in line:
            start = index
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end])


def check_current_inventory() -> list[str]:
    readme = ROOT / "docs/README.md"
    if not readme.is_file():
        return ["docs/README.md: missing current documentation index"]

    content = readme.read_text(encoding="utf-8")
    section = extract_heading_section(content, "当前文档清单")
    if not section:
        return ["docs/README.md: missing '当前文档清单' section"]

    listed = {match.group(1) for match in INVENTORY_PATH_RE.finditer(section)}
    if not listed:
        return ["docs/README.md: current document inventory is empty"]

    errors: list[str] = []
    docs_root = ROOT / "docs"
    for relative in sorted(listed):
        if not (docs_root / relative).is_file():
            errors.append(f"docs/README.md: inventory lists missing file: {relative}")

    for folder in CURRENT_CONTRACT_ROOTS:
        root = docs_root / folder
        if not root.is_dir():
            continue
        for path in root.rglob("*.md"):
            relative = path.relative_to(docs_root).as_posix()
            if path.name == "README.md":
                continue
            if relative not in listed:
                errors.append(
                    f"{path.relative_to(ROOT)}: current markdown file is not listed in docs/README.md inventory"
                )
    return errors


def main() -> int:
    files = documentation_files()
    errors = [*check_links(files), *check_stale_claims(), *check_current_inventory()]
    if errors:
        print("Documentation check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"Documentation check passed: {len(files)} files, 0 broken local links, inventory matches disk."
    )
    return 0



if __name__ == "__main__":
    sys.exit(main())
