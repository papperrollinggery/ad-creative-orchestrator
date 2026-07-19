"""Evidence-bound creative brief, candidate import, and critic lint contracts."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .facts import load_fact_inventory
from .ingestion import load_evidence_chunks


CREATIVE_ROOT = Path("AD-creative/creative")
BRIEF_SNAPSHOT_REL = CREATIVE_ROOT / "brief_snapshot.json"
BRIEF_CONTRACT_REL = CREATIVE_ROOT / "creative_brief_contract.json"
CANDIDATE_SCHEMA_REL = CREATIVE_ROOT / "creative_candidate.schema.json"
GENERATION_REQUEST_REL = CREATIVE_ROOT / "creative_generation_request.json"
OPEN_GAPS_REL = CREATIVE_ROOT / "creative_open_evidence_gaps.json"
CURRENT_CANDIDATE_REL = CREATIVE_ROOT / "current_candidate.json"
CANDIDATE_IMPORT_RECEIPT_REL = CREATIVE_ROOT / "candidate_import_receipt.json"
CRITIC_RECEIPT_REL = CREATIVE_ROOT / "creative_critic_receipt.json"
CREATIVE_DIRECTIONS_REL = CREATIVE_ROOT / "creative_directions.md"
OPTION_MATRIX_REL = CREATIVE_ROOT / "option_matrix.csv"

CREATIVE_DIRECTION_FIELDS = [
    "direction_id",
    "name",
    "human_tension",
    "brand_truth",
    "audience_truth",
    "single_minded_proposition",
    "creative_mechanism",
    "key_visual",
    "story_or_behavior",
    "product_role",
    "channel_execution",
    "why_brand_can_own_it",
    "production_risk",
    "evidence_refs",
]

CREATIVE_CANDIDATE_SCHEMA: dict[str, object] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "adco.creative-candidate/1.0",
    "title": "ADCO evidence-bound creative candidate",
    "type": "object",
    "required": ["candidate_version", "brief_snapshot_sha256", "directions"],
    "properties": {
        "candidate_version": {"const": "1.0"},
        "brief_snapshot_sha256": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$",
        },
        "directions": {
            "type": "array",
            "minItems": 2,
            "maxItems": 3,
            "items": {
                "type": "object",
                "required": CREATIVE_DIRECTION_FIELDS,
                "properties": {
                    **{
                        field: {"type": "string", "minLength": 1}
                        for field in CREATIVE_DIRECTION_FIELDS
                        if field != "evidence_refs"
                    },
                    "evidence_refs": {
                        "type": "array",
                        "minItems": 1,
                        "uniqueItems": True,
                        "items": {"type": "string", "minLength": 1},
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}


@dataclass
class CreativeBriefResult:
    snapshot_sha256: str
    paths: list[Path]
    evidence_refs: list[str]
    open_gaps: list[dict[str, object]]


@dataclass
class CreativeImportResult:
    candidate_path: Path
    current_path: Path
    receipt_path: Path
    directions_path: Path
    matrix_path: Path
    candidate_sha256: str
    direction_count: int
    warnings: list[str]


@dataclass
class CreativeReviewResult:
    status: str
    receipt_path: Path
    receipt: dict[str, object]
    blocking_issues: list[str]
    warnings: list[str]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def payload_sha256(payload: object) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _current_snapshot(project: Path) -> dict[str, object]:
    chunks = load_evidence_chunks(project)
    facts = load_fact_inventory(project)
    requirements = _read_csv(project / "AD-creative/orchestrator/requirements.csv")
    gaps = _read_csv(project / "AD-creative/orchestrator/gaps.csv")
    payload: dict[str, object] = {
        "snapshot_version": "1.0",
        "evidence": [
            {
                "chunk_id": item.chunk_id,
                "source_event_id": item.source_event_id,
                "source_path": item.source_path,
                "sha256": item.sha256,
                "inspection_status": item.inspection_status,
            }
            for item in chunks
        ],
        "facts": [item.as_dict() for item in facts],
        "requirements": requirements,
        "gaps": gaps,
    }
    payload["brief_snapshot_sha256"] = payload_sha256(payload)
    return payload


def _open_gaps(snapshot: dict[str, object]) -> list[dict[str, object]]:
    open_items: list[dict[str, object]] = []
    for fact in snapshot.get("facts", []):
        if not isinstance(fact, dict):
            continue
        if fact.get("state") in {"missing", "conflicting"} or (
            fact.get("state") == "unknown" and fact.get("blocking") is True
        ):
            open_items.append(
                {
                    "kind": "fact",
                    "id": fact.get("fact_key"),
                    "state": fact.get("state"),
                    "blocking": bool(fact.get("blocking")),
                    "evidence_refs": fact.get("evidence_refs", []),
                }
            )
    for gap in snapshot.get("gaps", []):
        if isinstance(gap, dict) and gap.get("status", "").lower() not in {
            "closed",
            "resolved",
        }:
            open_items.append(
                {
                    "kind": "gap",
                    "id": gap.get("gap_id"),
                    "state": gap.get("status"),
                    "blocking": gap.get("impact") == "blocking",
                    "description": gap.get("description", ""),
                }
            )
    return open_items


def create_creative_brief(project: Path) -> CreativeBriefResult:
    snapshot = _current_snapshot(project)
    snapshot_sha = str(snapshot["brief_snapshot_sha256"])
    evidence_refs = [
        str(item.get("chunk_id"))
        for item in snapshot["evidence"]
        if isinstance(item, dict) and item.get("chunk_id")
    ]
    open_gaps = _open_gaps(snapshot)
    contract = {
        "protocol_id": "adco.creative-brief-contract",
        "contract_version": "1.0",
        "brief_snapshot_sha256": snapshot_sha,
        "evidence_refs": evidence_refs,
        "confirmed_facts": [
            fact
            for fact in snapshot["facts"]
            if isinstance(fact, dict) and fact.get("state") == "present"
        ],
        "requirements": snapshot["requirements"],
        "open_evidence_gaps": open_gaps,
        "candidate_contract": {
            "generate_count": "4-6",
            "retain_after_independent_critic": "2-3",
            "mechanism_deduplication_required": True,
            "every_direction_requires_evidence_refs": True,
            "structure_pass_is_not_creative_pass": True,
        },
    }
    request = {
        "protocol_id": "adco.creative-generation-request",
        "request_version": "1.0",
        "model_role": "GPT-5.6 Sol creative reasoning",
        "brief_snapshot_sha256": snapshot_sha,
        "contract_path": BRIEF_CONTRACT_REL.as_posix(),
        "candidate_schema_path": CANDIDATE_SCHEMA_REL.as_posix(),
        "instructions": [
            "Generate 4-6 genuinely distinct candidate directions from the contract.",
            "Differentiate creative mechanism, not only name or wording.",
            "Bind every direction to evidence_refs from the snapshot.",
            "Run an independent Critic including the brand replacement test.",
            "Retain only 2-3 directions after mechanism deduplication.",
            "Do not claim structural validity as creative quality approval.",
        ],
    }
    paths = [
        _write_json(project / BRIEF_SNAPSHOT_REL, snapshot),
        _write_json(project / BRIEF_CONTRACT_REL, contract),
        _write_json(project / CANDIDATE_SCHEMA_REL, CREATIVE_CANDIDATE_SCHEMA),
        _write_json(project / GENERATION_REQUEST_REL, request),
        _write_json(
            project / OPEN_GAPS_REL,
            {
                "brief_snapshot_sha256": snapshot_sha,
                "open_evidence_gaps": open_gaps,
            },
        ),
    ]
    return CreativeBriefResult(
        snapshot_sha256=snapshot_sha,
        paths=paths,
        evidence_refs=evidence_refs,
        open_gaps=open_gaps,
    )


def _normalize_mechanism(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.casefold())


def _candidate_validation_errors(
    project: Path, payload: object
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(payload, dict):
        return ["candidate must be a JSON object"], []
    allowed_top = {"candidate_version", "brief_snapshot_sha256", "directions"}
    if set(payload) != allowed_top:
        errors.append(
            "candidate top-level fields must be exactly candidate_version, brief_snapshot_sha256, directions"
        )
    if payload.get("candidate_version") != "1.0":
        errors.append("candidate_version must be 1.0")
    snapshot_path = project / BRIEF_SNAPSHOT_REL
    if not snapshot_path.is_file():
        errors.append("creative brief snapshot is missing; run creative-brief first")
        current_snapshot_sha = ""
    else:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        current_snapshot_sha = str(snapshot.get("brief_snapshot_sha256", ""))
    if payload.get("brief_snapshot_sha256") != current_snapshot_sha:
        errors.append("brief_snapshot_sha256 does not match the current creative brief")
    directions = payload.get("directions")
    if not isinstance(directions, list) or not 2 <= len(directions) <= 3:
        errors.append("creative-import requires 2-3 post-Critic directions")
        return errors, warnings
    evidence_ids = {chunk.chunk_id for chunk in load_evidence_chunks(project)}
    ids: set[str] = set()
    names: set[str] = set()
    mechanisms: dict[str, str] = {}
    for index, direction in enumerate(directions):
        if not isinstance(direction, dict):
            errors.append(f"directions[{index}] must be an object")
            continue
        missing = set(CREATIVE_DIRECTION_FIELDS) - set(direction)
        extra = set(direction) - set(CREATIVE_DIRECTION_FIELDS)
        if missing or extra:
            errors.append(
                f"directions[{index}] fields mismatch; missing={sorted(missing)} extra={sorted(extra)}"
            )
            continue
        for field in CREATIVE_DIRECTION_FIELDS:
            value = direction.get(field)
            if field == "evidence_refs":
                if (
                    not isinstance(value, list)
                    or not value
                    or len(value) != len(set(value))
                    or not all(isinstance(ref, str) and ref in evidence_ids for ref in value)
                ):
                    errors.append(
                        f"directions[{index}].evidence_refs must bind existing unique evidence chunks"
                    )
            elif not isinstance(value, str) or not value.strip():
                errors.append(f"directions[{index}].{field} is required")
        direction_id = str(direction.get("direction_id", ""))
        name = str(direction.get("name", "")).casefold()
        if direction_id in ids:
            errors.append(f"duplicate direction_id: {direction_id}")
        ids.add(direction_id)
        if name in names:
            errors.append(f"duplicate direction name: {direction.get('name')}")
        names.add(name)
        mechanism = _normalize_mechanism(str(direction.get("creative_mechanism", "")))
        if mechanism in mechanisms:
            errors.append(
                f"duplicate creative mechanism: {direction_id} matches {mechanisms[mechanism]}"
            )
        mechanisms[mechanism] = direction_id
        ownership = str(direction.get("why_brand_can_own_it", ""))
        if len(ownership.strip()) < 20 or re.search(
            r"任何品牌|所有品牌|其他品牌|通用|any brand|every brand",
            ownership,
            re.I,
        ):
            warnings.append(f"{direction_id}: brand ownership is weak; brand replacement risk")
    return errors, warnings


def _candidate_version_path(project: Path, digest: str) -> Path:
    current = project / CURRENT_CANDIDATE_REL
    if current.is_file():
        try:
            current_payload = json.loads(current.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            current_payload = None
        if current_payload is not None and payload_sha256(current_payload) == digest:
            existing = sorted((project / CREATIVE_ROOT / "candidates").glob("candidate_v*.json"))
            if existing:
                return existing[-1]
    directory = project / CREATIVE_ROOT / "candidates"
    directory.mkdir(parents=True, exist_ok=True)
    versions = [
        int(match.group(1))
        for path in directory.glob("candidate_v*.json")
        if (match := re.fullmatch(r"candidate_v(\d+)\.json", path.name))
    ]
    return directory / f"candidate_v{max(versions, default=0) + 1:03d}.json"


def _render_directions(payload: dict[str, object]) -> str:
    directions = payload["directions"]
    assert isinstance(directions, list)
    sections: list[str] = []
    for raw in directions:
        assert isinstance(raw, dict)
        evidence = "; ".join(str(item) for item in raw["evidence_refs"])
        sections.append(
            f"""## {raw['direction_id']} {raw['name']}

