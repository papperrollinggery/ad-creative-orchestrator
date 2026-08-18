"""Dependency-aware scoped validation for ordinary ADCO mutations."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable, Iterable

from .creative_contract import (
    BRIEF_CONTRACT_REL,
    BRIEF_SNAPSHOT_REL,
    CANDIDATE_SCHEMA_REL,
    CURRENT_GENERATION_REL,
    LEGACY_CURRENT_CANDIDATE_REL,
    current_creative_generation_paths,
    payload_sha256,
    validate_creative_candidate,
)
from .facts import FACT_INVENTORY_REL, FACT_STATES, load_fact_inventory
from .ingestion import EVIDENCE_REL, load_evidence_chunks, sha256_text
from .safe_write import read_project_text


ALL_SCOPES = [
    "source_event",
    "evidence_chunks",
    "facts",
    "requirements_gaps",
    "creative_brief",
    "creative_candidate",
    "client_outline",
    "ppt",
    "derived_preview_pdf_text",
    "client_package",
    "final_delivery",
]

DEPENDENCY_GRAPH: dict[str, list[str]] = {
    "source_event": ["evidence_chunks"],
    "evidence_chunks": ["facts"],
    "facts": ["requirements_gaps"],
    "requirements_gaps": ["creative_brief"],
    "creative_brief": ["creative_candidate"],
    "creative_candidate": ["client_outline"],
    "client_outline": ["ppt"],
    "ppt": ["derived_preview_pdf_text"],
    "derived_preview_pdf_text": ["client_package"],
    "client_package": ["final_delivery"],
    "final_delivery": [],
}

FULL_VALIDATION_SCOPES = {
    "ppt",
    "derived_preview_pdf_text",
    "client_package",
    "final_delivery",
}

VALIDATORS_BY_TRIGGER: dict[str, list[str]] = {
    "source_event": [
        "validate_source_events",
        "validate_evidence_chunks",
        "validate_fact_inventory",
        "validate_requirements_gaps",
    ],
    "evidence_chunks": [
        "validate_evidence_chunks",
        "validate_fact_inventory",
        "validate_requirements_gaps",
    ],
    "facts": ["validate_fact_inventory", "validate_requirements_gaps"],
    "requirements_gaps": ["validate_requirements_gaps"],
    "creative_brief": ["validate_creative_brief"],
    "creative_candidate": ["validate_creative_candidate"],
    "client_outline": ["validate_client_outline"],
    "ppt": [],
    "derived_preview_pdf_text": [],
    "client_package": [],
    "final_delivery": [],
}

ALL_VALIDATORS = [
    "validate_source_events",
    "validate_evidence_chunks",
    "validate_fact_inventory",
    "validate_requirements_gaps",
    "validate_creative_brief",
    "validate_creative_candidate",
    "validate_client_outline",
    "validate_ppt",
    "validate_derived_preview_pdf_text",
    "validate_client_package",
    "validate_final_delivery",
]


@dataclass
class IncrementalValidationReport:
    affected_scopes: list[str]
    validators_run: list[str]
    validators_skipped: list[str]
    full_validation_required: bool
    errors: list[str]
    warnings: list[str]
    validation_ms: int

    def as_dict(self) -> dict[str, object]:
        return {
            "affected_scopes": self.affected_scopes,
            "validators_run": self.validators_run,
            "validators_skipped": self.validators_skipped,
            "full_validation_required": self.full_validation_required,
            "errors": self.errors,
            "warnings": self.warnings,
            "validation_ms": self.validation_ms,
            "status": "PASS" if not self.errors else "CHECK",
        }


def _scope_for_path(raw_path: str) -> str | None:
    path = raw_path.replace("\\", "/").lower()
    if path.endswith("source_events.csv"):
        return "source_event"
    if path.endswith(EVIDENCE_REL.as_posix().lower()):
        return "evidence_chunks"
    if path.endswith(FACT_INVENTORY_REL.as_posix().lower()):
        return "facts"
    if path.endswith("requirements.csv") or path.endswith("gaps.csv"):
        return "requirements_gaps"
    if any(
        path.endswith(item.as_posix().lower())
        for item in [BRIEF_SNAPSHOT_REL, BRIEF_CONTRACT_REL, CANDIDATE_SCHEMA_REL]
    ):
        return "creative_brief"
    if (
        "creative/candidates/" in path
        or "creative/generations/" in path
        or path.endswith(CURRENT_GENERATION_REL.as_posix().lower())
        or path.endswith(LEGACY_CURRENT_CANDIDATE_REL.as_posix().lower())
    ):
        return "creative_candidate"
    if "client_review/client_outline" in path:
        return "client_outline"
    if path.endswith(".pptx"):
        return "ppt"
    if path.endswith(".pdf") or "preview" in path or "text_extract" in path:
        return "derived_preview_pdf_text"
    if "client_pack" in path:
        return "client_package"
    if "05_最终交付_finaldelivery" in path.lower() or "final_delivery" in path:
        return "final_delivery"
    return None


def _scope_for_artifact_id(artifact_id: str) -> str | None:
    normalized = artifact_id.upper()
    if "SOURCE" in normalized:
        return "source_event"
    if "EVIDENCE" in normalized:
        return "evidence_chunks"
    if "FACT" in normalized:
        return "facts"
    if "REQUIREMENT" in normalized or "GAP" in normalized:
        return "requirements_gaps"
    if "CREATIVE-BRIEF" in normalized or "CANDIDATE-SCHEMA" in normalized:
        return "creative_brief"
    if "CREATIVE-CANDIDATE" in normalized or "CREATIVE-DIRECTIONS" in normalized:
        return "creative_candidate"
    if "OUTLINE" in normalized:
        return "client_outline"
    if "PPT" in normalized:
        return "ppt"
    if any(token in normalized for token in ["PDF", "PREVIEW", "TEXT-EXTRACT"]):
        return "derived_preview_pdf_text"
    if "CLIENT-PACK" in normalized:
        return "client_package"
    if "FINAL" in normalized or "DELIVERY" in normalized:
        return "final_delivery"
    return None


def changed_scopes(
    *,
    changed_artifact_ids: Iterable[str] = (),
    changed_file_paths: Iterable[str | Path] = (),
    changed_hashes: dict[str, str] | None = None,
) -> list[str]:
    scopes: set[str] = set()
    for artifact_id in changed_artifact_ids:
        scope = _scope_for_artifact_id(str(artifact_id))
        if scope:
            scopes.add(scope)
    for path in changed_file_paths:
        scope = _scope_for_path(str(path))
        if scope:
            scopes.add(scope)
    for path in (changed_hashes or {}):
        scope = _scope_for_path(str(path))
        if scope:
            scopes.add(scope)
    return [scope for scope in ALL_SCOPES if scope in scopes]


def affected_scopes(initial: Iterable[str]) -> list[str]:
    affected = set(initial)
    queue = list(initial)
    while queue:
        scope = queue.pop(0)
        for downstream in DEPENDENCY_GRAPH.get(scope, []):
            if downstream not in affected:
                affected.add(downstream)
                queue.append(downstream)
    return [scope for scope in ALL_SCOPES if scope in affected]


def plan_incremental_validation(
    *,
    changed_artifact_ids: Iterable[str] = (),
    changed_file_paths: Iterable[str | Path] = (),
    changed_hashes: dict[str, str] | None = None,
) -> dict[str, object]:
    initial = changed_scopes(
        changed_artifact_ids=changed_artifact_ids,
        changed_file_paths=changed_file_paths,
        changed_hashes=changed_hashes,
    )
    affected = affected_scopes(initial)
    validators: list[str] = []
    for scope in initial:
        for validator in VALIDATORS_BY_TRIGGER.get(scope, []):
            if validator not in validators:
                validators.append(validator)
    validators = [item for item in ALL_VALIDATORS if item in validators]
    return {
        "changed_scopes": initial,
        "affected_scopes": affected,
        "validators_run": validators,
        "validators_skipped": [item for item in ALL_VALIDATORS if item not in validators],
        "full_validation_required": any(scope in FULL_VALIDATION_SCOPES for scope in initial),
    }


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        return [], []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def _validate_source_events(project: Path) -> tuple[list[str], list[str]]:
    fields, rows = _read_csv(project / "AD-creative/orchestrator/source_events.csv")
    required = {"source_event_id", "file_paths", "declared_semantics"}
    missing = sorted(required - set(fields))
    errors = ["source_events.csv missing columns: " + ", ".join(missing)] if missing else []
    ids = [row.get("source_event_id", "") for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("source_events.csv contains duplicate source_event_id values")
    return errors, []


def _validate_evidence_chunks(project: Path) -> tuple[list[str], list[str]]:
    try:
        chunks = load_evidence_chunks(project)
    except ValueError as exc:
        return [str(exc)], []
    errors: list[str] = []
    ids: set[str] = set()
    for chunk in chunks:
        if chunk.chunk_id in ids:
            errors.append(f"duplicate evidence chunk_id: {chunk.chunk_id}")
        ids.add(chunk.chunk_id)
        if not chunk.source_event_id or not chunk.source_path:
            errors.append(f"evidence chunk lacks source binding: {chunk.chunk_id}")
        if len(chunk.sha256) != 64:
            errors.append(f"evidence chunk sha256 is invalid: {chunk.chunk_id}")
        if not chunk.text:
            errors.append(f"evidence chunk text is empty: {chunk.chunk_id}")
        if not chunk.inspection_status.startswith("requires_") and sha256_text(chunk.text) != chunk.sha256:
            errors.append(f"evidence chunk text hash mismatch: {chunk.chunk_id}")
    return errors, []


def _validate_fact_inventory(project: Path) -> tuple[list[str], list[str]]:
    try:
        chunks = load_evidence_chunks(project)
        facts = load_fact_inventory(project)
    except ValueError as exc:
        return [str(exc)], []
    evidence_ids = {item.chunk_id for item in chunks}
    errors: list[str] = []
    keys: set[str] = set()
    for fact in facts:
        if not fact.fact_key or fact.fact_key in keys:
            errors.append(f"fact inventory has missing/duplicate key: {fact.fact_key}")
        keys.add(fact.fact_key)
        if fact.state not in FACT_STATES:
            errors.append(f"fact inventory state is invalid: {fact.fact_key}")
        if any(ref not in evidence_ids for ref in fact.evidence_refs):
            errors.append(f"fact inventory evidence ref is stale: {fact.fact_key}")
        if not 0 <= fact.confidence <= 1:
            errors.append(f"fact inventory confidence is invalid: {fact.fact_key}")
    return errors, []


def _validate_requirements_gaps(project: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    for name, required in [
        ("requirements.csv", {"requirement_id", "statement", "source_event_id"}),
        ("gaps.csv", {"gap_id", "description", "status", "impact"}),
    ]:
        fields, rows = _read_csv(project / "AD-creative/orchestrator" / name)
        missing = sorted(required - set(fields))
        if missing:
            errors.append(f"{name} missing columns: {', '.join(missing)}")
        key = "requirement_id" if name.startswith("requirements") else "gap_id"
        ids = [row.get(key, "") for row in rows]
        if any(not item for item in ids) or len(ids) != len(set(ids)):
            errors.append(f"{name} contains missing or duplicate {key}")
    return errors, []


def _validate_creative_brief(project: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    payloads: dict[Path, object] = {}
    for rel_path in [BRIEF_SNAPSHOT_REL, BRIEF_CONTRACT_REL, CANDIDATE_SCHEMA_REL]:
        path = project / rel_path
        if not path.is_file():
            errors.append(f"creative brief artifact missing: {rel_path}")
            continue
        try:
            payloads[rel_path] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"creative brief artifact invalid JSON: {rel_path}: {exc}")
    snapshot = payloads.get(BRIEF_SNAPSHOT_REL)
    if isinstance(snapshot, dict):
        expected = snapshot.get("brief_snapshot_sha256")
        basis = dict(snapshot)
        basis.pop("brief_snapshot_sha256", None)
        if expected != payload_sha256(basis):
            errors.append("creative brief snapshot digest mismatch")
    contract = payloads.get(BRIEF_CONTRACT_REL)
    if isinstance(snapshot, dict) and isinstance(contract, dict):
        if contract.get("brief_snapshot_sha256") != snapshot.get("brief_snapshot_sha256"):
            errors.append("creative brief contract snapshot binding mismatch")
    return errors, []


def _validate_creative_candidate(project: Path) -> tuple[list[str], list[str]]:
    try:
        generation_paths = current_creative_generation_paths(project)
    except ValueError as exc:
        return [str(exc)], []
    if not generation_paths:
        return ["current creative candidate is missing"], []
    try:
        payload = json.loads(
            read_project_text(project, generation_paths["candidate"])
        )
    except (OSError, json.JSONDecodeError) as exc:
        return [f"current creative candidate invalid JSON: {exc}"], []
    return validate_creative_candidate(project, payload)


def _validate_client_outline(project: Path) -> tuple[list[str], list[str]]:
    fields, rows = _read_csv(project / "AD-creative/client_review/client_outline.csv")
    required = {
        "slide_id",
        "page_title",
        "body_copy",
        "client_confirmation_point",
        "visibility",
        "status",
    }
    missing = sorted(required - set(fields))
    errors = ["client_outline.csv missing columns: " + ", ".join(missing)] if missing else []
    ids = [row.get("slide_id", "") for row in rows if row.get("slide_id", "")]
    if len(ids) != len(set(ids)):
        errors.append("client_outline.csv contains duplicate slide_id values")
    return errors, []


VALIDATOR_FUNCTIONS: dict[str, Callable[[Path], tuple[list[str], list[str]]]] = {
    "validate_source_events": _validate_source_events,
    "validate_evidence_chunks": _validate_evidence_chunks,
    "validate_fact_inventory": _validate_fact_inventory,
    "validate_requirements_gaps": _validate_requirements_gaps,
    "validate_creative_brief": _validate_creative_brief,
    "validate_creative_candidate": _validate_creative_candidate,
    "validate_client_outline": _validate_client_outline,
}


def run_incremental_validation(
    project: Path,
    *,
    changed_artifact_ids: Iterable[str] = (),
    changed_file_paths: Iterable[str | Path] = (),
    changed_hashes: dict[str, str] | None = None,
) -> IncrementalValidationReport:
    started = perf_counter()
    plan = plan_incremental_validation(
        changed_artifact_ids=changed_artifact_ids,
        changed_file_paths=changed_file_paths,
        changed_hashes=changed_hashes,
    )
    errors: list[str] = []
    warnings: list[str] = []
    for validator_name in plan["validators_run"]:
        validator = VALIDATOR_FUNCTIONS.get(str(validator_name))
        if validator is None:
            continue
        try:
            validator_errors, validator_warnings = validator(project)
        except Exception as exc:  # scoped validation must fail closed with context
            errors.append(f"{validator_name} crashed: {type(exc).__name__}: {exc}")
            continue
        errors.extend(f"{validator_name}: {item}" for item in validator_errors)
        warnings.extend(f"{validator_name}: {item}" for item in validator_warnings)
    return IncrementalValidationReport(
        affected_scopes=list(plan["affected_scopes"]),
        validators_run=list(plan["validators_run"]),
        validators_skipped=list(plan["validators_skipped"]),
        full_validation_required=bool(plan["full_validation_required"]),
        errors=errors,
        warnings=warnings,
        validation_ms=round((perf_counter() - started) * 1000),
    )
