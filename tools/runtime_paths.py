#!/usr/bin/env python3
"""Runtime paths for source and installed package modes."""

from __future__ import annotations

from importlib.resources import files
import json
from pathlib import Path
import re


def source_root() -> Path | None:
    candidate = Path(__file__).resolve().parents[1]
    if (candidate / "templates/project").exists():
        return candidate
    return None


def repo_or_module_root() -> Path:
    return source_root() or Path(__file__).resolve().parent


def packaged_assets_root() -> Path:
    return Path(files("adco_resources"))


def template_root() -> Path:
    root = source_root()
    if root:
        return root / "templates/project"
    return packaged_assets_root() / "templates/project"


def skill_draft_dir() -> Path:
    root = source_root()
    if root:
        return root / "skill_drafts/ad-creative-orchestrator"
    return packaged_assets_root() / "skill_drafts/ad-creative-orchestrator"


def published_docs_root() -> Path:
    root = source_root()
    if root:
        return root
    return packaged_assets_root() / "published_docs"


CONTROL_PLANE_SCHEMA_REL = Path("AD-creative/orchestrator/control_plane_schema.json")
PROJECT_CONFIG_REL = Path("AD-creative/orchestrator/project.yml")


def is_adco_source_repository(candidate: Path) -> bool:
    """Return True only for an ADCO source checkout root, never a project fixture."""
    root = candidate.resolve()
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return False
    try:
        metadata = pyproject.read_text(encoding="utf-8")
    except OSError:
        return False
    return (
        'name = "ad-creative-orchestrator"' in metadata
        and (root / "tools/ad_creative_operator.py").is_file()
        and (root / "skill_drafts/ad-creative-orchestrator/SKILL.md").is_file()
    )


def is_initialized_adco_project(candidate: Path) -> bool:
    """Recognize a runtime project only from its valid local control-plane marker."""
    root = candidate.resolve()
    if is_adco_source_repository(root):
        return False
    schema_path = root / CONTROL_PLANE_SCHEMA_REL
    project_path = root / PROJECT_CONFIG_REL
    if not schema_path.is_file() or not project_path.is_file():
        return False
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        project_text = project_path.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError):
        return False
    schema_version = schema.get("schema_version") if isinstance(schema, dict) else None
    schema_id = schema.get("schema_id") if isinstance(schema, dict) else None
    if schema_id != "adco.control-plane" or not isinstance(schema_version, str):
        return False
    return re.search(
        rf'(?m)^  schema_version:[ \t]*["\']?{re.escape(schema_version)}["\']?[ \t]*$',
        project_text,
    ) is not None
