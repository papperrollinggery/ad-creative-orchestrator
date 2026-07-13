#!/usr/bin/env python3
"""Check public onboarding docs prefer the installed adco CLI."""

from __future__ import annotations

import re
from pathlib import Path

from ad_creative_operator import build_parser
from runtime_paths import published_docs_root, skill_draft_dir, source_root

ROOT = source_root()
CHECK_PATHS = (
    [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "ROADMAP.md",
        ROOT / "SECURITY.md",
        ROOT / "CHANGELOG.md",
        ROOT / "docs/operating",
        ROOT / "examples/moncler_protocol_dry_run/AD-creative/handoff",
        ROOT / "examples/simulated_qingling_outdoor_launch/AD-creative/handoff",
        ROOT / "templates/project",
        ROOT / "skill_drafts/ad-creative-orchestrator/SKILL.md",
        ROOT / "tools/adco_resources/templates/project",
        ROOT / "tools/adco_resources/skill_drafts/ad-creative-orchestrator/SKILL.md",
    ]
    if ROOT
    else [published_docs_root(), skill_draft_dir() / "SKILL.md"]
)
FORBIDDEN_SNIPPETS = [
    "python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/ad_creative_operator.py",
    "python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/init_project.py",
    "python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/validate_project.py",
    "python3 /Users/jinjungao/work/ad-creative-orchestrator/tools/test_goal_workflow.py",
    "python3 tools/ad_creative_operator.py",
    "python3 tools/init_project.py",
    "python3 tools/validate_project.py",
    "python3 tools/test_goal_workflow.py",
    "tools/test_goal_workflow.py",
    "ad_creative_operator.py",
    "ad_creative_operator.py validate",
]
PORTABILITY_FORBIDDEN_SNIPPETS = ["ad-creative:", "/Users/jinjungao"]
ADCO_COMMAND_PATTERN = re.compile(r"(?<![\w-])adco\s+([a-z][a-z0-9-]+)")


def installed_adco_commands() -> set[str]:
    parser = build_parser()
    choices: dict[str, object] = {}
    for action in getattr(parser, "_actions", []):
        action_choices = getattr(action, "choices", None)
        if isinstance(action_choices, dict):
            choices.update(action_choices)
    return set(choices)


def iter_markdown_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.rglob("*.md"))


def iter_adco_command_snippets(text: str) -> list[str]:
    snippets: list[str] = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        parts = line.split("`")
        snippets.extend(parts[index] for index in range(1, len(parts), 2))
        if in_fence or stripped.startswith("adco "):
            snippets.append(stripped)
    return snippets


def main() -> int:
    issues: list[str] = []
    files: list[Path] = []
    available_commands = installed_adco_commands()
    for path in CHECK_PATHS:
        files.extend(iter_markdown_files(path))
    for path in files:
        text = path.read_text(encoding="utf-8")
        forbidden_snippets = list(PORTABILITY_FORBIDDEN_SNIPPETS)
        if path.name != "CHANGELOG.md":
            forbidden_snippets.extend(FORBIDDEN_SNIPPETS)
        for snippet in forbidden_snippets:
            if snippet in text:
                label = str(path.relative_to(ROOT)) if ROOT else str(path)
                issues.append(f"{label} contains forbidden command: {snippet}")
        if path.name == "CHANGELOG.md":
            continue
        for snippet in iter_adco_command_snippets(text):
            for match in ADCO_COMMAND_PATTERN.finditer(snippet):
                command = match.group(1)
                if command not in available_commands:
                    label = str(path.relative_to(ROOT)) if ROOT else str(path)
                    issues.append(f"{label} references unavailable adco command: {command}")
    if issues:
        print("DOCS_COMMANDS_CHECK=FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("DOCS_COMMANDS_CHECK=PASS")
    print(f"DOCS_COMMANDS_FILES={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
