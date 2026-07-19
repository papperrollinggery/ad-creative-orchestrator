#!/usr/bin/env python3
"""Regression checks for explicit-only ADCO skill activation metadata."""

from __future__ import annotations

from pathlib import Path
import tempfile

from init_project import (
    AGENTS_REL,
    agents_policy_complete,
    copy_content_template,
    copy_template,
)
from runtime_paths import (
    CONTENT_SURFACE,
    DELIVERY_SURFACE,
    is_adco_source_repository,
    is_initialized_adco_project,
    project_surface,
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
    project_agents = read_required(template_root() / AGENTS_REL)

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

    assert "Apply these rules only inside" in project_agents
    assert "explicitly invokes" in project_agents
    assert "$ad-creative-orchestrator" in project_agents
    assert "content surface" in project_agents
    assert "delivery governance" in project_agents

    with tempfile.TemporaryDirectory(prefix="adco-activation-empty-") as raw:
        ordinary = Path(raw)
        assert not is_initialized_adco_project(ordinary)
        copy_content_template(template_root(), ordinary)
        assert is_initialized_adco_project(ordinary)
        assert agents_policy_complete(ordinary)
        assert project_surface(ordinary) == CONTENT_SURFACE
        generated = read_required(ordinary / AGENTS_REL)
        assert "content surface" in generated
        assert len([path for path in ordinary.rglob("*") if path.is_file()]) <= 20

    with tempfile.TemporaryDirectory(prefix="adco-activation-scoped-") as raw:
        existing = Path(raw)
        root_agents = existing / "AGENTS.md"
        root_agents.write_text("# Existing\n", encoding="utf-8")
        copy_content_template(template_root(), existing)
        assert root_agents.read_text(encoding="utf-8") == "# Existing\n"
        assert agents_policy_complete(existing)
        assert not (existing / "AD-creative/orchestrator/AGENTS.merge_suggestion.md").exists()

    with tempfile.TemporaryDirectory(prefix="adco-activation-full-") as raw:
        delivery = Path(raw)
        copy_template(template_root(), delivery)
        assert project_surface(delivery) == DELIVERY_SURFACE
        assert (delivery / "AD-creative/orchestrator/artifact_index.csv").is_file()
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
