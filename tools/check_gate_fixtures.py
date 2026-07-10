#!/usr/bin/env python3
"""Exercise high-risk ADCO gates through the real CLI."""

from __future__ import annotations

import csv
import os
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

from ad_creative_operator import CLIENT_OUTLINE_FIELDS, file_sha256
from runtime_paths import source_root


SOURCE_ROOT = source_root()
ROOT = SOURCE_ROOT or Path(__file__).resolve().parent


def optional_module_available(name: str) -> bool:
    try:
        __import__(name)
    except Exception:
        return False
    return True


def operator_command() -> list[str]:
    if SOURCE_ROOT is not None:
        return [sys.executable, "tools/ad_creative_operator.py"]
    return [sys.executable, "-m", "ad_creative_operator"]


def run_cli(args: list[str], *, expect_code: int, must_contain: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [*operator_command(), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    if completed.returncode != expect_code:
        raise AssertionError(
            f"{' '.join(args)} returned {completed.returncode}, expected {expect_code}\n{output}"
        )
    if must_contain not in output:
        raise AssertionError(f"{' '.join(args)} missing {must_contain!r}\n{output}")
    return completed


def write_client_outline_row(project: Path) -> None:
    outline = project / "AD-creative/client_review/client_outline.csv"
    row = {
        "slide_id": "S01",
        "page_title": "清晨山路的第一口补给",
        "body_copy": "用客户能读懂的故事段落说明场景、产品利益和这一页要解决的传播判断。",
        "client_confirmation_point": "确认这一页是否作为开篇故事页。",
        "material_role": "使用已登记或待生成主视觉承接场景情绪。",
        "visual_slot": "横屏主视觉占位，画面低密度并保留文字安全区。",
        "visual_asset_status": "placeholder",
        "asset_ids": "",
        "visibility": "client_visible_ready",
        "status": "ready",
        "notes": "",
    }
    with outline.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CLIENT_OUTLINE_FIELDS)
        writer.writerow(row)


def confirm_client_outline(project: Path, evidence_id: str) -> None:
    run_cli(
        [
            "confirm-client-outline",
            str(project),
            "--confirmed-by",
            "fixture-project-owner",
            "--confirmed-at",
            "2026-07-05T00:00:00Z",
            "--evidence-ref",
            f"user_confirmation:{evidence_id}",
        ],
        expect_code=0,
        must_contain="CLIENT_OUTLINE_CONFIRMATION=PASS",
    )


def write_png(path: Path, *, width: int = 1600, height: int = 900) -> None:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)

    raw = b"".join(b"\x00" + (b"\x72\x96\xc8" * width) for _ in range(height))
    payload = b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            chunk(b"IDAT", zlib.compress(raw, level=6)),
            chunk(b"IEND", b""),
        ]
    )
    path.write_bytes(payload)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        fieldnames = list(csv.DictReader(handle).fieldnames or [])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def append_csv_row(path: Path, row: dict[str, str]) -> None:
    rows = read_csv(path)
    rows.append(row)
    write_csv(path, rows)


def update_csv_row(path: Path, key: str, value: str, updates: dict[str, str]) -> dict[str, str]:
    rows = read_csv(path)
    original: dict[str, str] | None = None
    for row in rows:
        if row.get(key) == value:
            original = dict(row)
            row.update(updates)
            break
    if original is None:
        raise AssertionError(f"{path} missing row {key}={value}")
    write_csv(path, rows)
    return original


def write_safe_client_review_files(project: Path) -> None:
    (project / "AD-creative/client_review/client_review_outline.md").write_text(
        """# Client Review Outline

status: ready
visibility: client_visible_ready

清晨山路开篇，说明场景、产品利益和客户判断点。
""",
        encoding="utf-8",
    )
    (project / "AD-creative/client_review/slide_spec.md").write_text(
        """# Internal Slide Spec

status: draft
visibility: internal_only

This internal-only spec can mention AI, internal process, prompt, and thread without entering the client language scan.
""",
        encoding="utf-8",
    )


