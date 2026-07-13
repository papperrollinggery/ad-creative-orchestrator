#!/usr/bin/env python3
"""Verify packaged runtime assets mirror source templates and skill draft."""

from __future__ import annotations

import filecmp
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAIRS = [
    (ROOT / "templates/project", ROOT / "tools/adco_resources/templates/project"),
    (
        ROOT / "skill_drafts/ad-creative-orchestrator",
        ROOT / "tools/adco_resources/skill_drafts/ad-creative-orchestrator",
    ),
]
PUBLISHED_DOC_ROOT_PATHS = [
    Path("README.md"),
    Path("CHANGELOG.md"),
    Path("CONTRIBUTING.md"),
    Path("LICENSE"),
    Path("ROADMAP.md"),
    Path("SECURITY.md"),
]
PUBLISHED_DOCS_ROOT = ROOT / "tools/adco_resources/published_docs"


def published_doc_paths() -> list[Path]:
    paths = list(PUBLISHED_DOC_ROOT_PATHS)
    for directory in [ROOT / "docs/operating", ROOT / "docs/assets"]:
        paths.extend(path.relative_to(ROOT) for path in directory.rglob("*") if path.is_file())
    return sorted(paths)


def compare_dirs(source: Path, packaged: Path) -> list[str]:
    issues: list[str] = []
    source_files = {
        path.relative_to(source): path
        for path in source.rglob("*")
        if path.is_file()
    }
    packaged_files = {
        path.relative_to(packaged): path
        for path in packaged.rglob("*")
        if path.is_file()
    }
    for rel_path in sorted(source_files.keys() - packaged_files.keys()):
        issues.append(f"missing packaged asset: {packaged / rel_path}")
    for rel_path in sorted(packaged_files.keys() - source_files.keys()):
        issues.append(f"extra packaged asset: {packaged / rel_path}")
    for rel_path in sorted(source_files.keys() & packaged_files.keys()):
        if not filecmp.cmp(source_files[rel_path], packaged_files[rel_path], shallow=False):
            issues.append(f"stale packaged asset: {packaged / rel_path}")
    return issues


def main() -> int:
    issues: list[str] = []
    for source, packaged in PAIRS:
        if not source.exists():
            issues.append(f"missing source assets: {source}")
            continue
        if not packaged.exists():
            issues.append(f"missing packaged assets: {packaged}")
            continue
        issues.extend(compare_dirs(source, packaged))
    expected_paths = published_doc_paths()
    expected_packaged_docs = {PUBLISHED_DOCS_ROOT / path for path in expected_paths}
    actual_packaged_docs = {
        path for path in PUBLISHED_DOCS_ROOT.rglob("*") if path.is_file()
    } if PUBLISHED_DOCS_ROOT.exists() else set()
    for rel_path in expected_paths:
        source = ROOT / rel_path
        packaged = PUBLISHED_DOCS_ROOT / rel_path
        if not source.exists():
            issues.append(f"missing published doc source: {source}")
        elif not packaged.exists():
            issues.append(f"missing packaged published doc: {packaged}")
        elif not filecmp.cmp(source, packaged, shallow=False):
            issues.append(f"stale packaged published doc: {packaged}")
    for path in sorted(actual_packaged_docs - expected_packaged_docs):
        issues.append(f"extra packaged published doc: {path}")
    if issues:
        print("PACKAGED_ASSETS_CHECK=FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("PACKAGED_ASSETS_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
