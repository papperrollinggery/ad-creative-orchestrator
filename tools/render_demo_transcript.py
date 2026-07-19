#!/usr/bin/env python3
"""Render a stable first-run transcript for README/demo use."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/assets/first-run-transcript.md"
DISPLAY_PROJECT = "/tmp/adco-first-run"


def run(label: str, args: list[str], project: Path) -> str:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=True)
    stdout = scrub(result.stdout.strip(), project)
    return f"$ {label}\n{stdout}".rstrip()


def scrub(text: str, project: Path) -> str:
    aliases = [
        str(project),
        str(project.resolve()),
        f"/private{project}",
        f"/private{project.resolve()}",
    ]
    scrubbed = text
    for alias in sorted(set(aliases), key=len, reverse=True):
        scrubbed = scrubbed.replace(alias, DISPLAY_PROJECT)
    return scrubbed


def render() -> str:
    python = sys.executable
    with tempfile.TemporaryDirectory(prefix="adco-first-run-") as raw_tmp:
        project = Path(raw_tmp) / "project"
        blocks = [
            run(
                f"adco demo {DISPLAY_PROJECT} --no-open",
                [
                    python,
                    "tools/ad_creative_operator.py",
                    "demo",
                    str(project),
                    "--no-open",
                ],
                project,
            ),
            run(
                f"adco status {DISPLAY_PROJECT}",
                [python, "tools/ad_creative_operator.py", "status", str(project)],
                project,
            ),
            run(
                f"adco validate {DISPLAY_PROJECT}",
                [python, "tools/ad_creative_operator.py", "validate", str(project)],
                project,
            ),
            run(
                f"adco open-dashboard {DISPLAY_PROJECT} --no-open",
                [
                    python,
                    "tools/ad_creative_operator.py",
                    "open-dashboard",
                    str(project),
                    "--no-open",
                ],
                project,
            ),
            run(
                f"adco support-bundle {DISPLAY_PROJECT}",
                [python, "tools/ad_creative_operator.py", "support-bundle", str(project)],
                project,
            ),
            run(
                f"adco audit-dashboard {DISPLAY_PROJECT} --render",
                [
                    python,
                    "tools/ad_creative_operator.py",
                    "audit-dashboard",
                    str(project),
                    "--render",
                ],
                project,
            ),
        ]
    body = "\n\n".join(f"```console\n{block}\n```" for block in blocks)
    return f"""# First Run Transcript

Status: generated from local commands

This transcript is produced by:

```bash
python3 tools/render_demo_transcript.py
```

{body}

## Expected Files

```text
{DISPLAY_PROJECT}/AD-creative/handoff/操作台.html
{DISPLAY_PROJECT}/AD-creative/orchestrator/current_truth.md
{DISPLAY_PROJECT}/AD-creative/orchestrator/requirements.csv
{DISPLAY_PROJECT}/AD-creative/orchestrator/gaps.csv
{DISPLAY_PROJECT}/AD-creative/handoff/项目看板.md
{DISPLAY_PROJECT}/AD-creative/AGENTS.md
```
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if the transcript file is stale.")
    args = parser.parse_args()
    content = render()
    if args.check:
        if not OUTPUT.exists():
            print(f"DEMO_TRANSCRIPT_CHECK=FAIL missing {OUTPUT}")
            return 1
        existing = OUTPUT.read_text(encoding="utf-8")
        if existing != content:
            print(f"DEMO_TRANSCRIPT_CHECK=FAIL stale {OUTPUT}")
            return 1
        print("DEMO_TRANSCRIPT_CHECK=PASS")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"DEMO_TRANSCRIPT={OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
