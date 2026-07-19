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
CONTENT_SURFACE = "content"
DELIVERY_SURFACE = "delivery"
DELIVERY_SURFACE_EVIDENCE_RELS = (
    Path("AD-creative/orchestrator/artifact_index.csv"),
    Path("AD-creative/orchestrator/version_map.csv"),
    Path("AD-creative/orchestrator/gate_log.csv"),
    Path("AD-creative/orchestrator/work_items.csv"),
    Path("AD-creative/orchestrator/thread_registry.csv"),
    Path("AD-creative/orchestrator/final_delivery_lock.csv"),
    Path("AD-creative/client_review/client_outline.csv"),
    Path("AD-creative/visual_assets/asset_registry.csv"),
)


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


def declared_project_surface(candidate: Path) -> str | None:
    """Read only the explicit runtime surface declaration, if one exists."""
    project_path = candidate.resolve() / PROJECT_CONFIG_REL
    if project_path.is_file():
        try:
            project_text = project_path.read_text(encoding="utf-8")
        except OSError:
            project_text = ""
        match = re.search(
            r'(?m)^  surface:[ \t]*["\']?(content|delivery)["\']?[ \t]*$',
            project_text,
        )
        if match:
            return match.group(1)
    return None


def delivery_surface_evidence(candidate: Path) -> tuple[Path, ...]:
    """Return Delivery-only ledgers that make a Content declaration unsafe."""
    root = candidate.resolve()
    return tuple(
        rel_path
        for rel_path in DELIVERY_SURFACE_EVIDENCE_RELS
        if (root / rel_path).exists()
    )


def project_surface_conflict(candidate: Path) -> str:
    """Describe an unsafe explicit Content declaration over Delivery evidence."""
    if declared_project_surface(candidate) != CONTENT_SURFACE:
        return ""
    evidence = delivery_surface_evidence(candidate)
    if not evidence:
        return ""
    paths = ";".join(str(path) for path in evidence)
    return (
        "runtime surface conflict: project declares content while Delivery-only "
        f"evidence exists ({paths}); run adco init <project> --full or a real "
        "delivery migration before continuing"
    )


def project_surface(candidate: Path) -> str:
    """Resolve the safe runtime surface; legacy or conflicting projects fail closed."""
    declared = declared_project_surface(candidate)
    if declared == DELIVERY_SURFACE:
        return DELIVERY_SURFACE
    if declared == CONTENT_SURFACE:
        return (
            DELIVERY_SURFACE
            if delivery_surface_evidence(candidate)
            else CONTENT_SURFACE
        )
    if (candidate.resolve() / PROJECT_CONFIG_REL).is_file():
        # Every pre-surface project.yml predates the content-first runtime and
        # therefore represents the historical full Delivery Surface. Do not
        # infer its mode from a secondary ledger: that ledger may be the very
        # file validation needs to report or repair.
        return DELIVERY_SURFACE
    return CONTENT_SURFACE


def set_project_surface(candidate: Path, surface: str) -> None:
    """Persist a supported runtime surface without rewriting unrelated config."""
    if surface not in {CONTENT_SURFACE, DELIVERY_SURFACE}:
        raise ValueError(f"unsupported ADCO project surface: {surface}")
    project_path = candidate.resolve() / PROJECT_CONFIG_REL
    original = project_path.read_text(encoding="utf-8")
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
    if text != original:
        project_path.write_text(text, encoding="utf-8")