def write_client_outline_asset_row(project: Path, *, asset_ids: str) -> None:
    outline = project / "AD-creative/client_review/client_outline.csv"
    row = {
        "slide_id": "S-BROWSER-01",
        "page_title": "浏览器既有主视觉确认",
        "body_copy": "这一页使用用户已经在浏览器中确认的候选主视觉，先登记来源和用途，再进入客户审阅判断。",
        "client_confirmation_point": "确认这张已有图是否作为本轮客户审阅的视觉方向。",
        "material_role": "承接已有浏览器图，避免重新生成或误用旧图。",
        "visual_slot": "横屏主视觉，来自浏览器已有候选图。",
        "visual_asset_status": "existing_image",
        "asset_ids": asset_ids,
        "visibility": "client_visible_ready",
        "status": "ready",
        "notes": "browser_intake_fixture",
    }
    with outline.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CLIENT_OUTLINE_FIELDS)
        writer.writeheader()
        writer.writerow(row)


def preflight_asset_fixture(project: Path) -> None:
    base_args = [
        "preflight-asset",
        str(project),
        "--work-id",
        "W-PREFLIGHT-BROWSER-001",
        "--source-scope",
        "browser-held Grok candidate image",
        "--browser-checked",
        "yes",
        "--browser-tool",
        "browser",
    ]
    run_cli(
        [*base_args, "--status", "PASS"],
        expect_code=1,
        must_contain="ASSET_PREFLIGHT=BLOCKED",
    )
    run_cli(
        [*base_args, "--status", "PARTIAL_PASS", "--blocked-reason", "download still pending"],
        expect_code=1,
        must_contain="ASSET_PREFLIGHT=BLOCKED",
    )
    run_cli(
        [*base_args, "--status", "BLOCKED"],
        expect_code=1,
        must_contain="ASSET_PREFLIGHT=BLOCKED",
    )
    run_cli(
        [
            *base_args,
            "--status",
            "BLOCKED",
            "--blocked-reason",
            "browser image exists but has not been downloaded/imported",
        ],
        expect_code=0,
        must_contain="VALIDATION=PASS",
    )


def browser_asset_intake_fixture(project: Path) -> str:
    write_client_outline_asset_row(project, asset_ids="")
    run_cli(["client-outline-gate", str(project)], expect_code=1, must_contain="asset_ids 为空")

    run_cli(
        [
            "browser-asset-intake",
            str(project),
            "--work-id",
            "W-BROWSER-INTAKE-001",
            "--source",
            "Grok",
            "--browser-evidence",
            "grok://conversation/browser-fixture-001",
        ],
        expect_code=1,
        must_contain="at least one --asset-file is required",
    )

    browser_asset = project / "browser_grok_candidate.png"
    write_png(browser_asset)
    source_hash = file_sha256(browser_asset)
    completed = run_cli(
        [
            "browser-asset-intake",
            str(project),
            "--work-id",
            "W-BROWSER-INTAKE-001",
            "--source",
            "Grok",
            "--browser-evidence",
            "grok://conversation/browser-fixture-001",
            "--conversation",
            "browser-fixture-001",
            "--qa-flags",
            "browser_asset_registered;grok_browser_origin;needs_visual_layout_gate",
            "--asset-file",
            str(browser_asset),
            "--slot-id",
            "BROWSER-KV-01",
            "--asset-type",
            "grok_browser_download",
        ],
        expect_code=0,
        must_contain="BROWSER_ASSET_INTAKE=PASS",
    )
    asset_line = next(line for line in completed.stdout.splitlines() if line.startswith("ASSET_IDS="))
    asset_id = asset_line.split("=", 1)[1].strip()
    if not asset_id:
        raise AssertionError("browser-asset-intake did not return an asset id")

    write_client_outline_asset_row(project, asset_ids=asset_id)
    confirm_client_outline(project, "browser-asset-outline")
    run_cli(["client-outline-gate", str(project)], expect_code=0, must_contain="CLIENT_OUTLINE_GATE=PASS")
    run_cli(["asset-current-manifest", str(project)], expect_code=0, must_contain="ASSET_CURRENT_MANIFEST=PASS")

    manifest_rows = read_csv(project / "AD-creative/visual_assets/asset_manifest.csv")
    current_rows = read_csv(project / "AD-creative/visual_assets/asset_current_manifest.csv")
    manifest = next((row for row in manifest_rows if row.get("asset_id") == asset_id), None)
    current = next((row for row in current_rows if row.get("asset_id") == asset_id), None)
    if manifest is None or current is None:
        raise AssertionError(f"{asset_id} missing from asset manifest or current manifest")
    if manifest.get("path") != current.get("path"):
        raise AssertionError(
            f"{asset_id} manifest path={manifest.get('path')!r}, current path={current.get('path')!r}"
        )

    imported = project / current["path"]
    if not imported.exists():
        raise AssertionError(f"{asset_id} imported local file missing: {imported}")
    imported_hash = file_sha256(imported)
    if imported_hash != source_hash:
        raise AssertionError(
            f"{asset_id} imported hash={imported_hash}, original browser asset hash={source_hash}"
        )
    if current.get("sha256") != source_hash:
        raise AssertionError(
            f"{asset_id} current manifest sha256={current.get('sha256')!r}, expected source hash {source_hash!r}"
        )

    expected_fields = {
        "source": "Grok: grok://conversation/browser-fixture-001",
        "platform": "Grok",
        "conversation": "browser-fixture-001",
        "local_file": current["path"],
        "sha256": source_hash,
        "original_or_processed": "original",
        "direct_client_use": "no",
        "used_in_slide": "S-BROWSER-01",
        "qa_flags": "browser_asset_registered;grok_browser_origin;needs_visual_layout_gate",
    }
    for field, expected in expected_fields.items():
        actual = current.get(field, "")
        if actual != expected:
            raise AssertionError(f"{asset_id} current manifest {field}={actual!r}, expected {expected!r}")
    if manifest.get("prompt_or_edit_ref") != "grok://conversation/browser-fixture-001":
        raise AssertionError(f"{asset_id} manifest prompt/source evidence was not recorded")
    return asset_id


