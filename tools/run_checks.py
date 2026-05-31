#!/usr/bin/env python3
"""Run the project verification suite."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(args: list[str]) -> None:
    print("+ " + " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    python = sys.executable
    run(
        [
            python,
            "-m",
            "py_compile",
            "tools/ad_creative_operator.py",
            "tools/test_goal_workflow.py",
            "tools/validate_project.py",
            "tools/init_project.py",
        ]
    )
    run([python, "tools/test_goal_workflow.py"])
    run([python, "tools/validate_project.py", "templates/project"])
    run([python, "tools/validate_project.py", "examples/moncler_protocol_dry_run"])
    run([python, "tools/validate_project.py", "examples/simulated_qingling_outdoor_launch"])
    run([python, "tools/ad_creative_operator.py", "audit-dashboard", "examples/moncler_protocol_dry_run", "--render"])
    run([python, "tools/ad_creative_operator.py", "audit-dashboard", "examples/simulated_qingling_outdoor_launch", "--render"])
    print("RUN_CHECKS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
