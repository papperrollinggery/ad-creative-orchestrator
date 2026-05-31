#!/usr/bin/env python3
"""Initialize a project from templates/project without overwriting files."""

from __future__ import annotations

import argparse
from pathlib import Path

from runtime_paths import template_root as default_template_root


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

    print(f"PROJECT={target_root}")
    print(f"CREATED_FILES={created}")
    print(f"SKIPPED_EXISTING_FILES={skipped}")
    print("INIT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
