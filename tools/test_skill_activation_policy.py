#!/usr/bin/env python3
"""Regression checks for explicit-only ADCO skill activation metadata."""

from __future__ import annotations

from pathlib import Path
import tempfile

from init_project import (
    AGENTS_MERGE_SUGGESTION_REL,
    agents_policy_complete,
    copy_template,
)
from runtime_paths import (
    is_adco_source_repository,
    is_initialized_adco_project,
    skill_draft_dir,
    source_root,
    template_root,
)


EXPLICIT_TOKEN = "$ad-creative-orchestrator"


def read_required(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing activation policy file: {path}")
    return path.read_text(encoding="utf-8")


def main() -> int:
    skill_root = skill_draft_dir()
    metadata = read_required(skill_root / "agents/openai.yaml")
    skill = read_required(skill_root / "SKILL.md")
    normalized_skill = " ".join(skill.split())
    project_agents = read_required(template_root() / "AGENTS.md")

    assert "allow_implicit_invocation: false" in metadata
    assert EXPLICIT_TOKEN in metadata
    assert "Use only when the user explicitly invokes" in skill
    assert "ADCO source repository" in normalized_skill
    assert "DIRcreative source repository" in normalized_skill
    assert "ordinary advertising questions" in normalized_skill
    assert "ordinary code tasks" in normalized_skill
    assert "without ADCO project context" in normalized_skill

    # The metadata is the executable activation boundary: every implicit case is
    # disabled, while the explicit default prompt remains available.
    scenarios = {
        "maintain_adco_repository": False,
        "modify_adco_skill": False,
        "maintain_dircreative": False,
        "ordinary_advertising_question": False,
        "explicit_invocation": True,
        "initialized_project_and_explicit_invocation": True,
    }
    for name, expected in scenarios.items():
        explicit = name in {
            "explicit_invocation",
            "initialized_project_and_explicit_invocation",
        }
        actual = explicit and EXPLICIT_TOKEN in metadata
        if actual is not expected:
            raise AssertionError(f"activation scenario mismatch: {name}")

    assert "apply only when" in project_agents
    assert "explicitly" in project_agents
    assert "$ad-creative-orchestrator" in project_agents
    assert "Use `ad-creative-orchestrator` for this project." not in project_agents
    assert "Paperrolling-DIRcreative-SKILL" in project_agents
    assert "valid Specialist handoff" in project_agents

    with tempfile.TemporaryDirectory(prefix="adco-activation-empty-") as raw:
        ordinary = Path(raw)
        assert not is_initialized_adco_project(ordinary)
        copy_template(template_root(), ordinary)
        assert is_initialized_adco_project(ordinary)
        assert agents_policy_complete(ordinary)
        generated = read_required(ordinary / "AGENTS.md")
        assert "apply only when" in generated

    with tempfile.TemporaryDirectory(prefix="adco-activation-merge-") as raw:
        existing = Path(raw)
        (existing / "AGENTS.md").write_text("# Existing\n", encoding="utf-8")
        copy_template(template_root(), existing)
        assert not agents_policy_complete(existing)
        suggestion = read_required(existing / AGENTS_MERGE_SUGGESTION_REL)
        assert "conditional ADCO section" in suggestion
        assert "must not become an unconditional repository rule" in suggestion
    root = source_root()
    if root:
        assert is_adco_source_repository(root)
        assert not is_initialized_adco_project(root)
        repository_agents = read_required(root / "AGENTS.md")
        assert "ADCO Repository Self-Maintenance Mode" in repository_agents
        assert "Do not invoke an installed `ad-creative-orchestrator` skill" in repository_agents

    print("SKILL_ACTIVATION_POLICY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
