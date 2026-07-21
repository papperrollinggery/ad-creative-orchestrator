#!/usr/bin/env python3
"""Initialize a project from templates/project without overwriting files."""

from __future__ import annotations

import argparse
import os
import re
import secrets
import stat
from pathlib import Path

from runtime_paths import (
    CONTENT_SURFACE,
    DELIVERY_SURFACE,
    is_initialized_adco_project,
    project_surface,
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


def _assert_safe_target_path(target_root: Path, target: Path) -> None:
    """Reject symlinked managed paths before creating or writing template files."""
    try:
        relative = target.relative_to(target_root)
    except ValueError as exc:
        raise RuntimeError(f"template target escapes project root: {target}") from exc

    if target_root.is_symlink():
        raise RuntimeError(f"project root must not be a symlink: {target_root}")
    root_resolved = target_root.resolve()
    current = target_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeError(f"template target uses a symlink component: {current}")
        if current.exists():
            try:
                current.resolve().relative_to(root_resolved)
            except ValueError as exc:
                raise RuntimeError(
                    f"template target escapes project root after resolution: {current}"
                ) from exc


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
    return _copy_template(
        template_root,
        target_root,
        included_paths=None,
        surface=DELIVERY_SURFACE,
    )


def copy_content_template(template_root: Path, target_root: Path) -> tuple[int, int]:
    return _copy_template(
        template_root,
        target_root,
        included_paths=set(CONTENT_TEMPLATE_RELS),
        surface=CONTENT_SURFACE,
    )


def _open_target_root(target_root: Path) -> int:
    """Open a stable project-root dirfd without following the root as a symlink."""
    if target_root.is_symlink():
        raise RuntimeError(f"project root must not be a symlink: {target_root}")
    if target_root == Path("."):
        return os.open(
            ".",
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
    target_root.parent.mkdir(parents=True, exist_ok=True)
    parent = target_root.parent.resolve(strict=True)
    parent_fd = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        try:
            os.mkdir(target_root.name, mode=0o755, dir_fd=parent_fd)
        except FileExistsError:
            pass
        return os.open(
            target_root.name,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
    finally:
        os.close(parent_fd)


def _open_or_create_dir(parent_fd: int, name: str) -> int:
    try:
        return os.open(
            name,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
    except FileNotFoundError:
        try:
            os.mkdir(name, mode=0o755, dir_fd=parent_fd)
        except FileExistsError:
            pass
        return os.open(
            name,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )


def _read_regular_file(parent_fd: int, name: str) -> tuple[bytes, int]:
    fd = os.open(
        name,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
        dir_fd=parent_fd,
    )
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise RuntimeError(f"template source must be a regular file: {name}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks), stat.S_IMODE(info.st_mode)
    finally:
        os.close(fd)


def _publish_new_file(parent_fd: int, name: str, data: bytes, mode: int) -> bool:
    """Fully write a private temp inode, then atomically publish without clobbering."""
    try:
        existing = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        existing = None
    if existing is not None:
        if stat.S_ISLNK(existing.st_mode) or not stat.S_ISREG(existing.st_mode):
            raise RuntimeError(f"template target is not a regular file: {name}")
        return False

    temp_name = f".adco-tmp-{secrets.token_hex(12)}"
    temp_fd = os.open(
        temp_name,
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0),
        mode=0o600,
        dir_fd=parent_fd,
    )
    try:
        view = memoryview(data)
        while view:
            written = os.write(temp_fd, view)
            view = view[written:]
        os.fchmod(temp_fd, mode & 0o777 or 0o644)
        os.fsync(temp_fd)
    except BaseException:
        os.close(temp_fd)
        try:
            os.unlink(temp_name, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        raise
    else:
        os.close(temp_fd)

    try:
        os.link(
            temp_name,
            name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
            follow_symlinks=False,
        )
    except FileExistsError:
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if stat.S_ISLNK(current.st_mode) or not stat.S_ISREG(current.st_mode):
            raise RuntimeError(f"template target raced to an unsafe file: {name}")
        return False
    finally:
        try:
            os.unlink(temp_name, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
    os.fsync(parent_fd)
    return True


def _open_relative_dir(root_fd: int, relative: Path) -> int:
    current_fd = os.dup(root_fd)
    try:
        for part in relative.parts:
            next_fd = _open_or_create_dir(current_fd, part)
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except BaseException:
        os.close(current_fd)
        raise


def _set_surface_with_dirfd(root_fd: int, surface: str) -> None:
    parent_fd = _open_relative_dir(root_fd, Path("AD-creative/orchestrator"))
    try:
        raw, mode = _read_regular_file(parent_fd, "project.yml")
        original = raw.decode("utf-8")
        text = original
        if re.search(r"(?m)^  surface:", text):
            text = re.sub(
                r'(?m)^  surface:.*$',
                f'  surface: "{surface}"',
                text,
                count=1,
            )
        else:
            marker = "rules:\n"
            if marker not in text:
                text = text.rstrip() + "\n\nruntime:\n" + f'  surface: "{surface}"\n'
            else:
                text = text.replace(
                    marker,
                    f'runtime:\n  surface: "{surface}"\n  governance: "on_demand"\n\n{marker}',
                    1,
                )
        if text == original:
            return
        temp_name = f".adco-surface-{secrets.token_hex(12)}"
        temp_fd = os.open(
            temp_name,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            mode=0o600,
            dir_fd=parent_fd,
        )
        try:
            data = text.encode("utf-8")
            view = memoryview(data)
            while view:
                written = os.write(temp_fd, view)
                view = view[written:]
            os.fchmod(temp_fd, mode & 0o777 or 0o644)
            os.fsync(temp_fd)
        finally:
            os.close(temp_fd)
        try:
            current = os.stat("project.yml", dir_fd=parent_fd, follow_symlinks=False)
            if stat.S_ISLNK(current.st_mode) or not stat.S_ISREG(current.st_mode):
                raise RuntimeError("project.yml raced to an unsafe target")
            os.replace(
                temp_name,
                "project.yml",
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
            os.fsync(parent_fd)
        finally:
            try:
                os.unlink(temp_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
    finally:
        os.close(parent_fd)


def _copy_template(
    template_root: Path,
    target_root: Path,
    *,
    included_paths: set[Path] | None,
    surface: str,
) -> tuple[int, int]:
    if template_root.is_symlink():
        raise RuntimeError(f"template root must not be a symlink: {template_root}")
    source_root_fd = os.open(
        template_root,
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0),
    )
    target_root_fd = _open_target_root(target_root)
    created = 0
    skipped = 0
    checked_targets: set[Path] = {target_root}

    def copy_node(source_fd: int, target_fd: int, relative: Path = Path()) -> None:
        nonlocal created, skipped
        for name in sorted(os.listdir(source_fd)):
            child_info = os.stat(name, dir_fd=source_fd, follow_symlinks=False)
            if stat.S_ISLNK(child_info.st_mode):
                raise RuntimeError(
                    f"template source tree must not contain symlinks: {relative / name}"
                )
            child_relative = relative / name
            if included_paths is not None and not any(
                path == child_relative or child_relative in path.parents
                for path in included_paths
            ):
                continue
            checked_targets.add(target_root / child_relative)

            if stat.S_ISDIR(child_info.st_mode):
                child_source_fd = os.open(
                    name,
                    os.O_RDONLY
                    | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=source_fd,
                )
                child_target_fd = _open_or_create_dir(target_fd, name)
                try:
                    copy_node(child_source_fd, child_target_fd, child_relative)
                finally:
                    os.close(child_source_fd)
                    os.close(child_target_fd)
                continue

            if not stat.S_ISREG(child_info.st_mode):
                raise RuntimeError(f"unsupported template source node: {child_relative}")
            data, mode = _read_regular_file(source_fd, name)
            if _publish_new_file(target_fd, name, data, mode):
                created += 1
            else:
                skipped += 1

    try:
        copy_node(source_root_fd, target_root_fd)
        _set_surface_with_dirfd(target_root_fd, surface)
        for target in sorted(checked_targets):
            _assert_safe_target_path(target_root, target)
        root_stat = os.fstat(target_root_fd)
        path_stat = os.stat(target_root, follow_symlinks=False)
        if (root_stat.st_dev, root_stat.st_ino) != (path_stat.st_dev, path_stat.st_ino):
            raise RuntimeError("project root changed during template initialization")
        return created, skipped
    finally:
        os.close(source_root_fd)
        os.close(target_root_fd)


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
    target_root = Path(args.project).expanduser().absolute()

    if not template_root.exists():
        print(f"ERROR: template not found: {template_root}")
        return 1

    try:
        use_delivery = args.full or project_surface(target_root) == DELIVERY_SURFACE
        copy = copy_template if use_delivery else copy_content_template
        created, skipped = copy(template_root, target_root)
    except (OSError, RuntimeError, ValueError) as exc:
        print("INIT=CHECK")
        print(f"ERROR={exc}")
        return 1
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
