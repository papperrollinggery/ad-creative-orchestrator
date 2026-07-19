#!/usr/bin/env python3
"""Initialize a project from templates/project without overwriting files."""

from __future__ import annotations

import argparse
from pathlib import Path

from runtime_paths import (
    CONTENT_SURFACE,
    DELIVERY_SURFACE,
    is_initialized_adco_project,
    project_surface,
    set_project_surface,
    template_root as default_template_root,
)


AGENTS_REL = Path("AD-creative/AGENTS.md")

CONTENT_TEMPLATE_RELS = (
    AGENTS_REL,
    Path("AD-creative/orchestrator/project.yml"),
    Path("AD-creative/orchestrator/control_plane_schema.json"),
    Path("AD-creative/orchestrator/source_events.csv"),
    Path("AD-creative/orchestrator/current_truth.md"),
    Path("AD-creative/orchestrator/requirements.csv"),
    Path("AD-creative/orchestrator/gaps.csv"),
    Path("AD-creative/handoff/项目看板.md"),
    Path("AD-creative/handoff/待你确认.md"),
)


def agents_policy_status(target_root: Path) -> str:
    agents_path = target_root / AGENTS_REL
    if agents_path.exists():
        return "SCOPED_PRESENT"
    return "MISSING"


def agents_policy_complete(target_root: Path) -> bool:
    if not is_initialized_adco_project(target_root):
        return False
    agents_path = target_root / AGENTS_REL
    if not agents_path.exists():
        return False
    try:
        from validate_project import AGENTS_REQUIRED_SNIPPETS
    except ImportError:
        return False
    text = " ".join(
        agents_path.read_text(encoding="utf-8").replace("`", "").split()
    ).lower()
    return all(
        " ".join(snippet.replace("`", "").split()).lower() in text
        for snippet in AGENTS_REQUIRED_SNIPPETS
    )


def copy_template(template_root: Path, target_root: Path) -> tuple[int, int]:
    return _copy_template(template_root, target_root, included_paths=None)


def copy_content_template(template_root: Path, target_root: Path) -> tuple[int, int]:
    created, skipped = _copy_template(
        template_root,
        target_root,
        included_paths=set(CONTENT_TEMPLATE_RELS),
    )
    set_project_surface(target_root, CONTENT_SURFACE)
    return created, skipped


def _copy_template(
    template_root: Path,
    target_root: Path,
    *,
    included_paths: set[Path] | None,
) -> tuple[int, int]:
    created = 0
    skipped = 0

    def copy_node(source: Path, relative: Path = Path()) -> None:
        nonlocal created, skipped
        for child in sorted(source.iterdir(), key=lambda item: item.name):
            child_relative = relative / child.name
            if included_paths is not None and not any(
                path == child_relative or child_relative in path.parents
                for path in included_paths
            ):
                continue
            target = target_root / child_relative

            if child.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                copy_node(child, child_relative)
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
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
    parser.add_argument(
        "--full",
        action="store_true",
        help="Initialize the delivery surface instead of the default content surface.",
    )
    args = parser.parse_args()

    template_root = Path(args.template).resolve()
    target_root = Path(args.project).resolve()

    if not template_root.exists():
        print(f"ERROR: template not found: {template_root}")
        return 1

    target_root.mkdir(parents=True, exist_ok=True)
    use_delivery = args.full or project_surface(target_root) == DELIVERY_SURFACE
    copy = copy_template if use_delivery else copy_content_template
    created, skipped = copy(template_root, target_root)
    if use_delivery:
        set_project_surface(target_root, DELIVERY_SURFACE)
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
