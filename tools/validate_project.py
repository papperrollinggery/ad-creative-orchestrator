#!/usr/bin/env python3
"""Validate an Ad Creative Orchestrator project directory."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from runtime_paths import is_initialized_adco_project
from adco_core.specialist_exchange import validate_v2_exchange_row

from specialist_schema_validation import (
    specialist_control_plane_errors,
    specialist_generation_authorization_errors,
    specialist_schema_errors,
)


CLIENT_DELIVERY_VISIBILITIES = {"client_visible", "client_visible_ready", "sent"}
CONTROL_PLANE_SCHEMA_VERSION = "2.0"
CONTROL_PLANE_SCHEMA_REL = Path("AD-creative/orchestrator/control_plane_schema.json")
FINAL_DELIVERY_CONFIRMATION_PROTOCOL = (
    "adco.final-delivery-reconciliation-confirmation"
)
FINAL_DELIVERY_CONFIRMATION_VERSION = "1.0"
FINAL_DELIVERY_HOST_ATTESTATION_PROTOCOL = "adco.host-readback-attestation"
FINAL_DELIVERY_HOST_ATTESTATION_VERSION = "1.0"
FINAL_DELIVERY_HOST_ATTESTATION_ROOT = Path(
    "AD-creative/orchestrator/host_attestations"
)
ARTIFACT_LIFECYCLE_VALUES = {
    "active",
    "pending",
    "superseded",
    "withdrawn",
    "archived",
    "deprecated",
    "rejected",
    "removed",
    "legacy_unresolved_tombstone",
    "legacy_unknown",
}
ARTIFACT_INACTIVE_LIFECYCLE_VALUES = {
    "superseded",
    "withdrawn",
    "archived",
    "deprecated",
    "rejected",
    "removed",
    "legacy_unresolved_tombstone",
}
CURRENT_ARTIFACT_TRUTH_KEYS = (
    "current_pptx_artifact_id",
    "current_pdf_artifact_id",
    "current_preview_artifact_id",
    "current_text_extract_artifact_id",
    "current_ppt_editability_artifact_id",
)
CURRENT_VIEW_VERSION_STATUSES = {
    "draft",
    "internal_review",
    "ready",
    "active",
    "current",
}
FINAL_DELIVERY_METADATA_MARKERS = {
    "gate",
    "checklist",
    "preview",
    "editability",
    "manifest",
    "lock",
}
FINAL_DELIVERY_ALWAYS_DELIVERABLE_SUFFIXES = {
    ".pdf",
    ".pptx",
    ".docx",
    ".xlsx",
    ".key",
    ".mov",
    ".mp4",
    ".zip",
}


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    scope: str
    code: str
    message: str
    evidence: str = ""

    def as_dict(self) -> dict[str, str]:
        return asdict(self)
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
    "lane_run_id",
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
    "planned_thread_id",
    "dispatch_status",
    "real_thread_id",
    "title_action",
    "title_verified_at",
    "dispatch_receipt_path",
    "dispatch_evidence",
    "scope_baseline_path",
    "scope_baseline_sha256",
    "scope_proof_path",
    "scope_proof_sha256",
    "rescue_dispatch_receipt_path",
    "rescue_dispatch_evidence",
    "convergence_state",
    "last_progress_at",
    "absolute_deadline_at",
    "bounded_extension_used",
    "extension_reason",
    "convergence_reminder_at",
    "convergence_reason",
    "rescue_count",
    "rescue_thread_id",
    "receipt_thread_id",
    "adoption_decision",
    "rejection_reason",
    "schema_state",
    "legacy_evidence_sha256",
    "legacy_quarantine_reason",
    "legacy_raw_ref",
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
    "worker_recommendation": ("Adoption / Rejection Recommendation",),
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
THREADOPS_ADOPTION_DECISIONS = {"ADOPT", "PARTIAL_ADOPT", "REJECT", "BLOCKED"}
THREADOPS_CONVERGENCE_STATES = {
    "",
    "awaiting_first_readback",
    "active_with_progress",
    "silent",
    "finalizing_receipt",
    "thread_not_converged",
    "rescue_dispatched",
    "receipt_received",
    "receipt_rejected",
}
THREADOPS_REAL_THREAD_ID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
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
CLIENT_OUTLINE_FIELDS = [
    "slide_id",
    "page_title",
    "body_copy",
    "client_confirmation_point",
    "material_role",
    "visual_slot",
    "visual_asset_status",
    "asset_ids",
    "visibility",
    "status",
    "notes",
]
ASSET_CURRENT_FIELDS = [
    "asset_id",
    "source",
    "platform",
    "conversation",
    "local_file",
    "path",
    "sha256",
    "original_or_processed",
    "approval",
    "direct_client_use",
    "used_in_slide",
    "qa_flags",
    "protected",
    "status",
    "notes",
]
ASSET_AUTHORIZATION_FIELDS = [
    "authorization_id",
    "asset_id",
    "asset_sha256",
    "approval_scope",
    "approved_by",
    "approved_at",
    "evidence_ref",
    "evidence_sha256",
    "status",
    "revoked_at",
    "notes",
]
FINAL_DELIVERY_LOCK_FIELDS = [
    "lock_id",
    "path",
    "sha256",
    "size_bytes",
    "mtime",
    "protected",
    "registered_at",
    "notes",
    "inventory_state",
    "reconciliation_state",
    "reconciliation_kind",
    "reconciles_lock_id",
    "supersedes_lock_id",
    "confirmed_by",
    "confirmed_at",
    "evidence_ref",
    "evidence_sha256",
    "host_attestation_ref",
    "host_attestation_sha256",
    "version_id",
    "supersedes_version_id",
    "status_reason",
]
ARTIFACT_INDEX_FIELDS = [
    "artifact_id",
    "artifact_type",
    "path",
    "stage",
    "version",
    "status",
    "visibility",
    "source_event_ids",
    "linked_requirements",
    "linked_work_items",
    "linked_references",
    "linked_assets",
    "gate_status",
    "supersedes_artifact_id",
    "created_at",
    "updated_at",
    "sha256",
    "size_bytes",
    "derived_from_artifact_id",
    "derived_from_sha256",
    "lifecycle_state",
    "original_path",
    "cleanup_ref",
    "removed_at",
    "removal_reason",
    "superseded_by",
    "status_reason",
]
GATE_LOG_FIELDS = [
    "gate_id",
    "gate_run_id",
    "stage",
    "status",
    "score",
    "checked_artifacts",
    "target_ref",
    "target_sha256",
    "evidence_snapshot_ref",
    "evidence_snapshot_sha256",
    "blocking_issues",
    "revision_items",
    "questions",
    "next_state",
    "created_at",
    "owner",
    "supersedes_gate_run_id",
]
SPECIALIST_EXCHANGE_INDEX_FIELDS = [
    "exchange_id",
    "handoff_id",
    "attempt",
    "work_id",
    "provider_id",
    "profile_id",
    "contract_version",
    "descriptor_sha256",
    "handoff_sha256",
    "baseline_path",
    "baseline_sha256",
    "compatibility_status",
    "execution_mode",
    "lane_id",
    "thread_id",
    "handoff_path",
    "receipt_path",
    "receipt_sha256",
    "outcome",
    "adoption_path",
    "adoption_sha256",
    "adoption_decision",
    "thread_reconciliation_ref",
    "created_at",
    "updated_at",
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
    "$ad-creative-orchestrator",
    "apply only when",
    "project.yml",
    "control_plane_schema.json",
    "explicitly invokes",
    "ad-creative-orchestrator source repository",
    "Paperrolling-DIRcreative-SKILL",
    "Skill maintenance",
    "Skill Benchmark",
    "AGENTS/SKILL/Schema/test changes",
    "ordinary code refactoring",
    "ordinary advertising requests",
    "not explicitly invoked",
    "valid Specialist handoff",
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
    "explicit authorization",
    "Public official-source research",
    "final send",
    "dircreative",
    "adco.specialist-exchange",
    "asset_authorizations.csv",
    "client-send-readiness-gate",
    "Default to no Thread",
    "active_with_progress",
    "finalizing_receipt",
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
    "receipts containing their real thread_id",
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
    "AD-creative/orchestrator/final_delivery_lock.csv",
    "AD-creative/orchestrator/agency/skill_scout.csv",
    "AD-creative/orchestrator/agency/agent_scout.csv",
    "AD-creative/orchestrator/agency/specialist_preflight.csv",
    "AD-creative/orchestrator/specialist_exchange/exchange_index.csv",
    "AD-creative/orchestrator/agency/asset_preflight.csv",
    "AD-creative/orchestrator/agency/maintenance_heartbeat.md",
    "AD-creative/orchestrator/agency/self_improvement_log.md",
    "AD-creative/client_review/client_outline.csv",
    "AD-creative/visual_assets/asset_current_manifest.csv",
    "AD-creative/visual_assets/asset_authorizations.csv",
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


def normalized_artifact_lifecycle(row: dict[str, str]) -> str:
    explicit = (row.get("lifecycle_state") or "").strip().lower().replace("-", "_")
    if explicit:
        return explicit
    status = (row.get("status") or "").strip().lower().replace("-", "_").replace(" ", "_")
    if "removed" in status and any(token in status for token in ("clean", "cleanup")):
        return "legacy_unresolved_tombstone"
    return {
        "superseded": "superseded",
        "withdrawn": "withdrawn",
        "archived": "archived",
        "deprecated": "deprecated",
        "rejected": "rejected",
        "removed": "removed",
        "deleted": "removed",
        "pending": "pending",
        "planned": "pending",
        "draft": "pending",
        "blocked": "pending",
        "not_run": "pending",
    }.get(status, "active" if status in {"", "active", "current", "done", "complete", "completed", "approved", "registered", "pass", "passed", "internal_review", "ready"} else "legacy_unknown")


def canonical_row_sha256(row: dict[str, object]) -> str:
    payload = json.dumps(
        {str(key): row.get(key, "") or "" for key in sorted(key for key in row if key is not None)},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def canonical_payload_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def final_delivery_metadata_path(path: Path) -> bool:
    if path.suffix.lower() in FINAL_DELIVERY_ALWAYS_DELIVERABLE_SUFFIXES:
        return False
    stem = re.sub(r"[^a-z0-9]+", "_", path.stem.lower()).strip("_")
    tokens = {token for token in stem.split("_") if token}
    strong_phrases = {
        "text_extract",
        "gate_report",
        "gate_checklist",
        "delivery_gate",
        "final_delivery_index",
        "delivery_index",
        "lock_snapshot",
        "delivery_manifest",
    }
    return bool(tokens & FINAL_DELIVERY_METADATA_MARKERS) or any(
        phrase in stem for phrase in strong_phrases
    )


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
    if not is_initialized_adco_project(project):
        errors.append(
            "project is not an initialized ADCO runtime project with matching project.yml and control_plane_schema.json"
        )
        return False
    path = project / "AGENTS.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    normalized = " ".join(text.replace("`", "").split()).lower()
    missing = [
        snippet
        for snippet in AGENTS_REQUIRED_SNIPPETS
        if " ".join(snippet.replace("`", "").split()).lower() not in normalized
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
    lifecycle_state = normalize_threadops_status(row.get("lifecycle_state"))
    dispatch_status = normalize_threadops_status(row.get("dispatch_status"))
    thread_id = row.get("thread_id", "").strip()
    real_thread_id = row.get("real_thread_id", "").strip()
    lane_id = row.get("lane_id", "").strip()
    work_id = row.get("work_id", "").strip()
    lane_run_id = row.get("lane_run_id", "").strip()
    normalized_scope = write_scope.lower().replace("-", "_")
    if lane_id and work_id and lane_run_id != f"{work_id}:{lane_id}":
        errors.append(f"{owner} lane_run_id does not match work_id:lane_id")
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
    if lifecycle_state in {"dispatched", "running", "returned", "reconciled"} or dispatch_status in {"dispatched", "running", "returned", "reconciled"}:
        missing_dispatch = [
            field
            for field in [
                "real_thread_id",
                "title_verified_at",
                "dispatch_receipt_path",
                "dispatch_evidence",
                "scope_baseline_path",
                "scope_baseline_sha256",
            ]
            if not row.get(field, "").strip()
        ]
        if thread_id.startswith("planned:") or not real_thread_id or missing_dispatch:
            errors.append(
                f"{owner} claims worker execution without real thread dispatch proof: "
                + ", ".join(missing_dispatch or ["thread_id"])
            )
        if real_thread_id and not THREADOPS_REAL_THREAD_ID_PATTERN.fullmatch(real_thread_id):
            errors.append(f"{owner} real_thread_id is not a Codex Thread UUID")
        if not row.get("absolute_deadline_at", "").strip():
            errors.append(f"{owner} dispatched worker missing absolute_deadline_at")

    convergence_state = normalize_threadops_status(row.get("convergence_state"))
    if convergence_state not in THREADOPS_CONVERGENCE_STATES:
        errors.append(f"{owner} unknown convergence_state {convergence_state}")
    for timestamp_field in [
        "last_progress_at",
        "absolute_deadline_at",
        "convergence_reminder_at",
        "returned_at",
        "reconciled_at",
        "archived_at",
    ]:
        value = row.get(timestamp_field, "").strip()
        if value and not threadops_timestamp_is_aware(value):
            errors.append(f"{owner} {timestamp_field} is not an ISO-8601 timestamp with timezone")
    if convergence_state in {"active_with_progress", "finalizing_receipt"} and not row.get("last_progress_at", "").strip():
        errors.append(f"{owner} progress state missing last_progress_at")
    if normalize_threadops_bool(row.get("bounded_extension_used")):
        if not row.get("extension_reason", "").strip():
            errors.append(f"{owner} bounded extension missing extension_reason")
        if not row.get("last_progress_at", "").strip():
            errors.append(f"{owner} bounded extension missing last_progress_at")
    try:
        rescue_count = int(row.get("rescue_count", "0") or "0")
    except ValueError:
        rescue_count = 2
        errors.append(f"{owner} rescue_count is not an integer")
    if rescue_count < 0 or rescue_count > 1:
        errors.append(f"{owner} rescue_count exceeds bounded rescue limit")
    if rescue_count == 1:
        rescue_thread_id = row.get("rescue_thread_id", "").strip()
        if not THREADOPS_REAL_THREAD_ID_PATTERN.fullmatch(rescue_thread_id):
            errors.append(f"{owner} bounded rescue missing real rescue_thread_id")
        if rescue_thread_id == real_thread_id:
            errors.append(f"{owner} rescue_thread_id must differ from real_thread_id")
        if not row.get("rescue_dispatch_receipt_path", "").strip() or not row.get(
            "rescue_dispatch_evidence", ""
        ).strip():
            errors.append(f"{owner} bounded rescue missing dispatch/readback proof")
    if convergence_state == "thread_not_converged" and row.get("convergence_reason", "").strip() not in {
        "silent_past_absolute_deadline",
        "reminder_no_receipt",
    }:
        errors.append(f"{owner} thread_not_converged missing bounded convergence reason")

    if threadops_receipt_is_received(row):
        decision = row.get("adoption_decision", "").strip().upper()
        if decision not in THREADOPS_ADOPTION_DECISIONS:
            errors.append(f"{owner} received receipt missing main adoption_decision")
        if decision != "ADOPT" and not row.get("rejection_reason", "").strip():
            errors.append(f"{owner} non-ADOPT decision missing rejection_reason")
        if not row.get("receipt_thread_id", "").strip():
            errors.append(f"{owner} received receipt missing receipt_thread_id")
        if normalize_threadops_status(row.get("reconciliation_status")) == "reconciled":
            if not normalize_threadops_bool(row.get("archived")) or not row.get("archived_at", "").strip():
                errors.append(f"{owner} reconciled worker cleanup is not confirmed archived")


def normalize_threadops_status(value: str | None) -> str:
    return (value or "").strip().lower().replace("-", "_").replace(" ", "_")


def normalize_threadops_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def threadops_timestamp_is_aware(value: str) -> bool:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None


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
    if key == "worker_recommendation":
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
        "worker_recommendation",
        THREADOPS_RECEIPT_REQUIRED_PROOF["worker_recommendation"],
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


def receipt_thread_id_values(text: str) -> list[str]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        execution = payload.get("execution_evidence")
        values = [
            payload.get("thread_id"),
            execution.get("thread_id") if isinstance(execution, dict) else None,
        ]
        ids = [value.strip() for value in values if isinstance(value, str) and value.strip()]
        if ids:
            return list(dict.fromkeys(ids))
    pattern = re.compile(
        r"(?im)^\s*(?:[-*]\s*)?(?:receipt\.)?(?:thread_id|real_thread_id)\s*[:=]\s*([^\s,;]+)\s*$"
    )
    return list(dict.fromkeys(match.group(1).strip() for match in pattern.finditer(text)))


def check_threadops_receipt_identity(
    project: Path,
    errors: list[str],
    owner: str,
    row: dict[str, str],
) -> None:
    if not threadops_receipt_is_received(row):
        return
    rel_path = row.get("receipt_path", "").strip()
    if not rel_path:
        errors.append(f"{owner} received worker missing receipt_path")
        return
    try:
        receipt_path = project_contained_path(project, rel_path, f"{owner} receipt")
        text = receipt_path.read_text(encoding="utf-8")
    except (FileNotFoundError, ValueError) as exc:
        errors.append(f"{owner} received worker missing receipt file {rel_path}")
        if isinstance(exc, ValueError):
            errors.append(str(exc))
        return
    identities = receipt_thread_id_values(text)
    expected_ids = {
        value
        for value in [
            row.get("real_thread_id", "").strip(),
            row.get("rescue_thread_id", "").strip(),
        ]
        if value
    }
    if len(identities) != 1 or identities[0] not in expected_ids:
        errors.append(
            f"{owner} invalid_worker_thread_id: receipt={';'.join(identities) or 'missing'} "
            f"expected={';'.join(sorted(expected_ids)) or 'missing'}"
        )
        return
    registry_receipt_thread_id = row.get("receipt_thread_id", "").strip()
    if registry_receipt_thread_id != identities[0]:
        errors.append(
            f"{owner} receipt_thread_id does not match worker receipt identity {identities[0]}"
        )
    dispatch_rel = row.get("dispatch_receipt_path", "").strip()
    if dispatch_rel:
        try:
            dispatch_path = project_contained_path(
                project, dispatch_rel, f"{owner} dispatch receipt"
            )
            dispatch_text = dispatch_path.read_text(encoding="utf-8")
        except (FileNotFoundError, ValueError):
            errors.append(f"{owner} dispatch receipt file missing: {dispatch_rel}")
        else:
            dispatch_ids = receipt_thread_id_values(dispatch_text)
            if dispatch_ids != [row.get("real_thread_id", "").strip()]:
                errors.append(f"{owner} dispatch receipt real_thread_id does not match registry")
    if identities and identities[0] == row.get("rescue_thread_id", "").strip():
        rescue_dispatch_rel = row.get("rescue_dispatch_receipt_path", "").strip()
        if not rescue_dispatch_rel:
            errors.append(f"{owner} rescue receipt lacks rescue dispatch proof")
        else:
            try:
                rescue_dispatch_path = project_contained_path(
                    project, rescue_dispatch_rel, f"{owner} rescue dispatch receipt"
                )
            except ValueError as exc:
                errors.append(str(exc))
            else:
                if not rescue_dispatch_path.is_file():
                    errors.append(f"{owner} rescue dispatch receipt file missing")
                elif identities[0] not in rescue_dispatch_path.read_text(
                    encoding="utf-8", errors="ignore"
                ):
                    errors.append(f"{owner} rescue dispatch identity mismatch")


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
    try:
        receipt_path = project_contained_path(project, rel_path, f"{owner} receipt")
        text = receipt_path.read_text(encoding="utf-8")
    except (FileNotFoundError, ValueError):
        errors.append(f"{owner} received execution worker missing receipt file {rel_path}")
        return

    try:
        parsed_receipt = json.loads(text)
    except json.JSONDecodeError:
        parsed_receipt = None
    specialist_json = (
        isinstance(parsed_receipt, dict)
        and parsed_receipt.get("protocol_id") == "adco.specialist-exchange"
    )
    if not specialist_json:
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
    decision = row.get("adoption_decision", "").strip().upper()
    if decision in THREADOPS_ADOPTING_DECISIONS:
        try:
            json_receipt = json.loads(text)
        except json.JSONDecodeError:
            json_receipt = None
        is_specialist_json = (
            isinstance(json_receipt, dict)
            and json_receipt.get("protocol_id") == "adco.specialist-exchange"
        )
        validation_text = "\n".join(
            receipt_proof_values(
                text,
                "validation_result",
                THREADOPS_RECEIPT_REQUIRED_PROOF["validation_result"],
            )
        ).lower()
        validation_ok = (
            isinstance(json_receipt.get("qa"), dict)
            and json_receipt["qa"].get("status") == "pass"
            if is_specialist_json
            else not re.search(
                r"\b(fail(?:ed)?|error|blocked|not[_ ]?run|exit\s*[=:]?\s*[1-9])\b",
                validation_text,
            )
            and bool(
                re.search(
                    r"\b(pass(?:ed)?|success|ok|exit\s*[=:]?\s*0)\b",
                    validation_text,
                )
            )
        )
        if not validation_ok:
            errors.append(f"{owner} adopted receipt validation_result is not successful")
        loop_text = "\n".join(
            receipt_proof_values(text, "loop_state", ())
        ).lower()
        loop_ok = (
            json_receipt.get("outcome") == "completed"
            if is_specialist_json
            else bool(
                re.search(
                    r"\b(returned|reconciled|archived|completed|success)\b",
                    loop_text,
                )
            )
            and not bool(
                re.search(
                    r"\b(blocked|failed|error|frozen|replay_requested)\b",
                    loop_text,
                )
            )
        )
        if not loop_ok:
            errors.append(f"{owner} adopted receipt loop_state is not complete")
        if not row.get("scope_proof_path", "").strip() or not row.get(
            "scope_proof_sha256", ""
        ).strip():
            errors.append(f"{owner} adopted receipt missing host scope proof")
        else:
            try:
                proof_path = project_contained_path(
                    project,
                    row.get("scope_proof_path", "").strip(),
                    f"{owner} scope proof",
                )
            except ValueError as exc:
                errors.append(str(exc))
            else:
                if not proof_path.is_file() or file_sha256(proof_path) != row.get(
                    "scope_proof_sha256", ""
                ).strip():
                    errors.append(f"{owner} host scope proof missing or hash mismatch")
                else:
                    try:
                        proof = json.loads(proof_path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        errors.append(f"{owner} host scope proof invalid JSON")
                    else:
                        observed = proof.get("observed_changed_paths")
                        declared = proof.get("receipt_declared_paths")
                        if observed != declared or not isinstance(observed, list):
                            errors.append(f"{owner} host scope proof changed-path mismatch")
                        if proof.get("decision") != decision:
                            errors.append(f"{owner} host scope proof decision mismatch")
                        if proof.get("validation_success") is not True:
                            errors.append(f"{owner} host scope proof validation is not successful")
                        write_scopes = [
                            item.strip()
                            for item in row.get("write_scope", "").split(";")
                            if item.strip()
                        ]
                        try:
                            scope_roots = [
                                project_contained_path(
                                    project, item, f"{owner} write_scope"
                                )
                                for item in write_scopes
                            ]
                        except ValueError as exc:
                            errors.append(str(exc))
                            scope_roots = []
                        for rel_path in observed or []:
                            try:
                                changed_path = project_contained_path(
                                    project, str(rel_path), f"{owner} changed path"
                                )
                            except ValueError as exc:
                                errors.append(str(exc))
                                continue
                            if not any(
                                changed_path == root or root in changed_path.parents
                                for root in scope_roots
                            ):
                                errors.append(
                                    f"{owner} changed path outside write_scope: {rel_path}"
                                )
                            if not changed_path.is_file():
                                errors.append(f"{owner} adopted output missing: {rel_path}")
        if row.get("archived", "").strip().lower() not in {"true", "yes", "1"}:
            errors.append(f"{owner} adopted receipt is not archived")
        if not row.get("archived_at", "").strip() or not row.get(
            "cleanup_action", ""
        ).strip():
            errors.append(f"{owner} adopted receipt lacks cleanup/archive evidence")
    check_threadops_helper_receipt(errors, owner, text)


def id_set(rows: Iterable[dict[str, str]], key: str) -> set[str]:
    return {row.get(key, "").strip() for row in rows if row.get(key, "").strip()}


def project_contained_path(project: Path, raw_path: str, label: str) -> Path:
    candidate = Path(raw_path)
    if not raw_path or candidate.is_absolute():
        raise ValueError(f"{label} must be a non-empty project-relative path: {raw_path}")
    resolved = (project / candidate).resolve()
    try:
        resolved.relative_to(project.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes project scope: {raw_path}") from exc
    return resolved


def project_relative_path_has_symlink_component(project: Path, raw_path: str) -> bool:
    candidate = Path(raw_path.replace("\\", "/"))
    if candidate.is_absolute() or ".." in candidate.parts:
        return False
    current = project.resolve()
    for part in candidate.parts:
        if part in {"", "."}:
            continue
        current = current / part
        if current.is_symlink():
            return True
    return False


def specialist_handoff_semantic_errors(
    project: Path, handoff: dict[str, object]
) -> list[str]:
    errors: list[str] = []
    source_truth = handoff.get("source_truth")
    task = handoff.get("task")
    execution = handoff.get("execution")
    scope = handoff.get("scope")
    if not isinstance(source_truth, dict) or not isinstance(task, dict):
        return ["handoff authorization context is missing"]
    errors.extend(
        specialist_generation_authorization_errors(
            project,
            authorization=handoff.get("authorization"),
            work_id=str(handoff.get("work_id", "")),
            profile_id=str(handoff.get("profile_id", "")),
            input_artifact_ids=[
                str(item.get("artifact_id", ""))
                for item in source_truth.get("artifacts", [])
                if isinstance(item, dict)
            ],
            expected_output_kinds=[
                str(item) for item in task.get("expected_output_kinds", [])
            ],
        )
    )
    if not isinstance(execution, dict) or not isinstance(scope, dict):
        errors.append("handoff execution or scope is missing")
        return errors
    receipt_rel = str(scope.get("receipt_path", ""))
    write_scope = [str(item) for item in scope.get("write", [])]
    if execution.get("workspace_mode") == "read_only":
        if write_scope != [receipt_rel]:
            errors.append("read_only handoff may write only its exact receipt_path")
    elif receipt_rel not in write_scope or len(write_scope) < 2:
        errors.append("writable handoff must grant an output root and receipt_path")

    authorization = handoff.get("authorization")
    if isinstance(authorization, dict) and authorization.get("generation_mode") == "real_media":
        authorization_rel = str(authorization.get("authorization_ref", ""))
        baseline_ref = scope.get("host_baseline")
        try:
            authorization_path = project_contained_path(
                project, authorization_rel, "generation authorization_ref"
            )
            baseline_path = project_contained_path(
                project,
                str(baseline_ref.get("path", ""))
                if isinstance(baseline_ref, dict)
                else "",
                "specialist host baseline",
            )
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            errors.append(f"generation authorization baseline binding is invalid: {exc}")
        else:
            baseline_files = baseline.get("files")
            if (
                not isinstance(baseline_files, dict)
                or not authorization_path.is_file()
                or baseline_files.get(authorization_rel) != file_sha256(authorization_path)
            ):
                errors.append(
                    "generation authorization evidence is not bound by the host baseline"
                )
    return errors


def specialist_receipt_semantic_errors(
    project: Path,
    handoff: dict[str, object],
    receipt: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    outcome = str(receipt.get("outcome", ""))
    open_questions = receipt.get("open_questions")
    if outcome == "needs_user":
        if not isinstance(open_questions, list) or not open_questions:
            errors.append("needs_user receipt lacks open_questions")
        else:
            question_ids = [
                str(item.get("id", "")).strip()
                for item in open_questions
                if isinstance(item, dict)
            ]
            if (
                len(question_ids) != len(open_questions)
                or any(not item for item in question_ids)
            ):
                errors.append("needs_user receipt question ids must be non-empty")
            elif len(question_ids) != len(set(question_ids)):
                errors.append("needs_user receipt contains duplicate question id")

    scope = handoff.get("scope")
    execution = handoff.get("execution")
    task = handoff.get("task")
    source_truth = handoff.get("source_truth")
    acceptance = handoff.get("acceptance")
    outputs = receipt.get("output_artifacts")
    if (
        not isinstance(scope, dict)
        or not isinstance(execution, dict)
        or not isinstance(task, dict)
        or not isinstance(source_truth, dict)
        or not isinstance(acceptance, dict)
    ):
        errors.append("handoff execution, task, source truth, acceptance, or scope is missing")
        return errors
    if not isinstance(outputs, list):
        errors.append("receipt output_artifacts is missing")
        return errors
    if execution.get("workspace_mode") == "read_only" and outputs:
        errors.append("read_only receipt must not return output artifacts")
    expected_kinds = {
        str(item) for item in task.get("expected_output_kinds", []) if str(item)
    }
    source_input_ids = {
        str(item.get("artifact_id", ""))
        for item in source_truth.get("artifacts", [])
        if isinstance(item, dict)
    }
    evidence = receipt.get("execution_evidence")
    if (
        not isinstance(evidence, dict)
        or evidence.get("mode") != execution.get("mode")
    ):
        errors.append("receipt execution evidence does not match handoff")
    required_extensions = {
        (str(item.get("id", "")), str(item.get("version", "")))
        for item in acceptance.get("required_receipt_extensions", [])
        if isinstance(item, dict)
    }
    extensions = receipt.get("extensions")
    returned_extensions = (
        {
            (str(item.get("id", "")), str(item.get("version", "")))
            for item in extensions
            if isinstance(item, dict)
        }
        if isinstance(extensions, list)
        else set()
    )
    if not required_extensions.issubset(returned_extensions):
        errors.append("receipt is missing a required negotiated extension")

    receipt_rel = str(scope.get("receipt_path", ""))
    allowed_roots: list[Path] = []
    for raw_root in scope.get("write", []):
        if str(raw_root) == receipt_rel:
            continue
        try:
            allowed_roots.append(
                project_contained_path(project, str(raw_root), "specialist write scope")
            )
        except ValueError as exc:
            errors.append(str(exc))

    seen_ids: set[str] = set()
    seen_kinds: set[str] = set()
    seen_paths: set[str] = set()
    seen_inodes: set[tuple[int, int]] = set()
    for item in outputs:
        if not isinstance(item, dict):
            errors.append("invalid specialist output artifact entry")
            continue
        provider_artifact_id = str(item.get("provider_artifact_id", "")).strip()
        kind = str(item.get("kind", "")).strip()
        if provider_artifact_id in seen_ids:
            errors.append(f"duplicate provider_artifact_id: {provider_artifact_id}")
        seen_ids.add(provider_artifact_id)
        if kind in seen_kinds:
            errors.append(f"duplicate specialist output kind: {kind}")
        seen_kinds.add(kind)
        if kind not in expected_kinds:
            errors.append(f"unexpected specialist output kind: {kind}")
        if item.get("visibility") != "internal_only":
            errors.append(
                f"specialist output visibility must remain internal_only: {provider_artifact_id}"
            )
        output_sources = item.get("source_input_ids")
        if (
            not isinstance(output_sources, list)
            or not output_sources
            or not {str(source) for source in output_sources}.issubset(source_input_ids)
        ):
            errors.append(
                f"specialist output source_input_ids invalid: {provider_artifact_id}"
            )
        raw_path = str(item.get("path", ""))
        if "\\" in raw_path:
            errors.append(
                f"specialist output must use POSIX path separators: {provider_artifact_id}"
            )
            continue
        if project_relative_path_has_symlink_component(project, raw_path):
            errors.append(f"specialist output must not use symlink path: {provider_artifact_id}")
            continue
        try:
            output_path = project_contained_path(
                project, raw_path, f"specialist output {provider_artifact_id}"
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        canonical_path = output_path.relative_to(project.resolve()).as_posix()
        if canonical_path in seen_paths:
            errors.append(f"duplicate specialist output path: {canonical_path}")
        seen_paths.add(canonical_path)
        if not output_path.is_file():
            errors.append(f"specialist output missing: {provider_artifact_id}")
            continue
        if not any(
            output_path == root or root in output_path.parents for root in allowed_roots
        ):
            errors.append(f"specialist output outside write scope: {provider_artifact_id}")
        output_stat = output_path.stat()
        if output_stat.st_size == 0 or output_stat.st_nlink != 1:
            errors.append(
                f"specialist output must be non-empty and not hardlinked: {provider_artifact_id}"
            )
        physical_id = (output_stat.st_dev, output_stat.st_ino)
        if physical_id in seen_inodes:
            errors.append(
                f"specialist output physical file reused: {provider_artifact_id}"
            )
        seen_inodes.add(physical_id)
        if file_sha256(output_path) != str(item.get("sha256", "")):
            errors.append(f"specialist output hash mismatch: {provider_artifact_id}")
    if outcome == "completed" and not outputs:
        errors.append("completed specialist receipt has no outputs")
    if outcome == "completed" and not expected_kinds.issubset(seen_kinds):
        errors.append(
            "completed receipt missing expected output kinds: "
            + ",".join(sorted(expected_kinds - seen_kinds))
        )
    return errors


def specialist_manifest_digest(files: dict[str, str]) -> str:
    canonical = json.dumps(files, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def has_valid_asset_authorization(
    project: Path,
    asset_id: str,
    asset_sha256: str,
    authorizations: list[dict[str, str]],
) -> bool:
    for row in authorizations:
        if (row.get("asset_id") or "").strip() != asset_id:
            continue
        if (row.get("asset_sha256") or "").strip() != asset_sha256:
            continue
        if (row.get("approval_scope") or "").strip().lower() not in {
            "client_review",
            "client_delivery",
            "client_visible",
        }:
            continue
        if (row.get("status") or "").strip().lower() != "approved":
            continue
        if (row.get("revoked_at") or "").strip():
            continue
        approved_by = (row.get("approved_by") or "").strip().lower()
        if approved_by in {"", "ad_creative_operator", "automation", "worker", "main controller"}:
            continue
        if not threadops_timestamp_is_aware((row.get("approved_at") or "").strip()):
            continue
        evidence_ref = (row.get("evidence_ref") or "").strip()
        if evidence_ref.startswith(
            ("user_confirmation:", "client_confirmation:")
        ):
            return True
        try:
            evidence_path = project_contained_path(
                project, evidence_ref, "asset authorization evidence_ref"
            )
        except ValueError:
            continue
        if (
            evidence_path.is_file()
            and (row.get("evidence_sha256") or "").strip()
            == file_sha256(evidence_path)
        ):
            return True
    return False


def validate_version_integrity(
    project: Path,
    artifacts: list[dict[str, str]],
    versions: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    for rows, key, label in [
        (artifacts, "artifact_id", "artifact_index"),
        (versions, "version_id", "version_map"),
    ]:
        values = [(row.get(key) or "").strip() for row in rows]
        duplicates = sorted({value for value in values if value and values.count(value) > 1})
        errors.extend(f"{label} duplicate {key}: {value}" for value in duplicates)

    artifact_by_id = {
        (row.get("artifact_id") or "").strip(): row
        for row in artifacts
        if (row.get("artifact_id") or "").strip()
    }
    version_by_id = {
        (row.get("version_id") or "").strip(): row
        for row in versions
        if (row.get("version_id") or "").strip()
    }
    for row in versions:
        version_id = (row.get("version_id") or "").strip()
        supersedes = (row.get("supersedes_version_id") or "").strip()
        if supersedes == version_id and version_id:
            errors.append(f"version_map {version_id} supersedes itself")
        elif supersedes and supersedes not in version_by_id:
            errors.append(f"version_map {version_id} supersedes unknown version {supersedes}")
    for start in version_by_id:
        seen: set[str] = set()
        current = start
        while current:
            if current in seen:
                errors.append(f"version_map supersedes cycle detected from {start}")
                break
            seen.add(current)
            row = version_by_id.get(current)
            current = ((row or {}).get("supersedes_version_id") or "").strip()

    truth_path = project / "AD-creative/orchestrator/current_truth.md"
    truth_text = truth_path.read_text(encoding="utf-8") if truth_path.exists() else ""
    current_version = current_truth_value(truth_text, "current_version_id")
    current_pptx = current_truth_value(truth_text, "current_pptx_artifact_id")
    current_editability = current_truth_value(
        truth_text, "current_ppt_editability_artifact_id"
    )
    truth_status = current_truth_value(truth_text, "version_map_status")
    if current_version:
        version_row = version_by_id.get(current_version)
        if not version_row:
            errors.append(f"current_truth current_version_id unknown: {current_version}")
        else:
            if truth_status and (version_row.get("status") or "").strip().lower() != truth_status.lower():
                errors.append("current_truth version_map_status does not match current version row")
            if current_pptx and (version_row.get("artifact_id") or "").strip() != current_pptx:
                errors.append("current version_map artifact_id does not match current_pptx_artifact_id")
            pptx_row = artifact_by_id.get(current_pptx) if current_pptx else None
            if current_pptx and not pptx_row:
                errors.append(f"current_truth current_pptx_artifact_id unknown: {current_pptx}")
            elif pptx_row:
                if (pptx_row.get("artifact_type") or "").strip().lower() != "pptx":
                    errors.append(f"current PPT artifact {current_pptx} is not type pptx")
                if (pptx_row.get("version") or "").strip() != (version_row.get("version") or "").strip():
                    errors.append("current PPT artifact version does not match current version_map row")
                if not (pptx_row.get("sha256") or "").strip() or not (pptx_row.get("size_bytes") or "").strip():
                    errors.append(f"current PPT artifact {current_pptx} missing hash/size baseline")
            edit_row = artifact_by_id.get(current_editability) if current_editability else None
            if current_editability and not edit_row:
                errors.append(
                    f"current_truth current_ppt_editability_artifact_id unknown: {current_editability}"
                )
            elif edit_row and (edit_row.get("version") or "").strip() != (version_row.get("version") or "").strip():
                errors.append("current PPT editability artifact version does not match current version_map row")

    for artifact_id, row in artifact_by_id.items():
        expected_sha = (row.get("sha256") or "").strip()
        expected_size = (row.get("size_bytes") or "").strip()
        rel_path = (row.get("path") or "").strip()
        if not rel_path:
            if expected_sha or expected_size:
                errors.append(
                    f"artifact {artifact_id} hash baseline points to missing file: <missing>"
                )
            continue
        try:
            path = project_contained_path(
                project, rel_path, f"artifact {artifact_id} path"
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not expected_sha and not expected_size:
            continue
        if not rel_path or not path.exists() or not path.is_file():
            errors.append(f"artifact {artifact_id} hash baseline points to missing file: {rel_path or '<missing>'}")
            continue
        if not expected_sha or not expected_size:
            errors.append(f"artifact {artifact_id} has incomplete hash/size baseline")
            continue
        actual_sha = file_sha256(path)
        actual_size = str(path.stat().st_size)
        if actual_sha != expected_sha or actual_size != expected_size:
            errors.append(f"artifact {artifact_id} content changed after registration")
    return errors


def validate_specialist_exchange_index(
    project: Path,
    rows: list[dict[str, str]],
) -> list[str]:
    errors = [
        f"specialist_exchange control plane: {issue}"
        for issue in specialist_control_plane_errors(project, rows)
    ]
    seen_handoffs: set[str] = set()
    for row in rows:
        handoff_payload: dict[str, object] = {}
        receipt_payload: dict[str, object] = {}
        actual_handoff_sha = ""
        handoff_id = (row.get("handoff_id") or "").strip()
        if not handoff_id:
            errors.append("specialist_exchange row missing handoff_id")
            continue
        if handoff_id in seen_handoffs:
            errors.append(f"specialist_exchange duplicate handoff_id: {handoff_id}")
        seen_handoffs.add(handoff_id)
        contract_version = (row.get("contract_version") or "").strip()
        if contract_version == "2.0":
            errors.extend(validate_v2_exchange_row(project, row))
            continue
        if contract_version != "1.0":
            errors.append(f"specialist_exchange {handoff_id} unsupported contract_version")
        if (row.get("attempt") or "").strip() not in {"1", "2"}:
            errors.append(f"specialist_exchange {handoff_id} attempt must be 1 or 2")
        handoff_rel = (row.get("handoff_path") or "").strip()
        try:
            handoff_path = project_contained_path(
                project, handoff_rel, f"specialist_exchange {handoff_id} handoff"
            )
        except ValueError as exc:
            errors.append(str(exc))
            handoff_path = Path()
        if not handoff_rel or not handoff_path.is_file():
            errors.append(f"specialist_exchange {handoff_id} handoff file missing")
        else:
            expected_handoff_sha = (row.get("handoff_sha256") or "").strip()
            actual_handoff_sha = file_sha256(handoff_path)
            if not expected_handoff_sha or actual_handoff_sha != expected_handoff_sha:
                errors.append(f"specialist_exchange {handoff_id} handoff hash mismatch")
            try:
                handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                errors.append(f"specialist_exchange {handoff_id} handoff invalid JSON")
            else:
                if isinstance(handoff, dict):
                    handoff_payload = handoff
                for issue in specialist_schema_errors("handoff", handoff):
                    errors.append(
                        f"specialist_exchange {handoff_id} handoff schema: {issue}"
                    )
                if isinstance(handoff, dict):
                    for issue in specialist_handoff_semantic_errors(project, handoff):
                        errors.append(
                            f"specialist_exchange {handoff_id} handoff semantics: {issue}"
                        )
                for key in [
                    "exchange_id",
                    "handoff_id",
                    "work_id",
                    "provider_id",
                    "profile_id",
                ]:
                    if str(handoff.get(key, "")) != (row.get(key) or "").strip():
                        errors.append(
                            f"specialist_exchange {handoff_id} handoff {key} mismatch"
                        )
                if str(handoff.get("attempt", "")) != (row.get("attempt") or "").strip():
                    errors.append(
                        f"specialist_exchange {handoff_id} handoff attempt mismatch"
                    )
                if str(handoff.get("contract_version", "")) != (
                    row.get("contract_version") or ""
                ).strip():
                    errors.append(
                        f"specialist_exchange {handoff_id} handoff contract mismatch"
                    )
                descriptor_ref = handoff.get("descriptor_ref")
                handoff_descriptor_sha = (
                    str(descriptor_ref.get("sha256", ""))
                    if isinstance(descriptor_ref, dict)
                    else ""
                )
                if handoff_descriptor_sha != (row.get("descriptor_sha256") or "").strip():
                    errors.append(
                        f"specialist_exchange {handoff_id} descriptor hash mismatch"
                    )
                expected_compatibility = (
                    "compatible" if isinstance(descriptor_ref, dict) else "unverified"
                )
                if (row.get("compatibility_status") or "").strip() != expected_compatibility:
                    errors.append(
                        f"specialist_exchange {handoff_id} compatibility status mismatch"
                    )
        baseline_rel = (row.get("baseline_path") or "").strip()
        try:
            baseline_path = project_contained_path(
                project, baseline_rel, f"specialist_exchange {handoff_id} baseline"
            )
        except ValueError as exc:
            errors.append(str(exc))
            baseline_path = Path()
        baseline_sha = (row.get("baseline_sha256") or "").strip()
        baseline_payload: dict[str, object] = {}
        baseline_manifest_sha = ""
        if not baseline_path.is_file() or file_sha256(baseline_path) != baseline_sha:
            errors.append(f"specialist_exchange {handoff_id} baseline missing or hash mismatch")
        else:
            try:
                loaded_baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                errors.append(f"specialist_exchange {handoff_id} baseline invalid JSON")
            else:
                if not isinstance(loaded_baseline, dict):
                    errors.append(
                        f"specialist_exchange {handoff_id} baseline must be an object"
                    )
                else:
                    baseline_payload = loaded_baseline
                    baseline_files = baseline_payload.get("files")
                    if not isinstance(baseline_files, dict) or not all(
                        isinstance(key, str) and isinstance(value, str)
                        for key, value in baseline_files.items()
                    ):
                        errors.append(
                            f"specialist_exchange {handoff_id} baseline files are invalid"
                        )
                    else:
                        baseline_manifest_sha = specialist_manifest_digest(
                            {str(key): str(value) for key, value in baseline_files.items()}
                        )
                        if baseline_payload.get("manifest_sha256") != baseline_manifest_sha:
                            errors.append(
                                f"specialist_exchange {handoff_id} baseline manifest hash mismatch"
                            )
                    if baseline_payload.get("handoff_id") != handoff_id:
                        errors.append(
                            f"specialist_exchange {handoff_id} baseline handoff_id mismatch"
                        )
                    baseline_created_at = str(baseline_payload.get("created_at", ""))
                    row_created_at = (row.get("created_at") or "").strip()
                    row_updated_at = (row.get("updated_at") or "").strip()
                    if (
                        not baseline_created_at
                        or row_created_at != baseline_created_at
                        or not threadops_timestamp_is_aware(row_created_at)
                        or not threadops_timestamp_is_aware(row_updated_at)
                    ):
                        errors.append(
                            f"specialist_exchange {handoff_id} index timestamp binding mismatch"
                        )
                    if not (row.get("adoption_decision") or "").strip() and (
                        row_updated_at != row_created_at
                    ):
                        errors.append(
                            f"specialist_exchange {handoff_id} pending index updated_at mismatch"
                        )
        if handoff_payload:
            handoff_scope = handoff_payload.get("scope")
            baseline_ref = (
                handoff_scope.get("host_baseline")
                if isinstance(handoff_scope, dict)
                else None
            )
            if not isinstance(baseline_ref, dict):
                errors.append(
                    f"specialist_exchange {handoff_id} handoff baseline reference missing"
                )
            else:
                if baseline_ref.get("path") != baseline_rel:
                    errors.append(
                        f"specialist_exchange {handoff_id} handoff baseline path mismatch"
                    )
                if baseline_ref.get("sha256") != baseline_sha:
                    errors.append(
                        f"specialist_exchange {handoff_id} handoff baseline sha mismatch"
                    )
                if (
                    not baseline_manifest_sha
                    or baseline_ref.get("manifest_sha256") != baseline_manifest_sha
                ):
                    errors.append(
                        f"specialist_exchange {handoff_id} handoff baseline manifest mismatch"
                    )
        if (row.get("execution_mode") or "").strip() == "codex_thread":
            thread_id = (row.get("thread_id") or "").strip()
            if not THREADOPS_REAL_THREAD_ID_PATTERN.fullmatch(thread_id):
                errors.append(f"specialist_exchange {handoff_id} invalid_worker_thread_id")
            if not (row.get("lane_id") or "").strip():
                errors.append(f"specialist_exchange {handoff_id} codex_thread missing lane_id")
        receipt_sha = (row.get("receipt_sha256") or "").strip()
        receipt_rel = (row.get("receipt_path") or "").strip()
        if handoff_payload:
            handoff_scope = handoff_payload.get("scope")
            if (
                not isinstance(handoff_scope, dict)
                or handoff_scope.get("receipt_path") != receipt_rel
            ):
                errors.append(
                    f"specialist_exchange {handoff_id} handoff receipt path mismatch"
                )
            handoff_execution = handoff_payload.get("execution")
            if not isinstance(handoff_execution, dict):
                errors.append(
                    f"specialist_exchange {handoff_id} handoff execution binding missing"
                )
            else:
                for payload_key, row_key in [
                    ("mode", "execution_mode"),
                    ("lane_id", "lane_id"),
                    ("thread_id", "thread_id"),
                ]:
                    if str(handoff_execution.get(payload_key) or "") != (
                        row.get(row_key) or ""
                    ).strip():
                        errors.append(
                            f"specialist_exchange {handoff_id} handoff {payload_key} mismatch"
                        )
        if receipt_sha:
            if "\\" in receipt_rel or project_relative_path_has_symlink_component(
                project, receipt_rel
            ):
                errors.append(
                    f"specialist_exchange {handoff_id} receipt path must be non-symlink POSIX"
                )
            receipt_lexical = project / receipt_rel
            if receipt_lexical.is_file():
                receipt_stat = receipt_lexical.stat()
                if receipt_stat.st_size == 0 or receipt_stat.st_nlink != 1:
                    errors.append(
                        f"specialist_exchange {handoff_id} receipt must be non-empty and not hardlinked"
                    )
            try:
                receipt_path = project_contained_path(
                    project, receipt_rel, f"specialist_exchange {handoff_id} receipt"
                )
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if not receipt_path.is_file():
                errors.append(f"specialist_exchange {handoff_id} receipt file missing")
            else:
                if file_sha256(receipt_path) != receipt_sha:
                    errors.append(f"specialist_exchange {handoff_id} receipt hash mismatch")
                try:
                    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    errors.append(
                        f"specialist_exchange {handoff_id} receipt invalid JSON"
                    )
                else:
                    for issue in specialist_schema_errors("receipt", receipt):
                        errors.append(
                            f"specialist_exchange {handoff_id} receipt schema: {issue}"
                        )
                    if isinstance(receipt, dict) and handoff_payload:
                        receipt_payload = receipt
                        if receipt.get("outcome") != (row.get("outcome") or "").strip():
                            errors.append(
                                f"specialist_exchange {handoff_id} receipt outcome mismatch"
                            )
                        if receipt.get("handoff_sha256") != actual_handoff_sha:
                            errors.append(
                                f"specialist_exchange {handoff_id} receipt handoff hash mismatch"
                            )
                        for key in [
                            "exchange_id",
                            "handoff_id",
                            "work_id",
                            "provider_id",
                            "profile_id",
                        ]:
                            if receipt.get(key) != handoff_payload.get(key):
                                errors.append(
                                    f"specialist_exchange {handoff_id} receipt {key} mismatch"
                                )
                        descriptor_ref = handoff_payload.get("descriptor_ref")
                        descriptor_sha = (
                            str(descriptor_ref.get("sha256", ""))
                            if isinstance(descriptor_ref, dict)
                            else ""
                        )
                        if receipt.get("descriptor_sha256") != descriptor_sha:
                            errors.append(
                                f"specialist_exchange {handoff_id} receipt descriptor hash mismatch"
                            )
                        for issue in specialist_receipt_semantic_errors(
                            project, handoff_payload, receipt
                        ):
                            errors.append(
                                f"specialist_exchange {handoff_id} receipt semantics: {issue}"
                            )
        adoption_decision = (row.get("adoption_decision") or "").strip()
        if adoption_decision and adoption_decision not in {
            "adopt",
            "partial_adopt",
            "reject",
            "defer",
        }:
            errors.append(f"specialist_exchange {handoff_id} invalid adoption_decision")
        if adoption_decision in {"adopt", "partial_adopt"} and (row.get("compatibility_status") or "").strip() != "compatible":
            errors.append(f"specialist_exchange {handoff_id} adopted without compatible descriptor")
        adoption_rel = (row.get("adoption_path") or "").strip()
        if adoption_decision:
            try:
                adoption_path = project_contained_path(
                    project, adoption_rel, f"specialist_exchange {handoff_id} adoption"
                )
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if not adoption_rel or not adoption_path.is_file():
                errors.append(f"specialist_exchange {handoff_id} adoption record missing")
            else:
                expected_adoption_sha = (row.get("adoption_sha256") or "").strip()
                if (
                    not expected_adoption_sha
                    or file_sha256(adoption_path) != expected_adoption_sha
                ):
                    errors.append(
                        f"specialist_exchange {handoff_id} adoption hash mismatch"
                    )
                try:
                    adoption = json.loads(adoption_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    errors.append(f"specialist_exchange {handoff_id} adoption record invalid JSON")
                else:
                    for issue in specialist_schema_errors("adoption", adoption):
                        errors.append(
                            f"specialist_exchange {handoff_id} adoption schema: {issue}"
                        )
                    if adoption.get("receipt_sha256") != receipt_sha:
                        errors.append(f"specialist_exchange {handoff_id} adoption receipt hash mismatch")
                    if adoption.get("decision_owner") != "adco":
                        errors.append(f"specialist_exchange {handoff_id} adoption owner is not adco")
                    if adoption.get("handoff_id") != handoff_id:
                        errors.append(
                            f"specialist_exchange {handoff_id} adoption handoff_id mismatch"
                        )
                    if (
                        not receipt_payload
                        or adoption.get("receipt_id") != receipt_payload.get("receipt_id")
                    ):
                        errors.append(
                            f"specialist_exchange {handoff_id} adoption receipt_id mismatch"
                        )
                    if adoption.get("decision") != adoption_decision:
                        errors.append(
                            f"specialist_exchange {handoff_id} adoption decision mismatch"
                        )
                    outcome = str(receipt_payload.get("outcome", ""))
                    if adoption_decision == "adopt" and outcome != "completed":
                        errors.append(
                            f"specialist_exchange {handoff_id} full adoption requires completed outcome"
                        )
                    if (
                        adoption_decision in {"adopt", "partial_adopt"}
                        and outcome in {"blocked", "failed"}
                    ):
                        errors.append(
                            f"specialist_exchange {handoff_id} blocked/failed receipt was adopted"
                        )
                    adopted_outputs = adoption.get("adopted_outputs")
                    receipt_output_by_id = {
                        str(item.get("provider_artifact_id", "")): item
                        for item in receipt_payload.get("output_artifacts", [])
                        if isinstance(item, dict)
                        and str(item.get("provider_artifact_id", ""))
                    }
                    adopted_ids: list[str] = []
                    if not isinstance(adopted_outputs, list):
                        errors.append(
                            f"specialist_exchange {handoff_id} adoption outputs are invalid"
                        )
                    else:
                        for item in adopted_outputs:
                            if not isinstance(item, dict):
                                errors.append(
                                    f"specialist_exchange {handoff_id} adoption output entry is invalid"
                                )
                                continue
                            provider_artifact_id = str(
                                item.get("provider_artifact_id", "")
                            )
                            adopted_ids.append(provider_artifact_id)
                            receipt_output = receipt_output_by_id.get(provider_artifact_id)
                            if (
                                not isinstance(receipt_output, dict)
                                or item.get("sha256") != receipt_output.get("sha256")
                            ):
                                errors.append(
                                    f"specialist_exchange {handoff_id} adopted output binding mismatch: {provider_artifact_id}"
                                )
                            target_rel = str(item.get("target_path", ""))
                            if "\\" in target_rel or project_relative_path_has_symlink_component(
                                project, target_rel
                            ):
                                errors.append(
                                    f"specialist_exchange {handoff_id} adopted target path is unsafe: {target_rel}"
                                )
                                continue
                            try:
                                target_path = project_contained_path(
                                    project,
                                    target_rel,
                                    f"specialist_exchange {handoff_id} adopted target",
                                )
                            except ValueError as exc:
                                errors.append(str(exc))
                                continue
                            if not target_path.is_file():
                                errors.append(
                                    f"specialist_exchange {handoff_id} adopted target is missing: {target_rel}"
                                )
                            else:
                                target_stat = target_path.stat()
                                if (
                                    target_stat.st_size == 0
                                    or target_stat.st_nlink != 1
                                    or file_sha256(target_path) != item.get("sha256")
                                ):
                                    errors.append(
                                        f"specialist_exchange {handoff_id} adopted target hash/inode mismatch: {target_rel}"
                                    )
                    if len(adopted_ids) != len(set(adopted_ids)):
                        errors.append(
                            f"specialist_exchange {handoff_id} adoption repeats provider output"
                        )
                    adopted_id_set = set(adopted_ids)
                    receipt_output_ids = set(receipt_output_by_id)
                    if adoption_decision == "adopt" and adopted_id_set != receipt_output_ids:
                        errors.append(
                            f"specialist_exchange {handoff_id} full adoption output set mismatch"
                        )
                    if adoption_decision == "partial_adopt" and (
                        not adopted_id_set
                        or not adopted_id_set.issubset(receipt_output_ids)
                    ):
                        errors.append(
                            f"specialist_exchange {handoff_id} partial adoption output set mismatch"
                        )
                    if adoption_decision in {"reject", "defer"} and adopted_outputs not in (
                        [],
                        None,
                    ):
                        errors.append(
                            f"specialist_exchange {handoff_id} reject/defer adoption contains outputs"
                        )
                    rejected_outputs = adoption.get("rejected_outputs")
                    if (
                        not isinstance(rejected_outputs, list)
                        or set(str(item) for item in rejected_outputs)
                        != receipt_output_ids - adopted_id_set
                    ):
                        errors.append(
                            f"specialist_exchange {handoff_id} rejected output set mismatch"
                        )
                    execution = handoff_payload.get("execution")
                    if (
                        isinstance(execution, dict)
                        and execution.get("workspace_mode") == "read_only"
                        and adoption_decision not in {"reject", "defer"}
                    ):
                        errors.append(
                            f"specialist_exchange {handoff_id} read_only return must be deferred or rejected"
                        )
                    gate_effect = adoption.get("gate_effect")
                    expected_advance = outcome == "completed" and adoption_decision in {
                        "adopt",
                        "partial_adopt",
                    }
                    if (
                        not isinstance(gate_effect, dict)
                        or gate_effect.get("advance_allowed") is not expected_advance
                    ):
                        errors.append(
                            f"specialist_exchange {handoff_id} adoption gate advance mismatch"
                        )
                    host_proof = adoption.get("host_scope_proof")
                    if not isinstance(host_proof, dict) or host_proof.get("changed_paths") != []:
                        errors.append(
                            f"specialist_exchange {handoff_id} adoption lacks clean host scope proof"
                        )
                    elif (
                        host_proof.get("baseline_path") != baseline_rel
                        or host_proof.get("baseline_sha256") != baseline_sha
                        or host_proof.get("baseline_manifest_sha256")
                        != baseline_manifest_sha
                        or host_proof.get("observed_manifest_sha256")
                        != baseline_manifest_sha
                    ):
                        errors.append(
                            f"specialist_exchange {handoff_id} adoption host baseline binding mismatch"
                        )
                    if (
                        (row.get("execution_mode") or "").strip() == "codex_thread"
                        and adoption_decision in {"adopt", "partial_adopt"}
                        and not adoption.get("thread_reconciliation_ref")
                    ):
                        errors.append(
                            f"specialist_exchange {handoff_id} adoption lacks thread reconciliation ref"
                        )
    return errors


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
    sections = re.findall(
        r"(?ims)^##[ \t]+Current Version Truth[ \t]*\n(.*?)(?=^##[ \t]+|\Z)",
        text,
    )
    if len(sections) != 1:
        return ""
    pattern = re.compile(
        rf"^[ \t]*{re.escape(key)}[ \t]*:[ \t]*(.*?)[ \t]*$", re.MULTILINE
    )
    matches = pattern.findall(sections[0])
    if len(matches) != 1:
        return ""
    value = matches[0].strip()
    return "" if value in {"TBD", "todo", "pending"} else value


def current_truth_structure_errors(text: str) -> list[str]:
    sections = re.findall(
        r"(?ims)^##[ \t]+Current Version Truth[ \t]*\n(.*?)(?=^##[ \t]+|\Z)",
        text,
    )
    if len(sections) != 1:
        return [
            "current_truth must contain exactly one '## Current Version Truth' section"
        ]
    errors: list[str] = []
    for key in [
        "current_version_id",
        "current_pptx_artifact_id",
        "current_pdf_artifact_id",
        "current_preview_artifact_id",
        "current_text_extract_artifact_id",
        "current_ppt_editability_artifact_id",
        "version_map_status",
        "last_archive_before_edit",
    ]:
        count = len(
            re.findall(
                rf"(?m)^[ \t]*{re.escape(key)}[ \t]*:", sections[0]
            )
        )
        if count != 1:
            errors.append(
                f"current_truth Current Version Truth key {key} appears {count} times"
            )
    return errors


def validate_gate_history(
    project: Path, gate_log: list[dict[str, str]]
) -> list[str]:
    errors: list[str] = []
    seen_runs: dict[str, dict[str, str]] = {}
    previous_by_gate: dict[str, str] = {}
    for row in gate_log:
        gate_id = row.get("gate_id", "").strip() or "<missing>"
        run_id = row.get("gate_run_id", "").strip() or "<missing>"
        owner = f"gate_log {run_id}"
        supersedes = row.get("supersedes_gate_run_id", "").strip()
        expected_previous = previous_by_gate.get(gate_id, "")
        if supersedes != expected_previous:
            errors.append(
                f"{owner} supersedes_gate_run_id does not match previous run for {gate_id}"
            )
        if supersedes:
            previous = seen_runs.get(supersedes)
            if not previous or previous.get("gate_id", "").strip() != gate_id:
                errors.append(f"{owner} supersedes missing or different gate run")
        created_at = row.get("created_at", "").strip()
        if created_at and not threadops_timestamp_is_aware(created_at):
            errors.append(f"{owner} created_at is not timezone-aware ISO-8601")
        target_ref = row.get("target_ref", "").strip()
        target_sha = row.get("target_sha256", "").strip()
        if bool(target_ref) != bool(target_sha):
            errors.append(f"{owner} gate target_ref/target_sha256 must be paired")
        elif target_ref:
            if not re.fullmatch(r"[0-9a-f]{64}", target_sha):
                errors.append(f"{owner} target_sha256 is invalid")
            try:
                target = project_contained_path(project, target_ref, f"{owner} target")
            except ValueError as exc:
                errors.append(str(exc))
            else:
                if not target.is_file():
                    errors.append(f"{owner} target file missing: {target_ref}")
        snapshot_ref = row.get("evidence_snapshot_ref", "").strip()
        snapshot_sha = row.get("evidence_snapshot_sha256", "").strip()
        if bool(snapshot_ref) != bool(snapshot_sha):
            errors.append(f"{owner} evidence snapshot path/hash must be paired")
        elif snapshot_ref:
            if not re.fullmatch(r"[0-9a-f]{64}", snapshot_sha):
                errors.append(f"{owner} evidence snapshot sha256 is invalid")
            try:
                snapshot = project_contained_path(
                    project, snapshot_ref, f"{owner} evidence snapshot"
                )
            except ValueError as exc:
                errors.append(str(exc))
            else:
                if not snapshot.is_file() or file_sha256(snapshot) != snapshot_sha:
                    errors.append(f"{owner} immutable evidence snapshot missing or changed")
        if run_id != "<missing>":
            seen_runs[run_id] = row
        if gate_id != "<missing>" and run_id != "<missing>":
            previous_by_gate[gate_id] = run_id
    return errors


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def final_delivery_project_path(
    project: Path, raw_path: str, *, require_file: bool = False
) -> tuple[str, Path]:
    raw = (raw_path or "").strip().strip("`")
    candidate = Path(raw)
    if not raw or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"FinalDelivery path must be project-relative: {raw_path}")
    rel = unicodedata.normalize("NFC", candidate.as_posix())
    relative = Path(rel)
    if not relative.parts or relative.parts[0] != "05_最终交付_FinalDelivery":
        raise ValueError(f"FinalDelivery path is outside FinalDelivery: {raw_path}")
    if project_relative_path_has_symlink_component(project, rel):
        raise ValueError(f"FinalDelivery path contains a symlink component: {raw_path}")
    lexical = project / relative
    resolved = lexical.resolve()
    try:
        resolved.relative_to((project / "05_最终交付_FinalDelivery").resolve())
        resolved.relative_to(project.resolve())
    except ValueError as exc:
        raise ValueError(f"FinalDelivery path escapes the protected root: {raw_path}") from exc
    if require_file and (not lexical.is_file() or lexical.is_symlink()):
        raise ValueError(f"FinalDelivery path is not a regular file: {raw_path}")
    return rel, lexical


def final_delivery_human_identity_valid(value: str) -> bool:
    identity = value.strip()
    if len(re.sub(r"\s+", "", identity)) < 2:
        return False
    if identity.lower() in {"-", "tbd", "todo", "pending", "unknown", "n/a"}:
        return False
    normalized = re.sub(r"[^a-z0-9]+", "_", identity.lower()).strip("_")
    if "main_controller" in normalized or normalized == "maincontroller":
        return False
    tokens = {token for token in normalized.split("_") if token}
    if tokens & {
        "adco",
        "assistant",
        "automation",
        "agent",
        "bot",
        "chatgpt",
        "claude",
        "codex",
        "gemini",
        "model",
        "system",
        "worker",
        "ai",
    }:
        return False
    return not any(token in identity for token in ("自动化", "机器人", "系统代理", "执行代理"))


def final_delivery_evidence_binding_valid(
    project: Path, row: dict[str, str]
) -> bool:
    raw = (row.get("evidence_ref") or "").strip().strip("`")
    candidate = Path(raw)
    if not raw or candidate.is_absolute() or ".." in candidate.parts:
        return False
    rel = unicodedata.normalize("NFC", candidate.as_posix())
    if project_relative_path_has_symlink_component(project, rel):
        return False
    path = project / rel
    try:
        path.resolve().relative_to(project.resolve())
    except ValueError:
        return False
    if not path.is_file() or path.is_symlink() or path.stat().st_nlink != 1:
        return False
    expected_sha = (row.get("evidence_sha256") or "").strip()
    return bool(
        re.fullmatch(r"[0-9a-f]{64}", expected_sha)
        and file_sha256(path) == expected_sha
    )


def final_delivery_artifact_for_path(
    project: Path, rel_path: str, *, require_active: bool
) -> dict[str, str] | None:
    artifacts = load_optional_csv(
        project / "AD-creative/orchestrator/artifact_index.csv", []
    )
    matches: list[dict[str, str]] = []
    for row in artifacts:
        try:
            artifact_rel, _ = final_delivery_project_path(
                project, row.get("path") or row.get("original_path") or ""
            )
        except ValueError:
            continue
        if artifact_rel != rel_path:
            continue
        if require_active and normalized_artifact_lifecycle(row) != "active":
            continue
        matches.append(row)
    return matches[0] if len(matches) == 1 else None


def final_delivery_old_version_id(
    project: Path, old_row: dict[str, str]
) -> str:
    try:
        old_rel, _ = final_delivery_project_path(
            project, (old_row.get("path") or "").strip()
        )
    except ValueError:
        return ""
    artifact = final_delivery_artifact_for_path(
        project, old_rel, require_active=False
    )
    if not artifact:
        return ""
    artifact_id = (artifact.get("artifact_id") or "").strip()
    versions = load_optional_csv(
        project / "AD-creative/orchestrator/version_map.csv", []
    )
    explicit = (old_row.get("version_id") or "").strip()
    matches = [
        row
        for row in versions
        if (row.get("artifact_id") or "").strip() == artifact_id
        and (not explicit or (row.get("version_id") or "").strip() == explicit)
    ]
    return (
        (matches[0].get("version_id") or "").strip()
        if artifact_id and len(matches) == 1
        else ""
    )


def final_delivery_host_attestation_binding(
    project: Path,
    *,
    attestation_ref: str,
    confirmation_receipt_ref: str,
    confirmation_receipt_sha256: str,
) -> tuple[str, str] | None:
    raw = (attestation_ref or "").strip().strip("`")
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    rel = unicodedata.normalize("NFC", candidate.as_posix())
    if not rel.startswith(FINAL_DELIVERY_HOST_ATTESTATION_ROOT.as_posix() + "/"):
        return None
    if project_relative_path_has_symlink_component(project, rel):
        return None
    path = project / rel
    try:
        path.resolve().relative_to(project.resolve())
    except ValueError:
        return None
    if not path.is_file() or path.is_symlink() or path.stat().st_nlink != 1:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict):
        return None
    expected = {
        "protocol_id": FINAL_DELIVERY_HOST_ATTESTATION_PROTOCOL,
        "schema_version": FINAL_DELIVERY_HOST_ATTESTATION_VERSION,
        "attestation_scope": "final_delivery_reconciliation",
        "attestation_role": "host_main_thread",
        "verified_by": "main_controller",
        "readback_status": "verified",
        "readback_tool": "codex_app.read_thread",
        "confirmation_receipt_ref": confirmation_receipt_ref,
        "confirmation_receipt_sha256": confirmation_receipt_sha256,
    }
    if any(
        str(payload.get(key, "")).strip() != value
        for key, value in expected.items()
    ):
        return None
    if str(payload.get("authority", "")).strip() not in {
        "user",
        "client",
        "project_owner",
    }:
        return None
    if len(str(payload.get("attestation_id", "")).strip()) < 8:
        return None
    if not threadops_timestamp_is_aware(str(payload.get("verified_at", ""))):
        return None
    if not THREADOPS_REAL_THREAD_ID_PATTERN.fullmatch(
        str(payload.get("thread_id", "")).strip()
    ):
        return None
    if len(str(payload.get("user_message_id", "")).strip()) < 8:
        return None
    if not re.fullmatch(
        r"[0-9a-f]{64}", str(payload.get("user_message_sha256", "")).strip()
    ):
        return None
    return rel, file_sha256(path)


def final_delivery_confirmation_receipt_valid(
    project: Path,
    *,
    old_row: dict[str, str],
    new_row: dict[str, str],
    kind: str,
) -> bool:
    if not final_delivery_evidence_binding_valid(project, new_row):
        return False
    evidence_rel = (new_row.get("evidence_ref") or "").strip().strip("`")
    evidence_path = project / evidence_rel
    try:
        payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError):
        return False
    if not isinstance(payload, dict):
        return False
    try:
        old_rel, _ = final_delivery_project_path(
            project, (old_row.get("path") or "").strip()
        )
        new_rel, new_path = final_delivery_project_path(
            project, (new_row.get("path") or "").strip(), require_file=True
        )
    except ValueError:
        return False
    new_artifact = final_delivery_artifact_for_path(
        project, new_rel, require_active=True
    )
    new_artifact_id = (
        (new_artifact.get("artifact_id") or "").strip()
        if new_artifact
        else ""
    )
    old_version_id = (
        final_delivery_old_version_id(project, old_row)
        if kind == "supersession"
        else ""
    )
    if kind == "supersession" and not old_version_id:
        return False
    expected = {
        "protocol_id": FINAL_DELIVERY_CONFIRMATION_PROTOCOL,
        "schema_version": FINAL_DELIVERY_CONFIRMATION_VERSION,
        "confirmation_scope": "final_delivery_reconciliation",
        "decision": "approve_reconciliation",
        "confirmed_by": (new_row.get("confirmed_by") or "").strip(),
        "confirmed_at": (new_row.get("confirmed_at") or "").strip(),
        "reconciliation_kind": kind,
        "old_lock_id": (old_row.get("lock_id") or "").strip(),
        "old_path": old_rel,
        "old_sha256": (old_row.get("sha256") or "").strip(),
        "new_path": new_rel,
        "new_sha256": file_sha256(new_path),
        "new_artifact_id": new_artifact_id,
        "version_id": (new_row.get("version_id") or "").strip(),
        "supersedes_version_id": old_version_id,
    }
    if any(
        str(payload.get(key, "")).strip() != expected_value
        for key, expected_value in expected.items()
    ):
        return False
    confirmation_id = str(payload.get("confirmation_id", "")).strip()
    source_event_id = str(payload.get("source_event_id", "")).strip()
    if len(confirmation_id) < 8 or not source_event_id:
        return False
    source_events = load_optional_csv(
        project / "AD-creative/orchestrator/source_events.csv", []
    )
    sources = [
        row
        for row in source_events
        if (row.get("source_event_id") or "").strip() == source_event_id
    ]
    if len(sources) != 1:
        return False
    source = sources[0]
    if (source.get("source_type") or "").strip().lower() != "file":
        return False
    if (source.get("source_owner") or "").strip().casefold() != (
        new_row.get("confirmed_by") or ""
    ).strip().casefold():
        return False
    if (source.get("declared_semantics") or "").strip().lower() not in {
        "approval",
        "confirmation",
        "final_delivery_reconciliation",
    }:
        return False
    if (source.get("trust_level") or "").strip().lower() not in {
        "confirmed",
        "user_confirmed",
        "client_confirmed",
    }:
        return False
    source_paths = {
        unicodedata.normalize("NFC", Path(value).as_posix())
        for value in split_ids(source.get("file_paths"))
        if value and not Path(value).is_absolute() and ".." not in Path(value).parts
    }
    if source_paths != {evidence_rel}:
        return False
    if new_artifact_id and new_artifact_id not in set(
        split_ids(source.get("affects_artifacts"))
    ):
        return False
    host_binding = final_delivery_host_attestation_binding(
        project,
        attestation_ref=str(payload.get("host_attestation_ref", "")).strip(),
        confirmation_receipt_ref=evidence_rel,
        confirmation_receipt_sha256=(new_row.get("evidence_sha256") or "").strip(),
    )
    if not host_binding:
        return False
    host_rel, host_sha = host_binding
    if (
        (new_row.get("host_attestation_ref") or "").strip() != host_rel
        or (new_row.get("host_attestation_sha256") or "").strip() != host_sha
    ):
        return False
    return True


def final_delivery_version_binding_valid(
    project: Path, rel_path: str, version_id: str
) -> bool:
    version_id = version_id.strip()
    if not version_id:
        return False
    artifacts = load_optional_csv(
        project / "AD-creative/orchestrator/artifact_index.csv", []
    )
    artifact_matches: list[dict[str, str]] = []
    for row in artifacts:
        try:
            artifact_rel, _ = final_delivery_project_path(
                project, row.get("path") or row.get("original_path") or ""
            )
        except ValueError:
            continue
        if (
            artifact_rel == rel_path
            and normalized_artifact_lifecycle(row) == "active"
        ):
            artifact_matches.append(row)
    if len(artifact_matches) != 1:
        return False
    artifact_id = (artifact_matches[0].get("artifact_id") or "").strip()
    versions = load_optional_csv(
        project / "AD-creative/orchestrator/version_map.csv", []
    )
    version_matches = [
        row for row in versions if (row.get("version_id") or "").strip() == version_id
    ]
    if not artifact_id or len(version_matches) != 1:
        return False
    truth_path = project / "AD-creative/orchestrator/current_truth.md"
    truth_text = truth_path.read_text(encoding="utf-8") if truth_path.is_file() else ""
    truth_version_matches = current_truth_value(truth_text, "current_version_id") == version_id
    version = version_matches[0]
    version_artifact_id = (version.get("artifact_id") or "").strip()
    if (version.get("status") or "").strip().lower() != "current":
        return False
    if not truth_version_matches:
        return False
    if version_artifact_id != artifact_id:
        return False
    artifact_type = (artifact_matches[0].get("artifact_type") or "").strip().lower()
    truth_key_by_type = {
        "pptx": "current_pptx_artifact_id",
        "pdf": "current_pdf_artifact_id",
        "preview": "current_preview_artifact_id",
        "deck_preview": "current_preview_artifact_id",
        "png_preview": "current_preview_artifact_id",
        "jpg_preview": "current_preview_artifact_id",
        "text_extract": "current_text_extract_artifact_id",
        "ppt_text_extract": "current_text_extract_artifact_id",
        "ppt_editability_check": "current_ppt_editability_artifact_id",
    }
    truth_key = truth_key_by_type.get(artifact_type, "")
    if not truth_key or current_truth_value(truth_text, truth_key) != artifact_id:
        return False
    return True


def final_delivery_supersession_chain_valid(
    project: Path, old_row: dict[str, str], new_version_id: str
) -> bool:
    old_version_id = final_delivery_old_version_id(project, old_row)
    if not old_version_id:
        return False
    versions = load_optional_csv(
        project / "AD-creative/orchestrator/version_map.csv", []
    )
    matches = [
        row
        for row in versions
        if (row.get("version_id") or "").strip() == new_version_id.strip()
    ]
    return bool(
        len(matches) == 1
        and (matches[0].get("supersedes_version_id") or "").strip()
        == old_version_id
    )


def final_delivery_reconciliation_valid(
    project: Path,
    rows_by_path: dict[str, dict[str, str]],
    old_row: dict[str, str],
) -> bool:
    old_lock_id = (old_row.get("lock_id") or "").strip()
    if not old_lock_id:
        return False
    candidates = [
        row
        for row in rows_by_path.values()
        if (row.get("reconciles_lock_id") or "").strip() == old_lock_id
    ]
    if len(candidates) != 1:
        return False
    new_row = candidates[0]
    if not (
        (new_row.get("protected") or "").strip().lower() in {"yes", "true", "1"}
        and (new_row.get("reconciliation_state") or "").strip().lower()
        == "reconciled"
        and final_delivery_human_identity_valid(
            (new_row.get("confirmed_by") or "").strip()
        )
        and (new_row.get("confirmed_at") or "").strip()
    ):
        return False
    if not threadops_timestamp_is_aware((new_row.get("confirmed_at") or "").strip()):
        return False
    try:
        new_rel, path = final_delivery_project_path(
            project, (new_row.get("path") or "").strip(), require_file=True
        )
        final_delivery_project_path(project, (old_row.get("path") or "").strip())
    except ValueError:
        return False
    actual_sha = file_sha256(path)
    if actual_sha != (new_row.get("sha256") or "").strip():
        return False
    kind = (new_row.get("reconciliation_kind") or "").strip().lower()
    if not final_delivery_confirmation_receipt_valid(
        project, old_row=old_row, new_row=new_row, kind=kind
    ):
        return False
    old_version_id = (
        final_delivery_old_version_id(project, old_row)
        if kind == "supersession"
        else ""
    )
    if (new_row.get("supersedes_version_id") or "").strip() != old_version_id:
        return False
    old_sha = (old_row.get("sha256") or "").strip()
    if kind == "rename":
        return actual_sha == old_sha
    if kind == "supersession":
        return (
            actual_sha != old_sha
            and bool((new_row.get("version_id") or "").strip())
            and (new_row.get("supersedes_lock_id") or "").strip() == old_lock_id
            and final_delivery_version_binding_valid(
                project, new_rel, (new_row.get("version_id") or "").strip()
            )
            and final_delivery_supersession_chain_valid(
                project, old_row, (new_row.get("version_id") or "").strip()
            )
        )
    return False


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


def delivery_artifact_format_error(
    artifact_type: str,
    path: Path,
    *,
    current_pptx_sha256: str = "",
) -> str:
    try:
        if artifact_type == "pptx":
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())
            if "ppt/presentation.xml" not in names or not any(
                name.startswith("ppt/slides/slide") and name.endswith(".xml")
                for name in names
            ):
                return "PPTX package lacks presentation/slides XML"
        elif artifact_type == "pdf":
            data = path.read_bytes()
            if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-2048:]:
                return "PDF signature or EOF marker is invalid"
        elif artifact_type in {"preview", "deck_preview", "png_preview", "jpg_preview"}:
            data = path.read_bytes()
            is_png = data.startswith(b"\x89PNG\r\n\x1a\n") and b"IEND" in data[-64:]
            is_jpeg = data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9")
            if not (is_png or is_jpeg):
                return "preview is not a valid PNG/JPEG payload"
        elif artifact_type in {"text_extract", "ppt_text_extract"}:
            text = path.read_text(encoding="utf-8")
            if not text.strip() or "\x00" in text:
                return "text extract is empty or binary"
        elif artifact_type == "ppt_editability_check":
            text = path.read_text(encoding="utf-8")
            if not re.search(r"(?im)^status:\s*PASS\s*$", text):
                return "editability report status is not PASS"
            if not re.search(r"(?im)^sha256:\s*[0-9a-f]{64}\s*$", text):
                return "editability report lacks PPTX sha256"
            if current_pptx_sha256 and current_pptx_sha256 not in text:
                return "editability report is not bound to current PPTX hash"
    except (OSError, UnicodeDecodeError, zipfile.BadZipFile) as exc:
        return f"cannot parse artifact: {exc}"
    return ""


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
    current_version_matches = [
        row for row in version_map if (row.get("version_id") or "").strip() == current_version_id
    ]
    current_version = current_version_matches[0] if len(current_version_matches) == 1 else None
    if current_version_id and not current_version:
        errors.append(
            f"client delivery current_version_id {current_version_id} does not match exactly one version_map row"
        )
    if current_version and (current_version.get("status") or "").strip().lower() not in {"active", "current"}:
        errors.append(
            f"client delivery current version status is not active/current: {current_version.get('status')}"
        )

    current_artifact_ids: set[str] = set()
    current_version_label = (current_version or {}).get("version", "").strip()
    current_pptx_artifact_id = current_truth_value(
        current_truth_text, "current_pptx_artifact_id"
    )
    current_pptx_row = row_by_id(artifacts, "artifact_id", current_pptx_artifact_id)
    current_pptx_sha = (current_pptx_row or {}).get("sha256", "") or ""
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
        rel_path = (artifact.get("path") or "").strip()
        if not rel_path:
            errors.append(f"client delivery artifact {artifact_id} missing path")
            continue
        try:
            path = project_contained_path(
                project, rel_path, f"client delivery artifact {artifact_id} path"
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not path.exists() or not path.is_file():
            errors.append(f"client delivery artifact {artifact_id} missing path {rel_path}")
            continue
        if not artifact.get("version", "").strip():
            errors.append(f"client delivery artifact {artifact_id} missing version")
        elif current_version_label and artifact.get("version", "").strip() != current_version_label:
            errors.append(
                f"client delivery artifact {artifact_id} version {artifact.get('version')} does not match current version {current_version_label}"
            )
        expected_sha = (artifact.get("sha256") or "").strip()
        expected_size = (artifact.get("size_bytes") or "").strip()
        if not expected_sha or not expected_size:
            errors.append(f"client delivery artifact {artifact_id} missing hash/size baseline")
        else:
            actual_sha = file_sha256(path)
            actual_size = str(path.stat().st_size)
            if actual_sha != expected_sha or actual_size != expected_size:
                errors.append(f"client delivery artifact {artifact_id} hash/size mismatch")
        format_error = delivery_artifact_format_error(
            artifact_type,
            path,
            current_pptx_sha256=current_pptx_sha,
        )
        if format_error:
            errors.append(f"client delivery artifact {artifact_id} invalid format: {format_error}")
        if current_key != "current_pptx_artifact_id":
            if (artifact.get("derived_from_artifact_id") or "").strip() != current_pptx_artifact_id:
                errors.append(
                    f"client delivery artifact {artifact_id} not derived from current PPTX artifact"
                )
            if current_pptx_sha and (artifact.get("derived_from_sha256") or "").strip() != current_pptx_sha:
                errors.append(
                    f"client delivery artifact {artifact_id} not bound to current PPTX hash"
                )

    if current_version:
        version_artifact_id = current_version.get("artifact_id", "").strip()
        if not current_version.get("version", "").strip():
            errors.append("client delivery current version_map row missing version")
        if not version_artifact_id:
            errors.append("client delivery current version_map row missing artifact_id")
        elif version_artifact_id != current_pptx_artifact_id:
            errors.append(
                f"client delivery version_map artifact {version_artifact_id} is not the current PPTX artifact"
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


def _validate_strings(project: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    project = project.resolve()
    ad_root = project / "AD-creative"
    schema_v2 = False
    schema_path = project / CONTROL_PLANE_SCHEMA_REL
    if schema_path.is_file():
        try:
            schema_v2 = (
                json.loads(schema_path.read_text(encoding="utf-8")).get(
                    "schema_version"
                )
                == CONTROL_PLANE_SCHEMA_VERSION
            )
        except json.JSONDecodeError:
            schema_v2 = False

    for rel_path in REQUIRED_FILES:
        if not (project / rel_path).exists():
            errors.append(f"missing required file: {rel_path}")

    agents_policy_ok = check_agents_policy(project, errors)
    check_structured_files(project, errors)
    current_truth_path = ad_root / "orchestrator/current_truth.md"
    if current_truth_path.is_file():
        errors.extend(
            current_truth_structure_errors(
                current_truth_path.read_text(encoding="utf-8")
            )
        )

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
    client_outline = load_csv(ad_root / "client_review/client_outline.csv", errors)
    asset_current_manifest = load_csv(ad_root / "visual_assets/asset_current_manifest.csv", errors)
    asset_authorizations = load_csv(ad_root / "visual_assets/asset_authorizations.csv", errors)
    final_delivery_lock_rows = load_csv(ad_root / "orchestrator/final_delivery_lock.csv", errors)
    specialist_exchange_rows = load_csv(
        ad_root / "orchestrator/specialist_exchange/exchange_index.csv", errors
    )
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
    gate_run_ids = [
        row.get("gate_run_id", "").strip() for row in gate_log
    ]
    if any(not value for value in gate_run_ids):
        errors.append("gate_log row missing gate_run_id")
    for run_id in sorted(
        {value for value in gate_run_ids if value and gate_run_ids.count(value) > 1}
    ):
        errors.append(f"gate_log duplicate gate_run_id: {run_id}")
    errors.extend(validate_gate_history(project, gate_log))
    reference_ids = id_set(reference_cards, "reference_id")
    asset_ids = id_set(asset_manifest, "asset_id")
    current_asset_ids = id_set(asset_current_manifest, "asset_id")
    profile_subject_ids = id_set(profile_subjects, "subject_id")

    check_required_columns(errors, "client_outline", ad_root / "client_review/client_outline.csv", CLIENT_OUTLINE_FIELDS)
    check_required_columns(errors, "asset_current_manifest", ad_root / "visual_assets/asset_current_manifest.csv", ASSET_CURRENT_FIELDS)
    check_required_columns(errors, "asset_authorizations", ad_root / "visual_assets/asset_authorizations.csv", ASSET_AUTHORIZATION_FIELDS)
    check_required_columns(
        errors,
        "final_delivery_lock",
        ad_root / "orchestrator/final_delivery_lock.csv",
        FINAL_DELIVERY_LOCK_FIELDS if schema_v2 else FINAL_DELIVERY_LOCK_FIELDS[:8],
    )
    final_delivery_lock_ids = [
        (row.get("lock_id") or "").strip() for row in final_delivery_lock_rows
    ]
    for index, (row, lock_id) in enumerate(
        zip(final_delivery_lock_rows, final_delivery_lock_ids), start=2
    ):
        if not lock_id:
            errors.append(
                "FinalDelivery lock row missing lock_id: "
                f"row {index} path {(row.get('path') or '<blank>').strip()}"
            )
    for lock_id in sorted(
        {
            value
            for value in final_delivery_lock_ids
            if value and final_delivery_lock_ids.count(value) > 1
        }
    ):
        errors.append(f"FinalDelivery duplicate lock_id: {lock_id}")
    check_required_columns(
        errors,
        "artifact_index",
        ad_root / "orchestrator/artifact_index.csv",
        ARTIFACT_INDEX_FIELDS if schema_v2 else ARTIFACT_INDEX_FIELDS[:20],
    )
    check_required_columns(errors, "gate_log", ad_root / "orchestrator/gate_log.csv", GATE_LOG_FIELDS)
    check_required_columns(
        errors,
        "specialist_exchange",
        ad_root / "orchestrator/specialist_exchange/exchange_index.csv",
        SPECIALIST_EXCHANGE_INDEX_FIELDS,
    )
    errors.extend(validate_version_integrity(project, artifact_index, version_map))
    errors.extend(validate_specialist_exchange_index(project, specialist_exchange_rows))

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

    quarantined_thread_rows = [
        row
        for row in thread_registry_fields
        if (row.get("schema_state") or "").strip() == "legacy_quarantined"
    ]
    current_thread_rows = [
        row for row in thread_registry_fields if row not in quarantined_thread_rows
    ]
    quarantined_thread_ids = {
        (row.get("thread_id") or "").strip()
        for row in quarantined_thread_rows
        if (row.get("thread_id") or "").strip()
    }
    quarantined_work_lanes = {
        ((row.get("work_id") or "").strip(), (row.get("lane_id") or "").strip())
        for row in quarantined_thread_rows
    }
    threadops_enabled = bool(thread_registry_fields) or (
        ad_root / "orchestrator/thread_lane_plan.md"
    ).exists()
    if threadops_enabled:
        missing_threadops_registry_fields = [
            field
            for field in (
                THREADOPS_REGISTRY_FIELDS
                if schema_v2
                else THREADOPS_REGISTRY_FIELDS[:-4]
            )
            if field not in registry_fields
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
        lane_runs = [
            row.get("lane_run_id", "").strip()
            for row in current_thread_rows
            if row.get("lane_run_id", "").strip()
        ]
        for lane_run_id in sorted(
            {value for value in lane_runs if lane_runs.count(value) > 1}
        ):
            errors.append(f"thread_registry duplicate lane_run_id: {lane_run_id}")
        thread_ids = [
            value
            for row in current_thread_rows
            for value in [
                row.get("real_thread_id", "").strip(),
                row.get("rescue_thread_id", "").strip(),
            ]
            if value
        ]
        for thread_id in sorted(
            {value for value in thread_ids if thread_ids.count(value) > 1}
        ):
            errors.append(f"thread_registry duplicate real/rescue thread id: {thread_id}")
        for row in current_thread_rows:
            owner = f"thread_registry {row.get('thread_id', '').strip() or '<missing thread_id>'}"
            check_threadops_lane_contract(errors, owner, row)
            check_threadops_receipt_identity(project, errors, owner, row)
            check_threadops_execution_receipt(project, errors, owner, row)
            work_lane = (row.get("work_id", "").strip(), row.get("lane_id", "").strip())
            matching_runs = [
                run
                for run in agent_runs
                if (run.get("work_id", "").strip(), run.get("lane_id", "").strip()) == work_lane
            ]
            if len(matching_runs) != 1:
                errors.append(
                    f"{owner} expected exactly one matching agent_runs row; found {len(matching_runs)}"
                )
            else:
                run = matching_runs[0]
                if run.get("thread_id", "").strip() != row.get("thread_id", "").strip():
                    errors.append(f"{owner} agent_runs thread_id does not match registry")
                if run.get("receipt_path", "").strip() != row.get("receipt_path", "").strip():
                    errors.append(f"{owner} agent_runs receipt_path does not match registry")
                if normalize_threadops_status(run.get("reconciliation_status")) != normalize_threadops_status(row.get("reconciliation_status")):
                    errors.append(f"{owner} agent_runs reconciliation_status does not match registry")
        lane_plan_path = ad_root / "orchestrator/thread_lane_plan.md"
        if lane_plan_path.exists():
            lane_rows = parse_markdown_table_after_heading(
                lane_plan_path.read_text(encoding="utf-8"),
                "## Lane Map",
            )
            for row in lane_rows:
                owner = f"thread_lane_plan {row.get('lane_id', '').strip() or '<missing lane_id>'}"
                work_lane = (
                    row.get("work_id", "").strip(),
                    row.get("lane_id", "").strip(),
                )
                matching_registry_rows = [
                    registry_row
                    for registry_row in current_thread_rows
                    if (
                        registry_row.get("work_id", "").strip(),
                        registry_row.get("lane_id", "").strip(),
                    )
                    == work_lane
                ]
                if len(matching_registry_rows) != 1:
                    errors.append(
                        f"{owner} expected exactly one authoritative thread_registry row; "
                        f"found {len(matching_registry_rows)}"
                    )
                    continue
                authoritative = matching_registry_rows[0]
                projection_fields = {
                    "thread_id": "thread_id",
                    "lane_run_id": "lane_run_id",
                    "mode": "mode",
                    "environment": "environment",
                    "write_scope": "write_scope",
                    "receipt_path": "receipt_path",
                    "receipt_status": "receipt_status",
                    "reconciliation_status": "reconciliation_status",
                    "lifecycle_status": "lifecycle_state",
                }
                for plan_field, registry_field in projection_fields.items():
                    if row.get(plan_field, "").strip() != authoritative.get(
                        registry_field, ""
                    ).strip():
                        errors.append(
                            f"{owner} {plan_field} projection does not match thread_registry"
                        )
                check_threadops_lane_contract(errors, owner, authoritative)

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
        lifecycle = normalized_artifact_lifecycle(artifact)
        if (
            rel_path
            and not (project / rel_path).exists()
            and lifecycle not in ARTIFACT_INACTIVE_LIFECYCLE_VALUES
        ):
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
        work_lane = (work_id, (run.get("lane_id") or "").strip())
        if (
            (run.get("thread_id") or "").strip() in quarantined_thread_ids
            or work_lane in quarantined_work_lanes
        ):
            continue
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
        if rel_path and must_exist:
            try:
                asset_path = project_contained_path(
                    project, rel_path, f"asset {asset_id} path"
                )
            except ValueError as exc:
                errors.append(str(exc))
            else:
                if not asset_path.exists():
                    errors.append(f"asset {asset_id} missing path {rel_path}")
        if asset_id and asset_id not in current_asset_ids:
            errors.append(f"asset {asset_id} missing asset_current_manifest row")

    for current_asset in asset_current_manifest:
        asset_id = current_asset.get("asset_id", "").strip()
        if asset_id and asset_id not in asset_ids:
            errors.append(f"asset_current_manifest {asset_id} unknown asset")
        rel_path = current_asset.get("path", "").strip()
        current_status = current_asset.get("status", "").strip().lower()
        if current_status in {"registered", "selected", "approved", "done"}:
            for field in ["source", "platform", "local_file", "original_or_processed", "qa_flags"]:
                if not current_asset.get(field, "").strip():
                    errors.append(f"asset_current_manifest {asset_id} active asset missing {field}")
            if rel_path:
                try:
                    current_asset_path = project_contained_path(
                        project,
                        rel_path,
                        f"asset_current_manifest {asset_id} path",
                    )
                except ValueError as exc:
                    errors.append(str(exc))
                else:
                    if not current_asset_path.exists():
                        errors.append(
                            f"asset_current_manifest {asset_id} missing path {rel_path}"
                        )
        if current_asset.get("direct_client_use", "").strip().lower() == "yes":
            if not has_valid_asset_authorization(
                project,
                asset_id,
                (current_asset.get("sha256") or "").strip(),
                asset_authorizations,
            ):
                errors.append(
                    f"asset_current_manifest {asset_id} direct_client_use=yes without hash-bound authorization receipt"
                )
            if not current_asset.get("used_in_slide", "").strip():
                errors.append(f"asset_current_manifest {asset_id} direct_client_use=yes missing used_in_slide")
            if not current_asset.get("qa_flags", "").strip():
                errors.append(f"asset_current_manifest {asset_id} direct_client_use=yes missing qa_flags")

    for outline in client_outline:
        slide_id = outline.get("slide_id", "")
        if outline.get("visibility", "").strip().lower() in CLIENT_DELIVERY_VISIBILITIES:
            for field in ["page_title", "body_copy", "client_confirmation_point", "material_role", "visual_slot", "visual_asset_status"]:
                if not outline.get(field, "").strip():
                    errors.append(f"client_outline {slide_id} client-visible row missing {field}")
            if outline.get("visual_asset_status", "").strip().lower() in {"existing_image", "existing_asset"} and not outline.get("asset_ids", "").strip():
                errors.append(f"client_outline {slide_id} existing image status missing asset_ids")
        check_refs(errors, f"client_outline {slide_id}", outline.get("asset_ids"), asset_ids, "asset")

    final_dir = project / "05_最终交付_FinalDelivery"
    inventory_rows = {
        (row.get("path") or "").strip(): row
        for row in final_delivery_lock_rows
        if (row.get("path") or "").strip()
    }
    protected_rows = {
        row.get("path", "").strip(): row
        for row in final_delivery_lock_rows
        if row.get("protected", "").strip().lower() in {"yes", "true", "1"}
        and row.get("path", "").strip()
    }
    protected_paths = set(protected_rows)
    for rel_path, row in protected_rows.items():
        try:
            _, path = final_delivery_project_path(project, rel_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not path.exists() or not path.is_file():
            if not final_delivery_reconciliation_valid(
                project, inventory_rows, row
            ):
                errors.append(f"FinalDelivery locked file missing: {rel_path}")
            continue
        expected_sha = row.get("sha256", "").strip()
        expected_size = row.get("size_bytes", "").strip()
        if not expected_sha or not expected_size:
            errors.append(f"FinalDelivery lock baseline incomplete: {rel_path}")
            continue
        actual_size = str(path.stat().st_size)
        actual_sha = file_sha256(path)
        if actual_sha != expected_sha or actual_size != expected_size:
            errors.append(f"FinalDelivery protected file changed: {rel_path}")
    if final_dir.exists() and project_relative_path_has_symlink_component(
        project, "05_最终交付_FinalDelivery"
    ):
        errors.append("FinalDelivery root contains a forbidden symlink component")
    elif final_dir.exists():
        for path in final_dir.rglob("*"):
            if not path.is_file() or path.name in {"README.md", "目录索引.md", ".DS_Store"}:
                continue
            lexical_rel = path.relative_to(project).as_posix()
            try:
                rel_path, path = final_delivery_project_path(
                    project, lexical_rel, require_file=True
                )
            except ValueError as exc:
                errors.append(str(exc))
                continue
            inventory = inventory_rows.get(rel_path)
            if final_delivery_metadata_path(path):
                if inventory and (inventory.get("inventory_state") or "").strip() not in {"", "metadata_excluded"}:
                    errors.append(
                        f"FinalDelivery generated metadata incorrectly classified as user final: {rel_path}"
                    )
                continue
            if not inventory:
                errors.append(f"FinalDelivery file is not locked/protected: {rel_path}")
            elif (inventory.get("inventory_state") or "").strip() == "pending_reconciliation":
                errors.append(f"FinalDelivery pending inventory unresolved: {rel_path}")
            elif rel_path not in protected_paths:
                errors.append(f"FinalDelivery file is not locked/protected: {rel_path}")

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
        "asset_current_manifest": len(asset_current_manifest),
        "asset_authorizations": len(asset_authorizations),
        "specialist_exchanges": len(specialist_exchange_rows),
        "client_outline": len(client_outline),
        "final_delivery_locks": len(final_delivery_lock_rows),
        "feedback": len(feedback_rows),
        "profile_subjects": len(profile_subjects),
        "profile_insights": len(profile_insights),
        "profile_conflicts": len(profile_conflicts),
        "agents_policy": int(agents_policy_ok),
        "errors": len(errors),
    }
    return errors, stats


def string_validation_errors(project: Path) -> list[str]:
    errors, _ = _validate_strings(project)
    return errors


def migration_legacy_error_messages(project: Path) -> set[str]:
    """Never let a project-local manifest downgrade a live validation error.

    The migration manifest is valuable audit evidence, but it lives inside the
    same writable project as the rows it describes. Internal hashes can prove
    consistency, not that the snapshot really predates migration. Only the
    explicit row-level quarantine paths validated in
    ``supplemental_validation_issues`` may become non-blocking legacy debt.
    """
    del project
    return set()


LEGACY_BASELINE_ALLOWED_PATTERNS = (
    re.compile(r"^gate [^ ]+ unknown artifact .+$"),
    re.compile(r"^work [^ ]+ unknown (?:requirement|artifact|source_event|reference|asset|blocked_by) .+$"),
    re.compile(r"^gate_log row missing gate_run_id$"),
    re.compile(r"^gate_log duplicate gate_run_id: .+$"),
    re.compile(r"^gate_log .+ supersedes(?:_gate_run_id does not match previous run for| missing or different gate run).*$"),
    re.compile(r"^profile_(?:subject|voice|insight|conflict) .+ (?:invalid|unknown|missing) .+$"),
)


def legacy_baseline_message_allowed(message: str) -> bool:
    """Allowlist low-risk legacy row debt; safety/readiness errors never downgrade."""
    return any(pattern.fullmatch(message) for pattern in LEGACY_BASELINE_ALLOWED_PATTERNS)


def classify_string_issue(
    message: str, *, legacy_baseline: set[str] | None = None
) -> ValidationIssue:
    lowered = message.lower()
    if "finaldelivery" in lowered or "client delivery" in lowered:
        severity, scope = "P0", "current"
    elif "current_truth" in lowered or "current version truth" in lowered:
        severity, scope = "P0", "current"
    elif (
        message in (legacy_baseline or set())
        and legacy_baseline_message_allowed(message)
    ):
        severity, scope = "P2", "legacy"
    else:
        severity, scope = "P1", "active"
    known_codes = (
        ("FinalDelivery protected file changed", "final_delivery_protected_drift"),
        ("FinalDelivery locked file missing", "final_delivery_locked_missing"),
        ("FinalDelivery pending inventory unresolved", "final_delivery_pending_inventory"),
        ("FinalDelivery file is not locked/protected", "final_delivery_uninventoried_file"),
        ("current_truth", "current_truth_invalid"),
        ("client delivery", "current_delivery_invalid"),
    )
    code = next((value for marker, value in known_codes if marker.lower() in lowered), "")
    if not code:
        code = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")[:96] or "validation_issue"
    return ValidationIssue(severity, scope, code, message)


def supplemental_validation_issues(project: Path) -> list[ValidationIssue]:
    project = project.resolve()
    issues: list[ValidationIssue] = []
    schema_path = project / CONTROL_PLANE_SCHEMA_REL
    if not schema_path.is_file():
        issues.append(
            ValidationIssue(
                "P2",
                "legacy",
                "legacy_control_plane_schema_missing",
                f"legacy control plane has not been migrated to schema {CONTROL_PLANE_SCHEMA_VERSION}",
                CONTROL_PLANE_SCHEMA_REL.as_posix(),
            )
        )
    else:
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(
                ValidationIssue(
                    "P0",
                    "current",
                    "malformed_control_plane_schema",
                    f"control_plane_schema.json is malformed: {exc}",
                )
            )
        else:
            if schema.get("schema_version") != CONTROL_PLANE_SCHEMA_VERSION:
                issues.append(
                    ValidationIssue(
                        "P0",
                        "current",
                        "unsupported_control_plane_schema",
                        f"control plane schema is {schema.get('schema_version')!r}; expected {CONTROL_PLANE_SCHEMA_VERSION}",
                    )
                )
    project_yml = project / "AD-creative/orchestrator/project.yml"
    project_yml_text = project_yml.read_text(encoding="utf-8") if project_yml.is_file() else ""
    if schema_path.is_file() and not re.search(
        rf'(?m)^  schema_version:[ \t]*["\']?{re.escape(CONTROL_PLANE_SCHEMA_VERSION)}["\']?[ \t]*$',
        project_yml_text,
    ):
        issues.append(
            ValidationIssue(
                "P0",
                "current",
                "project_schema_version_mismatch",
                f"project.yml does not declare schema_version {CONTROL_PLANE_SCHEMA_VERSION}",
            )
        )

    artifact_errors: list[str] = []
    artifacts = load_optional_csv(
        project / "AD-creative/orchestrator/artifact_index.csv", artifact_errors
    )
    artifacts_by_id = {
        (row.get("artifact_id") or "").strip(): row
        for row in artifacts
        if (row.get("artifact_id") or "").strip()
    }
    truth_path = project / "AD-creative/orchestrator/current_truth.md"
    truth_text = truth_path.read_text(encoding="utf-8") if truth_path.is_file() else ""
    exact_ids = {
        key: current_truth_value(truth_text, key)
        for key in CURRENT_ARTIFACT_TRUTH_KEYS
        if current_truth_value(truth_text, key)
    }
    for key, artifact_id in exact_ids.items():
        row = artifacts_by_id.get(artifact_id)
        if row is None:
            issues.append(
                ValidationIssue(
                    "P0",
                    "current",
                    "exact_current_artifact_unknown",
                    f"{key} points to unknown artifact {artifact_id}",
                    artifact_id,
                )
            )
            continue
        lifecycle = normalized_artifact_lifecycle(row)
        if lifecycle != "active":
            issues.append(
                ValidationIssue(
                    "P0",
                    "current",
                    "exact_current_artifact_not_active",
                    f"{key} points to non-active artifact {artifact_id} ({lifecycle})",
                    artifact_id,
                )
            )
        rel_path = (row.get("path") or row.get("original_path") or "").strip()
        if not rel_path or not (project / rel_path).is_file():
            issues.append(
                ValidationIssue(
                    "P0",
                    "current",
                    "exact_current_artifact_missing",
                    f"{key} exact-current target is missing: {rel_path or '<blank>'}",
                    artifact_id,
                )
            )

    current_version_id = current_truth_value(truth_text, "current_version_id")
    if current_version_id:
        version_rows = load_optional_csv(
            project / "AD-creative/orchestrator/version_map.csv", []
        )
        current_versions = [
            row
            for row in version_rows
            if (row.get("version_id") or "").strip() == current_version_id
        ]
        if len(current_versions) == 1:
            version_status = (
                current_versions[0].get("status") or ""
            ).strip().lower()
            if version_status not in CURRENT_VIEW_VERSION_STATUSES:
                issues.append(
                    ValidationIssue(
                        "P0",
                        "current",
                        "exact_current_version_not_current_view",
                        f"current_version_id {current_version_id} has non-current-view status {version_status or '<blank>'}",
                        current_version_id,
                    )
                )

    legacy_artifacts: list[str] = []
    tombstones: list[str] = []
    for row in artifacts:
        artifact_id = (row.get("artifact_id") or "<missing>").strip()
        explicit = (row.get("lifecycle_state") or "").strip().lower().replace("-", "_")
        lifecycle = normalized_artifact_lifecycle(row)
        if explicit and explicit not in ARTIFACT_LIFECYCLE_VALUES:
            issues.append(
                ValidationIssue(
                    "P1",
                    "active",
                    "artifact_lifecycle_invalid",
                    f"artifact {artifact_id} has invalid lifecycle_state {explicit}",
                    artifact_id,
                )
            )
        if lifecycle in ARTIFACT_INACTIVE_LIFECYCLE_VALUES or lifecycle == "legacy_unknown":
            legacy_artifacts.append(artifact_id)
        if lifecycle == "legacy_unresolved_tombstone":
            tombstones.append(artifact_id)
            original = (row.get("original_path") or "").strip()
            cleanup_ref = (row.get("cleanup_ref") or "").strip()
            if not cleanup_ref or (original and original == cleanup_ref):
                issues.append(
                    ValidationIssue(
                        "P2",
                        "legacy",
                        "legacy_tombstone_malformed",
                        f"artifact {artifact_id} tombstone must keep cleanup_ref separate and must not fabricate original_path",
                        artifact_id,
                    )
                )
    if legacy_artifacts:
        issues.append(
            ValidationIssue(
                "P2",
                "legacy",
                "legacy_artifact_debt",
                f"legacy artifact debt grouped: {len(legacy_artifacts)} inactive/unknown rows",
                ";".join(legacy_artifacts[:12]),
            )
        )
    if tombstones:
        issues.append(
            ValidationIssue(
                "P2",
                "legacy",
                "legacy_unresolved_tombstones",
                f"legacy unresolved tombstones grouped: {len(tombstones)} rows",
                ";".join(tombstones[:12]),
            )
        )

    thread_rows = load_optional_csv(
        project / "AD-creative/orchestrator/thread_registry.csv", []
    )
    quarantined = [
        row
        for row in thread_rows
        if (row.get("schema_state") or "").strip() == "legacy_quarantined"
    ]
    manifest_path = (
        project
        / "AD-creative/orchestrator/migrations/control_plane_v2_manifest.json"
    )
    manifest: dict[str, object] = {}
    manifest_malformed = False
    if manifest_path.is_file():
        try:
            loaded_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(loaded_manifest, dict):
                raise ValueError("migration manifest must be a JSON object")
            manifest = loaded_manifest
        except (json.JSONDecodeError, ValueError):
            manifest = {}
            manifest_malformed = True
    raw_thread_rows = (
        manifest.get("raw_legacy_evidence", {}).get("thread_rows", [])
        if isinstance(manifest.get("raw_legacy_evidence"), dict)
        else []
    )
    raw_thread_rows_by_sha = (
        manifest.get("raw_legacy_evidence", {}).get("thread_rows_by_sha", {})
        if isinstance(manifest.get("raw_legacy_evidence"), dict)
        else {}
    )
    invalid_quarantine: list[str] = []
    for row in quarantined:
        thread_id = (row.get("thread_id") or "<missing>").strip()
        ref = (row.get("legacy_raw_ref") or "").strip()
        match = re.search(r"/thread_rows/(\d+)$", ref)
        sha_match = re.search(r"/thread_rows_by_sha/([0-9a-f]{64})$", ref)
        raw_entry: object = None
        if sha_match and isinstance(raw_thread_rows_by_sha, dict):
            raw_entry = raw_thread_rows_by_sha.get(sha_match.group(1))
        elif match and isinstance(raw_thread_rows, list):
            index = int(match.group(1))
            if 0 <= index < len(raw_thread_rows):
                raw_entry = raw_thread_rows[index]
        raw = raw_entry.get("raw") if isinstance(raw_entry, dict) else None
        expected = (row.get("legacy_evidence_sha256") or "").strip()
        if not isinstance(raw, dict) or not re.fullmatch(r"[0-9a-f]{64}", expected) or canonical_row_sha256(raw) != expected:
            invalid_quarantine.append(thread_id)
    if quarantined:
        issues.append(
            ValidationIssue(
                "P2",
                "legacy",
                "legacy_threadops_quarantine",
                f"legacy ThreadOps debt grouped: {len(quarantined)} hash-bound quarantined rows",
                ";".join((row.get("thread_id") or "") for row in quarantined[:12]),
            )
        )
    if invalid_quarantine:
        issues.append(
            ValidationIssue(
                "P0",
                "current",
                "legacy_threadops_quarantine_evidence_invalid",
                f"legacy ThreadOps quarantine evidence is invalid for {len(invalid_quarantine)} rows",
                ";".join(invalid_quarantine[:12]),
            )
        )

    if manifest_malformed:
        issues.append(
            ValidationIssue(
                "P0",
                "current",
                "malformed_migration_manifest",
                "control-plane migration manifest is malformed and cannot prove current blocker state",
                str(manifest_path),
            )
        )

    manifest_blockers = manifest.get("active_blockers", [])
    if "active_blockers" in manifest and isinstance(manifest_blockers, list):
        for blocker in manifest_blockers:
            if not isinstance(blocker, dict):
                issues.append(
                    ValidationIssue(
                        "P0",
                        "current",
                        "migration_active_blocker_malformed",
                        "migration manifest contains a malformed active blocker row",
                        str(manifest_path),
                    )
                )
                continue
            issues.append(
                ValidationIssue(
                    "P0",
                    "current",
                    str(blocker.get("code") or "migration_blocker"),
                    str(blocker.get("message") or "control-plane migration blocker"),
                    str(manifest_path),
                )
            )
    elif manifest_path.is_file() and not manifest_malformed:
        issues.append(
            ValidationIssue(
                "P0",
                "current",
                "migration_active_blocker_state_unknown",
                "migration manifest lacks active_blockers; rerun the schema-aware migration before current delivery",
                str(manifest_path),
            )
        )
    legacy_manifest_blockers = manifest.get("blockers", [])
    if (
        manifest_path.is_file()
        and "active_blockers" not in manifest
        and isinstance(legacy_manifest_blockers, list)
    ):
        issues.append(
            ValidationIssue(
                "P2",
                "legacy",
                "legacy_migration_blocker_history",
                f"legacy migration manifest retains {len(legacy_manifest_blockers)} historical blocker rows awaiting refresh",
                str(manifest_path),
            )
        )
    return issues


def validate_issues(
    project: Path, *, strict_legacy: bool = False
) -> tuple[list[ValidationIssue], dict[str, int]]:
    string_errors, stats = _validate_strings(project)
    legacy_baseline = migration_legacy_error_messages(project)
    issues = [
        classify_string_issue(message, legacy_baseline=legacy_baseline)
        for message in string_errors
    ]
    issues.extend(supplemental_validation_issues(project))
    deduped: dict[tuple[str, str, str], ValidationIssue] = {}
    for issue in issues:
        deduped.setdefault((issue.scope, issue.code, issue.message), issue)
    severity_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    scope_order = {"current": 0, "active": 1, "legacy": 2}
    ordered = sorted(
        deduped.values(),
        key=lambda issue: (
            severity_order.get(issue.severity, 9),
            scope_order.get(issue.scope, 9),
            issue.code,
            issue.message,
        ),
    )
    blocking = [
        issue for issue in ordered if strict_legacy or issue.scope != "legacy"
    ]
    stats = dict(stats)
    stats["issues"] = len(ordered)
    stats["errors"] = len(blocking)
    stats["p0"] = sum(1 for issue in ordered if issue.severity == "P0")
    stats["legacy_debt"] = sum(1 for issue in ordered if issue.scope == "legacy")
    return ordered, stats


def validate(
    project: Path, *, strict_legacy: bool = False
) -> tuple[list[str], dict[str, int]]:
    issues, stats = validate_issues(project, strict_legacy=strict_legacy)
    errors = [
        issue.message
        for issue in issues
        if strict_legacy or issue.scope != "legacy"
    ]
    return errors, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", help="Project root containing AD-creative/")
    parser.add_argument("--strict-legacy", action="store_true", help="Treat grouped legacy-only debt as blocking.")
    parser.add_argument("--json", action="store_true", help="Print structured validation issues as JSON.")
    args = parser.parse_args()

    issues, stats = validate_issues(
        Path(args.project), strict_legacy=args.strict_legacy
    )
    blocking = [
        issue for issue in issues if args.strict_legacy or issue.scope != "legacy"
    ]
    errors = [issue.message for issue in blocking]
    if args.json:
        print(
            json.dumps(
                {
                    "project": str(Path(args.project).resolve()),
                    "validation": "PASS" if not errors else "CHECK",
                    "strict_legacy": args.strict_legacy,
                    "stats": stats,
                    "issues": [issue.as_dict() for issue in issues],
                    "errors": errors,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 1 if errors else 0
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALIDATION=PASS")
    print("VALIDATION_SCOPE=structure_and_traceability_only")
    print("VALIDATION_NOT_CREATIVE_QUALITY=1")
    print("VALIDATION_NOT_CLIENT_LANGUAGE=1")
    print("VALIDATION_NOT_VISUAL_APPROVAL=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
