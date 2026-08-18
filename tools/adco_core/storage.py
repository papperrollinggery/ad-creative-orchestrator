"""Read-only project storage audit and organization recommendations."""

from __future__ import annotations

import hashlib
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .safe_write import sha256_project_file


PROJECT_METADATA = {
    "AGENTS.md",
    "README.md",
    "project.yml",
    ".gitignore",
}
MANAGED_ROOTS = {"AD-creative", ".adco-local"}
ZONE_PREFIXES = ("00_", "01_", "02_", "03_", "04_", "05_")
IGNORED_PARTS = {
    ".adco-local",
    ".dircreative",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
}
MEDIA_SUFFIXES = {
    ".3gp",
    ".aac",
    ".aif",
    ".aiff",
    ".avi",
    ".flac",
    ".gif",
    ".heic",
    ".jpeg",
    ".jpg",
    ".m4a",
    ".m4v",
    ".mov",
    ".mp3",
    ".mp4",
    ".png",
    ".psd",
    ".svg",
    ".tif",
    ".tiff",
    ".wav",
    ".webm",
}
KEY_ASSET_MARKERS = {
    "brand",
    "keyvisual",
    "key_visual",
    "kv",
    "logo",
    "packshot",
    "product",
    "品牌",
    "包装",
    "定装",
    "产品",
    "标志",
}


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_PARTS for part in path.parts) or path.name == ".DS_Store"


def _iter_regular_files(path: Path, errors: list[str]) -> Iterable[Path]:
    """Walk without following symlinks and make every traversal failure visible."""

    def walk(directory: Path) -> Iterable[Path]:
        try:
            entries = sorted(os.scandir(directory), key=lambda item: item.name)
        except OSError as exc:
            errors.append(f"{directory}: {exc}")
            return
        for entry in entries:
            candidate = Path(entry.path)
            if _is_ignored(candidate):
                continue
            try:
                if entry.is_symlink():
                    continue
                if entry.is_file(follow_symlinks=False):
                    yield candidate
                elif entry.is_dir(follow_symlinks=False):
                    yield from walk(candidate)
            except OSError as exc:
                errors.append(f"{candidate}: {exc}")

    try:
        info = path.lstat()
    except OSError as exc:
        errors.append(f"{path}: {exc}")
        return
    if stat.S_ISLNK(info.st_mode):
        return
    if stat.S_ISREG(info.st_mode):
        if not _is_ignored(path):
            yield path
        return
    if stat.S_ISDIR(info.st_mode):
        yield from walk(path)


def _sha256(
    path: Path,
    *,
    project: Path | None = None,
    expected_identity: tuple[int, int, int] | None = None,
) -> str:
    if project is not None:
        try:
            path.absolute().relative_to(project.absolute())
        except ValueError:
            pass
        else:
            return sha256_project_file(
                project,
                path,
                expected_identity=expected_identity,
            )

    digest = hashlib.sha256()
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise OSError("storage audit target is not a regular file")
        identity = (opened.st_dev, opened.st_ino, opened.st_size)
        stable_identity = (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
            opened.st_ctime_ns,
        )
        if expected_identity is not None and identity != expected_identity:
            raise OSError("file changed before storage audit hashing")
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        current_descriptor = os.fstat(descriptor)
        if (
            current_descriptor.st_dev,
            current_descriptor.st_ino,
            current_descriptor.st_size,
            current_descriptor.st_mtime_ns,
            current_descriptor.st_ctime_ns,
        ) != stable_identity:
            raise OSError("file changed during storage audit hashing")
    finally:
        os.close(descriptor)
    current = path.lstat()
    if (
        current.st_dev,
        current.st_ino,
        current.st_size,
        current.st_mtime_ns,
        current.st_ctime_ns,
    ) != stable_identity:
        raise OSError("file path changed during storage audit hashing")
    return digest.hexdigest()


def _display_path(project: Path, path: Path) -> str:
    try:
        return path.absolute().relative_to(project.absolute()).as_posix()
    except ValueError:
        return str(path.absolute())


def _zone_for_path(project: Path, path: Path) -> str:
    display = _display_path(project, path)
    first = display.split("/", 1)[0]
    if first.startswith("00_"):
        return "project_material"
    if first.startswith("01_"):
        return "reference"
    if first.startswith("02_"):
        return "key_asset"
    if first.startswith("03_"):
        return "work_in_progress"
    if first.startswith("04_"):
        return "client_review"
    if first.startswith("05_"):
        return "protected_final_delivery"
    lowered = display.lower()
    if "/visual_assets/raw/" in f"/{lowered}":
        return "key_asset"
    if "preview" in lowered:
        return "preview"
    if "contact" in lowered and "sheet" in lowered:
        return "contact_sheet"
    if "version_archive" in lowered or "archive" in lowered or "backup" in lowered:
        return "archive_copy"
    return "unclassified"


