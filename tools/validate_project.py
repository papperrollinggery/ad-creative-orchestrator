#!/usr/bin/env python3
"""Validate an Ad Creative Orchestrator project directory."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Iterable


CLIENT_DELIVERY_VISIBILITIES = {"client_visible", "client_visible_ready", "sent"}
PASS_GATE_VALUES = {"pass", "passed"}
CLIENT_DELIVERY_REQUIRED_TYPES = {
    "current_pptx_artifact_id": {"pptx"},
    "current_pdf_artifact_id": {"pdf"},
    "current_preview_artifact_id": {"preview", "deck_preview", "png_preview", "jpg_preview"},
    "current_text_extract_artifact_id": {"text_extract", "ppt_text_extract"},
    "current_ppt_editability_artifact_id": {"ppt_editability_check"},
}
FEEDBACK_CLOSED_STATUSES = {"applied", "resolved", "closed", "deferred", "not_applicable"}
THREAD_REGISTRY_REQUIRED_FIELDS = [
    "thread_id",
    "title",
    "role",
    "lane_id",
    "work_id",
    "lifecycle_state",
    "pinned",
    "archived",
    "created_at",
    "updated_at",
    "cleanup_action",
    "notes",
]
THREADOPS_REGISTRY_FIELDS = [
    *THREAD_REGISTRY_REQUIRED_FIELDS,
    "goal_id",
    "mode",
    "environment",
    "workspace_path",
    "write_scope",
    "professional_identity",
    "receipt_path",
    "receipt_status",
    "reconciliation_status",
    "assigned_at",
    "returned_at",
    "reconciled_at",
    "archived_at",
    "cleanup_reason",
    "last_seen_at",
    "duplicate_of",
]
THREADOPS_EXECUTION_MODE = "execution_worker"
THREADOPS_EXECUTION_MODES = {THREADOPS_EXECUTION_MODE, "isolated_worktree_execution_worker"}
THREADOPS_READ_ONLY_MODES = {"research", "read_only_review", "cold_review"}
THREADOPS_RECEIPT_ONLY_SCOPES = {"", "receipt only", "receipt_only", "none", "not_applicable"}
THREADOPS_PENDING_RECEIPT_STATUSES = {"", "missing", "pending", "planned", "todo", "tbd"}
THREADOPS_RECEIVED_RECEIPT_STATUSES = {
    "received",
    "returned",
    "complete",
    "completed",
    "reconciled",
}
THREADOPS_RECEIPT_REQUIRED_PROOF = {
    "files_changed": ("Files Changed",),
    "validation_result": ("Validation Result",),
    "dirty_state_impact": ("Dirty-State Impact",),
    "adoption_decision": ("Adoption / Rejection Recommendation",),
    "loop_state": (),
    "cleanup_actions": ("Cleanup Actions",),
    "evidence_refs": ("Evidence",),
}
THREADOPS_HELPER_MODE = "stateless_secondary_helper"
THREADOPS_HELPER_NONE_MODES = {"", "none", "no", "false", "n/a", "na", "not_applicable"}
THREADOPS_HELPER_ALLOWED_MODES = {*THREADOPS_HELPER_NONE_MODES, THREADOPS_HELPER_MODE}
THREADOPS_HELPER_REQUIRED_PROOF = {
    "helper_invocations": (),
    "helper_input_refs": (),
    "helper_output_refs": (),
    "helper_artifacts": (),
    "helper_validation_result": (),
    "helper_adopted_by_worker": (),
    "worker_synthesis": ("Worker Synthesis",),
}
THREADOPS_HELPER_REQUIRED_RECORDED_FIELDS = {
    "helper_failure_reason",
}
THREADOPS_HELPER_THREAD_SCAN_KEYS = (
    "helper_invocations",
    "helper_input_refs",
    "helper_output_refs",
    "helper_artifacts",
    "helper_validation_result",
    "helper_adopted_by_worker",
    "helper_failure_reason",
    "worker_synthesis",
)
THREADOPS_HELPER_THREAD_CLAIM_PATTERN = re.compile(
    r"\b(?:helper[_ -]?)?thread[_ -]?id\s*[:=]\s*"
    r"(?!(?:none|no|false|n/a|na|not[_ -]?applicable)\b)\S+",
    re.IGNORECASE,
)
THREADOPS_ADOPTING_DECISIONS = {"ADOPT", "PARTIAL_ADOPT"}
THREADOPS_NO_FILE_OUTPUT_VALUES = {
    "no files changed",
    "no file changed",
    "no file changes",
    "no output",
    "no file output",
    "no files",
    "none",
    "n/a",
    "na",
    "not_applicable",
    "nothing changed",
}
THREADOPS_NO_FILE_OUTPUT_FRAGMENTS = (
    "no files changed",
    "no file changed",
    "no file changes",
    "no files were changed",
    "no output files",
    "no file output",
    "nothing changed",
    "did not change files",
)
THREADOPS_RECEIPT_PLACEHOLDER_VALUES = {
    "",
    "pending",
    "missing",
    "planned",
    "todo",
    "tbd",
    "n/a",
    "na",
    "not_applicable",
    "required",
    "placeholder",
    "template",
    "none",
    "not run",
    "not_run",
}
THREADOPS_RECEIPT_PLACEHOLDER_FRAGMENTS = (
    "required_non_empty_for_adopt",
    "pending_if_not_adopted",
    "pending_main_control",
    "pending main/control",
    "forbidden_for_read_only",
    "confirm no files changed",
    "prompt_only_output: invalid",
    "prompt-only output is invalid",
)
THREADOPS_ADOPTION_DECISIONS = {"ADOPT", "PARTIAL_ADOPT", "REJECT", "BLOCKED"}
THREADOPS_RECEIVED_LOOP_STATES = {
    "returned",
    "reconciled",
    "blocked",
    "replay_requested",
    "frozen",
    "archived",
    "complete",
    "completed",
}
THREADOPS_AGENT_RUN_FIELDS = [
    "run_id",
    "work_id",
    "agent_role",
    "status",
    "started_at",
    "completed_at",
    "input_files",
    "output_files",
    "gate_id",
    "summary",
    "next_action",
    "thread_id",
    "lane_id",
    "receipt_path",
    "proof_status",
    "reconciliation_status",
]
PROFILE_SUBJECT_FIELDS = [
    "subject_id",
    "subject_type",
    "name",
    "role_or_title",
    "organization",
    "source_event_ids",
    "first_seen_at",
    "last_seen_at",
    "profile_status",
    "influence_level",
    "decision_power",
    "traits",
    "needs",
    "preferences",
    "concerns",
    "notes",
]
PROFILE_VOICE_FIELDS = [
    "voice_id",
    "source_event_id",
    "file_path",
    "speaker",
    "utterance",
    "need_signal",
    "preference_signal",
    "concern_signal",
    "decision_signal",
    "influence_level",
    "decision_power",
    "evidence_quote",
    "confidence",
    "status",
]
PROFILE_INSIGHT_FIELDS = [
    "insight_id",
    "subject_id",
    "subject_type",
    "source_event_id",
    "file_path",
    "insight_type",
    "statement",
    "evidence_quote",
    "confidence",
    "status",
    "priority",
    "linked_requirement_ids",
    "supersedes_insight_id",
    "created_at",
    "updated_at",
]
PROFILE_CONFLICT_FIELDS = [
    "conflict_id",
    "topic",
    "source_event_ids",
    "subject_ids",
    "conflict_summary",
    "recommended_resolution",
    "status",
    "confidence",
    "evidence_quotes",
    "created_at",
    "updated_at",
]
PROFILE_STATUS_VALUES = {"candidate", "confirmed", "conflicted", "deprecated"}
PROFILE_SUBJECT_TYPES = {"participant", "brand", "company", "client_group"}
PROFILE_DECISION_LEVELS = {"high", "medium", "low", "unknown", ""}

AGENTS_REQUIRED_SNIPPETS = [
    "ad-creative-orchestrator",
    "AD-creative/orchestrator/",
    "AD-creative/handoff/",
    "current_truth.md",
    "version_map.csv",
    "artifact_index.csv",
    "requirements.csv",
    "gaps.csv",
    "gate_log.csv",
    "internal comments",
    "prompts",
    "thread names",
    "worker names",
    "lane plans",
    "fake logos",
    "fake packaging copy",
    "imagegen",
    "untraceable references",
    "unapproved AI images",
    "archive",
    "version_archive",
    "VALIDATION=PASS",
    "does not mean creative quality",
    "human confirmation",
    "real search",
    "final send",
    "dircreative",
    "specialist film workflow",
    "adco validate",
    "stage gates",
    "search-quality-gate",
    "reference-pack-gate",
    "creative-quality-gate",
    "visual-quality-gate",
    "client-pack-gate",
    "handoff-readiness-gate",
    "Codex Threads",
    "main thread",
    "write scope",
    "worker receipts",
    "clean up",
    "thread_cleanup",
]


REQUIRED_FILES = [
    "AGENTS.md",
    "AD-creative/orchestrator/source_events.csv",
    "AD-creative/orchestrator/current_truth.md",
    "AD-creative/orchestrator/requirements.csv",
    "AD-creative/orchestrator/gaps.csv",
    "AD-creative/orchestrator/work_items.csv",
    "AD-creative/orchestrator/agent_runs.csv",
    "AD-creative/orchestrator/artifact_index.csv",
    "AD-creative/orchestrator/gate_log.csv",
    "AD-creative/orchestrator/version_map.csv",
    "AD-creative/orchestrator/thread_registry.csv",
    "AD-creative/feedback/feedback_map.csv",
    "AD-creative/feedback/affected_artifacts.md",
    "AD-creative/feedback/next_version_plan.md",
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


def csv_fieldnames(path: Path) -> list[str]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            return list(reader.fieldnames or [])
    except FileNotFoundError:
        return []


def load_optional_csv(path: Path, errors: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return load_csv(path, errors)


def check_required_columns(errors: list[str], label: str, path: Path, required: list[str]) -> None:
    fields = csv_fieldnames(path)
    missing = [field for field in required if field not in fields]
    if missing:
        errors.append(f"{label} missing columns: " + ", ".join(missing))


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


def check_agents_policy(project: Path, errors: list[str]) -> bool:
    path = project / "AGENTS.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    normalized = text.lower()
    missing = [
        snippet
        for snippet in AGENTS_REQUIRED_SNIPPETS
        if snippet.lower() not in normalized
    ]
    if missing:
        errors.append(
            "AGENTS.md missing required policy snippets: " + ", ".join(missing)
        )
    return not missing


def parse_markdown_table_after_heading(text: str, heading: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != heading:
            continue
        table_lines: list[str] = []
        for candidate in lines[index + 1 :]:
            stripped = candidate.strip()
            if not stripped:
                if table_lines:
                    break
                continue
            if stripped.startswith("|"):
                table_lines.append(stripped)
            elif table_lines:
                break
        if len(table_lines) < 2:
            return []
        headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
        rows: list[dict[str, str]] = []
        for raw_row in table_lines[2:]:
            values = [cell.strip() for cell in raw_row.strip("|").split("|")]
            values.extend([""] * max(0, len(headers) - len(values)))
            rows.append(dict(zip(headers, values)))
        return rows
    return []


def check_threadops_lane_contract(errors: list[str], owner: str, row: dict[str, str]) -> None:
    mode = row.get("mode", "").strip()
    environment = row.get("environment", "").strip()
    write_scope = row.get("write_scope", "").strip()
    normalized_scope = write_scope.lower().replace("-", "_")
    if mode in THREADOPS_EXECUTION_MODES:
        if environment == "read_only":
            errors.append(f"{owner} execution worker uses read_only environment")
        if normalized_scope in THREADOPS_RECEIPT_ONLY_SCOPES:
            errors.append(f"{owner} execution worker missing exact write_scope")
    elif mode in THREADOPS_READ_ONLY_MODES:
        if environment != "read_only":
            errors.append(f"{owner} read-only lane uses non-read_only environment {environment}")
        if normalized_scope not in THREADOPS_RECEIPT_ONLY_SCOPES:
            errors.append(f"{owner} read-only lane has writable write_scope {write_scope}")


def normalize_threadops_status(value: str | None) -> str:
    return (value or "").strip().lower().replace("-", "_").replace(" ", "_")


def threadops_receipt_is_received(row: dict[str, str]) -> bool:
    receipt_status = normalize_threadops_status(row.get("receipt_status"))
    reconciliation_status = normalize_threadops_status(row.get("reconciliation_status"))
    lifecycle_state = normalize_threadops_status(row.get("lifecycle_state"))
    if receipt_status and receipt_status not in THREADOPS_PENDING_RECEIPT_STATUSES:
        return True
    if reconciliation_status and reconciliation_status not in THREADOPS_PENDING_RECEIPT_STATUSES:
        return True
    if lifecycle_state in THREADOPS_RECEIVED_RECEIPT_STATUSES:
        return True
    return bool(row.get("returned_at", "").strip() or row.get("reconciled_at", "").strip())


def markdown_section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?ims)^##[ \t]+{re.escape(heading)}[ \t]*\n(.*?)(?=^##[ \t]+|\Z)"
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def key_value_blocks(text: str, key: str) -> list[str]:
    lines = text.splitlines()
    blocks: list[str] = []
    key_pattern = re.compile(rf"^\s*(?:[-*]\s*)?{re.escape(key)}\s*:\s*(.*)$", re.IGNORECASE)
    next_key_pattern = re.compile(r"^\s*(?:[-*]\s*)?[a-z][a-z0-9_ /-]{1,80}\s*:", re.IGNORECASE)
    for index, line in enumerate(lines):
        match = key_pattern.match(line)
        if not match:
            continue
        block = [match.group(1).strip()]
        for candidate in lines[index + 1 :]:
            stripped = candidate.strip()
            if stripped.startswith("#"):
                break
            if not stripped:
                if any(item.strip() for item in block):
                    break
                continue
            if next_key_pattern.match(stripped):
                break
            block.append(stripped)
        blocks.append("\n".join(item for item in block if item.strip()))
    return blocks


def receipt_proof_values(text: str, key: str, headings: tuple[str, ...]) -> list[str]:
    values = key_value_blocks(text, key)
    values.extend(section for heading in headings if (section := markdown_section(text, heading)))
    return values


def normalized_receipt_lines(value: str) -> list[str]:
    lines: list[str] = []
    for raw_line in value.splitlines():
        stripped = re.sub(r"^[ \t>*-]+", "", raw_line.strip())
        stripped = stripped.strip("` ")
        if stripped:
            lines.append(stripped)
    return lines


def receipt_line_is_concrete(line: str) -> bool:
    normalized = line.strip().lower().strip(".:;- ")
    if normalized in THREADOPS_RECEIPT_PLACEHOLDER_VALUES:
        return False
    return not any(fragment in normalized for fragment in THREADOPS_RECEIPT_PLACEHOLDER_FRAGMENTS)


def receipt_value_is_concrete(key: str, value: str) -> bool:
    lines = normalized_receipt_lines(value)
    if key == "adoption_decision":
        return any(
            re.search(rf"(?:^|[^A-Z0-9_]){re.escape(decision)}(?:$|[^A-Z0-9_])", line.upper())
            for decision in THREADOPS_ADOPTION_DECISIONS
            for line in lines
        )
    if key == "loop_state":
        return any(
            re.search(rf"\b{re.escape(state)}\b", line.lower())
            for state in THREADOPS_RECEIVED_LOOP_STATES
            for line in lines
        )
    return any(receipt_line_is_concrete(line) for line in lines)


def receipt_value_is_recorded(value: str) -> bool:
    return any(line.strip() for line in normalized_receipt_lines(value))


def receipt_has_adopting_decision(text: str) -> bool:
    values = receipt_proof_values(
        text,
        "adoption_decision",
        THREADOPS_RECEIPT_REQUIRED_PROOF["adoption_decision"],
    )
    return any(
        re.search(rf"(?:^|[^A-Z0-9_]){re.escape(decision)}(?:$|[^A-Z0-9_])", line.upper())
        for value in values
        for line in normalized_receipt_lines(value)
        for decision in THREADOPS_ADOPTING_DECISIONS
    )


def receipt_files_changed_means_no_output(text: str) -> bool:
    values = receipt_proof_values(
        text,
        "files_changed",
        THREADOPS_RECEIPT_REQUIRED_PROOF["files_changed"],
    )
    for value in values:
        for line in normalized_receipt_lines(value):
            normalized = line.strip().lower().strip(".:;- ")
            if normalized in THREADOPS_NO_FILE_OUTPUT_VALUES:
                return True
            if any(fragment in normalized for fragment in THREADOPS_NO_FILE_OUTPUT_FRAGMENTS):
                return True
    return False


def normalize_helper_mode(line: str) -> str:
    normalized = line.strip().lower().strip(".:;- ")
    normalized = normalized.replace("-", "_").replace(" ", "_")
    if THREADOPS_HELPER_MODE in normalized:
        return THREADOPS_HELPER_MODE
    if normalized in THREADOPS_HELPER_NONE_MODES:
        return "none"
    return normalized


def receipt_helper_modes(text: str) -> list[str]:
    modes: list[str] = []
    for value in receipt_proof_values(text, "helper_mode", ()):
        for line in normalized_receipt_lines(value):
            mode = normalize_helper_mode(line)
            if mode:
                modes.append(mode)
    return modes or ["none"]


def receipt_has_helper_thread_claim(text: str) -> bool:
    values: list[str] = []
    for key in THREADOPS_HELPER_THREAD_SCAN_KEYS:
        values.extend(receipt_proof_values(text, key, ()))
    values.append(markdown_section(text, "Helper Invocation Evidence"))
    for value in values:
        for line in normalized_receipt_lines(value):
            if THREADOPS_HELPER_THREAD_CLAIM_PATTERN.search(line):
                return True
    return False


def check_threadops_helper_receipt(errors: list[str], owner: str, text: str) -> None:
    modes = receipt_helper_modes(text)
    unknown_modes = sorted({mode for mode in modes if mode not in THREADOPS_HELPER_ALLOWED_MODES})
    if unknown_modes:
        errors.append(f"{owner} received execution worker receipt has unknown helper_mode: {', '.join(unknown_modes)}")
    if THREADOPS_HELPER_MODE not in modes:
        return

    missing: list[str] = []
    for key, headings in THREADOPS_HELPER_REQUIRED_PROOF.items():
        values = receipt_proof_values(text, key, headings)
        if not any(receipt_value_is_concrete(key, value) for value in values):
            missing.append(key)
    if missing:
        errors.append(
            f"{owner} received execution worker receipt lacks concrete helper evidence fields: "
            + ", ".join(missing)
        )
    missing_recorded: list[str] = []
    for key in THREADOPS_HELPER_REQUIRED_RECORDED_FIELDS:
        values = receipt_proof_values(text, key, ())
        if not any(receipt_value_is_recorded(value) for value in values):
            missing_recorded.append(key)
    if missing_recorded:
        errors.append(
            f"{owner} received execution worker receipt lacks recorded helper receipt fields: "
            + ", ".join(missing_recorded)
        )
    if receipt_has_helper_thread_claim(text):
        errors.append(f"{owner} helper invocation claims thread_id; stateless helpers are not Codex Threads")


def check_threadops_execution_receipt(
    project: Path,
    errors: list[str],
    owner: str,
    row: dict[str, str],
) -> None:
    if row.get("mode", "").strip() not in THREADOPS_EXECUTION_MODES:
        return
    if not threadops_receipt_is_received(row):
        return

    rel_path = row.get("receipt_path", "").strip()
    if not rel_path:
        errors.append(f"{owner} received execution worker missing receipt_path")
        return
    receipt_path = Path(rel_path)
    if not receipt_path.is_absolute():
        receipt_path = project / rel_path
    try:
        text = receipt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"{owner} received execution worker missing receipt file {rel_path}")
        return

    missing: list[str] = []
    for key, headings in THREADOPS_RECEIPT_REQUIRED_PROOF.items():
        values = receipt_proof_values(text, key, headings)
        if not any(receipt_value_is_concrete(key, value) for value in values):
            missing.append(key)
    if missing:
        errors.append(
            f"{owner} received execution worker receipt lacks concrete proof fields: "
            + ", ".join(missing)
        )
    if receipt_has_adopting_decision(text) and receipt_files_changed_means_no_output(text):
        errors.append(
            f"{owner} received execution worker receipt adopts without file output: files_changed"
        )
    check_threadops_helper_receipt(errors, owner, text)


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


def artifact_rows_by_type(
    artifacts: list[dict[str, str]], type_names: set[str]
) -> list[dict[str, str]]:
    return [
        row
        for row in artifacts
        if row.get("artifact_type", "").strip().lower() in type_names
    ]


def row_has_pass_gate(row: dict[str, str]) -> bool:
    return row.get("gate_status", "").strip().lower() in PASS_GATE_VALUES


def current_truth_value(text: str, key: str) -> str:
    pattern = re.compile(rf"^[ \t]*{re.escape(key)}[ \t]*:[ \t]*(.*?)[ \t]*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    value = match.group(1).strip()
    return "" if value in {"TBD", "todo", "pending"} else value


def has_client_delivery_artifact(artifacts: list[dict[str, str]]) -> bool:
    return any(
        row.get("visibility", "").strip().lower() in CLIENT_DELIVERY_VISIBILITIES
        for row in artifacts
    )


def row_by_id(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    for row in rows:
        if row.get(key, "").strip() == value:
            return row
    return None


def validate_client_delivery_readiness(
    project: Path,
    artifacts: list[dict[str, str]],
    version_map: list[dict[str, str]],
    feedback_rows: list[dict[str, str]],
) -> list[str]:
    """Validate facts required before a package can be called client-deliverable."""
    errors: list[str] = []

    current_truth = project / "AD-creative/orchestrator/current_truth.md"
    try:
        current_truth_text = current_truth.read_text(encoding="utf-8")
    except FileNotFoundError:
        current_truth_text = ""

    for key in [
        "current_version_id",
        "current_pptx_artifact_id",
        "current_pdf_artifact_id",
        "current_preview_artifact_id",
        "current_text_extract_artifact_id",
        "current_ppt_editability_artifact_id",
        "version_map_status",
    ]:
        if not current_truth_value(current_truth_text, key):
            errors.append(f"client delivery missing current_truth field {key}")

    current_version_id = current_truth_value(current_truth_text, "current_version_id")
    active_versions = [
        row
        for row in version_map
        if row.get("status", "").strip().lower() in {"active", "current"}
    ]
    if not active_versions:
        errors.append("client delivery has no active/current version_map row")
    current_version = row_by_id(active_versions, "version_id", current_version_id)
    if current_version_id and not current_version:
        errors.append(
            f"client delivery current_version_id {current_version_id} does not match an active/current version_map row"
        )
    if len(active_versions) > 1:
        errors.append("client delivery has multiple active/current version_map rows")

    current_artifact_ids: set[str] = set()
    current_version_label = (current_version or {}).get("version", "").strip()
    for current_key, type_names in CLIENT_DELIVERY_REQUIRED_TYPES.items():
        artifact_id = current_truth_value(current_truth_text, current_key)
        if not artifact_id:
            continue
        current_artifact_ids.add(artifact_id)
        artifact = row_by_id(artifacts, "artifact_id", artifact_id)
        if not artifact:
            errors.append(f"client delivery {current_key} unknown artifact {artifact_id}")
            continue
        artifact_type = artifact.get("artifact_type", "").strip().lower()
        if artifact_type not in type_names:
            errors.append(
                f"client delivery {current_key} {artifact_id} has wrong type {artifact_type}"
            )
        if not row_has_pass_gate(artifact):
            errors.append(f"client delivery {current_key} {artifact_id} gate is not PASS")
        rel_path = artifact.get("path", "").strip()
        if not rel_path:
            errors.append(f"client delivery artifact {artifact_id} missing path")
        elif not (project / rel_path).exists():
            errors.append(f"client delivery artifact {artifact_id} missing path {rel_path}")
        if not artifact.get("version", "").strip():
            errors.append(f"client delivery artifact {artifact_id} missing version")
        elif current_version_label and artifact.get("version", "").strip() != current_version_label:
            errors.append(
                f"client delivery artifact {artifact_id} version {artifact.get('version')} does not match current version {current_version_label}"
            )

    if current_version:
        version_artifact_id = current_version.get("artifact_id", "").strip()
        if not current_version.get("version", "").strip():
            errors.append("client delivery current version_map row missing version")
        if not version_artifact_id:
            errors.append("client delivery current version_map row missing artifact_id")
        elif version_artifact_id not in current_artifact_ids:
            errors.append(
                f"client delivery version_map artifact {version_artifact_id} is not one of the current package artifacts"
            )
        if current_version.get("status", "").strip().lower() != current_truth_value(current_truth_text, "version_map_status").lower():
            errors.append("client delivery current_truth version_map_status does not match version_map status")

    open_feedback = [
        row.get("feedback_id", "")
        for row in feedback_rows
        if row.get("status", "").strip().lower() not in FEEDBACK_CLOSED_STATUSES
    ]
    if open_feedback:
        errors.append(
            "client delivery has unresolved feedback rows: "
            + ";".join(item for item in open_feedback if item)
        )
    deferred_without_owner = [
        row.get("feedback_id", "")
        for row in feedback_rows
        if row.get("status", "").strip().lower() == "deferred"
        and not (row.get("deferred_owner", "").strip() and row.get("deferred_tracking_path", "").strip())
    ]
    if deferred_without_owner:
        errors.append(
            "client delivery has deferred feedback without owner/tracking path: "
            + ";".join(item for item in deferred_without_owner if item)
        )

    for rel_path in [
        "AD-creative/feedback/feedback_map.csv",
        "AD-creative/feedback/affected_artifacts.md",
        "AD-creative/feedback/next_version_plan.md",
    ]:
        if not (project / rel_path).exists():
            errors.append(f"client delivery missing feedback closure file: {rel_path}")

    return errors


def validate(project: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    project = project.resolve()
    ad_root = project / "AD-creative"

    for rel_path in REQUIRED_FILES:
        if not (project / rel_path).exists():
            errors.append(f"missing required file: {rel_path}")

    agents_policy_ok = check_agents_policy(project, errors)
    check_structured_files(project, errors)

    source_events = load_csv(ad_root / "orchestrator/source_events.csv", errors)
    requirements = load_csv(ad_root / "orchestrator/requirements.csv", errors)
    work_items = load_csv(ad_root / "orchestrator/work_items.csv", errors)
    agent_runs = load_csv(ad_root / "orchestrator/agent_runs.csv", errors)
    artifact_index = load_csv(ad_root / "orchestrator/artifact_index.csv", errors)
    gate_log = load_csv(ad_root / "orchestrator/gate_log.csv", errors)
    version_map = load_csv(ad_root / "orchestrator/version_map.csv", errors)
    thread_registry_fields = load_csv(
        ad_root / "orchestrator/thread_registry.csv", errors
    )
    reference_cards = load_csv(ad_root / "references/reference_cards.csv", errors)
    asset_manifest = load_csv(ad_root / "visual_assets/asset_manifest.csv", errors)
    feedback_rows = load_csv(ad_root / "feedback/feedback_map.csv", errors)
    profile_root = ad_root / "orchestrator/profile_knowledge"
    profile_enabled = profile_root.exists()
    profile_subjects = load_optional_csv(profile_root / "profile_subjects.csv", errors)
    profile_voices = load_optional_csv(profile_root / "meeting_voice_map.csv", errors)
    profile_insights = load_optional_csv(profile_root / "profile_insights.csv", errors)
    profile_conflicts = load_optional_csv(profile_root / "profile_conflicts.csv", errors)

    source_ids = id_set(source_events, "source_event_id")
    req_ids = id_set(requirements, "requirement_id")
    work_ids = id_set(work_items, "work_id")
    artifact_ids = id_set(artifact_index, "artifact_id")
    gate_ids = id_set(gate_log, "gate_id")
    reference_ids = id_set(reference_cards, "reference_id")
    asset_ids = id_set(asset_manifest, "asset_id")
    profile_subject_ids = id_set(profile_subjects, "subject_id")

    registry_path = ad_root / "orchestrator/thread_registry.csv"
    try:
        with registry_path.open(newline="", encoding="utf-8") as handle:
            registry_reader = csv.DictReader(handle)
            registry_fields = list(registry_reader.fieldnames or [])
    except FileNotFoundError:
        registry_fields = []
    missing_registry_fields = [
        field for field in THREAD_REGISTRY_REQUIRED_FIELDS if field not in registry_fields
    ]
    if missing_registry_fields:
        errors.append(
            "thread_registry missing columns: " + ", ".join(missing_registry_fields)
        )
    agent_runs_path = ad_root / "orchestrator/agent_runs.csv"
    try:
        with agent_runs_path.open(newline="", encoding="utf-8") as handle:
            agent_runs_reader = csv.DictReader(handle)
            agent_runs_fields = list(agent_runs_reader.fieldnames or [])
    except FileNotFoundError:
        agent_runs_fields = []

    threadops_enabled = bool(thread_registry_fields) or (
        ad_root / "orchestrator/thread_lane_plan.md"
    ).exists()
    if threadops_enabled:
        missing_threadops_registry_fields = [
            field for field in THREADOPS_REGISTRY_FIELDS if field not in registry_fields
        ]
        if missing_threadops_registry_fields:
            errors.append(
                "thread_registry missing ThreadOps columns: "
                + ", ".join(missing_threadops_registry_fields)
            )
        missing_threadops_agent_fields = [
            field for field in THREADOPS_AGENT_RUN_FIELDS if field not in agent_runs_fields
        ]
        if missing_threadops_agent_fields:
            errors.append(
                "agent_runs missing ThreadOps columns: "
                + ", ".join(missing_threadops_agent_fields)
            )
        for row in thread_registry_fields:
            owner = f"thread_registry {row.get('thread_id', '').strip() or '<missing thread_id>'}"
            check_threadops_lane_contract(errors, owner, row)
            check_threadops_execution_receipt(project, errors, owner, row)
        lane_plan_path = ad_root / "orchestrator/thread_lane_plan.md"
        if lane_plan_path.exists():
            lane_rows = parse_markdown_table_after_heading(
                lane_plan_path.read_text(encoding="utf-8"),
                "## Lane Map",
            )
            for row in lane_rows:
                owner = f"thread_lane_plan {row.get('lane_id', '').strip() or '<missing lane_id>'}"
                check_threadops_lane_contract(errors, owner, row)

    if profile_enabled:
        profile_files = {
            "profile_subjects": (profile_root / "profile_subjects.csv", PROFILE_SUBJECT_FIELDS),
            "meeting_voice_map": (profile_root / "meeting_voice_map.csv", PROFILE_VOICE_FIELDS),
            "profile_insights": (profile_root / "profile_insights.csv", PROFILE_INSIGHT_FIELDS),
            "profile_conflicts": (profile_root / "profile_conflicts.csv", PROFILE_CONFLICT_FIELDS),
        }
        for label, (path, required_fields) in profile_files.items():
            if not path.exists():
                errors.append(f"missing profile knowledge file: {path.relative_to(project)}")
            else:
                check_required_columns(errors, label, path, required_fields)
        if not (profile_root / "profile_current_truth.md").exists():
            errors.append("missing profile knowledge file: AD-creative/orchestrator/profile_knowledge/profile_current_truth.md")

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
        check_refs(errors, f"artifact {artifact_id}", artifact.get("supersedes_artifact_id"), artifact_ids, "artifact")

    for run in agent_runs:
        run_id = run.get("run_id", "")
        work_id = run.get("work_id", "").strip()
        if work_id and work_id not in work_ids:
            errors.append(f"agent_run {run_id} unknown work {work_id}")
        gate_id = run.get("gate_id", "").strip()
        if gate_id and gate_id not in gate_ids:
            errors.append(f"agent_run {run_id} unknown gate {gate_id}")

    for subject in profile_subjects:
        subject_id = subject.get("subject_id", "")
        subject_type = subject.get("subject_type", "").strip()
        if subject_type and subject_type not in PROFILE_SUBJECT_TYPES:
            errors.append(f"profile_subject {subject_id} invalid subject_type {subject_type}")
        status = subject.get("profile_status", "").strip()
        if status and status not in PROFILE_STATUS_VALUES:
            errors.append(f"profile_subject {subject_id} invalid profile_status {status}")
        for level_key in ["influence_level", "decision_power"]:
            level = subject.get(level_key, "").strip()
            if level not in PROFILE_DECISION_LEVELS:
                errors.append(f"profile_subject {subject_id} invalid {level_key} {level}")
        check_refs(errors, f"profile_subject {subject_id}", subject.get("source_event_ids"), source_ids, "source_event")

    for voice in profile_voices:
        voice_id = voice.get("voice_id", "")
        source_id = voice.get("source_event_id", "").strip()
        if source_id and source_id not in source_ids:
            errors.append(f"profile_voice {voice_id} unknown source_event {source_id}")
        rel_path = voice.get("file_path", "").strip()
        if rel_path and not Path(rel_path).is_absolute() and not (project / rel_path).exists():
            errors.append(f"profile_voice {voice_id} missing file_path {rel_path}")
        status = voice.get("status", "").strip()
        if status and status not in PROFILE_STATUS_VALUES:
            errors.append(f"profile_voice {voice_id} invalid status {status}")

    for insight in profile_insights:
        insight_id = insight.get("insight_id", "")
        subject_id = insight.get("subject_id", "").strip()
        if subject_id and subject_id not in profile_subject_ids:
            errors.append(f"profile_insight {insight_id} unknown subject {subject_id}")
        source_id = insight.get("source_event_id", "").strip()
        if source_id and source_id not in source_ids:
            errors.append(f"profile_insight {insight_id} unknown source_event {source_id}")
        status = insight.get("status", "").strip()
        if status and status not in PROFILE_STATUS_VALUES:
            errors.append(f"profile_insight {insight_id} invalid status {status}")
        check_refs(errors, f"profile_insight {insight_id}", insight.get("linked_requirement_ids"), req_ids, "requirement")

    for conflict in profile_conflicts:
        conflict_id = conflict.get("conflict_id", "")
        status = conflict.get("status", "").strip()
        if status and status not in PROFILE_STATUS_VALUES:
            errors.append(f"profile_conflict {conflict_id} invalid status {status}")
        check_refs(errors, f"profile_conflict {conflict_id}", conflict.get("source_event_ids"), source_ids, "source_event")
        check_refs(errors, f"profile_conflict {conflict_id}", conflict.get("subject_ids"), profile_subject_ids, "profile_subject")

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

    if has_client_delivery_artifact(artifact_index):
        errors.extend(
            validate_client_delivery_readiness(
                project, artifact_index, version_map, feedback_rows
            )
        )

    stats = {
        "source_events": len(source_events),
        "requirements": len(requirements),
        "work_items": len(work_items),
        "agent_runs": len(agent_runs),
        "artifacts": len(artifact_index),
        "gates": len(gate_log),
        "versions": len(version_map),
        "threads": len(thread_registry_fields),
        "references": len(reference_cards),
        "assets": len(asset_manifest),
        "feedback": len(feedback_rows),
        "profile_subjects": len(profile_subjects),
        "profile_insights": len(profile_insights),
        "profile_conflicts": len(profile_conflicts),
        "agents_policy": int(agents_policy_ok),
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
