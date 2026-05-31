#!/usr/bin/env python3
"""Run the project verification suite."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from runtime_paths import source_root, template_root


SOURCE_ROOT = source_root()
ROOT = SOURCE_ROOT or Path(__file__).resolve().parent
SOURCE_MODE = SOURCE_ROOT is not None


def run(args: list[str]) -> None:
    print("+ " + " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)


def run_json(args: list[str]) -> None:
    print("+ " + " ".join(args) + " >/dev/null")
    completed = subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=True)
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    try:
        json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        snippet = completed.stdout[:1000]
        raise AssertionError(f"Expected JSON output from {' '.join(args)}: {exc}\n{snippet}") from exc


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
                "tools/check_packaged_assets.py",
                "tools/check_docs_commands.py",
                "tools/render_demo_transcript.py",
                "tools/test_gates.py",
                "tools/test_goal_workflow.py",
                "tools/validate_project.py",
                "tools/init_project.py",
                "tools/runtime_paths.py",
            ]
        )
        run([python, "tools/check_packaged_assets.py"])
        run([python, "tools/check_docs_commands.py"])
        run([python, "tools/render_demo_transcript.py", "--check"])
        run([python, "tools/ad_creative_operator.py", "--version"])
        run([python, "tools/ad_creative_operator.py", "doctor"])
        run_json([python, "tools/ad_creative_operator.py", "doctor", "--json"])
        run([python, "tools/ad_creative_operator.py", "release-status"])
        run_json([python, "tools/ad_creative_operator.py", "release-status", "--json"])
        run([python, "tools/ad_creative_operator.py", "docs"])
        run_json([python, "tools/ad_creative_operator.py", "docs", "--json"])
        run([python, "tools/test_gates.py"])
        run([python, "tools/test_goal_workflow.py"])
    else:
        run(
            [
                python,
                "-m",
                "py_compile",
                "ad_creative_operator.py",
                "check_docs_commands.py",
                "check_packaged_assets.py",
                "render_demo_transcript.py",
                "test_gates.py",
                "test_goal_workflow.py",
                "validate_project.py",
                "init_project.py",
                "runtime_paths.py",
            ]
        )
        run([python, "-m", "ad_creative_operator", "--version"])
        run([python, "-m", "check_docs_commands"])
        run([python, "-m", "ad_creative_operator", "doctor"])
        run_json([python, "-m", "ad_creative_operator", "doctor", "--json"])
        run([python, "-m", "ad_creative_operator", "release-status"])
        run_json([python, "-m", "ad_creative_operator", "release-status", "--json"])
        run([python, "-m", "ad_creative_operator", "docs"])
        run_json([python, "-m", "ad_creative_operator", "docs", "--json"])
        run([python, "-m", "test_gates"])
        run([python, "-m", "test_goal_workflow"])
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
        initialized = tmp / "init_project"
        operator = ["tools/ad_creative_operator.py"] if SOURCE_MODE else ["-m", "ad_creative_operator"]
        validator = ["tools/validate_project.py"] if SOURCE_MODE else ["-m", "validate_project"]
        if SOURCE_MODE:
            shutil.copytree(ROOT / "examples/moncler_protocol_dry_run", moncler)
            shutil.copytree(ROOT / "examples/simulated_qingling_outdoor_launch", qingling)
        run([python, *operator, "init", str(initialized)])
        run_json([python, *operator, "validate", str(initialized), "--json"])
        run([python, *operator, "sample", str(sample)])
        run([python, *operator, "demo", str(demo), "--no-open"])
        run([python, *operator, "support-bundle", str(sample)])
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
    print("RUN_CHECKS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