def _suggest_destination(path: Path) -> tuple[str, str]:
    lowered = path.name.lower()
    suffix = path.suffix.lower()
    if any(marker in lowered for marker in KEY_ASSET_MARKERS):
        return "02_关键资产_KeyAssets/", "文件名显示它可能是品牌、产品或定装资产"
    if suffix in MEDIA_SUFFIXES:
        return "01_参考资料_References/", "媒体文件默认作为参考，确认后再升级为关键资产"
    if any(
        marker in lowered
        for marker in ("review", "feedback", "客户反馈", "审阅", "批注", "反馈")
    ):
        return "04_客户审阅_ClientReview/", "文件名显示它可能是客户审阅或反馈材料"
    if suffix in {".ppt", ".pptx", ".key", ".pdf"} and any(
        marker in lowered for marker in ("draft", "wip", "方案", "提案")
    ):
        return "03_阶段成果_WorkInProgress/", "文件名显示它可能是工作版本"
    return "00_项目资料_ProjectMaterials/", "默认归入项目事实与原始资料"


def _canonical_priority(zone: str) -> int:
    return {
        "key_asset": 0,
        "project_material": 1,
        "reference": 2,
        "protected_final_delivery": 3,
        "client_review": 4,
        "work_in_progress": 5,
        "unclassified": 6,
        "archive_copy": 7,
        "preview": 8,
        "contact_sheet": 9,
    }.get(zone, 10)


def root_loose_files(project: Path) -> list[Path]:
    if not project.is_dir():
        return []
    return [
        path
        for path in sorted(project.iterdir())
        if path.is_file()
        and not path.is_symlink()
        and path.name not in PROJECT_METADATA
        and not path.name.startswith(".")
    ]


def root_unorganized_entries(project: Path) -> list[Path]:
    if not project.is_dir():
        return []
    entries = []
    for path in sorted(project.iterdir()):
        if path.is_symlink() or path.name.startswith("."):
            continue
        if path.name in PROJECT_METADATA or path.name in MANAGED_ROOTS:
            continue
        if path.is_dir() and path.name.startswith(ZONE_PREFIXES):
            continue
        if path.is_file() or path.is_dir():
            entries.append(path)
    return entries


