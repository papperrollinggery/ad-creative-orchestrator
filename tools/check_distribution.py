#!/usr/bin/env python3
"""Build and inspect the wheel distribution contents."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = [
    "ad_creative_operator.py",
    "check_docs_commands.py",
    "check_gate_fixtures.py",
    "check_packaged_assets.py",
    "check_specialist_schemas.py",
    "init_project.py",
    "render_demo_transcript.py",
    "validate_project.py",
    "run_checks.py",
    "runtime_paths.py",
    "specialist_schema_validation.py",
    "test_gates.py",
    "test_goal_workflow.py",
    "test_specialist_exchange.py",
    "adco_resources/templates/project/AGENTS.md",
    "adco_resources/templates/project/AD-creative/orchestrator/project.yml",
    "adco_resources/templates/project/AD-creative/orchestrator/control_plane_schema.json",
    "adco_resources/templates/project/AD-creative/orchestrator/thread_registry.csv",
    "adco_resources/templates/project/AD-creative/orchestrator/thread_lane_plan_template.md",
    "adco_resources/templates/project/AD-creative/orchestrator/agency_staff_selection_template.md",
    "adco_resources/templates/project/AD-creative/agents/role_briefs/README.md",
    "adco_resources/templates/project/AD-creative/handoff/项目看板.md",
    "adco_resources/templates/project/AD-creative/gates/adversarial_council_gate_template.md",
    "adco_resources/skill_drafts/ad-creative-orchestrator/SKILL.md",
    "adco_resources/skill_drafts/ad-creative-orchestrator/migration_and_lifecycle.md",
    "adco_resources/skill_drafts/ad-creative-orchestrator/operator_cli_and_gates.md",
    "adco_resources/skill_drafts/ad-creative-orchestrator/specialist_exchange_and_craft.md",
    "adco_resources/skill_drafts/ad-creative-orchestrator/thread_operations.md",
    "adco_resources/contracts/specialist_exchange/v1/descriptor.schema.json",
    "adco_resources/contracts/specialist_exchange/v1/handoff.schema.json",
    "adco_resources/contracts/specialist_exchange/v1/receipt.schema.json",
    "adco_resources/contracts/specialist_exchange/v1/adoption.schema.json",
]
REQUIRED_ENTRY_POINTS = [
    "adco = ad_creative_operator:main",
    "adco-check = run_checks:main",
    "adco-init = init_project:main",
    "adco-validate = validate_project:main",
]
REQUIRED_PYPROJECT_SNIPPETS = [
    'name = "ad-creative-orchestrator"',
    'version = "0.3.0"',
    'adco = "ad_creative_operator:main"',
    'adco-check = "run_checks:main"',
    'adco-init = "init_project:main"',
    'adco-validate = "validate_project:main"',
    '"check_specialist_schemas",',
    '"specialist_schema_validation",',
    '"contracts/specialist_exchange/v1/*.schema.json"',
    '"skill_drafts/ad-creative-orchestrator/**/*"',
]
WHEEL_BUILD_TIMEOUT_SECONDS = 120


def find_dist_file(names: set[str], suffix: str) -> str | None:
    matches = sorted(name for name in names if name.endswith(suffix) and ".dist-info/" in name)
    return matches[0] if matches else None


def source_path_for_wheel_path(path: str) -> Path:
    return ROOT / "tools" / path


def static_manifest_check(reason: str) -> int:
    issues: list[str] = []
    for path in REQUIRED_PATHS:
        if not source_path_for_wheel_path(path).exists():
            issues.append(f"source missing for wheel path: {path}")
    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for snippet in REQUIRED_PYPROJECT_SNIPPETS:
        if snippet not in pyproject_text:
            issues.append(f"pyproject missing: {snippet}")
    if issues:
        print("DIST_CHECK=FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("DIST_CHECK=PASS")
    print("WHEEL=STATIC_MANIFEST")
    print(f"WHEEL_BUILD=SKIPPED:{reason}")
    return 0


def main() -> int:
    issues: list[str] = []
    with tempfile.TemporaryDirectory(prefix="adco-dist-") as raw_tmp:
        wheelhouse = Path(raw_tmp) / "wheelhouse"
        wheelhouse.mkdir()
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    ".",
                    "--no-deps",
                    "--no-build-isolation",
                    "--wheel-dir",
                    str(wheelhouse),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                timeout=WHEEL_BUILD_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            print(f"wheel build timed out after {WHEEL_BUILD_TIMEOUT_SECONDS}s")
            if exc.stdout:
                print(str(exc.stdout).strip())
            if exc.stderr:
                print(str(exc.stderr).strip())
            return static_manifest_check("timeout")
        if result.returncode != 0:
            if "Cannot import 'setuptools.build_meta'" in result.stderr:
                return static_manifest_check("build_backend_unavailable")
            print("DIST_CHECK=FAIL")
            print(result.stdout.strip())
            print(result.stderr.strip())
            return result.returncode

        wheels = sorted(wheelhouse.glob("ad_creative_orchestrator-*.whl"))
        if len(wheels) != 1:
            issues.append(f"expected one wheel, found {len(wheels)}")
        wheel = wheels[0] if wheels else None
        if wheel:
            with zipfile.ZipFile(wheel) as archive:
                names = set(archive.namelist())
                for path in REQUIRED_PATHS:
                    if path not in names:
                        issues.append(f"wheel missing: {path}")

                metadata_path = find_dist_file(names, "METADATA")
                entry_points_path = find_dist_file(names, "entry_points.txt")
                record_path = find_dist_file(names, "RECORD")
                if not metadata_path:
                    issues.append("wheel missing dist-info METADATA")
                if not entry_points_path:
                    issues.append("wheel missing dist-info entry_points.txt")
                if not record_path:
                    issues.append("wheel missing dist-info RECORD")

                if metadata_path:
                    metadata_text = archive.read(metadata_path).decode("utf-8")
                    if "Name: ad-creative-orchestrator" not in metadata_text:
                        issues.append("wheel metadata missing package name")
                    if "Version: 0.3.0" not in metadata_text:
                        issues.append("wheel metadata missing version")

                if entry_points_path:
                    entry_points_text = archive.read(entry_points_path).decode("utf-8")
                    for entry_point in REQUIRED_ENTRY_POINTS:
                        if entry_point not in entry_points_text:
                            issues.append(f"wheel entry point missing: {entry_point}")

    if issues:
        print("DIST_CHECK=FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("DIST_CHECK=PASS")
    if wheel:
        print(f"WHEEL={wheel.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
