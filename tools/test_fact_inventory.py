#!/usr/bin/env python3
"""Regression checks for evidence-bound facts and non-inverted gaps."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ad_creative_operator import ensure_project, gap_templates
from adco_core.facts import (
    export_intake_analysis_request,
    import_intake_analysis,
    run_evidence_intake,
)


def _row(source_id: str, path: Path, project: Path) -> dict[str, str]:
    return {
        "source_event_id": source_id,
        "file_paths": path.relative_to(project).as_posix(),
        "declared_semantics": "fact fixture",
    }


def test_present_assets_do_not_become_false_gaps() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-facts-present-") as raw:
        project = Path(raw)
        ensure_project(project)
        source = project / "brief.md"
        source.write_text(
            "客户已提供产品图，附件中有品牌 logo。客户要求交付可编辑 PPTX。",
            encoding="utf-8",
        )
        result = run_evidence_intake(project, [_row("SRC-001", source, project)])
        facts = {fact.fact_key: fact for fact in result.facts}
        assert facts["asset.product_images"].state == "present"
        assert facts["brand.logo"].state == "present"
        assert all("asset.product_images" not in gap["description"] for gap in result.new_gaps)
        assert all("brand.logo" not in gap["description"] for gap in result.new_gaps)
        assert gap_templates([], source.read_text(encoding="utf-8")) == []


def test_conflict_and_blocking_unknown_create_evidence_bound_gaps() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-facts-conflict-") as raw:
        project = Path(raw)
        ensure_project(project)
        present = project / "present.md"
        missing = project / "missing.md"
        present.write_text("客户已提供产品图。", encoding="utf-8")
        missing.write_text("客户尚未提供产品图。", encoding="utf-8")
        first = run_evidence_intake(project, [_row("SRC-001", present, project)])
        second = run_evidence_intake(project, [_row("SRC-002", missing, project)])
        facts = {fact.fact_key: fact for fact in second.facts}
        assert facts["asset.product_images"].state == "conflicting"
        assert len(facts["asset.product_images"].evidence_refs) == 2
        assert any("asset.product_images 冲突" in gap["description"] for gap in second.new_gaps)

        request, request_path = export_intake_analysis_request(project)
        assert request_path.is_file()
        evidence_id = request["evidence_chunks"][0]["chunk_id"]
        analysis_path = project / "analysis.json"
        analysis_path.write_text(
            json.dumps(
                {
                    "analysis_version": "1.0",
                    "facts": [
                        {
                            "fact_key": "legal.claims",
                            "state": "unknown",
                            "value": "",
                            "evidence_refs": [evidence_id],
                            "confidence": 0.6,
                            "owner": "client",
                            "blocking": True,
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        _, gaps, _ = import_intake_analysis(project, analysis_path)
        assert any("legal.claims 待确认" in gap["description"] for gap in gaps)

        invalid = project / "invalid-analysis.json"
        invalid.write_text(
            json.dumps(
                {
                    "analysis_version": "1.0",
                    "facts": [
                        {
                            "fact_key": "invalid.ref",
                            "state": "present",
                            "value": "x",
                            "evidence_refs": ["EVC-NOT-REAL"],
                            "confidence": 1.0,
                            "owner": "model",
                            "blocking": False,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        try:
            import_intake_analysis(project, invalid)
        except ValueError as exc:
            assert "evidence_refs" in str(exc)
        else:
            raise AssertionError("analysis with stale evidence_refs must fail")
        assert first.ingestion.chunks


def main() -> int:
    test_present_assets_do_not_become_false_gaps()
    test_conflict_and_blocking_unknown_create_evidence_bound_gaps()
    print("TEST_FACT_INVENTORY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
