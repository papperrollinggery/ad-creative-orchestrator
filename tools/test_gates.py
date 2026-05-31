#!/usr/bin/env python3
"""Structured regression checks for Gate review behavior."""

from __future__ import annotations

import tempfile
from pathlib import Path

from ad_creative_operator import (
    add_visual_asset,
    ensure_project,
    export_editable_pptx,
    read_csv_rows,
    render_goal_iteration_plan,
    review_client_pack,
    review_handoff_readiness,
    review_reference_pack,
    review_search_quality,
    review_visual_quality,
    write_csv_rows,
    write_text,
)
from validate_project import validate


OPTIONAL_SKIPS: list[str] = []


def assert_valid(project: Path) -> None:
    errors, _ = validate(project)
    if errors:
        raise AssertionError("\n".join(errors))


def add_row(project: Path, rel_path: str, row: dict[str, str]) -> None:
    path = project / rel_path
    fields, rows = read_csv_rows(path)
    if not fields:
        raise AssertionError(f"missing CSV header: {path}")
    rows.append(row)
    write_csv_rows(path, fields, rows)


def add_adversarial_record(project: Path, stage: str = "global") -> None:
    render_goal_iteration_plan(
        project,
        goal_id=f"GOAL-GATE-{stage.upper()}",
        title=f"Gate regression {stage}",
        objective="Verify Gate policy has an adversarial council record.",
        owner="Regression",
    )


def optional_module(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception as exc:  # noqa: BLE001 - tests report optional fixture coverage
        OPTIONAL_SKIPS.append(f"{name}: {exc}")
        return False


def add_requirement(project: Path, requirement_id: str = "REQ-001") -> None:
    add_row(
        project,
        "AD-creative/orchestrator/requirements.csv",
        {
            "requirement_id": requirement_id,
            "source_event_id": "",
            "owner": "operator",
            "statement": "Use internal visual QA fixture for selected asset validation.",
            "requirement_type": "visual",
            "priority": "high",
            "status": "extracted",
            "confidence": "0.90",
            "scope": "project",
            "affected_stage": "visual_review",
            "linked_artifacts": "",
            "supersedes_requirement_id": "",
            "open_questions": "",
        },
    )


def create_png(path: Path, size: tuple[int, int] = (960, 640)) -> None:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, (42, 96, 137))
    image.save(path)


def test_reference_pack_blocks_client_visible_bad_reference() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-gate-ref-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        add_adversarial_record(project)
        add_row(
            project,
            "AD-creative/references/reference_cards.csv",
            {
                "reference_id": "REF-001",
                "source_event_id": "",
                "platform": "unknown",
                "url": "http://example.com",
                "title": "Bad reference",
                "source_owner": "unknown",
                "reference_type": "reference",
                "role": "direction_reference",
                "why_relevant": "",
                "borrow": "",
                "do_not_copy": "",
                "client_visible": "true",
                "notes": "",
            },
        )
        status, findings, _ = review_reference_pack(project)
        assert status == "BLOCKED", (status, findings)
        assert any("https" in item or "do_not_copy" in item for item in findings), findings


def test_search_quality_passes_clean_plan_with_adversarial_record() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-gate-search-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        add_adversarial_record(project)
        write_text(
            project / "AD-creative/references/official_search_plan.md",
            """# Official Search Plan

## Why Search

Verify public, traceable direction references before any client-visible citation.

## Search Scope

Official brand sites, official campaign archives, public video platforms.

## Suggested Platforms

Official website, YouTube, Vimeo.

## Expected Output

Reference cards with source owner, relevance, borrow, and do_not_copy fields.

## do_not_copy

Do not copy logos, layouts, people, product markings, or protected composition.
""",
        )
        status, findings, _ = review_search_quality(project)
        assert status == "PASS", (status, findings)
        assert findings == [], findings
        assert_valid(project)


def test_visual_quality_blocks_missing_selected_asset_file() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-gate-visual-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        add_adversarial_record(project)
        add_row(
            project,
            "AD-creative/visual_assets/asset_manifest.csv",
            {
                "asset_id": "IMG-001",
                "slot_id": "SLOT-001",
                "requirement_id": "REQ-001",
                "reference_id": "",
                "path": "AD-creative/visual_assets/selected/missing.png",
                "asset_type": "uploaded_image",
                "stage": "visual_review",
                "version": "v001",
                "status": "selected",
                "visibility": "internal_only",
                "qa_status": "PASS",
                "risk_level": "low",
                "prompt_or_edit_ref": "",
                "notes": "",
            },
        )
        status, findings, _ = review_visual_quality(project)
        assert status == "BLOCKED", (status, findings)
        assert any("文件不存在" in item for item in findings), findings


def test_visual_quality_passes_real_internal_selected_asset() -> None:
    if not optional_module("PIL"):
        return
    with tempfile.TemporaryDirectory(prefix="adco-gate-visual-pass-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        add_adversarial_record(project)
        add_requirement(project)
        source = project / "fixture/selected.png"
        create_png(source)
        add_visual_asset(
            project,
            source,
            "SLOT-001",
            "REQ-001",
            "",
            "uploaded_image",
            "internal_only",
            "PASS",
            "low",
            "",
            "fixture image for positive visual gate regression",
            selected=True,
        )
        status, findings, _ = review_visual_quality(project)
        assert status == "PASS", (status, findings)
        assert findings == [], findings
        assert_valid(project)


def test_client_pack_blocks_without_editable_pptx() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-gate-client-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        add_adversarial_record(project)
        status, findings, _ = review_client_pack(project)
        assert status == "BLOCKED", (status, findings)
        assert any("PPTX" in item for item in findings), findings
        assert_valid(project)


def test_client_pack_passes_editable_internal_pptx() -> None:
    if not optional_module("pptx"):
        return
    with tempfile.TemporaryDirectory(prefix="adco-gate-client-pass-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        add_adversarial_record(project)
        pptx_path = export_editable_pptx(project)
        status, findings, _ = review_client_pack(project, pptx_path)
        assert status == "PASS", (status, findings)
        assert findings == [], findings
        assert_valid(project)


def test_handoff_readiness_blocks_incomplete_project() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-gate-handoff-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        add_adversarial_record(project)
        status, blockers, warnings, _ = review_handoff_readiness(project)
        assert status == "BLOCKED", (status, blockers, warnings)
        assert any("PPTX" in item or "GATE-" in item for item in blockers + warnings), (
            blockers,
            warnings,
        )
        assert_valid(project)


def main() -> int:
    test_reference_pack_blocks_client_visible_bad_reference()
    test_search_quality_passes_clean_plan_with_adversarial_record()
    test_visual_quality_blocks_missing_selected_asset_file()
    test_visual_quality_passes_real_internal_selected_asset()
    test_client_pack_blocks_without_editable_pptx()
    test_client_pack_passes_editable_internal_pptx()
    test_handoff_readiness_blocks_incomplete_project()
    if OPTIONAL_SKIPS:
        print("TEST_GATES_OPTIONAL_SKIPS=" + "; ".join(OPTIONAL_SKIPS))
    print("TEST_GATES=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