- human tension: {raw['human_tension']}
- brand truth: {raw['brand_truth']}
- audience truth: {raw['audience_truth']}
- single-minded proposition: {raw['single_minded_proposition']}
- creative mechanism: {raw['creative_mechanism']}
- key visual: {raw['key_visual']}
- story or behavior: {raw['story_or_behavior']}
- product role: {raw['product_role']}
- channel execution: {raw['channel_execution']}
- why brand can own it: {raw['why_brand_can_own_it']}
- production risk: {raw['production_risk']}
- evidence refs: {evidence}
"""
        )
    return """# Imported Creative Candidates

status: imported_for_internal_review
visibility: internal_only
artifact_role: evidence_bound_model_generated_candidates

These directions were imported through `adco creative-import`. ADCO validates
structure and traceability only; an independent creative Critic remains required.

""" + "\n".join(sections)


def _write_option_matrix(path: Path, payload: dict[str, object]) -> None:
    fields = [
        "direction_id",
        "name",
        "role",
        "strategy_path",
        "creative_proposition",
        "core_message",
        "target_feeling",
        "product_feature",
        "communication_benefit",
        "behavior_barrier",
        "key_visual_or_action",
        "title_or_use_case",
        "reference_ids",
        "risk",
        "why_choose",
        "evidence_refs",
        "status",
        "notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for raw in payload["directions"]:
            assert isinstance(raw, dict)
            writer.writerow(
                {
                    "direction_id": raw["direction_id"],
                    "name": raw["name"],
                    "role": raw["product_role"],
                    "strategy_path": raw["creative_mechanism"],
                    "creative_proposition": raw["single_minded_proposition"],
                    "core_message": raw["single_minded_proposition"],
                    "target_feeling": raw["human_tension"],
                    "product_feature": raw["product_role"],
                    "communication_benefit": raw["single_minded_proposition"],
                    "behavior_barrier": raw["audience_truth"],
                    "key_visual_or_action": raw["key_visual"],
                    "title_or_use_case": raw["channel_execution"],
                    "reference_ids": "",
                    "risk": raw["production_risk"],
                    "why_choose": raw["why_brand_can_own_it"],
                    "evidence_refs": ";".join(raw["evidence_refs"]),
                    "status": "imported",
                    "notes": "candidate_schema=1.0",
                }
            )


def import_creative_candidate(project: Path, candidate_file: Path) -> CreativeImportResult:
    try:
        payload = json.loads(candidate_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read creative candidate: {exc}") from exc
    errors, warnings = _candidate_validation_errors(project, payload)
    if errors:
        raise ValueError("creative candidate validation failed: " + "; ".join(errors[:20]))
    assert isinstance(payload, dict)
    digest = payload_sha256(payload)
    candidate_path = _candidate_version_path(project, digest)
    current_path = project / CURRENT_CANDIDATE_REL
    if not candidate_path.is_file():
        _write_json(candidate_path, payload)
    _write_json(current_path, payload)
    directions_path = project / CREATIVE_DIRECTIONS_REL
    directions_path.write_text(_render_directions(payload), encoding="utf-8")
    matrix_path = project / OPTION_MATRIX_REL
    _write_option_matrix(matrix_path, payload)
    receipt = {
        "protocol_id": "adco.creative-candidate-import",
        "receipt_version": "1.0",
        "candidate_path": candidate_path.relative_to(project).as_posix(),
        "candidate_sha256": digest,
        "brief_snapshot_sha256": payload["brief_snapshot_sha256"],
        "direction_count": len(payload["directions"]),
        "warnings": warnings,
        "structure_validation": "PASS",
        "creative_quality": "NOT_EVALUATED",
        "imported_at": now_iso(),
    }
    receipt_path = _write_json(project / CANDIDATE_IMPORT_RECEIPT_REL, receipt)
    return CreativeImportResult(
        candidate_path=candidate_path,
        current_path=current_path,
        receipt_path=receipt_path,
        directions_path=directions_path,
        matrix_path=matrix_path,
        candidate_sha256=digest,
        direction_count=len(payload["directions"]),
        warnings=warnings,
    )


GENERIC_CREATIVE_PATTERN = re.compile(
    r"unlock|elevate|game changer|next level|seamless|innovative|empower|reimagine|breakthrough|重新定义|引爆|破圈|赋能|无限可能",
    re.I,
)


def _status_map(status: str, reason: str) -> dict[str, str]:
    return {"status": status, "reason": reason}


def review_creative_candidate(project: Path) -> CreativeReviewResult:
    path = project / CURRENT_CANDIDATE_REL
    if not path.is_file():
        raise ValueError("current creative candidate is missing; run creative-import first")
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors, import_warnings = _candidate_validation_errors(project, payload)
    if errors:
        raise ValueError("current creative candidate is invalid: " + "; ".join(errors[:20]))
    directions = payload["directions"]
    assert isinstance(directions, list)
    receipt: dict[str, object] = {
        "protocol_id": "adco.creative-critic-receipt",
        "receipt_version": "1.0",
        "candidate_sha256": payload_sha256(payload),
        "brief_snapshot_sha256": payload["brief_snapshot_sha256"],
        "review_kind": "deterministic_structure_and_language_lint",
        "brief_adherence": {},
        "insight_quality": {},
        "brand_ownership": {},
        "mechanism_difference": {},
        "key_visual_clarity": {},
        "shootability": {},
        "production_risk": {},
        "brand_replacement_test": {},
    }
    blocking: list[str] = []
    warnings = list(import_warnings)
    mechanisms: dict[str, str] = {}
    for raw in directions:
        assert isinstance(raw, dict)
        direction_id = str(raw["direction_id"])
        refs = raw["evidence_refs"]
        receipt["brief_adherence"][direction_id] = _status_map(
            "PASS" if refs else "FAIL",
            f"evidence_refs={len(refs)}",
        )
        insight = str(raw["human_tension"])
        insight_ok = len(insight.strip()) >= 15 and not GENERIC_CREATIVE_PATTERN.search(insight)
        receipt["insight_quality"][direction_id] = _status_map(
            "LINT_PASS" if insight_ok else "REVIEW_REQUIRED",
            "human tension is concrete" if insight_ok else "human tension is thin or generic",
        )
        if not insight_ok:
            warnings.append(f"{direction_id}: insight quality requires independent review")
        ownership = str(raw["why_brand_can_own_it"])
        ownership_ok = len(ownership.strip()) >= 20 and not re.search(
            r"任何品牌|所有品牌|其他品牌|通用|any brand|every brand",
            ownership,
            re.I,
        )
        receipt["brand_ownership"][direction_id] = _status_map(
            "LINT_PASS" if ownership_ok else "REVIEW_REQUIRED",
            ownership,
        )
        receipt["brand_replacement_test"][direction_id] = _status_map(
            "REVIEW_REQUIRED" if ownership_ok else "FAIL",
            (
                "Independent Critic must replace the brand and test whether the mechanism still fully works."
                if ownership_ok
                else "Ownership language is generic enough that another brand may replace it."
            ),
        )
        if not ownership_ok:
            warnings.append(f"{direction_id}: brand replacement risk")
        mechanism = _normalize_mechanism(str(raw["creative_mechanism"]))
        mechanism_ok = mechanism not in mechanisms
        receipt["mechanism_difference"][direction_id] = _status_map(
            "PASS" if mechanism_ok else "FAIL",
            (
                "mechanism differs from prior directions"
                if mechanism_ok
                else f"duplicates {mechanisms[mechanism]}"
            ),
        )
        if not mechanism_ok:
            blocking.append(f"{direction_id}: duplicate mechanism")
        mechanisms[mechanism] = direction_id
        key_visual = str(raw["key_visual"])
        visual_ok = len(key_visual.strip()) >= 15 and not re.search(
            r"TBD|待定|抽象氛围|some visual|nice image",
            key_visual,
            re.I,
        )
        receipt["key_visual_clarity"][direction_id] = _status_map(
            "LINT_PASS" if visual_ok else "REVIEW_REQUIRED",
            key_visual,
        )
        story = str(raw["story_or_behavior"])
        shootable = len(story.strip()) >= 20 and not re.search(
            r"TBD|待定|以后再说|抽象表达",
            story,
            re.I,
        )
        receipt["shootability"][direction_id] = _status_map(
            "LINT_PASS" if shootable else "REVIEW_REQUIRED",
            story,
        )
        receipt["production_risk"][direction_id] = _status_map(
            "DECLARED" if len(str(raw["production_risk"]).strip()) >= 8 else "REVIEW_REQUIRED",
            str(raw["production_risk"]),
        )
        combined = " ".join(str(raw[field]) for field in CREATIVE_DIRECTION_FIELDS if field != "evidence_refs")
        if GENERIC_CREATIVE_PATTERN.search(combined):
            warnings.append(f"{direction_id}: generic AI advertising vocabulary detected")
    receipt["blocking_issues"] = blocking
    receipt["warnings"] = sorted(set(warnings))
    receipt["independent_critic_required"] = True
    receipt["creative_quality"] = "NOT_APPROVED_BY_DETERMINISTIC_LINT"
    receipt["verdict"] = "BLOCKED" if blocking else "STRUCTURE_PASS_REQUIRES_INDEPENDENT_CRITIC"
    receipt["reviewed_at"] = now_iso()
    receipt_path = _write_json(project / CRITIC_RECEIPT_REL, receipt)
    return CreativeReviewResult(
        status="BLOCKED" if blocking else "PARTIAL_PASS",
        receipt_path=receipt_path,
        receipt=receipt,
        blocking_issues=blocking,
        warnings=sorted(set(warnings)),
    )
