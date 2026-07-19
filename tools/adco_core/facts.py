"""Evidence-bound fact inventory, analysis exchange, requirements, and gaps."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .ingestion import EVIDENCE_REL, IngestionReport, ingest_source_rows, load_evidence_chunks
from .models import EvidenceChunk, FactInventoryItem


FACT_INVENTORY_REL = Path("AD-creative/orchestrator/fact_inventory.jsonl")
ANALYSIS_REQUEST_REL = Path("AD-creative/orchestrator/intake_analysis_request.json")
FACT_STATES = {"present", "missing", "unknown", "conflicting"}
FACT_OWNERS = {"client", "operator", "model"}

INTAKE_ANALYSIS_SCHEMA: dict[str, object] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ADCO evidence-bound intake analysis",
    "type": "object",
    "required": ["analysis_version", "facts"],
    "properties": {
        "analysis_version": {"const": "1.0"},
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "fact_key",
                    "state",
                    "value",
                    "evidence_refs",
                    "confidence",
                    "owner",
                    "blocking",
                ],
                "properties": {
                    "fact_key": {"type": "string", "minLength": 1},
                    "state": {"enum": sorted(FACT_STATES)},
                    "value": {"type": "string"},
                    "evidence_refs": {
                        "type": "array",
                        "minItems": 1,
                        "uniqueItems": True,
                        "items": {"type": "string", "minLength": 1},
                    },
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "owner": {"enum": sorted(FACT_OWNERS)},
                    "blocking": {"type": "boolean"},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}


@dataclass(frozen=True)
class RequirementCandidate:
    source_event_id: str
    statement: str
    evidence_ref: str
    requirement_type: str
    priority: str
    affected_stage: str
    owner: str


@dataclass
class IntakeResult:
    ingestion: IngestionReport
    new_requirements: list[dict[str, str]]
    new_gaps: list[dict[str, str]]
    facts: list[FactInventoryItem]

    def stats(self) -> dict[str, int]:
        return {
            "requirements": len(self.new_requirements),
            "gaps": len(self.new_gaps),
            "materials": self.ingestion.files_processed,
            "characters_read": self.ingestion.characters_read,
            "evidence_chunks": len(self.ingestion.chunks),
            "over_budget_files": len(self.ingestion.over_budget),
            "parser_errors": len(self.ingestion.parser_errors),
            "facts": len(self.facts),
        }


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        return [], []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def _write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _next_id(rows: list[dict[str, str]], key: str, prefix: str) -> str:
    numbers: list[int] = []
    for row in rows:
        match = re.fullmatch(rf"{re.escape(prefix)}-(\d+)", row.get(key, ""))
        if match:
            numbers.append(int(match.group(1)))
    return f"{prefix}-{max(numbers, default=0) + 1:03d}"


def load_fact_inventory(project: Path) -> list[FactInventoryItem]:
    path = project / FACT_INVENTORY_REL
    if not path.is_file():
        return []
    facts: list[FactInventoryItem] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid fact inventory JSONL at line {line_number}: {exc}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"invalid fact inventory record at line {line_number}")
            facts.append(FactInventoryItem.from_dict(payload))
    return facts


def write_fact_inventory(project: Path, facts: Iterable[FactInventoryItem]) -> Path:
    path = project / FACT_INVENTORY_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(facts, key=lambda item: item.fact_key)
    path.write_text(
        "".join(
            json.dumps(item.as_dict(), ensure_ascii=False, sort_keys=True) + "\n"
            for item in ordered
        ),
        encoding="utf-8",
    )
    return path


def _observation(
    fact_key: str,
    state: str,
    value: str,
    chunk: EvidenceChunk,
    *,
    confidence: float,
    blocking: bool,
) -> FactInventoryItem:
    return FactInventoryItem(
        fact_key=fact_key,
        state=state,
        value=value,
        evidence_refs=[chunk.chunk_id],
        confidence=confidence,
        owner="client",
        blocking=blocking,
    )


EXPLICIT_FACT_PATTERNS: list[tuple[str, str, re.Pattern[str], bool]] = [
    (
        "brand.logo",
        "present",
        re.compile(r"(?:已提供|已经提供|附件(?:中)?有|provided).{0,24}(?:logo|标志|品牌标识)", re.I),
        False,
    ),
    (
        "brand.logo",
        "missing",
        re.compile(r"(?:缺少|未提供|尚未提供|待提供|missing).{0,24}(?:logo|标志|品牌标识)", re.I),
        True,
    ),
    (
        "asset.product_images",
        "present",
        re.compile(r"(?:已提供|已经提供|附件(?:中)?有|provided).{0,24}(?:产品图|产品高清图|包装图|product image)", re.I),
        False,
    ),
    (
        "asset.product_images",
        "missing",
        re.compile(r"(?:缺少|未提供|尚未提供|待提供|missing).{0,24}(?:产品图|产品高清图|包装图|product image)", re.I),
        True,
    ),
    (
        "delivery.editable_pptx",
        "present",
        re.compile(r"(?:交付|需要|要求|deliver).{0,24}(?:可编辑\s*PPT|editable\s*PPT|PPTX)", re.I),
        False,
    ),
    (
        "policy.ai_client_visibility",
        "present",
        re.compile(r"(?:允许|可用于|可以).{0,24}(?:AI|生成图).{0,24}(?:客户|审阅|client)", re.I),
        False,
    ),
    (
        "policy.ai_client_visibility",
        "missing",
        re.compile(r"(?:禁止|不允许|不可).{0,24}(?:AI|生成图).{0,24}(?:客户|审阅|client)", re.I),
        True,
    ),
]


def _merge_fact_group(items: list[FactInventoryItem]) -> FactInventoryItem:
    states = {item.state for item in items}
    concrete = states & {"present", "missing"}
    if len(concrete) > 1 or "conflicting" in states:
        state = "conflicting"
    elif "present" in states:
        state = "present"
    elif "missing" in states:
        state = "missing"
    else:
        state = "unknown"
    values = list(dict.fromkeys(item.value for item in items if item.value))
    evidence = list(
        dict.fromkeys(ref for item in items for ref in item.evidence_refs if ref)
    )
    return FactInventoryItem(
        fact_key=items[0].fact_key,
        state=state,
        value=" | ".join(values),
        evidence_refs=evidence,
        confidence=max(item.confidence for item in items),
        owner=("model" if any(item.owner == "model" for item in items) else items[0].owner),
        blocking=any(item.blocking for item in items) or state == "conflicting",
    )


def merge_facts(*collections: Iterable[FactInventoryItem]) -> list[FactInventoryItem]:
    grouped: dict[str, list[FactInventoryItem]] = {}
    for collection in collections:
        for item in collection:
            grouped.setdefault(item.fact_key, []).append(item)
    return [_merge_fact_group(items) for _, items in sorted(grouped.items())]


def explicit_facts_from_evidence(chunks: Iterable[EvidenceChunk]) -> list[FactInventoryItem]:
    observations: list[FactInventoryItem] = []
    for chunk in chunks:
        if chunk.inspection_status.startswith("requires_"):
            continue
        for fact_key, state, pattern, blocking in EXPLICIT_FACT_PATTERNS:
            match = pattern.search(chunk.text)
            if match:
                observations.append(
                    _observation(
                        fact_key,
                        state,
                        match.group(0),
                        chunk,
                        confidence=0.95,
                        blocking=blocking,
                    )
                )
    return merge_facts(observations)


REQUIREMENT_TRIGGER_PATTERN = re.compile(
    r"项目|客户希望|希望|要求|交付|方向|关键画面|关键帧|moodboard|参考|PPT|不要|不能|必须|需要|新增要求|客户明确|deliver|must|should",
    re.I,
)


def _clean_statement(value: str) -> str:
    value = value.strip().strip("|").strip()
    value = re.sub(r"^[-*#>`\s]+", "", value).strip()
    return re.sub(r"\s+", " ", value)


def classify_requirement(statement: str) -> tuple[str, str, str]:
    lowered = statement.lower()
    if any(token in statement for token in ["不要", "禁区", "不能", "未经授权", "禁止"]):
        return "constraint", "high", "client_review"
    if any(token in lowered for token in ["交付", "ppt", "可编辑", "slidespec", "deliver"]):
        return "delivery", "high", "ppt_gate"
    if any(token in lowered for token in ["参考", "moodboard", "视频链接", "摄影参考", "reference"]):
        return "research", "high", "reference_research"
    if any(token in statement for token in ["画面", "视觉", "关键帧", "产品", "logo", "人物", "场景", "颜色"]):
        return "visual", "high", "visual_plan"
    if any(token in statement for token in ["方向", "主张", "创意", "情绪", "功能"]):
        return "creative", "high", "creative"
    return "brief", "medium", "intake"


def requirement_candidates(chunks: Iterable[EvidenceChunk]) -> list[RequirementCandidate]:
    candidates: list[RequirementCandidate] = []
    seen: set[str] = set()
    for chunk in chunks:
        if chunk.inspection_status.startswith("requires_"):
            continue
        for raw in chunk.text.splitlines():
            statement = _clean_statement(raw)
            if len(statement) < 6 or len(statement) > 1000:
                continue
            if not REQUIREMENT_TRIGGER_PATTERN.search(statement):
                continue
            normalized = statement.casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            requirement_type, priority, affected_stage = classify_requirement(statement)
            owner = "client" if any(token in statement for token in ["客户", "品牌方", "必须", "不要", "不能"]) else "operator"
            candidates.append(
                RequirementCandidate(
                    source_event_id=chunk.source_event_id,
                    statement=statement,
                    evidence_ref=chunk.chunk_id,
                    requirement_type=requirement_type,
                    priority=priority,
                    affected_stage=affected_stage,
                    owner=owner,
                )
            )
    return candidates


def fact_gap_templates(facts: Iterable[FactInventoryItem]) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []
    for fact in facts:
        if fact.state not in {"missing", "conflicting"} and not (
            fact.state == "unknown" and fact.blocking
        ):
            continue
        state_label = {
            "missing": "缺失",
            "conflicting": "冲突",
            "unknown": "待确认",
        }[fact.state]
        gaps.append(
            {
                "linked_requirement_id": "",
                "impact": "blocking" if fact.blocking or fact.state == "conflicting" else "high_impact",
                "status": "open",
                "description": f"fact:{fact.fact_key} {state_label}；仅依据已绑定证据，不由关键词反推。",
                "recommended_action": f"核对 {fact.fact_key} 的来源证据并由 {fact.owner} 补充或裁决。",
                "owner": fact.owner,
                "question_for_user": "" if fact.owner == "client" else f"请确认 {fact.fact_key}。",
                "question_for_client": f"请补充或确认 {fact.fact_key}。" if fact.owner == "client" else "",
                "question_for_director": "",
            }
        )
    return gaps


def _sync_requirements(
    project: Path, candidates: Iterable[RequirementCandidate]
) -> list[dict[str, str]]:
    path = project / "AD-creative/orchestrator/requirements.csv"
    fields, rows = _read_csv(path)
    existing = {row.get("statement", "").casefold() for row in rows}
    new_rows: list[dict[str, str]] = []
    for candidate in candidates:
        if candidate.statement.casefold() in existing:
            continue
        row = {
            "requirement_id": _next_id([*rows, *new_rows], "requirement_id", "REQ"),
            "source_event_id": candidate.source_event_id,
            "owner": candidate.owner,
            "statement": candidate.statement,
            "requirement_type": candidate.requirement_type,
            "priority": candidate.priority,
            "status": "candidate",
            "confidence": "0.55",
            "scope": "project",
            "affected_stage": candidate.affected_stage,
            "linked_artifacts": "",
            "supersedes_requirement_id": "",
            "open_questions": f"evidence_ref:{candidate.evidence_ref}",
        }
        new_rows.append(row)
        existing.add(candidate.statement.casefold())
    if new_rows:
        _write_csv(path, fields, [*rows, *new_rows])
    return new_rows


def sync_fact_gaps(
    project: Path, facts: Iterable[FactInventoryItem]
) -> list[dict[str, str]]:
    path = project / "AD-creative/orchestrator/gaps.csv"
    fields, rows = _read_csv(path)
    existing = {row.get("description", "") for row in rows}
    new_rows: list[dict[str, str]] = []
    for template in fact_gap_templates(facts):
        if template["description"] in existing:
            continue
        row = {
            "gap_id": _next_id([*rows, *new_rows], "gap_id", "GAP"),
            **template,
        }
        new_rows.append(row)
        existing.add(template["description"])
    if new_rows:
        _write_csv(path, fields, [*rows, *new_rows])
    return new_rows


def run_evidence_intake(
    project: Path,
    source_rows: list[dict[str, str]],
    *,
    max_total_chars: int = 2_000_000,
) -> IntakeResult:
    ingestion = ingest_source_rows(
        project,
        source_rows,
        max_total_chars=max_total_chars,
    )
    all_chunks = load_evidence_chunks(project)
    explicit_facts = explicit_facts_from_evidence(all_chunks)
    existing_facts = load_fact_inventory(project)
    facts = merge_facts(existing_facts, explicit_facts)
    write_fact_inventory(project, facts)
    new_requirements = _sync_requirements(project, requirement_candidates(ingestion.chunks))
    new_gaps = sync_fact_gaps(project, facts)
    return IntakeResult(
        ingestion=ingestion,
        new_requirements=new_requirements,
        new_gaps=new_gaps,
        facts=facts,
    )


def export_intake_analysis_request(project: Path) -> tuple[dict[str, object], Path]:
    chunks = load_evidence_chunks(project)
    if not chunks:
        raise ValueError("no evidence chunks; run intake-evidence first")
    payload: dict[str, object] = {
        "protocol_id": "adco.intake-analysis-request",
        "request_version": "1.0",
        "instructions": [
            "Return only facts supported by evidence_refs from this request.",
            "Use missing only when evidence explicitly says an item is absent.",
            "Use unknown when evidence is insufficient; mark blocking only when it stops downstream work.",
            "Use conflicting when bound evidence disagrees.",
        ],
        "analysis_schema": INTAKE_ANALYSIS_SCHEMA,
        "evidence_path": EVIDENCE_REL.as_posix(),
        "evidence_chunks": [chunk.as_dict() for chunk in chunks],
    }
    path = project / ANALYSIS_REQUEST_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload, path


def validate_analysis_payload(
    payload: object, evidence_ids: set[str]
) -> list[FactInventoryItem]:
    if not isinstance(payload, dict):
        raise ValueError("intake analysis must be a JSON object")
    if payload.get("analysis_version") != "1.0":
        raise ValueError("intake analysis_version must be 1.0")
    raw_facts = payload.get("facts")
    if not isinstance(raw_facts, list):
        raise ValueError("intake analysis facts must be an array")
    facts: list[FactInventoryItem] = []
    seen_keys: set[str] = set()
    for index, raw in enumerate(raw_facts):
        if not isinstance(raw, dict):
            raise ValueError(f"fact[{index}] must be an object")
        required = {
            "fact_key",
            "state",
            "value",
            "evidence_refs",
            "confidence",
            "owner",
            "blocking",
        }
        extra = set(raw) - required
        missing = required - set(raw)
        if missing or extra:
            raise ValueError(
                f"fact[{index}] fields mismatch; missing={sorted(missing)} extra={sorted(extra)}"
            )
        fact_key = raw.get("fact_key")
        state = raw.get("state")
        value = raw.get("value")
        refs = raw.get("evidence_refs")
        confidence = raw.get("confidence")
        owner = raw.get("owner")
        blocking = raw.get("blocking")
        if not isinstance(fact_key, str) or not fact_key.strip():
            raise ValueError(f"fact[{index}].fact_key is required")
        if fact_key in seen_keys:
            raise ValueError(f"duplicate fact_key in imported analysis: {fact_key}")
        seen_keys.add(fact_key)
        if state not in FACT_STATES:
            raise ValueError(f"fact[{index}].state is invalid")
        if not isinstance(value, str):
            raise ValueError(f"fact[{index}].value must be a string")
        if (
            not isinstance(refs, list)
            or not refs
            or not all(isinstance(ref, str) and ref in evidence_ids for ref in refs)
            or len(refs) != len(set(refs))
        ):
            raise ValueError(f"fact[{index}].evidence_refs must bind existing unique chunks")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            raise ValueError(f"fact[{index}].confidence must be between 0 and 1")
        if owner not in FACT_OWNERS:
            raise ValueError(f"fact[{index}].owner is invalid")
        if not isinstance(blocking, bool):
            raise ValueError(f"fact[{index}].blocking must be boolean")
        facts.append(
            FactInventoryItem(
                fact_key=fact_key,
                state=state,
                value=value,
                evidence_refs=list(refs),
                confidence=float(confidence),
                owner=owner,
                blocking=blocking,
            )
        )
    return facts


def import_intake_analysis(
    project: Path, analysis_path: Path
) -> tuple[list[FactInventoryItem], list[dict[str, str]], Path]:
    try:
        payload = json.loads(analysis_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read intake analysis: {exc}") from exc
    evidence_ids = {chunk.chunk_id for chunk in load_evidence_chunks(project)}
    imported = validate_analysis_payload(payload, evidence_ids)
    existing = [fact for fact in load_fact_inventory(project) if fact.fact_key not in {item.fact_key for item in imported}]
    facts = merge_facts(existing, imported)
    path = write_fact_inventory(project, facts)
    gaps = sync_fact_gaps(project, facts)
    return facts, gaps, path