def visual_layout_asset_fixture(project: Path, asset_id: str) -> None:
    current_path = project / "AD-creative/visual_assets/asset_current_manifest.csv"
    manifest_path = project / "AD-creative/visual_assets/asset_manifest.csv"
    current = next(row for row in read_csv(current_path) if row.get("asset_id") == asset_id)
    rel_path = current["path"]
    actual_hash = file_sha256(project / rel_path)
    update_csv_row(
        manifest_path,
        "asset_id",
        asset_id,
        {
            "visibility": "client_visible_ready",
            "qa_status": "PASS",
        },
    )
    update_csv_row(
        current_path,
        "asset_id",
        asset_id,
        {
            "approval": "PASS",
            "direct_client_use": "yes",
            "used_in_slide": "S-BROWSER-01",
            "qa_flags": "browser_asset_registered;visual_layout_fixture_ready",
            "sha256": actual_hash,
        },
    )
    run_cli(
        ["visual-layout-gate", str(project)],
        expect_code=1,
        must_contain="授权 receipt",
    )

    append_csv_row(
        project / "AD-creative/visual_assets/asset_authorizations.csv",
        {
            "authorization_id": "AUTH-BROWSER-001",
            "asset_id": asset_id,
            "asset_sha256": actual_hash,
            "approval_scope": "client_review",
            "approved_by": "fixture_human_reviewer",
            "approved_at": "2026-07-05T00:00:00Z",
            "evidence_ref": "user_confirmation:fixture-001",
            "status": "approved",
            "revoked_at": "",
            "notes": "hash-bound authorization fixture",
        },
    )

    run_cli(["visual-layout-gate", str(project)], expect_code=0, must_contain="VISUAL_LAYOUT_GATE=PASS")

    update_csv_row(current_path, "asset_id", asset_id, {"sha256": "0" * 64})
    run_cli(["visual-layout-gate", str(project)], expect_code=1, must_contain="sha256 过期")

    original_manifest = update_csv_row(
        manifest_path,
        "asset_id",
        asset_id,
        {"path": "AD-creative/visual_assets/raw/missing-browser-fixture.png"},
    )
    run_cli(["visual-layout-gate", str(project)], expect_code=1, must_contain="文件不存在")
    update_csv_row(manifest_path, "asset_id", asset_id, {"path": original_manifest["path"]})
    run_cli(["asset-current-manifest", str(project)], expect_code=0, must_contain="ASSET_CURRENT_MANIFEST=PASS")

    update_csv_row(manifest_path, "asset_id", asset_id, {"status": "archived"})
    run_cli(["visual-layout-gate", str(project)], expect_code=1, must_contain="status=archived")
    update_csv_row(manifest_path, "asset_id", asset_id, {"status": original_manifest["status"]})
    run_cli(["asset-current-manifest", str(project)], expect_code=0, must_contain="ASSET_CURRENT_MANIFEST=PASS")

    update_csv_row(current_path, "asset_id", asset_id, {"approval": "NOT_APPROVED"})
    run_cli(["visual-layout-gate", str(project)], expect_code=0, must_contain="VISUAL_LAYOUT_GATE=PASS")
    update_csv_row(current_path, "asset_id", asset_id, {"approval": "PASS", "sha256": actual_hash})

    run_cli(["visual-layout-gate", str(project)], expect_code=0, must_contain="VISUAL_LAYOUT_GATE=PASS")


