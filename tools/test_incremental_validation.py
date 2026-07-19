#!/usr/bin/env python3
"""Regression checks for dependency-aware validation and lightweight `adco run`."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from adco_core.incremental_validation import plan_incremental_validation
from runtime_paths import source_root


SOURCE_ROOT = source_root()


def test_dependency_plans_do_not_run_unaffected_delivery_validators() -> None:
    intake = plan_incremental_validation(
        changed_file_paths=[
            "AD-creative/orchestrator/evidence_chunks.jsonl",
            "AD-creative/orchestrator/fact_inventory.jsonl",
            "AD-creative/orchestrator/requirements.csv",
        ]
    )
    assert intake["validators_run"] == [
        "validate_evidence_chunks",
        "validate_fact_inventory",
        "validate_requirements_gaps",
    ]
    assert intake["full_validation_required"] is False
    for forbidden in [
        "validate_ppt",
        "validate_client_package",
        "validate_final_delivery",
    ]:
        assert forbidden in intake["validators_skipped"]

    candidate = plan_incremental_validation(
        changed_artifact_ids=["ART-AUTO-CREATIVE-CANDIDATE"]
    )
    assert candidate["validators_run"] == ["validate_creative_candidate"]
    assert candidate["full_validation_required"] is False

    ppt = plan_incremental_validation(changed_file_paths=["AD-creative/ppt/exports/deck.pptx"])
    assert ppt["full_validation_required"] is True


def test_default_run_is_content_first_zero_dashboard_and_timed() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-run-latency-") as raw:
        project = Path(raw) / "project"
        material = Path(raw) / "brief.md"
        material.write_text(
            "客户已提供产品图。客户要求交付可编辑广告提案。\n"
            + ("长资料必须完整读取。" * 1600)
            + "END-OF-MATERIAL",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        operator = (
            [str(SOURCE_ROOT / "tools/ad_creative_operator.py")]
            if SOURCE_ROOT
            else ["-m", "ad_creative_operator"]
        )
        completed = subprocess.run(
            [
                sys.executable,
                *operator,
                "run",
                str(project),
                "--material",
                str(material),
                "--goal",
                "整理已提供资料，不自动进入创意或交付。",
                "--json",
            ],
            cwd=SOURCE_ROOT or Path(raw),
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        payload = json.loads(completed.stdout)
        assert payload["dashboard_render_count"] == 0
        assert payload["dashboard"] == ""
        assert payload["council_run_count"] == 0
        assert payload["specialist_handoff_count"] == 0
        assert payload["ppt_auto_generated"] == 0
        assert payload["client_pack_run_count"] == 0
        assert payload["full_validation_run_count"] == 0
        assert payload["content_answer"]["objective"]
        assert payload["content_answer"]["next_action"]
        assert payload["content_answer"]["markdown"].startswith("## 当前目标")
        assert payload["intake"]["characters_read"] > 12_000
        assert payload["intake"]["evidence_chunks"] > 1
        assert "validate_final_delivery" in payload["incremental_validation"][
            "validators_skipped"
        ]
        assert not (
            project / "AD-creative/gates/THREE-COUNCIL-READINESS_report.md"
        ).exists()
        assert not (project / "AD-creative/handoff/操作台.html").exists()
        assert not (project / "AD-creative/orchestrator/artifact_index.csv").exists()
        assert len([path for path in project.rglob("*") if path.is_file()]) <= 12
        timings = payload["timings"]
        assert set(timings) == {
            "parse_ms",
            "fact_analysis_ms",
            "write_ms",
            "dashboard_ms",
            "validation_ms",
            "total_ms",
        }
        assert all(isinstance(value, int) and value >= 0 for value in timings.values())
        assert timings["total_ms"] < 20_000


def main() -> int:
    test_dependency_plans_do_not_run_unaffected_delivery_validators()
    test_default_run_is_content_first_zero_dashboard_and_timed()
    print("TEST_INCREMENTAL_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
