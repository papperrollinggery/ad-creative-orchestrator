#!/usr/bin/env python3
"""Runtime paths for source and installed package modes."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


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
