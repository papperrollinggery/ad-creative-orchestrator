#!/usr/bin/env python3
"""Validate an Ad Creative Orchestrator project directory."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable


REQUIRED_FILES = [
    "AD-creative/orchestrator/source_events.csv",
    "AD-creative/orchestrator/current_truth.md",
    "AD-creative/orchestrator/requirements.csv",
    "AD-creative/orchestrator/gaps.csv",
    "AD-creative/orchestrator/work_items.csv",
    "AD-creative/orchestrator/agent_runs.csv",
    "AD-creative/orchestrator/artifact_index.csv",
    "AD-creative/orchestrator/gate_log.csv",
    "AD-creative/orchestrator/version_map.csv",
    "AD-creative/handoff/项目看板.md",
    "AD-creative/handoff/待你确认.md",
]


def split_ids(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def load_csv(path: Path, errors: list[str]) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                errors.append(f"empty csv: {path}")
                return []

            rows = []
            for index, row in enumerate(reader, 2):
                if None in row:
                    errors.append(
                        f"csv width mismatch: {path}:{index} has extra columns"
                    )
                    row.pop(None, None)
                missing = [key for key, value in row.items() if value is None]
                if missing:
                    errors.append(
                        f"csv width mismatch: {path}:{index} missing columns: {', '.join(missing)}"
                    )
                    for key in missing:
                        row[key] = ""
                rows.append(row)
    except FileNotFoundError:
        errors.append(f"missing csv: {path}")
        return []

    return rows


def check_structured_files(project: Path, errors: list[str]) -> None:
    for path in project.rglob("*"):
        if path.suffix == ".jsonl":
            with path.open(encoding="utf-8") as handle:
                for index, line in enumerate(handle, 1):
                    if not line.strip():
                        continue
                    try:
                        json.loads(line)
                    except json.JSONDecodeError as exc:
                        errors.append(f"jsonl parse error: {path}:{index}: {exc}")
        elif path.suffix == ".json":
            try:
                with path.open(encoding="utf-8") as handle:
                    json.load(handle)
            except json.JSONDecodeError as exc:
                errors.append(f"json parse error: {path}: {exc}")


def id_set(rows: Iterable[dict[str, str]], key: str) -> set[str]:
    return {row.get(key, "").strip() for row in rows if row.get(key, "").strip()}


def check_refs(
    errors: list[str],
    owner: str,
    raw_ids: str | None,
    valid_ids: set[str],
    target_name: str,
) -> None:
    for item_id in split_ids(raw_ids):
        if item_id not in valid_ids:
            errors.append(f"{owner} unknown {target_name} {item_id}")


def validate(project: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    project = project.resolve()
    ad_root = project / "AD-creative"

    for rel_path in REQUIRED_FILES:
        if not (project / rel_path).exists():
            errors.append(f"missing required file: {rel_path}")

    check_structured_files(project, errors)

    source_events = load_csv(ad_root / "orchestrator/source_events.csv", errors)
    requirements = load_csv(ad_root / "orchestrator/requirements.csv", errors)
    work_items = load_csv(ad_root / "orchestrator/work_items.csv", errors)
    agent_runs = load_csv(ad_root / "orchestrator/agent_runs.csv", errors)
    artifact_index = load_csv(ad_root / "orchestrator/artifact_index.csv", errors)
    gate_log = load_csv(ad_root / "orchestrator/gate_log.csv", errors)
    version_map = load_csv(ad_root / "orchestrator/version_map.csv", errors)
    reference_cards = load_csv(ad_root / "references/reference_cards.csv", errors)
    asset_manifest = load_csv(ad_root / "visual_assets/asset_manifest.csv", errors)

    source_ids = id_set(source_events, "source_event_id")
    req_ids = id_set(requirements, "requirement_id")
    work_ids = id_set(work_items, "work_id")
    artifact_ids = id_set(artifact_index, "artifact_id")
    gate_ids = id_set(gate_log, "gate_id")
    reference_ids = id_set(reference_cards, "reference_id")
    asset_ids = id_set(asset_manifest, "asset_id")

    for req in requirements:
        req_id = req.get("requirement_id", "")
        source_id = req.get("source_event_id", "").strip()
        if source_id and source_id not in source_ids:
            errors.append(f"requirement {req_id} unknown source_event {source_id}")
        check_refs(errors, f"requirement {req_id}", req.get("linked_artifacts"), artifact_ids, "artifact")

    for work in work_items:
        work_id = work.get("work_id", "")
        check_refs(errors, f"work {work_id}", work.get("linked_requirements"), req_ids, "requirement")
        check_refs(errors, f"work {work_id}", work.get("output_artifacts"), artifact_ids, "artifact")
        check_refs(errors, f"work {work_id}", work.get("linked_source_events"), source_ids, "source_event")
        check_refs(errors, f"work {work_id}", work.get("linked_references"), reference_ids, "reference")
        check_refs(errors, f"work {work_id}", work.get("linked_assets"), asset_ids, "asset")
        blocked_by = work.get("blocked_by", "").strip()
        if blocked_by and blocked_by not in work_ids:
            errors.append(f"work {work_id} unknown blocked_by {blocked_by}")

    for artifact in artifact_index:
        artifact_id = artifact.get("artifact_id", "")
        rel_path = artifact.get("path", "").strip()
        if rel_path and not (project / rel_path).exists():
            errors.append(f"artifact {artifact_id} missing path {rel_path}")
        check_refs(errors, f"artifact {artifact_id}", artifact.get("linked_work_items"), work_ids, "work")
        check_refs(errors, f"artifact {artifact_id}", artifact.get("linked_requirements"), req_ids, "requirement")
        check_refs(errors, f"artifact {artifact_id}", artifact.get("source_event_ids"), source_ids, "source_event")
        check_refs(errors, f"artifact {artifact_id}", artifact.get("linked_references"), reference_ids, "reference")
        check_refs(errors, f"artifact {artifact_id}", artifact.get("linked_assets"), asset_ids, "asset")

    for run in agent_runs:
        run_id = run.get("run_id", "")
        work_id = run.get("work_id", "").strip()
        if work_id and work_id not in work_ids:
            errors.append(f"agent_run {run_id} unknown work {work_id}")
        gate_id = run.get("gate_id", "").strip()
        if gate_id and gate_id not in gate_ids:
            errors.append(f"agent_run {run_id} unknown gate {gate_id}")

    for gate in gate_log:
        gate_id = gate.get("gate_id", "")
        check_refs(errors, f"gate {gate_id}", gate.get("checked_artifacts"), artifact_ids, "artifact")

    for version in version_map:
        artifact_id = version.get("artifact_id", "").strip()
        if artifact_id and artifact_id not in artifact_ids:
            errors.append(f"version {version.get('version_id')} unknown artifact {artifact_id}")

    for reference in reference_cards:
        ref_id = reference.get("reference_id", "")
        source_id = reference.get("source_event_id", "").strip()
        if source_id and source_id not in source_ids:
            errors.append(f"reference {ref_id} unknown source_event {source_id}")
        url = reference.get("url", "").strip()
        if url and url != "TBD" and not url.startswith("https://"):
            errors.append(f"reference {ref_id} non-https url {url}")

    for asset in asset_manifest:
        asset_id = asset.get("asset_id", "")
        req_id = asset.get("requirement_id", "").strip()
        if req_id and req_id not in req_ids:
            errors.append(f"asset {asset_id} unknown requirement {req_id}")
        ref_id = asset.get("reference_id", "").strip()
        if ref_id and ref_id != "pending" and ref_id not in reference_ids:
            errors.append(f"asset {asset_id} unknown reference {ref_id}")
        rel_path = asset.get("path", "").strip()
        status = asset.get("status", "").strip().lower()
        qa_status = asset.get("qa_status", "").strip().upper()
        must_exist = status in {"registered", "selected", "approved", "done"} and qa_status != "NOT_RUN"
        if rel_path and must_exist and not (project / rel_path).exists():
            errors.append(f"asset {asset_id} missing path {rel_path}")

    stats = {
        "source_events": len(source_events),
        "requirements": len(requirements),
        "work_items": len(work_items),
        "agent_runs": len(agent_runs),
        "artifacts": len(artifact_index),
        "gates": len(gate_log),
        "versions": len(version_map),
        "references": len(reference_cards),
        "assets": len(asset_manifest),
        "errors": len(errors),
    }
    return errors, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", help="Project root containing AD-creative/")
    args = parser.parse_args()

    errors, stats = validate(Path(args.project))
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
