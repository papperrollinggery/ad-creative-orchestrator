#!/usr/bin/env python3
"""Regression checks for goal-plan and adversarial Gate policy."""

from __future__ import annotations

import tempfile
from pathlib import Path

from ad_creative_operator import (
    add_reference,
    ensure_project,
    render_goal_iteration_plan,
    review_reference_pack,
)
from validate_project import validate


def assert_valid(project: Path) -> None:
    errors, _ = validate(project)
    if errors:
        raise AssertionError("\n".join(errors))


def add_clean_reference(project: Path) -> None:
    add_reference(
        project,
        "https://example.com",
        "Example",
        "direction_reference",
        "official_or_public_reference",
        why_relevant="Evidence source for regression testing.",
        borrow="Structure only.",
        do_not_copy="Do not copy visible identity.",
        live_check=False,
    )


def test_gate_downgrades_without_adversarial_record() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-goal-no-adv-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        add_clean_reference(project)
        status, findings, _ = review_reference_pack(project)
        assert status == "PARTIAL_PASS", status
        assert any("反驳性议会" in item for item in findings), findings
        assert_valid(project)


def test_goal_plan_allows_clean_gate_pass() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-goal-with-adv-") as raw_project:
        project = Path(raw_project)
        ensure_project(project)
        render_goal_iteration_plan(
            project,
            goal_id="GOAL-REGRESSION-001",
            title="Goal regression",
            objective="Verify adversarial council record allows clean Gate PASS.",
            owner="Regression",
        )
        add_clean_reference(project)
        status, findings, _ = review_reference_pack(project)
        assert status == "PASS", (status, findings)
        assert not findings, findings
        assert_valid(project)


def main() -> int:
    test_gate_downgrades_without_adversarial_record()
    test_goal_plan_allows_clean_gate_pass()
    print("TEST_GOAL_WORKFLOW=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
