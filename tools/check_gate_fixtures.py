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
            "approval": "",
            "direct_client_use": "yes",
            "used_in_slide": "S-BROWSER-01",
            "qa_flags": "browser_asset_registered;visual_layout_fixture_ready",
            "sha256": actual_hash,
        },
    )
    run_cli(["visual-layout-gate", str(project)], expect_code=1, must_contain="approval=missing")

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
    run_cli(["visual-layout-gate", str(project)], expect_code=1, must_contain="approval=NOT_APPROVED")
    update_csv_row(current_path, "asset_id", asset_id, {"approval": "PASS", "sha256": actual_hash})

    run_cli(["visual-layout-gate", str(project)], expect_code=0, must_contain="VISUAL_LAYOUT_GATE=PASS")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="adco-gate-fixture-") as raw_tmp:
        project = Path(raw_tmp) / "project"
        run_cli(["init", str(project)], expect_code=0, must_contain="INIT=PASS")

        run_cli(["client-outline-gate", str(project)], expect_code=1, must_contain="CLIENT_OUTLINE_GATE=BLOCKED")
        write_client_outline_row(project)
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
        visual_layout_asset_fixture(project, asset_id)

    print("GATE_FIXTURES=PASS")
    print("CLIENT_OUTLINE_GATE_FIXTURE=BLOCKED_THEN_PASS")
    print("CLIENT_LANGUAGE_GATE_FIXTURE=INTERNAL_ONLY_SKIPPED_AND_CLIENT_VISIBLE_BLOCKED")
    print("PREFLIGHT_ASSET_FIXTURE=BROWSER_EMPTY_ONLY_BLOCKED_WITH_REASON")
    print("BROWSER_ASSET_INTAKE_FIXTURE=BLOCKED_THEN_REGISTERED_WITH_PROVENANCE")
    print("VISUAL_LAYOUT_GATE_FIXTURE=CLIENT_ASSET_TRACEABILITY_AND_EXPLICIT_APPROVAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
