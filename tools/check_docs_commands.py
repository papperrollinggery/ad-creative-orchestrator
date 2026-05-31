#!/usr/bin/env python3
"""Check public onboarding docs prefer the installed adco CLI."""

from __future__ import annotations

from pathlib import Path

from runtime_paths import skill_draft_dir, source_root

ROOT = source_root()
CHECK_PATHS = (
    [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "ROADMAP.md",
        ROOT / "docs/operating",
        ROOT / "skill_drafts/ad-creative-orchestrator/SKILL.md",
        ROOT / "tools/adco_resources/skill_drafts/ad-creative-orchestrator/SKILL.md",
    ]
    if ROOT
    else [skill_draft_dir() / "SKILL.md"]
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


def iter_markdown_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.glob("*.md"))


def main() -> int:
    issues: list[str] = []
    files: list[Path] = []
    for path in CHECK_PATHS:
        files.extend(iter_markdown_files(path))
    for path in files:
        text = path.read_text(encoding="utf-8")
        for snippet in FORBIDDEN_SNIPPETS:
            if snippet in text:
                label = str(path.relative_to(ROOT)) if ROOT else str(path)
                issues.append(f"{label} contains forbidden command: {snippet}")
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
