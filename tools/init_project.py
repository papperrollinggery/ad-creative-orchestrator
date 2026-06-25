#!/usr/bin/env python3
"""Initialize a project from templates/project without overwriting files."""

from __future__ import annotations

import argparse
from pathlib import Path

from runtime_paths import template_root as default_template_root


AGENTS_REL = Path("AGENTS.md")
AGENTS_MERGE_SUGGESTION_REL = Path("AD-creative/orchestrator/AGENTS.merge_suggestion.md")


def write_agents_merge_suggestion(source: Path, target_root: Path) -> bool:
    suggestion = target_root / AGENTS_MERGE_SUGGESTION_REL
    if suggestion.exists():
        return False
    suggestion.parent.mkdir(parents=True, exist_ok=True)
    source_text = source.read_text(encoding="utf-8")
    suggestion.write_text(
        "\n".join(
            [
                "# AGENTS.md Merge Suggestion",
                "",
                "`AGENTS.md` already existed at the project root, so adco did not overwrite it.",
                "Copy or adapt the required ad-creative-orchestrator section below into the root `AGENTS.md`, then run `adco validate` again.",
                "",
                "## Required Section",
                "",
                source_text.rstrip(),
                "",
            ]
        ),
        encoding="utf-8",
    )
    return True


def agents_policy_status(target_root: Path) -> str:
    agents_path = target_root / AGENTS_REL
    suggestion_path = target_root / AGENTS_MERGE_SUGGESTION_REL
    if suggestion_path.exists() and not agents_policy_complete(target_root):
        return f"MERGE_REQUIRED:{suggestion_path.relative_to(target_root)}"
    if agents_path.exists():
        return "PRESENT"
    return "MISSING"


def agents_policy_complete(target_root: Path) -> bool:
    agents_path = target_root / AGENTS_REL
    if not agents_path.exists():
        return False
    try:
        from validate_project import AGENTS_REQUIRED_SNIPPETS
    except ImportError:
        return False
    text = agents_path.read_text(encoding="utf-8").lower()
    return all(snippet.lower() in text for snippet in AGENTS_REQUIRED_SNIPPETS)


def copy_template(template_root: Path, target_root: Path) -> tuple[int, int]:
    created = 0
    skipped = 0

    def copy_node(source: Path, relative: Path = Path()) -> None:
        nonlocal created, skipped
        for child in sorted(source.iterdir(), key=lambda item: item.name):
            child_relative = relative / child.name
            target = target_root / child_relative

            if child.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                copy_node(child, child_relative)
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                skipped += 1
                if child_relative == AGENTS_REL and child.read_bytes() != target.read_bytes():
                    if write_agents_merge_suggestion(child, target_root):
                        created += 1
                    else:
                        skipped += 1
                continue

            target.write_bytes(child.read_bytes())
            created += 1

    copy_node(template_root)

    return created, skipped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", help="Target project directory")
    parser.add_argument(
        "--template",
        default=str(default_template_root()),
        help="Template directory. Defaults to this repository's templates/project.",
    )
    args = parser.parse_args()

    template_root = Path(args.template).resolve()
    target_root = Path(args.project).resolve()

    if not template_root.exists():
        print(f"ERROR: template not found: {template_root}")
        return 1

    target_root.mkdir(parents=True, exist_ok=True)
    created, skipped = copy_template(template_root, target_root)
    from validate_project import validate

    errors, stats = validate(target_root)

    print(f"PROJECT={target_root}")
    print(f"CREATED_FILES={created}")
    print(f"SKIPPED_EXISTING_FILES={skipped}")
    print(f"AGENTS_MD={agents_policy_status(target_root)}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"INIT={'PASS' if not errors else 'CHECK'}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
