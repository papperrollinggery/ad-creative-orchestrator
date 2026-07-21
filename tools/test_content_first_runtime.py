#!/usr/bin/env python3
"""Regression checks for the content-first runtime and on-demand promotion."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path
from unittest.mock import patch

import init_project as init_project_module
import adco_core.creative_contract as creative_contract_module
import adco_core.facts as facts_module
import adco_core.ingestion as ingestion_module
import ad_creative_operator as operator_module

from ad_creative_operator import (
    build_client_pack_input_manifest,
    read_csv_rows,
    render_handoff,
    render_support_bundle,
    specialist_scope_manifest,
    write_csv_rows,
)
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


def write_compressed_text_pdf(path: Path, visible_text: str) -> None:
    escaped = (
        visible_text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )
    content = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("utf-8")
    compressed = zlib.compress(content)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (
            f"<< /Length {len(compressed)} /Filter /FlateDecode >>\nstream\n".encode()
            + compressed
            + b"\nendstream"
        ),
    ]
    payload = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{index} 0 obj\n".encode())
        payload.extend(body)
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode())
    payload.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode()
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(payload))


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


def test_unbiased_chatgpt_evidence_receipt_is_hash_bound_and_manual() -> None:
    fixture_root = forward_fixture_root()
    receipt = json.loads(
        (fixture_root / "mori_spark_unbiased_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["schema_version"] == 1
    conversation = receipt["conversation"]
    assert conversation["provider"] == "ChatGPT"
    assert conversation["browser"] == "Chrome"
    assert conversation["reasoning_mode"] == "极高"
    assert conversation["mode_ui_confirmed"] is True
    assert conversation["fresh_conversation"] is True
    assert conversation["url"].startswith("https://chatgpt.com/c/")
    verification = receipt["verification_scope"]
    assert verification["status"] == "MANUAL_READBACK_ONLY"
    assert verification["automated_conversation_attestation"] is False
    assert "artifact_hashes" in verification["verified_by_automation"]
    assert "reasoning_mode_ui" in verification["verified_by_manual_browser_readback"]
    assert "do not independently read" in verification["limitation"]

    protocol = receipt["unbiased_protocol"]
    assert set(protocol["included_materials"]) == {
        "current_SKILL.md",
        "current_creative_contract.md",
        "task_brief",
    }
    assert set(protocol["excluded_materials"]) == {
        "prior_answers",
        "prior_findings",
        "evaluation_rubric",
        "desired_direction",
        "desired_verdict",
    }

    artifact_paths = {
        "brief": fixture_root / "mori_spark_unbiased_brief.md",
        "output": fixture_root / "mori_spark_unbiased_output.md",
        "skill": skill_draft_dir() / "SKILL.md",
        "creative_reference": skill_draft_dir() / "creative_contract.md",
        "creative_contract": Path(creative_contract_module.__file__),
        "facts": Path(facts_module.__file__),
        "semantic_test": Path(__file__).with_name("test_creative_contract.py"),
        "full_pptx_fixture": (
            skill_draft_dir()
            / "fixtures/chat-visualization/sample-deck.pptx"
        ),
    }
    artifacts = receipt["artifacts"]
    assert set(artifact_paths) <= set(artifacts)
    for artifact_id, path in artifact_paths.items():
        assert path.is_file(), (artifact_id, path)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifacts[
            artifact_id
        ]["sha256"]

    tree_files = operator_module.skill_tree_files(skill_draft_dir())
    tree_receipt = artifacts["skill_tree"]
    assert len(tree_files) == tree_receipt["managed_file_count"]
    assert operator_module.skill_tree_hash(tree_files) == tree_receipt["sha256"]
    observed = receipt["observed_result"]
    output_text = artifact_paths["output"].read_text(encoding="utf-8")
    assert observed["answer_nonempty"] is True
    assert observed["answer_character_count"] >= 1500
    assert len(output_text) == observed["fixture_character_count"]
    assert observed["fixture_transcription"].startswith("Normalized Markdown")
    assert not {
        "制作复杂度最低",
        "最容易执行",
        "最安全",
        "9:00",
        "7:30",
        "21:16",
        "22:03",
        "清醒社交",
        "低负担",
    }.intersection(output_text)
    # Boundary and claim words are allowed only when the answer explicitly
    # rejects them. A raw blacklist would punish a useful compliance statement
    # such as “没有扩展到……冰箱” while failing to distinguish it from a scene
    # invention.
    denial_markers = {"不", "没有", "未", "避免", "未经允许"}
    in_denial_section = False
    for line in output_text.splitlines():
        if line.strip() == "# 七、禁用表达":
            in_denial_section = True
        elif in_denial_section and line.startswith("# "):
            in_denial_section = False
        if {"冰箱", "冰柜", "冷柜", "货架", "收银台"}.intersection(line):
            assert in_denial_section or any(
                marker in line for marker in denial_markers
            ), line
        if {"睡眠", "醒酒", "健康", "减肥"}.intersection(line):
            assert in_denial_section or any(
                marker in line for marker in denial_markers
            ), line


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
        answer = payload["intake_summary"]
        assert payload["content_answer"] == answer
        assert answer["artifact_role"] == "intake_summary_not_creative_output"
        assert payload["run"] == "PASS"
        assert answer["objective"] == "给出内部策略判断与下一步创意动作"
        assert answer["requirements"], answer
        assert answer["next_action"], answer
        assert "## 当前目标" in answer["markdown"]
        assert payload["dashboard_render_count"] == 0
        assert payload["council_run_count"] == 0
        assert payload["full_validation_run_count"] == 0
        assert file_count(project) <= 14, file_count(project)
        source_rows = (
            project / "AD-creative/orchestrator/source_events.csv"
        ).read_text(encoding="utf-8")
        assert "local-source://SRC-001" in source_rows
        evidence = (
            project / "AD-creative/orchestrator/evidence_chunks.jsonl"
        ).read_text(encoding="utf-8")
        assert str(root) not in source_rows
        assert str(root) not in evidence
        for public_path in (project / "AD-creative").rglob("*"):
            if public_path.is_file():
                assert str(root) not in public_path.read_text(
                    encoding="utf-8", errors="ignore"
                ), public_path
        local_map = project / ".adco-local/source_paths.json"
        assert str(material.resolve()) in local_map.read_text(encoding="utf-8")
        assert (project / ".adco-local/.gitignore").read_text(encoding="utf-8") == (
            "*\n!.gitignore\n"
        )
        assert local_map.stat().st_mode & 0o077 == 0
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

        support_report = render_support_bundle(project)
        support_text = support_report.read_text(encoding="utf-8")
        assert str(material.resolve()) not in support_text
        assert ".adco-local" not in support_text

        private_client = project / "AD-creative/client_review/private-marker.md"
        private_client.parent.mkdir(parents=True, exist_ok=True)
        private_client.write_text(
            f"must never export {material.resolve()}",
            encoding="utf-8",
        )
        manifest, _, manifest_errors = build_client_pack_input_manifest(
            project,
            [
                {
                    "artifact_id": "ART-PRIVATE-MAP",
                    "visibility": "client_visible",
                    "path": ".adco-local/source_paths.json",
                },
                {
                    "artifact_id": "ART-PRIVATE-MARKER",
                    "visibility": "client_visible",
                    "path": "AD-creative/client_review/private-marker.md",
                },
            ],
        )
        manifest_text = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        assert ".adco-local" not in manifest_text
        assert str(material.resolve()) not in manifest_text
        assert any("private local source path" in item for item in manifest_errors)
        scope = specialist_scope_manifest(project, excluded_roots=[])
        assert not any(
            rel == ".adco-local" or rel.startswith(".adco-local/")
            for rel in scope
        )


def test_external_source_map_repairs_unsafe_local_gitignore() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-local-ignore-") as raw:
        root = Path(raw)
        project = root / "project"
        local_state = project / ".adco-local"
        local_state.mkdir(parents=True)
        (local_state / ".gitignore").write_text(
            "*\n!source_paths.json\n",
            encoding="utf-8",
        )
        material = root / "brief.md"
        material.write_text("用于验证私有映射忽略规则。", encoding="utf-8")

        completed = run_operator(
            "run",
            str(project),
            "--material",
            str(material),
            "--json",
        )
        payload = json.loads(completed.stdout)
        assert payload["run"] == "PASS", payload
        assert (local_state / ".gitignore").read_text(encoding="utf-8") == (
            "*\n!.gitignore\n"
        )
        assert (local_state / "source_paths.json").stat().st_mode & 0o077 == 0
        subprocess.run(
            ["git", "init", "--quiet", str(project)],
            check=True,
            capture_output=True,
            text=True,
        )
        ignored = subprocess.run(
            [
                "git",
                "-C",
                str(project),
                "check-ignore",
                "--quiet",
                ".adco-local/source_paths.json",
            ],
            check=False,
        )
        assert ignored.returncode == 0, ignored.returncode


def test_local_source_state_dirfd_resists_concurrent_symlink_swap() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-local-swap-") as raw:
        root = Path(raw)
        project = root / "project"
        run_operator("init", str(project))
        material = root / "brief.md"
        material.write_text("private source marker", encoding="utf-8")
        outside = root / "outside"
        outside.mkdir()
        (outside / "sentinel.txt").write_text("unchanged", encoding="utf-8")
        outside_before = {
            path.relative_to(outside).as_posix(): path.read_bytes()
            for path in outside.rglob("*")
            if path.is_file()
        }
        original_replace = ingestion_module.os.replace
        swapped = False

        def swapping_replace(
            source: str,
            target: str,
            *,
            src_dir_fd: int | None = None,
            dst_dir_fd: int | None = None,
        ) -> None:
            nonlocal swapped
            if not swapped:
                local_state = project / ".adco-local"
                assert local_state.is_dir()
                local_state.rename(project / ".adco-local.before-swap")
                local_state.symlink_to(outside, target_is_directory=True)
                swapped = True
            original_replace(
                source,
                target,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
            )

        with patch.object(
            ingestion_module.os,
            "replace",
            side_effect=swapping_replace,
        ):
            try:
                ingestion_module.register_local_source_path(
                    project,
                    "SRC-SWAP",
                    material,
                )
            except ValueError as exc:
                assert "changed during operation" in str(exc)
            else:
                raise AssertionError("local state swap must fail closed")

        assert swapped
        outside_after = {
            path.relative_to(outside).as_posix(): path.read_bytes()
            for path in outside.rglob("*")
            if path.is_file()
        }
        assert outside_after == outside_before


def test_open_project_dir_closes_fd_when_visible_binding_disappears() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-project-fd-close-") as raw:
        project = Path(raw) / "project"
        project.mkdir()
        original_close = ingestion_module.os.close
        closed_fds: list[int] = []

        def tracking_close(fd: int) -> None:
            closed_fds.append(fd)
            original_close(fd)

        with (
            patch.object(
                ingestion_module.os,
                "stat",
                side_effect=FileNotFoundError("simulated binding loss"),
            ),
            patch.object(
                ingestion_module.os,
                "close",
                side_effect=tracking_close,
            ),
        ):
            try:
                ingestion_module._open_project_dir(project)
            except FileNotFoundError:
                pass
            else:
                raise AssertionError("binding loss must fail project dir open")
        assert len(closed_fds) == 1


def test_private_source_map_failures_block_support_and_client_pack() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-private-map-fail-closed-") as raw:
        root = Path(raw)
        project = root / "project"
        run_operator("init", str(project))
        local_state = project / ".adco-local"
        local_state.mkdir(mode=0o700)
        (local_state / ".gitignore").write_text(
            "*\n!.gitignore\n",
            encoding="utf-8",
        )
        map_path = local_state / "source_paths.json"
        support_path = project / "AD-creative/handoff/support_bundle.md"

        def assert_exports_blocked() -> None:
            try:
                render_support_bundle(project)
            except ValueError as exc:
                assert "invalid or unreadable" in str(exc)
            else:
                raise AssertionError("unsafe private source map must block support bundle")
            payload, _, errors = build_client_pack_input_manifest(project, [])
            assert any("invalid or unreadable" in item for item in errors), errors
            assert payload["files"] == []
            assert not support_path.exists()

        map_path.write_text("{not-json", encoding="utf-8")
        assert_exports_blocked()
        blocked_cli = run_operator(
            "support-bundle",
            str(project),
            check=False,
        )
        assert blocked_cli.returncode == 1
        assert "SUPPORT_BUNDLE=BLOCKED" in blocked_cli.stdout
        assert not support_path.exists()

        outside_map = root / "outside-source-map.json"
        outside_map.write_text(
            json.dumps(
                {
                    "version": 1,
                    "sources": {"SRC-OUTSIDE": str((root / "source.md").resolve())},
                }
            ),
            encoding="utf-8",
        )
        outside_before = outside_map.read_bytes()
        map_path.unlink()
        map_path.symlink_to(outside_map)
        assert_exports_blocked()
        assert outside_map.read_bytes() == outside_before

        map_path.unlink()
        map_path.write_text(outside_map.read_text(encoding="utf-8"), encoding="utf-8")
        with patch.object(
            ingestion_module,
            "_read_private_text_at",
            side_effect=PermissionError("simulated unreadable private state"),
        ):
            assert_exports_blocked()


def test_missing_private_map_with_registered_alias_blocks_exports() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-private-map-missing-") as raw:
        root = Path(raw)
        project = root / "project"
        run_operator("init", str(project))
        source = root / "private-source.md"
        source.write_text("private", encoding="utf-8")
        ingestion_module.register_local_source_path(project, "SRC-MISSING", source)
        source_events = project / "AD-creative/orchestrator/source_events.csv"
        fields, rows = read_csv_rows(source_events)
        rows.append(
            {
                "source_event_id": "SRC-MISSING",
                "received_at": "2026-01-01T00:00:00+08:00",
                "source_owner": "operator",
                "source_type": "file",
                "declared_semantics": "initial",
                "file_paths": "local-source://SRC-MISSING",
                "raw_summary": "private material",
                "trust_level": "unreviewed",
                "affects_requirements": "unknown",
                "notes": "",
            }
        )
        write_csv_rows(source_events, fields, rows)
        client_file = project / "AD-creative/client_review/private-path.md"
        client_file.parent.mkdir(parents=True, exist_ok=True)
        client_file.write_text(str(source.resolve()), encoding="utf-8")
        (project / ".adco-local/source_paths.json").unlink()

        try:
            render_support_bundle(project)
        except ValueError as exc:
            assert "invalid or unreadable" in str(exc)
        else:
            raise AssertionError("missing map with aliases must block support bundle")
        manifest, _, errors = build_client_pack_input_manifest(
            project,
            [
                {
                    "artifact_id": "ART-MISSING-MAP",
                    "visibility": "client_visible",
                    "path": client_file.relative_to(project).as_posix(),
                }
            ],
        )
        assert any("invalid or unreadable" in item for item in errors), errors
        assert manifest["files"] == []


def test_client_pack_private_marker_zip_scan_is_bounded_and_directory_safe() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-private-zip-scan-") as raw:
        root = Path(raw)
        project = root / "project"
        run_operator("init", str(project))
        source = root / "private-source.md"
        source.write_text("private", encoding="utf-8")
        ingestion_module.register_local_source_path(project, "SRC-ZIP", source)

        client_root = project / "AD-creative/client_review"
        client_root.mkdir(parents=True, exist_ok=True)
        safe_pptx = client_root / "safe-directory-entry.pptx"
        with zipfile.ZipFile(safe_pptx, "w") as archive:
            archive.writestr("folder/", b"")
            archive.writestr("folder/document.xml", b"safe client content")
        safe_artifact = {
            "artifact_id": "ART-SAFE-ZIP",
            "visibility": "client_visible",
            "path": safe_pptx.relative_to(project).as_posix(),
        }
        safe_manifest, _, safe_errors = build_client_pack_input_manifest(
            project,
            [safe_artifact],
        )
        assert not [item for item in safe_errors if "safe-directory-entry.pptx" in item]
        assert any(
            item["path"] == safe_artifact["path"]
            for item in safe_manifest["files"]
        )

        leaking_pptx = client_root / "leaking.pptx"
        with zipfile.ZipFile(leaking_pptx, "w") as archive:
            archive.writestr("ppt/slides/slide1.xml", str(source.resolve()))
        leaking_artifact = {
            "artifact_id": "ART-LEAKING-ZIP",
            "visibility": "client_visible",
            "path": leaking_pptx.relative_to(project).as_posix(),
        }
        leaking_manifest, _, leaking_errors = build_client_pack_input_manifest(
            project,
            [leaking_artifact],
        )
        assert any(
            "leaking.pptx" in item and "private local source path marker" in item
            for item in leaking_errors
        ), leaking_errors
        assert not any(
            item["path"] == leaking_artifact["path"]
            for item in leaking_manifest["files"]
        )

        oversized_pptx = client_root / "oversized.pptx"
        with zipfile.ZipFile(oversized_pptx, "w") as archive:
            archive.writestr("ppt/slides/slide1.xml", b"x" * 64)
        oversized_artifact = {
            "artifact_id": "ART-OVERSIZED-ZIP",
            "visibility": "client_visible",
            "path": oversized_pptx.relative_to(project).as_posix(),
        }
        with patch.object(
            operator_module,
            "PRIVATE_MARKER_SCAN_MAX_MEMBER_BYTES",
            32,
        ):
            oversized_manifest, _, oversized_errors = build_client_pack_input_manifest(
                project,
                [oversized_artifact],
            )
        assert any(
            "oversized.pptx" in item and "archive limit exceeded" in item
            for item in oversized_errors
        ), oversized_errors
        assert not any(
            item["path"] == oversized_artifact["path"]
            for item in oversized_manifest["files"]
        )


def test_client_pack_scan_and_hash_share_one_stable_file_binding() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-private-scan-hash-race-") as raw:
        root = Path(raw)
        project = root / "project"
        run_operator("init", str(project))
        source = root / "private-source.md"
        source.write_text("private", encoding="utf-8")
        ingestion_module.register_local_source_path(project, "SRC-RACE", source)

        client_file = project / "AD-creative/client_review/race.md"
        client_file.parent.mkdir(parents=True, exist_ok=True)
        client_file.write_text("safe client content", encoding="utf-8")
        safe_inode = client_file.stat().st_ino
        replacement = root / "replacement.md"
        replacement.write_text(str(source.resolve()), encoding="utf-8")
        original_scan = operator_module._scan_and_hash_regular_fd
        swapped = False

        def swapping_scan(
            fd: int,
            markers: list[bytes],
            *,
            limit: int,
        ) -> tuple[str, int, bool, bool]:
            nonlocal swapped
            result = original_scan(fd, markers, limit=limit)
            if not swapped and os.fstat(fd).st_ino == safe_inode:
                os.replace(replacement, client_file)
                swapped = True
            return result

        with patch.object(
            operator_module,
            "_scan_and_hash_regular_fd",
            side_effect=swapping_scan,
        ):
            manifest, _, errors = build_client_pack_input_manifest(
                project,
                [
                    {
                        "artifact_id": "ART-SCAN-HASH-RACE",
                        "visibility": "client_visible",
                        "path": client_file.relative_to(project).as_posix(),
                    }
                ],
            )
        assert swapped
        assert any(
            "race.md" in item and "target changed during inspection" in item
            for item in errors
        ), errors
        assert not any(
            item["path"] == client_file.relative_to(project).as_posix()
            for item in manifest["files"]
        )


def test_client_pack_parent_directory_swap_cannot_escape_project() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-private-parent-swap-") as raw:
        root = Path(raw)
        project = root / "project"
        run_operator("init", str(project))
        source = root / "private-source.md"
        source.write_text("private", encoding="utf-8")
        ingestion_module.register_local_source_path(project, "SRC-PARENT", source)

        client_root = project / "AD-creative/client_review"
        client_root.mkdir(parents=True, exist_ok=True)
        client_file = client_root / "parent-race.md"
        client_file.write_text("safe client content", encoding="utf-8")
        outside = root / "outside"
        outside.mkdir()
        outside_file = outside / client_file.name
        outside_file.write_text(str(source.resolve()), encoding="utf-8")
        outside_hash = operator_module.file_sha256(outside_file)
        moved_client_root = project / "AD-creative/client_review-before-swap"
        original_open = operator_module._open_project_relative_regular_file
        swapped = False

        def swapping_open(
            candidate_project: Path,
            relative_path: str | Path,
            *,
            project_root_fd: int | None = None,
        ) -> tuple[int, os.stat_result, list[int], tuple[str, ...]]:
            nonlocal swapped
            if not swapped and str(relative_path).endswith(client_file.name):
                client_root.rename(moved_client_root)
                client_root.symlink_to(outside, target_is_directory=True)
                swapped = True
            return original_open(
                candidate_project,
                relative_path,
                project_root_fd=project_root_fd,
            )

        with patch.object(
            operator_module,
            "_open_project_relative_regular_file",
            side_effect=swapping_open,
        ):
            manifest, _, errors = build_client_pack_input_manifest(
                project,
                [
                    {
                        "artifact_id": "ART-PARENT-RACE",
                        "visibility": "client_visible",
                        "path": client_file.relative_to(project).as_posix(),
                    }
                ],
            )
        assert swapped
        assert any("parent-race.md" in item and "privacy" in item for item in errors)
        assert not any(item.get("sha256") == outside_hash for item in manifest["files"])
        assert outside_file.read_text(encoding="utf-8") == str(source.resolve())


def test_client_pack_manifest_binds_one_project_root_inode() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-private-root-replace-") as raw:
        root = Path(raw)
        project = root / "project"
        replacement_project = root / "replacement-project"
        original_project = root / "original-project"
        run_operator("init", str(project))
        run_operator("init", str(replacement_project))

        source_a = root / "private-source-a.md"
        source_a.write_text("private-a", encoding="utf-8")
        ingestion_module.register_local_source_path(project, "SRC-ROOT-A", source_a)
        client_rel = Path("AD-creative/client_review/root-race.md")
        client_a = project / client_rel
        client_a.parent.mkdir(parents=True, exist_ok=True)
        client_a.write_text("safe project A", encoding="utf-8")

        source_b = root / "private-source-b.md"
        source_b.write_text("private-b", encoding="utf-8")
        ingestion_module.register_local_source_path(
            replacement_project,
            "SRC-ROOT-B",
            source_b,
        )
        client_b = replacement_project / client_rel
        client_b.parent.mkdir(parents=True, exist_ok=True)
        client_b.write_text(str(source_b.resolve()), encoding="utf-8")
        replacement_hash = operator_module.file_sha256(client_b)

        original_markers = operator_module.private_source_path_markers
        swapped = False

        def swapping_markers(
            candidate_project: Path,
            *,
            project_root_fd: int | None = None,
        ) -> list[bytes]:
            nonlocal swapped
            markers = original_markers(
                candidate_project,
                project_root_fd=project_root_fd,
            )
            project.rename(original_project)
            replacement_project.rename(project)
            swapped = True
            return markers

        with patch.object(
            operator_module,
            "private_source_path_markers",
            side_effect=swapping_markers,
        ):
            manifest, _, errors = build_client_pack_input_manifest(
                project,
                [
                    {
                        "artifact_id": "ART-ROOT-RACE",
                        "visibility": "client_visible",
                        "path": client_rel.as_posix(),
                    }
                ],
            )

        assert swapped
        assert any("project root changed" in item for item in errors), errors
        assert manifest["files"] == [], manifest
        assert not any(
            item.get("sha256") == replacement_hash for item in manifest["files"]
        )
        assert (project / client_rel).read_text(encoding="utf-8") == str(
            source_b.resolve()
        )


def test_client_pack_scans_compressed_pdf_visible_text() -> None:
    with (
        tempfile.TemporaryDirectory(prefix="adco-private-pdf-scan-") as raw,
        tempfile.TemporaryDirectory(
            prefix="adco-pdf-source-",
            dir="/tmp",
        ) as raw_source,
    ):
        root = Path(raw)
        project = root / "project"
        run_operator("init", str(project))
        source = Path(raw_source) / "private-source.md"
        source.write_text("private", encoding="utf-8")
        ingestion_module.register_local_source_path(project, "SRC-PDF", source)

        marker = str(source.resolve())
        pdf_path = project / "AD-creative/client_review/compressed-marker.pdf"
        write_compressed_text_pdf(pdf_path, marker)
        assert marker.encode("utf-8") not in pdf_path.read_bytes()

        manifest, _, errors = build_client_pack_input_manifest(
            project,
            [
                {
                    "artifact_id": "ART-COMPRESSED-PDF",
                    "visibility": "client_visible",
                    "path": pdf_path.relative_to(project).as_posix(),
                }
            ],
        )
        assert any(
            "compressed-marker.pdf" in item
            and "private local source path marker" in item
            for item in errors
        ), errors
        assert not any(
            item["path"] == pdf_path.relative_to(project).as_posix()
            for item in manifest["files"]
        )


def test_pdf_extractor_enforces_output_limit_while_streaming() -> None:
    if not operator_module.shutil.which("pdftotext"):
        return
    with tempfile.TemporaryDirectory(prefix="adco-private-pdf-limit-") as raw:
        pdf_path = Path(raw) / "expanding.pdf"
        visible_text = "bounded-output " * 20_000
        write_compressed_text_pdf(pdf_path, visible_text)
        raw_size = pdf_path.stat().st_size
        assert raw_size < 8_192, raw_size
        fd = os.open(pdf_path, os.O_RDONLY)
        try:
            with patch.object(
                operator_module,
                "PRIVATE_MARKER_SCAN_MAX_ARCHIVE_BYTES",
                4_096,
            ):
                issue, found = operator_module._scan_pdf_fd(
                    fd,
                    [b"marker-that-is-not-present"],
                )
        finally:
            os.close(fd)
        assert issue == "privacy scan PDF text limit exceeded", issue
        assert found is False


def test_pypdf_fallback_isolated_with_memory_and_stream_limits() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-pypdf-limit-") as raw:
        dummy = Path(raw) / "dummy.pdf"
        dummy.write_bytes(b"%PDF-1.4\n%%EOF\n")
        fd = os.open(dummy, os.O_RDONLY)
        try:
            with (
                patch.object(
                    operator_module.importlib.util,
                    "find_spec",
                    return_value=object(),
                ),
                patch.object(
                    operator_module,
                    "_scan_pdf_command_fd",
                    return_value=("", False),
                ) as bounded_scan,
            ):
                issue, found = operator_module._scan_pdf_with_pypdf_fd(
                    fd,
                    [b"marker-that-is-not-present"],
                )
        finally:
            os.close(fd)
    assert issue == ""
    assert found is False
    command = bounded_scan.call_args.args[2]
    assert command[:3] == [sys.executable, "-I", "-c"], command
    script = command[3]
    assert "resource.setrlimit" in script
    assert "visitor_text" in script
    assert "sys.stdout.buffer" in script


def test_run_preflight_rejects_invalid_inputs_before_project_write() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-run-preflight-") as raw:
        root = Path(raw)
        missing = root / "missing.md"
        unsupported = root / "brief.bin"
        unsupported.write_bytes(b"unsupported")
        empty_file = root / "empty.md"
        empty_file.touch()
        empty_dir = root / "empty-dir"
        empty_dir.mkdir()

        cases = [
            ("missing", missing, 2_000_000, "material_not_found"),
            ("unsupported", unsupported, 2_000_000, "empty_or_unsupported_material"),
            ("empty-file", empty_file, 2_000_000, "empty_material"),
            ("empty-dir", empty_dir, 2_000_000, "empty_or_unsupported_material"),
            ("bad-budget", unsupported, 0, "invalid_character_budget"),
        ]
        for name, material, budget, expected_code in cases:
            project = root / f"project-{name}"
            completed = run_operator(
                "run",
                str(project),
                "--material",
                str(material),
                "--max-total-chars",
                str(budget),
                "--json",
                check=False,
            )
            assert completed.returncode == 1, completed.stdout
            payload = json.loads(completed.stdout)
            assert payload["error"]["code"] == expected_code, payload
            assert payload["project_created"] is False, payload
            assert not project.exists(), project

        material_parent = root / "material-parent"
        material_parent.mkdir()
        (material_parent / "brief.md").write_text(
            "项目父级材料目录不应递归包含即将创建的项目。",
            encoding="utf-8",
        )
        nested_project = material_parent / "project"
        completed = run_operator(
            "run",
            str(nested_project),
            "--material",
            str(material_parent),
            "--json",
            check=False,
        )
        assert completed.returncode == 1, completed.stdout
        payload = json.loads(completed.stdout)
        assert payload["error"]["code"] == "recursive_project_material", payload
        assert payload["project_created"] is False, payload
        assert not nested_project.exists(), nested_project

        existing_project = root / "existing-project"
        managed_material = existing_project / "AD-creative"
        managed_material.mkdir(parents=True)
        (existing_project / "brief.md").write_text(
            "项目根目录不能作为自身材料。",
            encoding="utf-8",
        )
        (managed_material / "managed.md").write_text(
            "受管控制面不能作为材料。",
            encoding="utf-8",
        )
        before = {
            path.relative_to(existing_project).as_posix(): path.read_bytes()
            for path in existing_project.rglob("*")
            if path.is_file()
        }
        for material in (existing_project, managed_material):
            completed = run_operator(
                "run",
                str(existing_project),
                "--material",
                str(material),
                "--json",
                check=False,
            )
            assert completed.returncode == 1, completed.stdout
            payload = json.loads(completed.stdout)
            assert payload["error"]["code"] == "recursive_project_material", payload
            after = {
                path.relative_to(existing_project).as_posix(): path.read_bytes()
                for path in existing_project.rglob("*")
                if path.is_file()
            }
            assert after == before


def test_init_and_run_reject_managed_symlink_without_escape_write() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-project-symlink-") as raw:
        root = Path(raw)
        outside = root / "outside"
        outside.mkdir()
        sentinel = outside / "sentinel.txt"
        sentinel.write_text("unchanged", encoding="utf-8")
        before = {path.name: path.read_bytes() for path in outside.iterdir()}

        for command in ("init", "run"):
            project = root / f"project-{command}"
            project.mkdir()
            (project / "AD-creative").symlink_to(outside, target_is_directory=True)
            if command == "init":
                completed = run_operator("init", str(project), check=False)
                assert "INIT=CHECK" in completed.stdout
            else:
                material = root / "brief.md"
                material.write_text("客户希望测试安全边界。", encoding="utf-8")
                completed = run_operator(
                    "run",
                    str(project),
                    "--material",
                    str(material),
                    "--json",
                    check=False,
                )
                payload = json.loads(completed.stdout)
                assert payload["error"]["code"] == "unsafe_project_symlink"
            assert completed.returncode == 1
            assert {path.name: path.read_bytes() for path in outside.iterdir()} == before

        standalone = root / "project-standalone"
        standalone.mkdir()
        (standalone / "AD-creative").symlink_to(outside, target_is_directory=True)
        completed = run_init(str(standalone), check=False)
        assert completed.returncode == 1
        assert "INIT=CHECK" in completed.stdout
        assert {path.name: path.read_bytes() for path in outside.iterdir()} == before


def test_init_dirfd_resists_concurrent_managed_symlink_swap() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-init-symlink-swap-") as raw:
        root = Path(raw)
        project = root / "project"
        project.mkdir()
        outside = root / "outside"
        outside.mkdir()
        sentinel = outside / "sentinel.txt"
        sentinel.write_text("unchanged", encoding="utf-8")
        outside_before = {
            path.relative_to(outside).as_posix(): path.read_bytes()
            for path in outside.rglob("*")
            if path.is_file()
        }
        original_link = init_project_module.os.link
        swapped = False

        def swapping_link(
            source: str,
            target: str,
            *,
            src_dir_fd: int | None = None,
            dst_dir_fd: int | None = None,
            follow_symlinks: bool = True,
        ) -> None:
            nonlocal swapped
            if not swapped:
                managed = project / "AD-creative"
                assert managed.is_dir()
                managed.rename(project / "AD-creative.before-swap")
                managed.symlink_to(outside, target_is_directory=True)
                swapped = True
            original_link(
                source,
                target,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
                follow_symlinks=follow_symlinks,
            )

        with patch.object(init_project_module.os, "link", side_effect=swapping_link):
            try:
                init_project_module.copy_content_template(template_root(), project)
            except (OSError, RuntimeError) as exc:
                assert "symlink" in str(exc).lower() or "not a directory" in str(exc).lower()
            else:
                raise AssertionError("concurrent managed symlink swap must fail closed")

        assert swapped
        outside_after = {
            path.relative_to(outside).as_posix(): path.read_bytes()
            for path in outside.rglob("*")
            if path.is_file()
        }
        assert outside_after == outside_before


def test_profile_analysis_stays_on_content_surface_without_governance_noise() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-profile-content-") as raw:
        project = Path(raw) / "project"
        project.mkdir()
        material = project / "meeting.md"
        material.write_text(
            "张总: 我们希望品牌更年轻，但不要像普通快消广告。\n"
            "李经理: 产品卖点必须清楚，内部还没统一偏功能还是偏情绪。\n",
            encoding="utf-8",
        )
        run_operator(
            "run",
            str(project),
            "--material",
            str(material),
            "--goal",
            "先理解会议内容",
            "--json",
        )
        analyzed = run_operator(
            "profile-analyze",
            str(project),
            "--source-id",
            "SRC-001",
            "--brand",
            "NOVA",
            "--json",
        )
        payload = json.loads(analyzed.stdout)
        assert payload["profile_analysis"] == "PASS", payload
        assert payload["work_id"] == ""
        assert payload["dashboard"] == ""
        assert payload["stats"]["governance_records_written"] == 0
        assert project_surface(project) == CONTENT_SURFACE
        assert file_count(project) <= 20, file_count(project)
        assert (
            project / "AD-creative/orchestrator/profile_knowledge/profile_current_truth.md"
        ).is_file()
        assert (project / "AD-creative/handoff/画像分析简报.md").is_file()
        forbidden = [
            "AD-creative/handoff/操作台.html",
            "AD-creative/orchestrator/events.jsonl",
            "AD-creative/orchestrator/artifact_index.csv",
            "AD-creative/orchestrator/version_map.csv",
            "AD-creative/orchestrator/gate_log.csv",
            "AD-creative/orchestrator/work_items.csv",
        ]
        assert not [path for path in forbidden if (project / path).exists()]


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
    test_unbiased_chatgpt_evidence_receipt_is_hash_bound_and_manual()
    test_default_run_emits_content_answer_without_delivery_theatre()
    test_external_source_map_repairs_unsafe_local_gitignore()
    test_local_source_state_dirfd_resists_concurrent_symlink_swap()
    test_open_project_dir_closes_fd_when_visible_binding_disappears()
    test_private_source_map_failures_block_support_and_client_pack()
    test_missing_private_map_with_registered_alias_blocks_exports()
    test_client_pack_private_marker_zip_scan_is_bounded_and_directory_safe()
    test_client_pack_scan_and_hash_share_one_stable_file_binding()
    test_client_pack_parent_directory_swap_cannot_escape_project()
    test_client_pack_scans_compressed_pdf_visible_text()
    test_run_preflight_rejects_invalid_inputs_before_project_write()
    test_init_and_run_reject_managed_symlink_without_escape_write()
    test_init_dirfd_resists_concurrent_managed_symlink_swap()
    test_profile_analysis_stays_on_content_surface_without_governance_noise()
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
