"""Small, dependency-free helpers for fail-closed project artifact I/O."""

from __future__ import annotations

import errno
import os
import secrets
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


_DIRECTORY_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(
    os, "O_NOFOLLOW", 0
)
_READ_FLAGS = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
_WRITE_FLAGS = (
    os.O_WRONLY
    | os.O_CREAT
    | os.O_EXCL
    | getattr(os, "O_NOFOLLOW", 0)
)


def _absolute_lexical(path: Path) -> Path:
    """Normalize ``.``/``..`` without following symlinks."""
    return Path(os.path.abspath(os.fspath(path)))


def _require_anchored_io() -> None:
    """Fail closed on platforms without the POSIX primitives used below."""
    required = (os.open, os.mkdir, os.stat, os.unlink, os.rename)
    if (
        os.name != "posix"
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or any(function not in os.supports_dir_fd for function in required)
    ):
        raise OSError(
            errno.ENOTSUP,
            "secure project artifact I/O requires POSIX dir_fd, O_DIRECTORY, and O_NOFOLLOW support",
        )


def _target_parts(project: Path, path: Path) -> tuple[Path, Path, tuple[str, ...]]:
    root = _absolute_lexical(project)
    target = _absolute_lexical(path)
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"project artifact escapes project root: {path}") from exc
    parts = relative.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"project artifact must name a file below project root: {path}")
    return root, target, parts


def _component_error(parent_fd: int, name: str, display: Path) -> ValueError:
    try:
        info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError:
        return ValueError(f"project artifact parent is not a directory: {display}")
    if stat.S_ISLNK(info.st_mode):
        return ValueError(f"project artifact parent must not be a symlink: {display}")
    return ValueError(f"project artifact parent is not a directory: {display}")


@contextmanager
def _anchored_parent(
    project: Path,
    path: Path,
    *,
    create_parent: bool,
) -> Iterator[tuple[int, str, Path]]:
    """Yield an open parent directory and basename anchored below ``project``.

    Every component is opened relative to the preceding directory descriptor.
    Concurrent renames or symlink swaps therefore cannot redirect the eventual
    read or write to a different filesystem path.
    """
    _require_anchored_io()
    root, target, parts = _target_parts(project, path)
    try:
        root_fd = os.open(root, _DIRECTORY_FLAGS)
    except OSError as exc:
        raise ValueError(
            f"project root is missing, not a directory, or a symlink: {root}"
        ) from exc
    current_fd = root_fd
    try:
        if not stat.S_ISDIR(os.fstat(root_fd).st_mode):
            raise ValueError(f"project root is not a directory: {root}")
        current_display = root
        for part in parts[:-1]:
            current_display = current_display / part
            try:
                next_fd = os.open(part, _DIRECTORY_FLAGS, dir_fd=current_fd)
            except FileNotFoundError:
                if not create_parent:
                    raise ValueError(
                        f"project artifact parent is missing: {current_display}"
                    ) from None
                try:
                    os.mkdir(part, mode=0o700, dir_fd=current_fd)
                except FileExistsError:
                    # Another actor won the create race. Opening with
                    # O_NOFOLLOW below still decides whether it is safe.
                    pass
                try:
                    next_fd = os.open(part, _DIRECTORY_FLAGS, dir_fd=current_fd)
                except OSError as exc:
                    raise _component_error(current_fd, part, current_display) from exc
            except OSError as exc:
                raise _component_error(current_fd, part, current_display) from exc
            if current_fd != root_fd:
                os.close(current_fd)
            current_fd = next_fd
        yield current_fd, parts[-1], target
    finally:
        if current_fd != root_fd:
            os.close(current_fd)
        os.close(root_fd)


def _target_stat(parent_fd: int, name: str, target: Path) -> os.stat_result | None:
    try:
        info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(info.st_mode):
        raise ValueError(f"project artifact must not be a symlink: {target}")
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"project artifact is not a regular file: {target}")
    return info


def safe_project_path(
    project: Path,
    path: Path,
    *,
    create_parent: bool = False,
    require_file: bool = False,
) -> Path:
    """Validate one lexical project path without following symlinks.

    This function is useful for preflight checks only. Callers that consume or
    mutate file bytes must use :func:`read_project_bytes` or
    :func:`atomic_write_bytes`, which keep the parent directory descriptor open
    for the complete operation.
    """
    with _anchored_parent(project, path, create_parent=create_parent) as (
        parent_fd,
        name,
        target,
    ):
        info = _target_stat(parent_fd, name, target)
        if require_file and info is None:
            raise ValueError(f"project artifact is missing: {target}")
        return target


def read_project_bytes(project: Path, path: Path) -> bytes:
    """Read a project-local regular file through an anchored descriptor."""
    with _anchored_parent(project, path, create_parent=False) as (
        parent_fd,
        name,
        target,
    ):
        try:
            descriptor = os.open(name, _READ_FLAGS, dir_fd=parent_fd)
        except FileNotFoundError:
            raise ValueError(f"project artifact is missing: {target}") from None
        except OSError as exc:
            # ELOOP/ENOTDIR differ across supported POSIX kernels for a final
            # symlink. A no-follow stat provides a stable user-facing error.
            _target_stat(parent_fd, name, target)
            raise ValueError(f"project artifact cannot be opened safely: {target}") from exc
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise ValueError(f"project artifact is not a regular file: {target}")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    return b"".join(chunks)
                chunks.append(chunk)
        finally:
            os.close(descriptor)


def read_project_text(project: Path, path: Path, *, encoding: str = "utf-8") -> str:
    return read_project_bytes(project, path).decode(encoding)


def atomic_write_bytes(project: Path, path: Path, data: bytes) -> Path:
    """Atomically replace one project-local file without a pathname race."""
    if not isinstance(data, bytes):
        raise TypeError("atomic_write_bytes data must be bytes")
    with _anchored_parent(project, path, create_parent=True) as (
        parent_fd,
        name,
        target,
    ):
        existing = _target_stat(parent_fd, name, target)
        mode = stat.S_IMODE(existing.st_mode) if existing is not None else 0o600
        temp_name = f".adco-tmp-{secrets.token_hex(16)}"
        descriptor = os.open(temp_name, _WRITE_FLAGS, mode, dir_fd=parent_fd)
        temp_exists = True
        try:
            os.fchmod(descriptor, mode)
            view = memoryview(data)
            written = 0
            while written < len(view):
                try:
                    count = os.write(descriptor, view[written:])
                except InterruptedError:
                    continue
                if count <= 0:
                    raise OSError(errno.EIO, "short write to project artifact")
                written += count
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = -1

            # POSIX renameat replaces the directory entry itself. If an
            # attacker races in a symlink after _target_stat, the symlink is
            # replaced rather than followed; both directory descriptors refer
            # to the already-open safe parent.
            os.rename(
                temp_name,
                name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
            temp_exists = False
            os.fsync(parent_fd)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if temp_exists:
                try:
                    os.unlink(temp_name, dir_fd=parent_fd)
                except FileNotFoundError:
                    pass
        return target


def atomic_write_text(
    project: Path,
    path: Path,
    text: str,
    *,
    encoding: str = "utf-8",
) -> Path:
    return atomic_write_bytes(project, path, text.encode(encoding))