def prepare_visual_package(project: Path) -> None:
    run_cli(["export-pptx", str(project)], expect_code=0, must_contain="PPTX_EDITABLE=PASS")
    artifact_path = project / "AD-creative/orchestrator/artifact_index.csv"
    artifacts = read_csv(artifact_path)
    pptx = next(row for row in artifacts if row.get("artifact_id") == "ART-PPTX-001")
    preview_path = project / "AD-creative/ppt/exports/client_review_v001_preview.png"
    write_png(preview_path)
    append_csv_row(
        artifact_path,
        {
            "artifact_id": "ART-PREVIEW-001",
            "artifact_type": "preview",
            "path": str(preview_path.relative_to(project)),
            "stage": "ppt_gate",
            "version": "v001",
            "status": "done",
            "visibility": "internal_only",
            "source_event_ids": "",
            "linked_requirements": "",
            "linked_work_items": "",
            "linked_references": "",
            "linked_assets": "",
            "gate_status": "PASS",
            "supersedes_artifact_id": "",
            "created_at": "2026-07-05T00:00:00Z",
            "updated_at": "2026-07-05T00:00:00Z",
            "sha256": file_sha256(preview_path),
            "size_bytes": str(preview_path.stat().st_size),
            "derived_from_artifact_id": "ART-PPTX-001",
            "derived_from_sha256": pptx["sha256"],
        },
    )
    truth_path = project / "AD-creative/orchestrator/current_truth.md"
    truth = truth_path.read_text(encoding="utf-8")
    truth = truth.replace(
        "current_preview_artifact_id:",
        "current_preview_artifact_id: ART-PREVIEW-001",
    )
    truth_path.write_text(truth, encoding="utf-8")