def audit_project_storage(
    project: Path,
    *,
    material_paths: Iterable[Path] = (),
    deep: bool = False,
) -> dict[str, object]:
    """Inspect storage without creating, moving, copying, or deleting files."""
    requested_project = project.expanduser().absolute()
    project = requested_project.resolve()
    errors: list[str] = []
    if requested_project.is_symlink():
        errors.append(f"project root must not be a symlink: {requested_project}")
    elif not requested_project.exists():
        errors.append(f"project root does not exist: {requested_project}")
    elif not requested_project.is_dir():
        errors.append(f"project root is not a directory: {requested_project}")
    root_valid = not errors
    loose = root_loose_files(project) if root_valid else []
    unorganized = root_unorganized_entries(project) if root_valid else []
    scopes = list(material_paths)
    if deep and root_valid:
        scopes = [project]
    elif not scopes:
        scopes = loose

    paths: dict[str, Path] = {}
    for scope in scopes:
        for path in _iter_regular_files(scope.expanduser().absolute(), errors):
            paths[str(path.absolute())] = path
    for path in loose:
        paths.setdefault(str(path.absolute()), path)

    inventory: list[dict[str, object]] = []
    size_groups: dict[int, list[dict[str, object]]] = {}
    for path in sorted(paths.values(), key=lambda item: _display_path(project, item)):
        try:
            path_stat = path.lstat()
        except OSError as exc:
            errors.append(f"{_display_path(project, path)}: {exc}")
            continue
        if not stat.S_ISREG(path_stat.st_mode):
            errors.append(
                f"{_display_path(project, path)}: storage audit target is no longer a regular file"
            )
            continue
        row: dict[str, object] = {
            "path": _display_path(project, path),
            "size_bytes": path_stat.st_size,
            "zone": _zone_for_path(project, path),
            "device": path_stat.st_dev,
            "inode": path_stat.st_ino,
            "_path": path,
        }
        inventory.append(row)
        # Empty placeholders consume no duplicate storage and are usually control
        # files, so exclude them from duplicate groups while keeping them in the
        # scanned inventory.
        if path_stat.st_size > 0:
            size_groups.setdefault(path_stat.st_size, []).append(row)

    hash_groups: dict[str, list[dict[str, object]]] = {}
    for same_size in size_groups.values():
        if len(same_size) < 2:
            continue
        for row in same_size:
            path = row["_path"]
            assert isinstance(path, Path)
            try:
                digest = _sha256(
                    path,
                    project=project,
                    expected_identity=(
                        int(row["device"]),
                        int(row["inode"]),
                        int(row["size_bytes"]),
                    ),
                )
            except (OSError, ValueError) as exc:
                errors.append(f"{row['path']}: {exc}")
                continue
            row["sha256"] = digest
            hash_groups.setdefault(digest, []).append(row)

    duplicate_groups: list[dict[str, object]] = []
    reclaimable = 0
    for digest, rows in hash_groups.items():
        if len(rows) < 2:
            continue
        ordered = sorted(
            rows,
            key=lambda row: (_canonical_priority(str(row["zone"])), str(row["path"])),
        )
        unique_inodes = {(row["device"], row["inode"]) for row in ordered}
        group_reclaimable = int(ordered[0]["size_bytes"]) * max(0, len(unique_inodes) - 1)
        reclaimable += group_reclaimable
        duplicate_groups.append(
            {
                "sha256": digest,
                "size_bytes": ordered[0]["size_bytes"],
                "canonical_path": ordered[0]["path"],
                "duplicate_paths": [row["path"] for row in ordered[1:]],
                "zones": [row["zone"] for row in ordered],
                "contains_protected_final": any(
                    row["zone"] == "protected_final_delivery" for row in ordered
                ),
                "hardlinked_paths": len(ordered) - len(unique_inodes),
                "reclaimable_bytes": group_reclaimable,
                "recommended_action": (
                    "protect_final_and_review_other_copies"
                    if any(row["zone"] == "protected_final_delivery" for row in ordered)
                    else "keep_one_canonical_byte_owner_after_confirmation"
                ),
            }
        )
    duplicate_groups.sort(
        key=lambda group: (-int(group["reclaimable_bytes"]), str(group["canonical_path"]))
    )

    suggestions = []
    for path in unorganized:
        destination, reason = _suggest_destination(path)
        suggestions.append(
            {
                "path": _display_path(project, path),
                "entry_type": "folder" if path.is_dir() else "file",
                "suggested_destination": destination,
                "reason": reason,
                "action": "ask_before_move",
            }
        )

    audit_complete = not errors
    return {
        "schema": "adco.storage-audit@1.0",
        "status": "PASS" if audit_complete else "INCOMPLETE",
        "audit_complete": audit_complete,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": str(project),
        "scope": "project_deep" if deep else "materials_and_project_root",
        "read_only": True,
        "files_scanned": len(inventory),
        "bytes_scanned": sum(int(row["size_bytes"]) for row in inventory),
        "root_loose_file_count": len(loose),
        "root_loose_files": [_display_path(project, path) for path in loose],
        "root_unorganized_entry_count": len(unorganized),
        "root_unorganized_entries": [
            _display_path(project, path) for path in unorganized
        ],
        "organization_suggestions": suggestions,
        "organization_suggestion_count": len(suggestions),
        "duplicate_group_count": len(duplicate_groups),
        # Path aliases and hard links are still useful diagnostics, but only
        # independent inodes represent another physical byte owner.
        "duplicate_path_count": sum(
            len(group["duplicate_paths"]) for group in duplicate_groups
        ),
        "duplicate_file_count": sum(
            int(group["reclaimable_bytes"]) // int(group["size_bytes"])
            for group in duplicate_groups
            if int(group["size_bytes"]) > 0
        ),
        "reclaimable_bytes": reclaimable,
        "duplicate_groups": duplicate_groups,
        "errors": errors,
        "organization_recommended": bool(suggestions or duplicate_groups),
        "policy": {
            "canonical_byte_owner": "one",
            "intake": "reference material in place; do not copy source bytes",
            "views_and_meeting_packs": "reference_or_index; do not copy source bytes",
            "final_delivery": "protected; never move, overwrite, or delete automatically",
            "mutation": "requires explicit user confirmation and a reviewed plan",
        },
    }


def cleanup_actions(audit: dict[str, object]) -> list[str]:
    actions = [
        f"{item['path']} => ASK_BEFORE_MOVE_TO {item['suggested_destination']}"
        for item in audit.get("organization_suggestions", [])
        if isinstance(item, dict)
    ]
    for group in audit.get("duplicate_groups", []):
        if not isinstance(group, dict):
            continue
        action = (
            "PROTECT_FINAL_AND_REVIEW_OTHER_COPIES"
            if group.get("contains_protected_final")
            else "REVIEW_KEEP_ONE_CANONICAL_BYTE_OWNER"
        )
        size_bytes = int(group.get("size_bytes") or 0)
        independent_copies = (
            int(group.get("reclaimable_bytes") or 0) // size_bytes
            if size_bytes > 0
            else 0
        )
        hardlinked_paths = int(group.get("hardlinked_paths") or 0)
        actions.append(
            f"{group.get('canonical_path', '')} <= "
            f"independent_duplicate_byte_owners={independent_copies}; "
            f"hardlinked_paths={hardlinked_paths} => {action}"
        )
    return actions
