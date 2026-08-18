#!/usr/bin/env python3
"""Verify packaged runtime assets mirror source templates and skill draft."""

from __future__ import annotations

import filecmp
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAIRS = [
    (ROOT / "templates/project", ROOT / "tools/adco_resources/templates/project"),
    (ROOT / "tools/fixtures", ROOT / "tools/adco_resources/fixtures"),
    (
        ROOT / "skill_drafts/ad-creative-orchestrator",
        ROOT / "tools/adco_resources/skill_drafts/ad-creative-orchestrator",
    ),
]
PUBLISHED_DOC_ROOT_PATHS = [
    Path("README.md"),
    Path("CHANGELOG.md"),
    Path("CONTRIBUTING.md"),
    Path("LICENSE"),
    Path("ROADMAP.md"),
    Path("SECURITY.md"),
]
PUBLISHED_DOCS_ROOT = ROOT / "tools/adco_resources/published_docs"
CHAT_NATIVE_SKILL_PATH = (
    ROOT / "skill_drafts/ad-creative-orchestrator/chat_interaction_and_visualization.md"
)
CHAT_NATIVE_RENDERER_PATH = (
    ROOT / "skill_drafts/ad-creative-orchestrator/scripts/adco_visualization.py"
)
CHAT_NATIVE_REGISTRY_PATH = (
    ROOT / "skill_drafts/ad-creative-orchestrator/assets/visualizations/surface-registry.json"
)
CHAT_NATIVE_REQUIRED_SNIPPETS = [
    "OpenAI Visualizations is a product capability",
    "actual Visualize capability",
    "adco.chat-visualization@1.0",
    "Data Analytics evidence",
    ".codex/visualizations",
    "USER_VISIBLE=UNVERIFIED",
    "window.openai.sendFollowUpMessage",
    "does not redesign the dashboard",
    "The frontstage is for the user",
]
CHAT_NATIVE_FORBIDDEN_SNIPPETS = [
    "adco interaction-view",
    "adco interaction-resolve",
    "adco.interaction-response",
    "build_interaction_projection",
    "native render_table",
    "native render_chart",
    "::codex-inline-vis",
]
SKILL_METADATA_REL = Path("agents/openai.yaml")
SKILL_METADATA_REQUIRED_SNIPPETS = [
    'display_name: "Ad Creative Orchestrator"',
    'default_prompt: "Use $ad-creative-orchestrator to reason from this project\'s real materials and produce the requested advertising outcome."',
    "allow_implicit_invocation: false",
]


def published_doc_paths() -> list[Path]:
    paths = list(PUBLISHED_DOC_ROOT_PATHS)
    for directory in [ROOT / "docs/operating", ROOT / "docs/assets"]:
        paths.extend(path.relative_to(ROOT) for path in directory.rglob("*") if path.is_file())
    return sorted(paths)


def compare_dirs(source: Path, packaged: Path) -> list[str]:
    issues: list[str] = []
    source_files = {
        path.relative_to(source): path
        for path in source.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    }
    packaged_files = {
        path.relative_to(packaged): path
        for path in packaged.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    }
    for rel_path in sorted(source_files.keys() - packaged_files.keys()):
        issues.append(f"missing packaged asset: {packaged / rel_path}")
    for rel_path in sorted(packaged_files.keys() - source_files.keys()):
        issues.append(f"extra packaged asset: {packaged / rel_path}")
    for rel_path in sorted(source_files.keys() & packaged_files.keys()):
        if not filecmp.cmp(source_files[rel_path], packaged_files[rel_path], shallow=False):
            issues.append(f"stale packaged asset: {packaged / rel_path}")
    return issues


def main() -> int:
    issues: list[str] = []
    for source, packaged in PAIRS:
        if not source.exists():
            issues.append(f"missing source assets: {source}")
            continue
        if not packaged.exists():
            issues.append(f"missing packaged assets: {packaged}")
            continue
        issues.extend(compare_dirs(source, packaged))
    expected_paths = published_doc_paths()
    expected_packaged_docs = {PUBLISHED_DOCS_ROOT / path for path in expected_paths}
    actual_packaged_docs = {
        path for path in PUBLISHED_DOCS_ROOT.rglob("*") if path.is_file()
    } if PUBLISHED_DOCS_ROOT.exists() else set()
    for rel_path in expected_paths:
        source = ROOT / rel_path
        packaged = PUBLISHED_DOCS_ROOT / rel_path
        if not source.exists():
            issues.append(f"missing published doc source: {source}")
        elif not packaged.exists():
            issues.append(f"missing packaged published doc: {packaged}")
        elif not filecmp.cmp(source, packaged, shallow=False):
            issues.append(f"stale packaged published doc: {packaged}")
    for path in sorted(actual_packaged_docs - expected_packaged_docs):
        issues.append(f"extra packaged published doc: {path}")
    if not CHAT_NATIVE_SKILL_PATH.exists():
        issues.append(f"missing chat-native skill reference: {CHAT_NATIVE_SKILL_PATH}")
    else:
        chat_native_text = CHAT_NATIVE_SKILL_PATH.read_text(encoding="utf-8")
        for snippet in CHAT_NATIVE_REQUIRED_SNIPPETS:
            if snippet not in chat_native_text:
                issues.append(f"chat-native skill missing required contract: {snippet}")
        for snippet in CHAT_NATIVE_FORBIDDEN_SNIPPETS:
            if snippet in chat_native_text:
                issues.append(f"chat-native skill contains rebuilt-UI contract: {snippet}")
    if not CHAT_NATIVE_RENDERER_PATH.exists():
        issues.append(f"missing chat-native renderer: {CHAT_NATIVE_RENDERER_PATH}")
    else:
        renderer_text = CHAT_NATIVE_RENDERER_PATH.read_text(encoding="utf-8")
        if "::codex-inline-vis" in renderer_text:
            issues.append("chat-native renderer emits an unverified inline-mount directive")
        if "USER_VISIBLE=UNVERIFIED" not in renderer_text:
            issues.append("chat-native renderer does not disclose unverified user visibility")
    if not CHAT_NATIVE_REGISTRY_PATH.exists():
        issues.append(f"missing chat-native surface registry: {CHAT_NATIVE_REGISTRY_PATH}")
    else:
        registry_text = CHAT_NATIVE_REGISTRY_PATH.read_text(encoding="utf-8")
        if "codex-inline-vis" in registry_text:
            issues.append("chat-native surface registry advertises a private inline renderer")
        if "native-openai-visualize-when-exposed" not in registry_text:
            issues.append("chat-native surface registry lacks native capability detection")
    for root_label, skill_root in [
        ("source", ROOT / "skill_drafts/ad-creative-orchestrator"),
        ("packaged", ROOT / "tools/adco_resources/skill_drafts/ad-creative-orchestrator"),
    ]:
        metadata_path = skill_root / SKILL_METADATA_REL
        if not metadata_path.is_file():
            issues.append(f"missing {root_label} skill invocation metadata: {metadata_path}")
            continue
        metadata_text = metadata_path.read_text(encoding="utf-8")
        for snippet in SKILL_METADATA_REQUIRED_SNIPPETS:
            if snippet not in metadata_text:
                issues.append(
                    f"{root_label} skill invocation metadata missing contract: {snippet}"
                )
    if issues:
        print("PACKAGED_ASSETS_CHECK=FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("PACKAGED_ASSETS_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