def threadops_receipt_fixture(project: Path) -> None:
    real_thread_id = "019f2222-3333-7444-8555-666666666666"
    receipt_rel = "AD-creative/agents/receipts/WORK-THREADOPS-FIXTURE/LANE-01-DEV_receipt.md"
    receipt_path = project / receipt_rel
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        """# LANE-01-DEV Receipt

status: returned
thread_id: 019f2222-3333-7444-8555-666666666666
loop_state: returned

## Files Changed

pending

## Validation Result

pending

## Dirty-State Impact

pending

## Adoption / Rejection Recommendation

worker_recommendation: pending
worker_rejection_reason: pending_if_not_adopted

## Cleanup Actions

pending

## Evidence

pending
""",
        encoding="utf-8",
    )
    append_csv_row(
        project / "AD-creative/orchestrator/thread_registry.csv",
        {
            "thread_id": real_thread_id,
            "title": "Fixture execution worker",
            "role": "DEV",
            "lane_id": "LANE-01-DEV",
            "lane_run_id": "WORK-THREADOPS-FIXTURE:LANE-01-DEV",
            "work_id": "WORK-THREADOPS-FIXTURE",
            "lifecycle_state": "returned",
            "pinned": "false",
            "archived": "true",
            "created_at": "2026-07-05T00:00:00Z",
            "updated_at": "2026-07-05T00:01:00Z",
            "cleanup_action": "archive_after_receipt_reconcile",
            "notes": "fixture: received receipt with placeholder evidence must be blocked",
            "goal_id": "GOAL-THREADOPS-FIXTURE",
            "mode": "execution_worker",
            "environment": "isolated_worktree",
            "workspace_path": "/tmp/adco-threadops-fixture",
            "write_scope": "tools/ad_creative_operator.py",
            "professional_identity": "development worker",
            "receipt_path": receipt_rel,
            "receipt_status": "received",
            "reconciliation_status": "returned",
            "assigned_at": "2026-07-05T00:00:00Z",
            "returned_at": "2026-07-05T00:01:00Z",
            "reconciled_at": "",
            "archived_at": "2026-07-05T00:02:00Z",
            "cleanup_reason": "",
            "last_seen_at": "2026-07-05T00:01:00Z",
            "duplicate_of": "",
            "planned_thread_id": "planned:WORK-THREADOPS-FIXTURE:LANE-01-DEV",
            "dispatch_status": "dispatched",
            "real_thread_id": real_thread_id,
            "title_action": "dispatcher_set",
            "title_verified_at": "2026-07-05T00:00:10Z",
            "dispatch_receipt_path": "AD-creative/orchestrator/thread_dispatch_WORK-THREADOPS-FIXTURE.md",
            "dispatch_evidence": "read_thread fixture evidence",
            "convergence_state": "receipt_received",
            "last_progress_at": "2026-07-05T00:00:50Z",
            "absolute_deadline_at": "2026-07-05T00:05:00Z",
            "bounded_extension_used": "false",
            "extension_reason": "",
            "convergence_reminder_at": "",
            "convergence_reason": "",
            "rescue_count": "0",
            "rescue_thread_id": "",
            "receipt_thread_id": real_thread_id,
            "adoption_decision": "ADOPT",
            "rejection_reason": "",
        },
    )
    (project / "AD-creative/orchestrator/thread_dispatch_WORK-THREADOPS-FIXTURE.md").write_text(
        f"real_thread_id: {real_thread_id}\nabsolute_deadline_at: 2026-07-05T00:05:00Z\n",
        encoding="utf-8",
    )
    append_csv_row(
        project / "AD-creative/orchestrator/work_items.csv",
        {
            "work_id": "WORK-THREADOPS-FIXTURE",
            "stage": "threadops",
            "title": "ThreadOps fixture",
            "objective": "Validate worker receipt identity and proof.",
            "owner_agent": "DEV",
            "status": "done",
            "priority": "P1",
            "input_refs": "fixture",
            "output_artifacts": "",
            "linked_requirements": "",
            "linked_source_events": "",
            "linked_references": "",
            "linked_assets": "",
            "linked_slides": "",
            "blocked_by": "",
            "gate_required": "thread_discipline",
            "client_visibility": "internal_only",
            "created_at": "2026-07-05T00:00:00Z",
            "updated_at": "2026-07-05T00:02:00Z",
            "supersedes_work_id": "",
        },
    )
    append_csv_row(
        project / "AD-creative/orchestrator/agent_runs.csv",
        {
            "run_id": "RUN-THREADOPS-FIXTURE",
            "work_id": "WORK-THREADOPS-FIXTURE",
            "agent_role": "DEV",
            "status": "reconciled",
            "started_at": "2026-07-05T00:00:00Z",
            "completed_at": "2026-07-05T00:01:00Z",
            "input_files": "fixture",
            "output_files": receipt_rel,
            "gate_id": "",
            "summary": "fixture",
            "next_action": "archive",
            "thread_id": real_thread_id,
            "lane_id": "LANE-01-DEV",
            "receipt_path": receipt_rel,
            "proof_status": "receipt_identity_verified",
            "reconciliation_status": "returned",
        },
    )
    run_cli(
        ["validate", str(project)],
        expect_code=1,
        must_contain="received execution worker receipt lacks concrete proof fields",
    )

    receipt_path.write_text(
        """# LANE-01-DEV Receipt

status: returned
thread_id: 019f2222-3333-7444-8555-666666666666
loop_state: returned
helper_mode: none
helper_failure_reason: none

## Files Changed

tools/ad_creative_operator.py

## Validation Result

python3 tools/check_gate_fixtures.py PASS

## Dirty-State Impact

isolated worktree only; no user files touched

## Adoption / Rejection Recommendation

worker_recommendation: PARTIAL_ADOPT
worker_rejection_reason: not_applicable
files_merged: pending_main_control_decision

## Cleanup Actions

archive_after_receipt; cleanup_status=ready

## Evidence

real_thread_id=019f2222-3333-7444-8555-666666666666; dispatch_evidence=read_thread fixture evidence
""",
        encoding="utf-8",
    )
    run_cli(
        ["validate", str(project)],
        expect_code=1,
        must_contain="adopted receipt missing host scope proof",
    )
    update_csv_row(
        project / "AD-creative/orchestrator/thread_registry.csv",
        "lane_run_id",
        "WORK-THREADOPS-FIXTURE:LANE-01-DEV",
        {
            "lifecycle_state": "rejected_evidence",
            "dispatch_status": "rejected_evidence",
            "receipt_status": "rejected",
            "reconciliation_status": "rejected_evidence",
            "convergence_state": "receipt_rejected",
            "adoption_decision": "REJECT",
            "rejection_reason": "missing_host_scope_proof",
        },
    )
    update_csv_row(
        project / "AD-creative/orchestrator/agent_runs.csv",
        "run_id",
        "RUN-THREADOPS-FIXTURE",
        {
            "status": "rejected_evidence",
            "proof_status": "missing_host_scope_proof",
            "reconciliation_status": "rejected_evidence",
        },
    )
    run_cli(["validate", str(project)], expect_code=0, must_contain="VALIDATION=PASS")


