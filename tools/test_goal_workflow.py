#!/usr/bin/env python3
"""Regression checks for goal-plan and adversarial Gate policy."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from ad_creative_operator import (
    add_reference,
    creative_doctor_report,
    ensure_project,
    import_creative_production_run,
    render_goal_iteration_plan,
    review_film_quality,
    review_reference_pack,
    run_goal,
)
from validate_project import validate


def assert_valid(project: Path) -> None:
    errors, _ = validate(project)
    if errors:
        raise AssertionError("\n".join(errors))


def add_clean_reference(project: Path) -> None:
    add_reference(
        project,
        "https://example.com",
        "Example",
        "direction_reference",
        "official_or_public_reference",
        why_relevant="Evidence source for regression testing.",
        borrow="Structure only.",
        do_not_copy="Do not copy visible identity.",
        live_check=False,
    )


def test_gate_downgrades_without_adversarial_record() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-goal-no-adv-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        add_clean_reference(project)
        status, findings, _ = review_reference_pack(project)
        assert status == "PARTIAL_PASS", status
        assert any("反驳性议会" in item for item in findings), findings
        assert_valid(project)


def test_goal_plan_allows_clean_gate_pass() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-goal-with-adv-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        render_goal_iteration_plan(
            project,
            goal_id="GOAL-REGRESSION-001",
            title="Goal regression",
            objective="Verify adversarial council record allows clean Gate PASS.",
            owner="Regression",
        )
        add_clean_reference(project)
        status, findings, _ = review_reference_pack(project)
        assert status == "PASS", (status, findings)
        assert not findings, findings
        assert_valid(project)


def test_goal_run_stops_without_material() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-goal-run-empty-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        result = run_goal(project, goal_id="latest", max_steps=1, allow_generate=False)
        assert result["stop_reason"] == "NEEDS_MATERIAL", result
        assert (project / "AD-creative/handoff/操作台.html").exists()
        assert_valid(project)


def test_creative_doctor_respects_env_root() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-cp-root-") as raw_root:
        root = Path(raw_root)
        for rel in [
            "skills/ads-explorer/scripts/build_ads_explorer.py",
            "skills/shot-explorer/scripts/create_shot_explorer.py",
            "skills/moodboard-explorer/scripts/create_mood_board.py",
            "scripts/review_renderer.py",
        ]:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# fixture\n", encoding="utf-8")
        old = os.environ.get("ADCO_CREATIVE_PRODUCTION_ROOT")
        os.environ["ADCO_CREATIVE_PRODUCTION_ROOT"] = str(root)
        try:
            status, issues, _, evidence = creative_doctor_report()
        finally:
            if old is None:
                os.environ.pop("ADCO_CREATIVE_PRODUCTION_ROOT", None)
            else:
                os.environ["ADCO_CREATIVE_PRODUCTION_ROOT"] = old
        assert status == "PASS", (status, issues, evidence)


def test_import_creative_production_run_registers_assets() -> None:
    from PIL import Image

    with tempfile.TemporaryDirectory(prefix="adco-cp-import-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        run_dir = project / "cp-run"
        run_dir.mkdir()
        image_path = run_dir / "01-hero.png"
        Image.new("RGB", (900, 640), color=(120, 150, 180)).save(image_path)
        (run_dir / "prompts-manifest.json").write_text(
            """[
  {"id":"hero","title":"Hero","output":"01-hero.png","prompt":"single commercial frame"}
]
""",
            encoding="utf-8",
        )
        (run_dir / "jobs.jsonl").write_text(
            '{"id":"hero","output":"01-hero.png","prompt":"single commercial frame"}\n',
            encoding="utf-8",
        )
        (run_dir / "review-board.html").write_text("<!doctype html><title>Review</title>\n", encoding="utf-8")
        asset_ids, metadata_dir = import_creative_production_run(
            project,
            run_dir=run_dir,
            kind="ads",
            slot_prefix="CP",
        )
        assert len(asset_ids) == 1
        assert (metadata_dir / "manifest.json").exists()
        assert_valid(project)


def test_film_quality_gate_writes_report() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-film-gate-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        status, findings, report = review_film_quality(project)
        assert status == "BLOCKED", (status, findings)
        assert report.exists()
        assert_valid(project)


def main() -> int:
    test_gate_downgrades_without_adversarial_record()
    test_goal_plan_allows_clean_gate_pass()
    test_goal_run_stops_without_material()
    test_creative_doctor_respects_env_root()
    test_import_creative_production_run_registers_assets()
    test_film_quality_gate_writes_report()
    print("TEST_GOAL_WORKFLOW=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
