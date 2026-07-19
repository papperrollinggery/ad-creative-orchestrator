#!/usr/bin/env python3
"""Regression checks for creative brief, candidate, and Critic boundaries."""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from ad_creative_operator import ensure_project, render_creative_proposal
from adco_core.creative_contract import (
    BRIEF_CONTRACT_REL,
    BRIEF_SNAPSHOT_REL,
    CANDIDATE_SCHEMA_REL,
    CREATIVE_DIRECTION_FIELDS,
    CURRENT_CANDIDATE_REL,
    create_creative_brief,
    import_creative_candidate,
    review_creative_candidate,
)
from adco_core.facts import run_evidence_intake


def _prepare(project: Path) -> tuple[str, str]:
    ensure_project(project)
    source = project / "brief.md"
    source.write_text(
        "客户已提供产品图和品牌 logo。客户要求面向雨天通勤人群制作可编辑广告提案。",
        encoding="utf-8",
    )
    result = run_evidence_intake(
        project,
        [
            {
                "source_event_id": "SRC-001",
                "file_paths": source.name,
                "declared_semantics": "creative fixture",
            }
        ],
    )
    brief = create_creative_brief(project)
    return brief.snapshot_sha256, result.ingestion.chunks[0].chunk_id


def _direction(number: int, evidence_ref: str) -> dict[str, object]:
    values: dict[str, object] = {
        "direction_id": f"DIR-{number:02d}",
        "name": "雨线显形" if number == 1 else "收纳时刻",
        "human_tension": "通勤者不相信泛泛的防水承诺，只相信眼前可见的具体变化。",
        "brand_truth": "品牌的三层防水结构和可收纳设计均由已绑定资料支持。",
        "audience_truth": "城市通勤人群会在出门前快速判断装备是否值得携带。",
        "single_minded_proposition": "让防护价值在真实动作中被看见。",
        "creative_mechanism": "雨滴路径实时显形" if number == 1 else "一镜到底折叠收纳",
        "key_visual": "雨水沿夹克表面形成清晰分流线并在胸前定格。" if number == 1 else "夹克从穿着状态连续折叠进入通勤包侧袋。",
        "story_or_behavior": "镜头跟随通勤者穿过雨幕，防护效果通过连续动作而非旁白完成证明。" if number == 1 else "镜头从办公室门口跟随人物收纳夹克并切换到周末步道使用。",
        "product_role": "产品是完成防护或收纳动作的因果核心，不是背景道具。",
        "channel_execution": "15 秒竖屏视频与一张动作中段关键视觉。",
        "why_brand_can_own_it": "该机制直接依赖资料中已确认的三层面料与可收纳结构，替换普通品牌后因果链会失效。",
        "production_risk": "需要可控降雨、连续动作排练和面料反光测试。",
        "evidence_refs": [evidence_ref],
    }
    assert set(values) == set(CREATIVE_DIRECTION_FIELDS)
    return values


def test_brief_generates_contracts_not_directions() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-brief-") as raw:
        project = Path(raw)
        snapshot_sha, _ = _prepare(project)
        assert (project / BRIEF_SNAPSHOT_REL).is_file()
        assert (project / BRIEF_CONTRACT_REL).is_file()
        assert (project / CANDIDATE_SCHEMA_REL).is_file()
        assert not (project / CURRENT_CANDIDATE_REL).exists()
        payload = render_creative_proposal(project)
        assert payload["directions_generated"] == 0
        assert payload["deprecated_alias"] == "creative-brief"
        assert "ART-AUTO-CREATIVE-DIRECTIONS" not in payload["artifact_ids"]
        snapshot = json.loads((project / BRIEF_SNAPSHOT_REL).read_text(encoding="utf-8"))
        assert snapshot["brief_snapshot_sha256"] == snapshot_sha


def test_candidate_requires_evidence_and_distinct_mechanisms() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-candidate-") as raw:
        project = Path(raw)
        snapshot_sha, evidence_ref = _prepare(project)
        candidate = {
            "candidate_version": "1.0",
            "brief_snapshot_sha256": snapshot_sha,
            "directions": [_direction(1, evidence_ref), _direction(2, evidence_ref)],
        }
        candidate_path = project / "candidate.json"
        candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
        imported = import_creative_candidate(project, candidate_path)
        assert imported.direction_count == 2
        review = review_creative_candidate(project)
        assert review.status == "PARTIAL_PASS"
        assert review.receipt["independent_critic_required"] is True
        assert review.receipt["creative_quality"] == "NOT_APPROVED_BY_DETERMINISTIC_LINT"
        for field in [
            "brief_adherence",
            "insight_quality",
            "brand_ownership",
            "mechanism_difference",
            "key_visual_clarity",
            "shootability",
            "production_risk",
            "brand_replacement_test",
            "verdict",
        ]:
            assert field in review.receipt

        duplicate = copy.deepcopy(candidate)
        duplicate["directions"][1]["creative_mechanism"] = duplicate["directions"][0][
            "creative_mechanism"
        ]
        duplicate_path = project / "duplicate.json"
        duplicate_path.write_text(json.dumps(duplicate, ensure_ascii=False), encoding="utf-8")
        try:
            import_creative_candidate(project, duplicate_path)
        except ValueError as exc:
            assert "duplicate creative mechanism" in str(exc)
        else:
            raise AssertionError("duplicate creative mechanisms must fail")

        unbound = copy.deepcopy(candidate)
        unbound["directions"][0]["evidence_refs"] = ["EVC-NOT-REAL"]
        unbound_path = project / "unbound.json"
        unbound_path.write_text(json.dumps(unbound, ensure_ascii=False), encoding="utf-8")
        try:
            import_creative_candidate(project, unbound_path)
        except ValueError as exc:
            assert "evidence_refs" in str(exc)
        else:
            raise AssertionError("unbound creative evidence must fail")


def main() -> int:
    test_brief_generates_contracts_not_directions()
    test_candidate_requires_evidence_and_distinct_mechanisms()
    print("TEST_CREATIVE_CONTRACT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