def thread_convergence_fixture(project: Path) -> None:
    work_id = "WORK-THREAD-CONVERGENCE"
    lane_id = "LANE-01-COPY_CREATIVE"
    real_thread_id = "019f3333-4444-7555-8666-777777777777"
    rescue_thread_id = "019f4444-5555-7666-8777-888888888888"
    wrong_thread_id = "019f5555-6666-7777-8888-999999999999"
    run_cli(
        [
            "thread-plan",
            str(project),
            "--goal-id",
            "GOAL-THREAD-CONVERGENCE",
            "--work-id",
            work_id,
            "--roles",
            "copy_creative",
            "--title",
            "Bounded convergence fixture",
            "--objective",
            "Progress must not be killed by poll count and rescue must stay bounded.",
        ],
        expect_code=0,
        must_contain="THREAD_PLAN=PASS",
    )
    run_cli(
        [
            "dispatch-record",
            str(project),
            "--work-id",
            work_id,
            "--lane-id",
            lane_id,
            "--real-thread-id",
            real_thread_id,
            "--title-verified-at",
            "2026-07-05T00:00:00Z",
            "--absolute-deadline-at",
            "2026-07-05T00:01:00Z",
            "--dispatch-evidence",
            "read_thread title and id matched fixture worker",
        ],
        expect_code=0,
        must_contain="DISPATCH_RECORD=dispatched",
    )
    run_cli(
        [
            "thread-observe",
            str(project),
            "--work-id",
            work_id,
            "--lane-id",
            lane_id,
            "--state",
            "active_with_progress",
            "--observed-at",
            "2026-07-05T00:00:20Z",
            "--evidence",
            "worker produced new analysis",
        ],
        expect_code=0,
        must_contain="THREAD_OBSERVE=active_with_progress",
    )
    run_cli(
        [
            "thread-observe",
            str(project),
            "--work-id",
            work_id,
            "--lane-id",
            lane_id,
            "--state",
            "finalizing_receipt",
            "--observed-at",
            "2026-07-05T00:00:50Z",
            "--absolute-deadline-at",
            "2026-07-05T00:02:00Z",
            "--extension-reason",
            "visible receipt assembly in progress",
            "--evidence",
            "worker is organizing final receipt",
        ],
        expect_code=0,
        must_contain="BOUNDED_EXTENSION_USED=true",
    )
    run_cli(
        [
            "thread-observe",
            str(project),
            "--work-id",
            work_id,
            "--lane-id",
            lane_id,
            "--state",
            "active_with_progress",
            "--observed-at",
            "2026-07-05T00:01:00Z",
            "--absolute-deadline-at",
            "2026-07-05T00:03:00Z",
            "--extension-reason",
            "second extension must be blocked",
            "--evidence",
            "new activity",
        ],
        expect_code=1,
        must_contain="bounded_extension_already_used",
    )
    run_cli(
        [
            "thread-observe",
            str(project),
            "--work-id",
            work_id,
            "--lane-id",
            lane_id,
            "--state",
            "silent",
            "--observed-at",
            "2026-07-05T00:02:01Z",
            "--convergence-reminder-sent",
            "--evidence",
            "no new activity after absolute deadline",
        ],
        expect_code=0,
        must_contain="THREAD_OBSERVE=silent",
    )
    run_cli(
        [
            "thread-observe",
            str(project),
            "--work-id",
            work_id,
            "--lane-id",
            lane_id,
            "--state",
            "thread_not_converged",
            "--observed-at",
            "2026-07-05T00:02:02Z",
            "--evidence",
            "reminder produced no receipt",
        ],
        expect_code=0,
        must_contain="THREAD_OBSERVE=thread_not_converged",
    )
    run_cli(
        [
            "thread-observe",
            str(project),
            "--work-id",
            work_id,
            "--lane-id",
            lane_id,
            "--state",
            "rescue_dispatched",
            "--observed-at",
            "2026-07-05T00:02:03Z",
            "--absolute-deadline-at",
            "2026-07-05T00:03:00Z",
            "--rescue-thread-id",
            rescue_thread_id,
            "--evidence",
            "single bounded rescue dispatched",
        ],
        expect_code=0,
        must_contain="RESCUE_COUNT=1",
    )
    run_cli(
        [
            "thread-observe",
            str(project),
            "--work-id",
            work_id,
            "--lane-id",
            lane_id,
            "--state",
            "rescue_dispatched",
            "--observed-at",
            "2026-07-05T00:02:04Z",
            "--absolute-deadline-at",
            "2026-07-05T00:04:00Z",
            "--rescue-thread-id",
            wrong_thread_id,
            "--evidence",
            "second rescue attempt",
        ],
        expect_code=1,
        must_contain="rescue_limit_exceeded",
    )

    receipt_rel = f"AD-creative/agents/receipts/{work_id}/{lane_id}_receipt.md"
    receipt_path = project / receipt_rel
    rescue_receipt_rel = (
        f"AD-creative/agents/receipts/{work_id}/{lane_id}_receipt_rescue.md"
    )
    rescue_receipt_path = project / rescue_receipt_rel
    rescue_receipt_path.write_text(
        f"""# {lane_id} Receipt

status: returned
thread_id: {wrong_thread_id}
worker_recommendation: ADOPT
files_changed: AD-creative/workspaces/{work_id}/{lane_id}/copy_drafts.md
validation_result: PASS - fixture
dirty_state_impact: isolated workspace only
loop_state: returned
cleanup_actions: archive after reconciliation
evidence_refs: fixture evidence
""",
        encoding="utf-8",
    )
    run_cli(
        [
            "thread-reconcile",
            str(project),
            "--work-id",
            work_id,
            "--lane-id",
            lane_id,
            "--receipt-path",
            rescue_receipt_rel,
            "--adoption-decision",
            "ADOPT",
            "--reconciled-at",
            "2026-07-05T00:02:30Z",
            "--cleanup-action",
            "archive_after_receipt_reconcile",
        ],
        expect_code=1,
        must_contain="invalid_worker_thread_id",
    )
    output_path = (
        project
        / "AD-creative/workspaces"
        / work_id
        / lane_id
        / "copy_drafts.md"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("# Verified worker output\n", encoding="utf-8")
    rescue_receipt_path.write_text(
        f"""# {lane_id} Receipt

status: returned
thread_id: {rescue_thread_id}
worker_recommendation: ADOPT
files_changed: AD-creative/workspaces/{work_id}/{lane_id}/copy_drafts.md
validation_result: PASS - fixture
dirty_state_impact: isolated workspace only
loop_state: returned
cleanup_actions: archived worker after reconciliation
evidence_refs: fixture evidence and matching rescue thread identity
""",
        encoding="utf-8",
    )
    run_cli(
        [
            "thread-reconcile",
            str(project),
            "--work-id",
            work_id,
            "--lane-id",
            lane_id,
            "--receipt-path",
            rescue_receipt_rel,
            "--adoption-decision",
            "ADOPT",
            "--reconciled-at",
            "2026-07-05T00:02:40Z",
            "--cleanup-action",
            "archived_after_receipt_reconcile",
            "--archived-at",
            "2026-07-05T00:02:45Z",
        ],
        expect_code=0,
        must_contain="THREAD_RECONCILE=reconciled",
    )
    run_cli(["validate", str(project)], expect_code=0, must_contain="VALIDATION=PASS")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="adco-gate-fixture-") as raw_tmp:
        project = Path(raw_tmp) / "project"
        run_cli(["init", str(project)], expect_code=0, must_contain="INIT=PASS")

        run_cli(["client-outline-gate", str(project)], expect_code=1, must_contain="CLIENT_OUTLINE_GATE=BLOCKED")
        write_client_outline_row(project)
        confirm_client_outline(project, "base-outline")
        run_cli(["client-outline-gate", str(project)], expect_code=0, must_contain="CLIENT_OUTLINE_GATE=PASS")

        write_safe_client_review_files(project)
        run_cli(
            ["client-language-gate", str(project)],
            expect_code=0,
            must_contain="CLIENT_LANGUAGE_GATE=PASS",
        )
        client_copy = project / "AD-creative/client_review/client_copy_fixture.md"
        client_copy.write_text(
            """# Client Copy Fixture

status: ready
visibility: client_visible_ready

客户稿不能出现 prompt 或 thread 执行过程。
""",
            encoding="utf-8",
        )
        run_cli(
            ["client-language-gate", str(project)],
            expect_code=1,
            must_contain="client_copy_fixture.md",
        )
        client_copy.write_text(
            """# Client Copy Fixture

status: ready
visibility: client_visible_ready

客户稿只保留客户能判断的故事、利益和确认点。
""",
            encoding="utf-8",
        )
        run_cli(
            ["client-language-gate", str(project)],
            expect_code=0,
            must_contain="CLIENT_LANGUAGE_GATE=PASS",
        )
        preflight_asset_fixture(project)
        asset_id = browser_asset_intake_fixture(project)
        run_cli(
            [
                "preflight-asset",
                str(project),
                "--work-id",
                "W-PREFLIGHT-BROWSER-002",
                "--source-scope",
                "browser-held Grok candidate image",
                "--browser-checked",
                "yes",
                "--browser-tool",
                "browser",
                "--imported-asset-ids",
                asset_id,
                "--status",
                "PASS",
            ],
            expect_code=0,
            must_contain="VALIDATION=PASS",
        )
        visual_layout_exercised = optional_module_available("pptx")
        if visual_layout_exercised:
            prepare_visual_package(project)
            visual_layout_asset_fixture(project, asset_id)
        threadops_receipt_fixture(project)
        thread_convergence_fixture(project)

    print("GATE_FIXTURES=PASS")
    print("CLIENT_OUTLINE_GATE_FIXTURE=BLOCKED_THEN_PASS")
    print("CLIENT_LANGUAGE_GATE_FIXTURE=INTERNAL_ONLY_SKIPPED_AND_CLIENT_VISIBLE_BLOCKED")
    print("PREFLIGHT_ASSET_FIXTURE=BROWSER_EMPTY_ONLY_BLOCKED_WITH_REASON")
    print("BROWSER_ASSET_INTAKE_FIXTURE=BLOCKED_THEN_REGISTERED_WITH_PROVENANCE")
    print(
        "VISUAL_LAYOUT_GATE_FIXTURE="
        + (
            "REAL_DECK_PREVIEW_AND_HASH_BOUND_AUTHORIZATION"
            if visual_layout_exercised
            else "SKIPPED_OPTIONAL_DEPENDENCY_MISSING:python-pptx"
        )
    )
    print("THREADOPS_RECEIPT_FIXTURE=PLACEHOLDER_AND_MISSING_HOST_PROOF_REJECTED")
    print("THREAD_CONVERGENCE_FIXTURE=PROGRESS_EXTENSION_TIMEOUT_ONE_RESCUE_IDENTITY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
