#!/usr/bin/env python3
"""Regression checks for explicit-only ADCO skill activation metadata."""

from __future__ import annotations

from pathlib import Path

from runtime_paths import skill_draft_dir, source_root, template_root


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

    assert "Use `ad-creative-orchestrator` for this project." in project_agents
    root = source_root()
    if root:
        repository_agents = read_required(root / "AGENTS.md")
        assert "ADCO Repository Self-Maintenance Mode" in repository_agents
        assert "Do not invoke an installed `ad-creative-orchestrator` skill" in repository_agents

    print("SKILL_ACTIVATION_POLICY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
