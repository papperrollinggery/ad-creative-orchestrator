#!/usr/bin/env python3
"""Regression checks for the content-first runtime and on-demand promotion."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from ad_creative_operator import read_csv_rows, render_handoff, write_csv_rows
from runtime_paths import (
    CONTENT_SURFACE,
    DELIVERY_SURFACE,
    packaged_assets_root,
    project_surface,
    project_surface_conflict,
    skill_draft_dir,
    source_root,
    template_root,
)


SOURCE_ROOT = source_root()


def forward_fixture_root() -> Path:
    if SOURCE_ROOT:
        return SOURCE_ROOT / "tools/fixtures/content_first_forward"
    return packaged_assets_root() / "fixtures/content_first_forward"


def operator_command() -> list[str]:
    if SOURCE_ROOT:
        return [sys.executable, str(SOURCE_ROOT / "tools/ad_creative_operator.py")]
    return [sys.executable, "-m", "ad_creative_operator"]


def init_command() -> list[str]:
    if SOURCE_ROOT:
        return [sys.executable, str(SOURCE_ROOT / "tools/init_project.py")]
    return [sys.executable, "-m", "init_project"]


def run_operator(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [*operator_command(), *args],
        cwd=SOURCE_ROOT or Path.cwd(),
        check=check,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


def run_init(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [*init_command(), *args],
        cwd=SOURCE_ROOT or Path.cwd(),
        check=check,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


def file_count(project: Path) -> int:
    return sum(path.is_file() for path in project.rglob("*"))


def test_skill_and_default_project_budgets() -> None:
    skill_lines = (skill_draft_dir() / "SKILL.md").read_text(encoding="utf-8").splitlines()
    assert len(skill_lines) <= 120, len(skill_lines)

    with tempfile.TemporaryDirectory(prefix="adco-content-init-") as raw:
        root = Path(raw)
        project = root / "project"
        project.mkdir()
        root_policy = project / "AGENTS.md"
        root_policy.write_text("# Host policy\n", encoding="utf-8")
        initialized = run_operator("init", str(project))
        assert "PROJECT_SURFACE=content" in initialized.stdout
        assert "CREATED_FILES=9" in initialized.stdout
        assert file_count(project) <= 20
        assert root_policy.read_text(encoding="utf-8") == "# Host policy\n"
        assert (project / "AD-creative/AGENTS.md").is_file()
        assert project_surface(project) == CONTENT_SURFACE


def test_standalone_init_full_upgrades_existing_content_project() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-standalone-init-") as raw:
        project = Path(raw) / "project"
        run_init(str(project))
        assert project_surface(project) == CONTENT_SURFACE
        assert not (project / "AD-creative/orchestrator/artifact_index.csv").exists()

        upgraded = run_init(str(project), "--full")
        assert "INIT=PASS" in upgraded.stdout
        assert project_surface(project) == DELIVERY_SURFACE
        assert (project / "AD-creative/orchestrator/artifact_index.csv").is_file()


def test_delivery_preflight_failures_and_dry_runs_do_not_initialize() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-delivery-preflight-") as raw:
        root = Path(raw)

        dry_migration = root / "dry-migration"
        migrated = run_operator(
            "migrate-control-plane",
            str(dry_migration),
            "--dry-run",
            "--json",
        )
        assert json.loads(migrated.stdout)["dry_run"] is True
        assert not dry_migration.exists()

        dry_adoption = root / "dry-adoption"
        adoption = run_operator(
            "specialist-adopt",
            str(dry_adoption),
            "--handoff",
            str(dry_adoption / "handoff.json"),
            "--receipt",
            str(dry_adoption / "receipt.json"),
            "--decision",
            "reject",
            "--reason",
            "preflight only",
            "--dry-run",
            check=False,
        )
        assert adoption.returncode == 1
        assert "SPECIALIST_ADOPTION=BLOCKED" in adoption.stdout
        assert not dry_adoption.exists()

        for name, extra_args in [
            ("bad-role", ["--roles", "not_a_role"]),
            ("bad-budget", ["--max-active", "4"]),
        ]:
            project = root / name
            planned = run_operator(
                "thread-plan",
                str(project),
                "--objective",
                "reject invalid preflight",
                *extra_args,
                check=False,
            )
            assert planned.returncode == 1
            assert "THREAD_PLAN=CHECK" in planned.stdout
            assert not project.exists()

        invalid_creative = root / "invalid-creative"
        creative = run_operator(
            "creative-run",
            str(invalid_creative),
            "--kind",
            "ads",
            "--work-id",
            "WORK-INVALID",
            "--brief-file",
            str(root / "missing-brief.md"),
            "--review-only",
            "--generate",
            check=False,
        )
        assert creative.returncode == 1
        assert "CREATIVE_RUN=CHECK" in creative.stdout
        assert not invalid_creative.exists()


def test_forward_test_contracts_are_machine_readable() -> None:
    fixture_root = forward_fixture_root()
    for name in ["answer.schema.json", "delivery_answer.schema.json"]:
        schema = json.loads((fixture_root / name).read_text(encoding="utf-8"))
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert schema["required"]
    assert (fixture_root / "brief.md").is_file()
    assert (fixture_root / "delivery_request.md").is_file()

    answer_schema = json.loads(
        (fixture_root / "answer.schema.json").read_text(encoding="utf-8")
    )
    answer = json.loads(
        (fixture_root / "answer.example.json").read_text(encoding="utf-8")
    )
    assert set(answer) == set(answer_schema["required"])
    assert answer["surface"] == "content"
    assert len(answer["creative_directions"]) == 3
    assert {row["name"] for row in answer["creative_directions"]} == {
        "早高峰删减键",
        "3g 的一站",
        "一瓶到工位",
    }
    assert answer["blocking_unknowns"] == []
    assert set(answer["control_operations"].values()) == {0}

    delivery_schema = json.loads(
        (fixture_root / "delivery_answer.schema.json").read_text(encoding="utf-8")
    )
    delivery_answer = json.loads(
        (fixture_root / "delivery_answer.example.json").read_text(encoding="utf-8")
    )
    assert set(delivery_answer) == set(delivery_schema["required"])
    assert delivery_answer["surface"] == "delivery"
    assert delivery_answer["decision"] == "BLOCKED_BEFORE_SEND"
    assert delivery_answer["external_action_taken"] is False
    assert len(delivery_answer["required_controls"]) >= 4
    assert delivery_answer["work_that_can_continue"]


def test_default_run_emits_content_answer_without_delivery_theatre() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-content-run-") as raw:
        root = Path(raw)
        project = root / "project"
        material = root / "brief.md"
        material.write_text(
            "品牌要向一线城市独居青年推广低糖即饮咖啡。\n"
            "核心证据是每瓶糖含量 3g；不能宣称减肥。\n"
            "本轮先要内部策略判断和三条创意方向，不做客户 PPT。\n",
            encoding="utf-8",
        )
        completed = run_operator(
            "run",
            str(project),
            "--material",
            str(material),
            "--goal",
            "给出内部策略判断与下一步创意动作",
            "--json",
        )
        payload = json.loads(completed.stdout)
        answer = payload["content_answer"]
        assert payload["run"] == "PASS"
        assert answer["objective"] == "给出内部策略判断与下一步创意动作"
        assert answer["requirements"], answer
        assert answer["next_action"], answer
        assert "## 当前目标" in answer["markdown"]
        assert payload["dashboard_render_count"] == 0
        assert payload["council_run_count"] == 0
        assert payload["full_validation_run_count"] == 0
        assert file_count(project) <= 12, file_count(project)
        forbidden = [
            "AD-creative/handoff/操作台.html",
            "AD-creative/orchestrator/events.jsonl",
            "AD-creative/orchestrator/artifact_index.csv",
            "AD-creative/orchestrator/version_map.csv",
            "AD-creative/orchestrator/gate_log.csv",
            "AD-creative/orchestrator/thread_registry.csv",
            "00_项目资料_ProjectMaterials/目录索引.md",
        ]
        assert not [path for path in forbidden if (project / path).exists()]
        status = json.loads(run_operator("status", str(project), "--json").stdout)
        assert status["surface"] == CONTENT_SURFACE
        assert status["phase"] == "CONTENT"
        assert status["next_status"] == "READY_FOR_CONTENT_WORK"
        assert status["lane_states"] == {}
        assert status["completion_readiness"]["delivery_gates_required"] is False
        assert "missing_gates" not in status["completion_readiness"]


def test_content_answer_prioritizes_current_requirements_and_real_blockers() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-content-answer-rows-") as raw:
        project = Path(raw) / "project"
        run_operator("init", str(project))
        requirement_path = project / "AD-creative/orchestrator/requirements.csv"
        requirement_fields, _ = read_csv_rows(requirement_path)
        requirements: list[dict[str, str]] = []
        for index in range(8):
            row = {field: "" for field in requirement_fields}
            row.update(
                {
                    "requirement_id": f"REQ-OLD-{index + 1:03d}",
                    "source_event_id": "SRC-OLD",
                    "statement": f"历史要求 {index + 1}",
                    "requirement_type": "creative",
                    "status": "active",
                }
            )
            requirements.append(row)
        current = {field: "" for field in requirement_fields}
        current.update(
            {
                "requirement_id": "REQ-CURRENT-001",
                "source_event_id": "SRC-CURRENT",
                "statement": "本轮新增要求必须优先出现",
                "requirement_type": "creative",
                "status": "active",
            }
        )
        requirements.append(current)
        write_csv_rows(requirement_path, requirement_fields, requirements)

        gap_path = project / "AD-creative/orchestrator/gaps.csv"
        gap_fields, _ = read_csv_rows(gap_path)
        blocking = {field: "" for field in gap_fields}
        blocking.update(
            {
                "gap_id": "GAP-BLOCKING-001",
                "impact": "blocking",
                "status": "open",
                "description": "缺少决定核心主张所必需的产品证据",
            }
        )
        non_blocking = {field: "" for field in gap_fields}
        non_blocking.update(
            {
                "gap_id": "GAP-NONBLOCKING-001",
                "impact": "low",
                "status": "open",
                "description": "代言人尚未确定但无明星版本可以继续",
            }
        )
        write_csv_rows(gap_path, gap_fields, [blocking, non_blocking])

        answer = render_handoff(
            project,
            "处理本轮新增材料",
            ["SRC-CURRENT"],
        )
        assert answer["requirements"][0] == "本轮新增要求必须优先出现"
        assert answer["blocking_gaps"] == ["缺少决定核心主张所必需的产品证据"]
        assert answer["non_blocking_unknowns"] == [
            "代言人尚未确定但无明星版本可以继续"
        ]
        markdown = str(answer["markdown"])
        blocking_section = markdown.split("## 真正阻塞", 1)[1].split(
            "## 非阻塞未知", 1
        )[0]
        assert "代言人" not in blocking_section
        assert "代言人" in markdown.split("## 非阻塞未知", 1)[1]


def test_non_blocking_unknown_does_not_block_content_status() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-content-nonblocking-") as raw:
        project = Path(raw) / "project"
        run_operator("init", str(project))
        source_path = project / "AD-creative/orchestrator/source_events.csv"
        source_fields, _ = read_csv_rows(source_path)
        source = {field: "" for field in source_fields}
        source.update(
            {
                "source_event_id": "SRC-001",
                "received_at": "2026-07-19T00:00:00+08:00",
                "source_owner": "operator",
                "source_type": "file",
                "declared_semantics": "initial",
                "file_paths": "brief.md",
                "raw_summary": "测试 brief",
                "trust_level": "reviewed",
                "affects_requirements": "yes",
            }
        )
        write_csv_rows(source_path, source_fields, [source])

        gap_path = project / "AD-creative/orchestrator/gaps.csv"
        gap_fields, _ = read_csv_rows(gap_path)
        gap = {field: "" for field in gap_fields}
        gap.update(
            {
                "gap_id": "GAP-LOW-001",
                "impact": "low",
                "status": "open",
                "description": "代言人尚未确定但无明星版本可以继续",
                "recommended_action": "先推进无明星方案",
                "question_for_user": "是否后续考虑明星版本？",
            }
        )
        write_csv_rows(gap_path, gap_fields, [gap])
        answer = render_handoff(project, "继续内部创意", ["SRC-001"])
        assert answer["blocking_gaps"] == []
        assert answer["non_blocking_unknowns"] == [gap["description"]]
        confirmation_text = (
            project / "AD-creative/handoff/待你确认.md"
        ).read_text(encoding="utf-8")
        assert "GAP-LOW-001" not in confirmation_text

        status = json.loads(run_operator("status", str(project), "--json").stdout)
        assert status["next_status"] == "READY_FOR_CONTENT_WORK"
        assert status["pending_confirmation_count"] == 0
        assert status["completion_readiness"]["status"] == "READY_FOR_CONTENT_WORK"


def remove_runtime_surface(project: Path) -> str:
    project_yml = project / "AD-creative/orchestrator/project.yml"
    text = project_yml.read_text(encoding="utf-8")
    legacy_text = text.replace(
        '\nruntime:\n  surface: "delivery"\n  governance: "on_demand"\n',
        "",
    )
    assert legacy_text != text
    project_yml.write_text(legacy_text, encoding="utf-8")
    return legacy_text


def test_legacy_surface_detection_does_not_depend_on_a_delivery_ledger() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-legacy-surface-") as raw:
        project = Path(raw) / "project"
        run_operator("init", str(project), "--full")
        legacy_project_yml = remove_runtime_surface(project)
        artifact_path = project / "AD-creative/orchestrator/artifact_index.csv"
        artifact_path.unlink()

        assert project_surface(project) == DELIVERY_SURFACE
        checked = run_operator("validate", str(project), check=False)
        assert checked.returncode == 1
        assert "missing required file: AD-creative/orchestrator/artifact_index.csv" in checked.stdout
        assert project_surface(project) == DELIVERY_SURFACE
        assert (
            project / "AD-creative/orchestrator/project.yml"
        ).read_text(encoding="utf-8") == legacy_project_yml

        run_operator("init", str(project))
        assert project_surface(project) == DELIVERY_SURFACE
        assert artifact_path.is_file()


def test_content_declaration_with_delivery_ledgers_fails_closed() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-surface-conflict-") as raw:
        project = Path(raw) / "project"
        run_operator("init", str(project))
        artifact_path = project / "AD-creative/orchestrator/artifact_index.csv"
        artifact_path.write_bytes(
            (
                template_root()
                / "AD-creative/orchestrator/artifact_index.csv"
            ).read_bytes()
        )

        conflict = project_surface_conflict(project)
        assert "declares content while Delivery-only evidence exists" in conflict
        assert project_surface(project) == DELIVERY_SURFACE
        checked = run_operator("validate", str(project), check=False)
        assert checked.returncode == 1
        assert "runtime surface conflict" in checked.stdout
        assert "missing required file: AD-creative/orchestrator/version_map.csv" in checked.stdout

        repaired = run_operator("init", str(project), "--full")
        assert "INIT=PASS" in repaired.stdout
        assert project_surface(project) == DELIVERY_SURFACE
        assert project_surface_conflict(project) == ""


def test_delivery_run_preserves_audit_bookkeeping_for_explicit_and_legacy_projects() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-delivery-run-") as raw:
        root = Path(raw)
        material = root / "brief.md"
        material.write_text(
            "品牌要向通勤人群推广低糖即饮咖啡。\n"
            "核心证据是每瓶糖含量 3g；本轮需要进入客户审阅交付。\n",
            encoding="utf-8",
        )
        for name, legacy in [("explicit", False), ("legacy", True)]:
            project = root / name
            run_operator("init", str(project), "--full")
            if legacy:
                remove_runtime_surface(project)
            payload = json.loads(
                run_operator(
                    "run",
                    str(project),
                    "--material",
                    str(material),
                    "--goal",
                    "整理需求并保留交付审计记录",
                    "--json",
                ).stdout
            )
            assert payload["run"] == "PASS"
            assert project_surface(project) == DELIVERY_SURFACE

            events = [
                json.loads(line)
                for line in (
                    project / "AD-creative/orchestrator/events.jsonl"
                ).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            event_types = {row.get("event_type") for row in events}
            assert {"material_registered", "intake_completed"} <= event_types

            _, work_rows = read_csv_rows(
                project / "AD-creative/orchestrator/work_items.csv"
            )
            intake_work = next(
                row for row in work_rows if row.get("title") == "需求整理与缺口判断"
            )
            assert intake_work["status"] == "done"
            assert "ART-AUTO-CURRENT-TRUTH" in intake_work["output_artifacts"]

            _, artifacts = read_csv_rows(
                project / "AD-creative/orchestrator/artifact_index.csv"
            )
            artifact_ids = {row.get("artifact_id") for row in artifacts}
            assert {
                "ART-AUTO-CURRENT-TRUTH",
                "ART-AUTO-CLIENT-QUESTIONS",
            } <= artifact_ids
            _, gates = read_csv_rows(project / "AD-creative/orchestrator/gate_log.csv")
            assert any(row.get("gate_id") == "GATE-AUTO-BRIEF-001" for row in gates)


def test_sample_preserves_delivery_intake_linkage() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-delivery-sample-") as raw:
        project = Path(raw) / "project"
        run_operator("init", str(project), "--full")
        completed = run_operator("sample", str(project))
        assert "SAMPLE=PASS" in completed.stdout
        assert project_surface(project) == DELIVERY_SURFACE

        _, work_rows = read_csv_rows(
            project / "AD-creative/orchestrator/work_items.csv"
        )
        intake_work = next(
            row for row in work_rows if row.get("title") == "需求整理与缺口判断"
        )
        assert intake_work["status"] == "done"

        _, artifacts = read_csv_rows(
            project / "AD-creative/orchestrator/artifact_index.csv"
        )
        linked_artifacts = [
            row
            for row in artifacts
            if row.get("artifact_id")
            in {"ART-AUTO-CURRENT-TRUTH", "ART-AUTO-CLIENT-QUESTIONS"}
        ]
        assert len(linked_artifacts) == 2
        assert all(
            row.get("linked_work_items") == intake_work["work_id"]
            for row in linked_artifacts
        )


def test_creative_brief_is_light_on_content_and_traceable_on_delivery() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-creative-surface-") as raw:
        root = Path(raw)
        content = root / "content"
        run_operator("init", str(content))
        run_operator("creative-brief", str(content), "--json")
        assert not (content / "AD-creative/orchestrator/artifact_index.csv").exists()
        assert not (content / "AD-creative/orchestrator/work_items.csv").exists()
        assert not (content / "AD-creative/orchestrator/events.jsonl").exists()

        delivery = root / "delivery"
        run_operator("init", str(delivery), "--full")
        artifact_path = delivery / "AD-creative/orchestrator/artifact_index.csv"
        artifact_path.unlink()
        payload = json.loads(
            run_operator("creative-brief", str(delivery), "--json").stdout
        )
        assert project_surface(delivery) == DELIVERY_SURFACE
        assert artifact_path.is_file(), "Delivery repair must restore missing template files"
        _, artifacts = read_csv_rows(artifact_path)
        registered = {row.get("artifact_id") for row in artifacts}
        assert set(payload["artifact_ids"]) <= registered
        work_id = payload["work_id"]
        assert work_id
        assert all(
            work_id in row.get("linked_work_items", "")
            for row in artifacts
            if row.get("artifact_id") in payload["artifact_ids"]
        )
        events = (
            delivery / "AD-creative/orchestrator/events.jsonl"
        ).read_text(encoding="utf-8")
        assert '"event_type": "creative_brief_created"' in events


def test_explicit_governance_command_promotes_without_overwriting_content() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-content-promote-") as raw:
        project = Path(raw) / "project"
        run_operator("init", str(project))
        truth_path = project / "AD-creative/orchestrator/current_truth.md"
        truth_path.write_text(
            truth_path.read_text(encoding="utf-8")
            + "\n## Operator note\nkeep-this-content\n",
            encoding="utf-8",
        )
        run_operator(
            "goal-plan",
            str(project),
            "--goal-id",
            "GOAL-PROMOTION-TEST",
            "--title",
            "客户审阅交付计划",
            "--objective",
            "建立客户可见 PPT 交付计划",
        )
        assert project_surface(project) == DELIVERY_SURFACE
        assert "keep-this-content" in truth_path.read_text(encoding="utf-8")
        assert (project / "AD-creative/orchestrator/artifact_index.csv").is_file()
        assert (project / "AD-creative/orchestrator/version_map.csv").is_file()
        assert (project / "AD-creative/orchestrator/goal_iterations/GOAL-PROMOTION-TEST.md").is_file()
        run_operator("init", str(project))
        assert project_surface(project) == DELIVERY_SURFACE
        assert "keep-this-content" in truth_path.read_text(encoding="utf-8")

        second_project = Path(raw) / "explicit-full"
        run_operator("init", str(second_project))
        assert project_surface(second_project) == CONTENT_SURFACE
        run_operator("init", str(second_project), "--full")
        assert project_surface(second_project) == DELIVERY_SURFACE
        assert (
            second_project / "AD-creative/orchestrator/artifact_index.csv"
        ).is_file()


def main() -> int:
    test_skill_and_default_project_budgets()
    test_standalone_init_full_upgrades_existing_content_project()
    test_delivery_preflight_failures_and_dry_runs_do_not_initialize()
    test_forward_test_contracts_are_machine_readable()
    test_default_run_emits_content_answer_without_delivery_theatre()
    test_content_answer_prioritizes_current_requirements_and_real_blockers()
    test_non_blocking_unknown_does_not_block_content_status()
    test_legacy_surface_detection_does_not_depend_on_a_delivery_ledger()
    test_content_declaration_with_delivery_ledgers_fails_closed()
    test_delivery_run_preserves_audit_bookkeeping_for_explicit_and_legacy_projects()
    test_sample_preserves_delivery_intake_linkage()
    test_creative_brief_is_light_on_content_and_traceable_on_delivery()
    test_explicit_governance_command_promotes_without_overwriting_content()
    print("TEST_CONTENT_FIRST_RUNTIME=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
