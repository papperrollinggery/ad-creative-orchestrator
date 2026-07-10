#!/usr/bin/env python3
"""Run the project verification suite."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

from runtime_paths import source_root, template_root


SOURCE_ROOT = source_root()
ROOT = SOURCE_ROOT or Path(__file__).resolve().parent
SOURCE_MODE = SOURCE_ROOT is not None
EXPECTED_CLI_VERSION = "adco 0.2.0"


def run(args: list[str]) -> None:
    print("+ " + " ".join(args))
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(args, cwd=ROOT, check=True, env=env)


def run_exact_output(args: list[str], expected: str) -> None:
    print("+ " + " ".join(args))
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    actual = completed.stdout.strip()
    print(actual)
    if actual != expected:
        raise AssertionError(
            f"Expected exact output from {' '.join(args)}: {expected!r}; got {actual!r}"
        )


def run_json(args: list[str]) -> None:
    print("+ " + " ".join(args) + " >/dev/null")
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=True, env=env)
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    try:
        json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        snippet = completed.stdout[:1000]
        raise AssertionError(f"Expected JSON output from {' '.join(args)}: {exc}\n{snippet}") from exc


def cleanup_python_caches(root: Path) -> None:
    pollution_dirs = ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")
    for path in [found for name in pollution_dirs for found in root.rglob(name)]:
        if ".git" not in path.parts and path.exists():
            try:
                shutil.rmtree(path)
            except FileNotFoundError:
                pass
    for pattern in ("*.pyc", "*.pyo", ".DS_Store"):
        for path in root.rglob(pattern):
            if ".git" not in path.parts and path.exists():
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass


def main() -> int:
    python = sys.executable
    if SOURCE_MODE:
        run(
            [
                python,
                "-m",
                "py_compile",
                "tools/ad_creative_operator.py",
                "tools/check_distribution.py",
                "tools/check_gate_fixtures.py",
                "tools/check_packaged_assets.py",
                "tools/check_specialist_schemas.py",
                "tools/check_docs_commands.py",
                "tools/render_demo_transcript.py",
                "tools/test_gates.py",
                "tools/test_goal_workflow.py",
                "tools/test_specialist_exchange.py",
                "tools/validate_project.py",
                "tools/init_project.py",
                "tools/runtime_paths.py",
                "tools/specialist_schema_validation.py",
            ]
        )
        run([python, "tools/check_packaged_assets.py"])
        run([python, "tools/check_specialist_schemas.py"])
        run([python, "tools/check_docs_commands.py"])
        run([python, "tools/check_gate_fixtures.py"])
        run([python, "tools/render_demo_transcript.py", "--check"])
        run_exact_output([python, "tools/ad_creative_operator.py", "--version"], EXPECTED_CLI_VERSION)
        run([python, "tools/ad_creative_operator.py", "doctor"])
        run_json([python, "tools/ad_creative_operator.py", "doctor", "--json"])
        run([python, "tools/ad_creative_operator.py", "release-status"])
        run_json([python, "tools/ad_creative_operator.py", "release-status", "--json"])
        run([python, "tools/ad_creative_operator.py", "docs"])
        run_json([python, "tools/ad_creative_operator.py", "docs", "--json"])
        run([python, "tools/test_gates.py"])
        run([python, "tools/test_goal_workflow.py"])
        run([python, "tools/test_specialist_exchange.py"])
    else:
        run(
            [
                python,
                "-m",
                "py_compile",
                "ad_creative_operator.py",
                "check_docs_commands.py",
                "check_gate_fixtures.py",
                "check_packaged_assets.py",
                "check_specialist_schemas.py",
                "render_demo_transcript.py",
                "test_gates.py",
                "test_goal_workflow.py",
                "test_specialist_exchange.py",
                "validate_project.py",
                "init_project.py",
                "runtime_paths.py",
            ]
        )
        run_exact_output([python, "-m", "ad_creative_operator", "--version"], EXPECTED_CLI_VERSION)
        run([python, "-m", "check_specialist_schemas"])
        run([python, "-m", "check_docs_commands"])
        run([python, "-m", "check_gate_fixtures"])
        run([python, "-m", "ad_creative_operator", "doctor"])
        run_json([python, "-m", "ad_creative_operator", "doctor", "--json"])
        run([python, "-m", "ad_creative_operator", "release-status"])
        run_json([python, "-m", "ad_creative_operator", "release-status", "--json"])
        run([python, "-m", "ad_creative_operator", "docs"])
        run_json([python, "-m", "ad_creative_operator", "docs", "--json"])
        run([python, "-m", "test_gates"])
        run([python, "-m", "test_goal_workflow"])
        run([python, "-m", "test_specialist_exchange"])
    if SOURCE_MODE:
        run([python, "tools/validate_project.py", str(template_root())])
        run([python, "tools/validate_project.py", "examples/moncler_protocol_dry_run"])
        run([python, "tools/validate_project.py", "examples/simulated_qingling_outdoor_launch"])
    else:
        run([python, "-m", "validate_project", str(template_root())])
    with tempfile.TemporaryDirectory(prefix="adco-check-") as raw_tmp:
        tmp = Path(raw_tmp)
        moncler = tmp / "moncler_protocol_dry_run"
        qingling = tmp / "simulated_qingling_outdoor_launch"
        sample = tmp / "sample_project"
        demo = tmp / "demo_project"
        quickstart = tmp / "quickstart_project"
        quickstart_json = tmp / "quickstart_json_project"
        initialized = tmp / "init_project"
        operator = ["tools/ad_creative_operator.py"] if SOURCE_MODE else ["-m", "ad_creative_operator"]
        validator = ["tools/validate_project.py"] if SOURCE_MODE else ["-m", "validate_project"]
        if SOURCE_MODE:
            shutil.copytree(ROOT / "examples/moncler_protocol_dry_run", moncler)
            shutil.copytree(ROOT / "examples/simulated_qingling_outdoor_launch", qingling)
        run([python, *operator, "init", str(initialized)])
        run_json([python, *operator, "validate", str(initialized), "--json"])
        run([python, *operator, "sample", str(sample)])
        run_json([python, *operator, "creative-proposal", str(sample), "--json"])
        run([python, *operator, "creative-quality-gate", str(sample)])
        run([python, *operator, "profile-analyze", str(sample), "--brand", "NOVA Trail", "--company", "NOVA Client"])
        run_json([python, *operator, "profile-analyze", str(sample), "--brand", "NOVA Trail", "--company", "NOVA Client", "--json"])
        run([python, *operator, "hygiene", str(sample), "--strict"])
        run_json([python, *operator, "hygiene", str(sample), "--json"])
        run([python, *operator, "goal-run", str(sample), "--goal-id", "latest", "--max-steps", "1"])
        run_json([python, *operator, "goal-run", str(sample), "--goal-id", "latest", "--max-steps", "1", "--json"])
        run([python, *operator, "film-quality-gate", str(sample)])
        run([python, *operator, "demo", str(demo), "--no-open"])
        run([python, *operator, "quickstart", str(quickstart), "--no-open"])
        run_json([python, *operator, "quickstart", str(quickstart_json), "--no-open", "--json"])
        run([python, *operator, "support-bundle", str(sample)])
        run_json([python, *operator, "support-bundle", str(sample), "--json"])
        run([python, *operator, "open-dashboard", str(sample), "--no-open"])
        run_json([python, *operator, "status", str(sample), "--json"])
        run([python, *operator, "next", str(sample)])
        run_json([python, *operator, "next", str(sample), "--json"])
        run_json([python, *operator, "validate", str(sample), "--json"])
        run([python, *validator, str(sample)])
        if SOURCE_MODE:
            run([python, *operator, "audit-dashboard", str(moncler), "--render"])
            run([python, *operator, "audit-dashboard", str(qingling), "--render"])
        run([python, *operator, "audit-dashboard", str(sample), "--render"])
        run_json([python, *operator, "audit-dashboard", str(sample), "--render", "--json"])
    cleanup_python_caches(ROOT)
    print("RUN_CHECKS=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        cleanup_python_caches(ROOT)
