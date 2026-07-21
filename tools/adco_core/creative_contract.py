"""Evidence-bound creative brief, candidate import, and critic lint contracts."""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .facts import FACT_INVENTORY_REL, load_fact_inventory
from .ingestion import EVIDENCE_REL, load_evidence_chunks
from .safe_write import (
    atomic_write_bytes,
    atomic_write_text,
    read_project_bytes,
    read_project_text,
    safe_project_path,
)


CREATIVE_ROOT = Path("AD-creative/creative")
BRIEF_SNAPSHOT_REL = CREATIVE_ROOT / "brief_snapshot.json"
BRIEF_CONTRACT_REL = CREATIVE_ROOT / "creative_brief_contract.json"
CANDIDATE_SCHEMA_REL = CREATIVE_ROOT / "creative_candidate.schema.json"
GENERATION_REQUEST_REL = CREATIVE_ROOT / "creative_generation_request.json"
OPEN_GAPS_REL = CREATIVE_ROOT / "creative_open_evidence_gaps.json"
BRIEF_MANIFEST_REL = CREATIVE_ROOT / "creative_brief_manifest.json"
CURRENT_CANDIDATE_REL = CREATIVE_ROOT / "current_candidate.json"
CANDIDATE_IMPORT_RECEIPT_REL = CREATIVE_ROOT / "candidate_import_receipt.json"
CRITIC_RECEIPT_REL = CREATIVE_ROOT / "creative_critic_receipt.json"
CONSTRAINT_RESOLUTIONS_REL = CREATIVE_ROOT / "constraint_resolutions.json"
CREATIVE_DIRECTIONS_REL = CREATIVE_ROOT / "creative_directions.md"
OPTION_MATRIX_REL = CREATIVE_ROOT / "option_matrix.csv"
REQUIREMENTS_REL = Path("AD-creative/orchestrator/requirements.csv")
GAPS_REL = Path("AD-creative/orchestrator/gaps.csv")
SOURCE_EVENTS_REL = Path("AD-creative/orchestrator/source_events.csv")
REQUIREMENT_CONFIRMATIONS_REL = Path(
    "AD-creative/orchestrator/requirement_confirmations.json"
)
REQUIREMENT_CONFIRMATION_FIELDS = [
    "evidence_ref",
    "confirmation_ref",
    "confirmed_by",
    "confirmed_at",
]
CONFIRMATION_AUTHORITY: dict[str, tuple[str, str]] = {
    "user_confirmation": ("user", "user_confirmed"),
    "client_confirmation": ("client", "client_confirmed"),
}
REQUIREMENT_CONFIRMATION_SEMANTICS = {"creative_requirement_confirmation"}
CONSTRAINT_CONFIRMATION_SEMANTICS = {
    "approved": "creative_constraint_approval",
    "rejected": "creative_constraint_rejection",
}
POST_BRIEF_CONTROL_SEMANTICS = set(CONSTRAINT_CONFIRMATION_SEMANTICS.values())
AUTHORITY_EVENT_SEMANTICS = (
    REQUIREMENT_CONFIRMATION_SEMANTICS | POST_BRIEF_CONTROL_SEMANTICS
)
BRIEF_ARTIFACT_RELS = (
    BRIEF_SNAPSHOT_REL,
    BRIEF_CONTRACT_REL,
    CANDIDATE_SCHEMA_REL,
    GENERATION_REQUEST_REL,
    OPEN_GAPS_REL,
)

CREATIVE_NARRATIVE_FIELDS = [
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

CREATIVE_STRUCTURE_FIELDS = [
    "runtime_seconds",
    "cast_count",
    "locations",
    "product_exposure",
    "claims",
]

CREATIVE_DIRECTION_FIELDS = CREATIVE_NARRATIVE_FIELDS + CREATIVE_STRUCTURE_FIELDS

CREATIVE_CANDIDATE_SCHEMA: dict[str, object] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "adco.creative-candidate/1.1",
    "title": "ADCO evidence-bound creative candidate",
    "type": "object",
    "required": ["candidate_version", "brief_snapshot_sha256", "directions"],
    "properties": {
        "candidate_version": {"const": "1.1"},
        "brief_snapshot_sha256": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$",
        },
        "directions": {
            "type": "array",
            "minItems": 1,
            "maxItems": 6,
            "items": {
                "type": "object",
                "required": CREATIVE_DIRECTION_FIELDS,
                "properties": {
                    **{
                        field: {"type": "string", "minLength": 1}
                        for field in CREATIVE_NARRATIVE_FIELDS
                        if field != "evidence_refs"
                    },
                    "evidence_refs": {
                        "type": "array",
                        "minItems": 1,
                        "uniqueItems": True,
                        "items": {"type": "string", "minLength": 1},
                    },
                    "runtime_seconds": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 3600,
                    },
                    "cast_count": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "locations": {
                        "type": "array",
                        "minItems": 1,
                        "uniqueItems": True,
                        "items": {"type": "string", "minLength": 1},
                    },
                    "product_exposure": {
                        "type": "object",
                        "required": ["physical_product_visible", "description"],
                        "properties": {
                            "physical_product_visible": {"type": "boolean"},
                            "description": {"type": "string", "minLength": 1},
                        },
                        "additionalProperties": False,
                    },
                    "claims": {
                        "type": "array",
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
    receipt_path: Path | None
    receipt: dict[str, object]
    blocking_issues: list[str]
    warnings: list[str]


@dataclass
class RequirementConfirmationResult:
    requirement_id: str
    path: Path
    receipt: dict[str, object]


@dataclass
class ConstraintResolutionResult:
    constraint_id: str
    direction_id: str
    path: Path
    resolution: dict[str, object]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def persisted_json_bytes(payload: object) -> bytes:
    """Return the exact UTF-8 representation used for persisted JSON artifacts."""
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def payload_sha256(payload: object) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(project: Path, relative: Path) -> list[dict[str, str]]:
    path = project / relative
    if not path.exists():
        return []
    text = read_project_text(project, path)
    with io.StringIO(text, newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _csv_bytes(fields: list[str], rows: Iterable[dict[str, object]]) -> bytes:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return handle.getvalue().encode("utf-8")


def _write_json(project: Path, path: Path, payload: object) -> Path:
    return atomic_write_bytes(project, path, persisted_json_bytes(payload))


def _read_json(project: Path, path: Path) -> object:
    try:
        return json.loads(read_project_text(project, path))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"invalid project JSON artifact {path}: {exc}") from exc


def _optional_json_list(project: Path, relative: Path) -> list[dict[str, object]]:
    path = project / relative
    if not path.exists():
        return []
    payload = _read_json(project, path)
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ValueError(f"{relative.as_posix()} must be a JSON array of objects")
    return [dict(item) for item in payload]


def _validate_snapshot_inputs(project: Path) -> None:
    for relative in (
        EVIDENCE_REL,
        FACT_INVENTORY_REL,
        REQUIREMENTS_REL,
        GAPS_REL,
        SOURCE_EVENTS_REL,
        REQUIREMENT_CONFIRMATIONS_REL,
    ):
        path = project / relative
        if path.exists() or path.is_symlink():
            safe_project_path(project, path, require_file=True)


def _current_snapshot(project: Path) -> dict[str, object]:
    _validate_snapshot_inputs(project)
    all_source_events = _read_csv(project, SOURCE_EVENTS_REL)
    authority_event_ids = {
        str(item.get("source_event_id", "")).strip()
        for item in all_source_events
        if str(item.get("declared_semantics", "")).strip().casefold()
        in AUTHORITY_EVENT_SEMANTICS
        and str(item.get("source_type", "")).strip().casefold()
        in CONFIRMATION_AUTHORITY
    }
    post_brief_control_ids = {
        str(item.get("source_event_id", "")).strip()
        for item in all_source_events
        if str(item.get("declared_semantics", "")).strip().casefold()
        in POST_BRIEF_CONTROL_SEMANTICS
        and str(item.get("source_type", "")).strip().casefold()
        in CONFIRMATION_AUTHORITY
    }
    all_chunks = load_evidence_chunks(project)
    authority_event_chunk_ids = {
        item.chunk_id
        for item in all_chunks
        if item.source_event_id in authority_event_ids
    }
    chunks = [
        item
        for item in all_chunks
        if item.source_event_id not in authority_event_ids
    ]
    facts = [
        item
        for item in load_fact_inventory(project)
        if not set(item.evidence_refs).intersection(authority_event_chunk_ids)
    ]
    requirements = [
        item
        for item in _read_csv(project, REQUIREMENTS_REL)
        if str(item.get("source_event_id", "")).strip()
        not in authority_event_ids
    ]
    gaps = _read_csv(project, GAPS_REL)
    source_events = [
        _snapshot_source_event(project, item)
        for item in all_source_events
        if str(item.get("source_event_id", "")).strip()
        not in post_brief_control_ids
    ]
    confirmations = _optional_json_list(project, REQUIREMENT_CONFIRMATIONS_REL)
    payload: dict[str, object] = {
        "snapshot_version": "1.1",
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
        "source_events": source_events,
        "requirement_confirmations": confirmations,
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


RUNTIME_MAX_PATTERNS = (
    re.compile(
        r"(?:不超过|最多|最长|控制在|上限(?:为)?|≤|<=|up\s+to|max(?:imum)?(?:\s+of)?)\s*"
        r"(?P<value>\d{1,3})\s*(?:秒|s(?:ec(?:ond)?s?)?\b)",
        re.I,
    ),
    re.compile(
        r"(?P<value>\d{1,3})\s*(?:秒|s(?:ec(?:ond)?s?)?\b)\s*"
        r"(?:以内|内|以下|封顶|or\s+less|max(?:imum)?)",
        re.I,
    ),
)
CAST_MAX_PATTERNS = (
    re.compile(
        r"(?:不超过|最多|限|≤|<=|up\s+to|max(?:imum)?(?:\s+of)?)\s*"
        r"(?P<value>\d{1,2}|[一二两三四五六七八九十])\s*"
        r"(?:位|名|个)?\s*(?:演员|人物|角色|人|actors?|people|cast\s+members?)",
        re.I,
    ),
    re.compile(
        r"(?P<value>\d{1,2})\s*(?:actors?|people|cast\s+members?)\s*"
        r"(?:max(?:imum)?|or\s+fewer)",
        re.I,
    ),
)
LOCATION_ALLOWLIST_PATTERN = re.compile(
    r"(?:只能|仅限|只允许|限于|only\s+(?:in|at)|limited\s+to)"
    r"(?P<value>[^。；;\n]{2,160})",
    re.I,
)
PRODUCT_EXPOSURE_PATTERN = re.compile(
    r"(?:必须|需要|要求|真实|must|required).{0,24}"
    r"(?:产品|实物|包装|product).{0,16}"
    r"(?:露出|出镜|展示|可见|曝光|exposure|visible|on[ -]?screen)"
    r"|(?:产品|实物|包装|product).{0,16}"
    r"(?:必须|需要|required|must).{0,16}"
    r"(?:露出|出镜|展示|可见|曝光|exposure|visible|on[ -]?screen)",
    re.I,
)
PRODUCT_EXPOSURE_PROHIBITED_PATTERN = re.compile(
    r"(?:禁止|不得|不能|避免|无需|不需要|不允许|严禁).{0,20}"
    r"(?:产品|实物|包装|product).{0,16}"
    r"(?:露出|出镜|展示|可见|曝光|exposure|visible|on[ -]?screen)|"
    r"(?:产品|实物|包装|product).{0,16}"
    r"(?:禁止|不得|不能|避免|无需|不需要|不允许|严禁|must\s+not|"
    r"should\s+not|avoid|without|no).{0,16}"
    r"(?:露出|出镜|展示|可见|曝光|exposure|visible|on[ -]?screen)|"
    r"(?:must\s+not|should\s+not|avoid|without|no).{0,20}"
    r"(?:product|packaging).{0,16}(?:exposure|visible|on[ -]?screen)",
    re.I,
)
PROHIBITED_CLAIM_PATTERN = re.compile(
    r"(?:不得(?:使用|作出|做出)?|不能(?:使用|作出|做出)?|禁止(?:使用|作出|做出)?|"
    r"不允许(?:使用|作出|做出)?|must\s+not\s+(?:use|make|include)?|"
    r"do(?:es)?\s+not\s+(?:use|make|include)?|(?<!\w)no\b)\s*[:：]?\s*"
    r"(?P<value>[^。；;\n]{1,160}?)"
    r"(?:宣称|声称|表述|claims?\b)",
    re.I,
)
CONSTRAINT_SPLIT_PATTERN = re.compile(r"\s*(?:、|，|,|/|和|与|及|或|\band\b|\bor\b)\s*", re.I)
LOCATION_TRAILING_PATTERN = re.compile(
    r"(?:内)?(?:拍摄|取景|完成|进行|两个?场景|场景|locations?|shoot(?:ing)?)$",
    re.I,
)
LOCATION_MARKERS = (
    "便利店冷柜",
    "便利店店内",
    "便利店内",
    "便利店门口",
    "公寓客厅",
    "摄影棚内",
    "摄影棚",
    "办公室",
    "会议室",
    "咖啡馆",
    "美术馆",
    "博物馆",
    "图书馆",
    "学校",
    "便利店",
    "收银台",
    "货架",
    "冰箱",
    "冰柜",
    "冷柜",
    "店内",
    "客厅",
    "门口",
    "卧室",
    "卫生间",
    "浴室",
    "仓库",
    "厨房",
    "餐厅",
    "酒吧",
    "天台",
    "地铁",
    "超市",
    "公园",
    "海边",
    "街道",
    "车内",
    "棚内",
    "apartment living room",
    "convenience-store entrance",
    "convenience store entrance",
    "convenience-store interior",
    "convenience store interior",
    "refrigerated case",
    "cold case",
    "checkout counter",
    "office",
    "bedroom",
    "bathroom",
    "warehouse",
    "kitchen",
    "restaurant",
    "bar",
    "rooftop",
    "subway",
    "supermarket",
    "studio",
    "museum",
    "gallery",
    "library",
    "school",
)

DIRECTION_COUNT_PATTERNS = (
    re.compile(
        r"(?:只要|仅要|需要|要求|提供|给出|生成|保留|选择)\s*"
        r"(?P<value>\d{1,2}|[一二两三四五六])\s*(?:个|条)?\s*"
        r"(?:创意)?(?:方向|方案|概念)",
        re.I,
    ),
    re.compile(
        r"(?P<value>\d{1,2})\s+(?:creative\s+)?(?:directions?|concepts?|options?)",
        re.I,
    ),
)
CRITIC_REQUEST_PATTERN = re.compile(
    r"独立(?:创意)?(?:审查|复核|评审|critic)|(?:independent\s+)?critic\b|"
    r"双人复核|第二视角",
    re.I,
)
CRITIC_NEGATION_PATTERN = re.compile(
    r"(?:不需要|无需|不要|不要求|without|no)\s*(?:独立)?\s*(?:创意)?\s*"
    r"(?:审查|复核|评审|critic)",
    re.I,
)
HARD_REQUIREMENT_PATTERN = re.compile(
    r"制作硬条件|硬性条件|必须|不得|不能|禁止|严禁|不允许|最多|不超过|"
    r"以内|只能|仅限|只允许|一天拍完|一日内拍完|任何虚构数据|"
    r"\bmust\b|\brequired\b|\bprohibited\b|\bforbidden\b|"
    r"\bmaximum\b|\bmax\b|\bonly\b|\bno\s+invented\s+data\b|"
    r"\bone[- ]day\s+shoot\b",
    re.I,
)
ONE_DAY_SHOOT_PATTERN = re.compile(
    r"一天(?:内)?拍完|一日(?:内)?拍完|单日(?:内)?拍完|one[- ]day\s+shoot",
    re.I,
)
NO_FABRICATED_DATA_PATTERN = re.compile(
    r"(?:禁止|不得|不能|不允许|严禁|不要).{0,16}(?:任何)?(?:虚构|编造|捏造)"
    r"(?:的)?(?:数据|事实|信息)|"
    r"(?:no|without|must\s+not\s+use).{0,12}(?:invented|fabricated|made[- ]up)"
    r"\s+(?:data|facts?|information)",
    re.I,
)
CONFIRMED_REQUIREMENT_STATUSES = {
    "approved",
    "accepted",
    "confirmed",
    "confirmed_by_workflow",
    "locked",
}


def _number_value(value: str) -> int | None:
    if value.isdigit():
        return int(value)
    return {
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }.get(value)


def _first_number(patterns: Iterable[re.Pattern[str]], statement: str) -> int | None:
    for pattern in patterns:
        match = pattern.search(statement)
        if match:
            return _number_value(match.group("value"))
    return None


def _clean_constraint_item(value: str) -> str:
    value = value.strip(" ：:，,。.；;()（）")
    value = re.sub(r"^(?:在|于|to|in|at)\s*", "", value, flags=re.I)
    value = re.sub(r"^(?:使用|涉及|包含|关于|use)\s*", "", value, flags=re.I)
    value = LOCATION_TRAILING_PATTERN.sub("", value).strip()
    return value.strip(" ：:，,。.；;()（）")


def _allowed_locations(statement: str) -> list[str]:
    if not re.search(r"场景|拍摄|取景|location|shoot", statement, re.I):
        return []
    match = LOCATION_ALLOWLIST_PATTERN.search(statement)
    if not match:
        return []
    raw = match.group("value")
    raw = re.split(r"(?:，|,)?\s*(?:且|并且|同时|while\b|with\b)", raw, maxsplit=1, flags=re.I)[0]
    values = [_clean_constraint_item(item) for item in CONSTRAINT_SPLIT_PATTERN.split(raw)]
    return list(dict.fromkeys(item for item in values if len(item) >= 2))


def _prohibited_claims(statement: str) -> list[str]:
    match = PROHIBITED_CLAIM_PATTERN.search(statement)
    if not match:
        return []
    values = [_clean_constraint_item(item) for item in CONSTRAINT_SPLIT_PATTERN.split(match.group("value"))]
    return list(dict.fromkeys(item for item in values if len(item) >= 2))


def _binding_tokens(value: object) -> set[str]:
    return {
        item.strip()
        for item in re.split(r"[;\n]+", str(value or ""))
        if item.strip()
    }


def _source_event_sha256(source_event: dict[str, object]) -> str:
    return payload_sha256(
        {
            key: str(source_event.get(key, "")).strip()
            for key in sorted(source_event)
        }
    )


def _snapshot_source_event(
    project: Path, source_event: dict[str, object]
) -> dict[str, object]:
    """Add a content fingerprint for pre-brief typed confirmation evidence."""
    snapshot_event: dict[str, object] = dict(source_event)
    semantics = str(source_event.get("declared_semantics", "")).strip().casefold()
    source_type = str(source_event.get("source_type", "")).strip().casefold()
    if (
        semantics not in REQUIREMENT_CONFIRMATION_SEMANTICS
        or source_type not in CONFIRMATION_AUTHORITY
    ):
        return snapshot_event
    raw_path = str(source_event.get("file_paths", "")).strip()
    try:
        if not raw_path or any(
            separator in raw_path for separator in (";", "\n", "\r")
        ):
            raise ValueError("confirmation evidence path is not singular")
        evidence_bytes = read_project_bytes(project, project / Path(raw_path))
    except (OSError, ValueError):
        snapshot_event["confirmation_evidence_sha256"] = "INVALID"
    else:
        snapshot_event["confirmation_evidence_sha256"] = hashlib.sha256(
            evidence_bytes
        ).hexdigest()
    return snapshot_event


def _typed_confirmation_event(
    project: Path,
    confirmation_ref: str,
    *,
    expected_semantics: set[str],
    required_requirements: set[str],
    required_artifacts: set[str],
) -> dict[str, str]:
    """Validate one authority event and its immutable project-local evidence.

    A display name is never accepted as authority. The reference must resolve
    to one typed user/client confirmation event whose owner, trust class,
    semantics, and exact target bindings all agree.
    """
    match = re.fullmatch(
        r"(?P<kind>user_confirmation|client_confirmation):"
        r"(?P<event_id>[A-Za-z0-9][A-Za-z0-9._-]{0,127})",
        confirmation_ref.strip(),
    )
    if match is None:
        raise ValueError(
            "confirmation_ref must be user_confirmation:<source_event_id> or "
            "client_confirmation:<source_event_id>"
        )
    kind = match.group("kind")
    event_id = match.group("event_id")
    authority_class, required_trust = CONFIRMATION_AUTHORITY[kind]
    matches = [
        item
        for item in _read_csv(project, SOURCE_EVENTS_REL)
        if str(item.get("source_event_id", "")).strip() == event_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"confirmation_ref must match exactly one source event: {confirmation_ref}"
        )
    source = matches[0]
    if str(source.get("source_type", "")).strip().casefold() != kind:
        raise ValueError(
            f"confirmation source_type must be {kind}: {event_id}"
        )
    if str(source.get("source_owner", "")).strip().casefold() != authority_class:
        raise ValueError(
            f"confirmation source_owner must be {authority_class}: {event_id}"
        )
    if str(source.get("trust_level", "")).strip().casefold() != required_trust:
        raise ValueError(
            f"confirmation trust_level must be {required_trust}: {event_id}"
        )
    semantics = str(source.get("declared_semantics", "")).strip().casefold()
    if semantics not in expected_semantics:
        raise ValueError(
            "confirmation declared_semantics does not authorize this operation: "
            f"{semantics or 'missing'}"
        )
    actual_requirements = _binding_tokens(source.get("affects_requirements", ""))
    if actual_requirements != required_requirements:
        raise ValueError(
            "confirmation affects_requirements must exactly bind "
            f"{sorted(required_requirements)}; got {sorted(actual_requirements)}"
        )
    actual_artifacts = _binding_tokens(source.get("affects_artifacts", ""))
    if actual_artifacts != required_artifacts:
        raise ValueError(
            "confirmation affects_artifacts must exactly bind "
            f"{sorted(required_artifacts)}; got {sorted(actual_artifacts)}"
        )
    received_at = str(source.get("received_at", "")).strip()
    try:
        parsed_at = datetime.fromisoformat(received_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"confirmation received_at is not an ISO-8601 timestamp: {event_id}"
        ) from exc
    if parsed_at.tzinfo is None:
        raise ValueError(f"confirmation received_at must include a timezone: {event_id}")

    raw_path = str(source.get("file_paths", "")).strip()
    if not raw_path or any(separator in raw_path for separator in (";", "\n", "\r")):
        raise ValueError(
            f"confirmation event must bind exactly one project-local evidence file: {event_id}"
        )
    relative_path = Path(raw_path)
    if (
        relative_path.is_absolute()
        or any(part in {"", ".", ".."} for part in relative_path.parts)
        or relative_path.as_posix() != raw_path
    ):
        raise ValueError(
            f"confirmation evidence path must be canonical and project-relative: {event_id}"
        )
    evidence_bytes = read_project_bytes(project, project / relative_path)
    return {
        "confirmation_ref": confirmation_ref.strip(),
        "confirmation_id": event_id,
        "authority_class": authority_class,
        "source_event_sha256": _source_event_sha256(source),
        "evidence_path": relative_path.as_posix(),
        "evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
        "received_at": received_at,
    }


def _requirement_evidence_ref(requirement: dict[str, object]) -> str:
    direct = str(requirement.get("evidence_ref", "")).strip()
    if direct:
        return direct
    match = re.search(
        r"(?:^|[;\s])evidence_ref:([^;\s]+)",
        str(requirement.get("open_questions", "")),
    )
    return match.group(1).strip() if match else ""


def _requirement_binding_payload(requirement: dict[str, object]) -> dict[str, str]:
    fields = (
        "requirement_id",
        "source_event_id",
        "owner",
        "statement",
        "requirement_type",
        "priority",
        "status",
        "scope",
        "affected_stage",
        "evidence_ref",
        "confirmation_ref",
        "confirmed_by",
        "confirmed_at",
    )
    return {field: str(requirement.get(field, "")).strip() for field in fields}


def confirm_creative_requirement(
    project: Path,
    requirement_id: str,
    *,
    confirmation_ref: str,
    evidence_ref: str = "",
) -> RequirementConfirmationResult:
    """Bind one requirement to source evidence and a typed authority event."""
    requirements_path = project / REQUIREMENTS_REL
    text = read_project_text(project, requirements_path)
    with io.StringIO(text, newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    matches = [row for row in rows if row.get("requirement_id", "").strip() == requirement_id]
    if len(matches) != 1:
        raise ValueError(f"requirement_id must match exactly one row: {requirement_id}")
    row = matches[0]
    source_event_id = row.get("source_event_id", "").strip()
    source_rows = {
        item.get("source_event_id", "").strip(): item
        for item in _read_csv(project, SOURCE_EVENTS_REL)
        if item.get("source_event_id", "").strip()
    }
    if source_event_id not in source_rows:
        raise ValueError(
            f"requirement source_event_id is not registered: {source_event_id or 'missing'}"
        )
    confirmation = _typed_confirmation_event(
        project,
        confirmation_ref,
        expected_semantics=REQUIREMENT_CONFIRMATION_SEMANTICS,
        required_requirements={requirement_id},
        required_artifacts=set(),
    )
    source_received_at = str(source_rows[source_event_id].get("received_at", "")).strip()
    try:
        source_time = datetime.fromisoformat(source_received_at.replace("Z", "+00:00"))
        confirmation_time = datetime.fromisoformat(
            confirmation["received_at"].replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ValueError(
            "requirement and confirmation source events must use ISO-8601 timestamps"
        ) from exc
    if source_time.tzinfo is None or confirmation_time.tzinfo is None:
        raise ValueError(
            "requirement and confirmation source event timestamps must include timezones"
        )
    if confirmation_time < source_time:
        raise ValueError("requirement confirmation predates the requirement source event")
    selected_ref = evidence_ref.strip() or _requirement_evidence_ref(row)
    chunks = {item.chunk_id: item for item in load_evidence_chunks(project)}
    chunk = chunks.get(selected_ref)
    if chunk is None:
        raise ValueError(f"requirement evidence_ref is not an existing chunk: {selected_ref or 'missing'}")
    if chunk.source_event_id != source_event_id:
        raise ValueError(
            "requirement evidence_ref does not belong to its source_event_id: "
            f"{selected_ref} -> {chunk.source_event_id}"
        )

    confirmed_at = confirmation["received_at"]
    row.update(
        {
            "status": "confirmed_by_workflow",
            "confidence": "1.0",
            "evidence_ref": selected_ref,
            "confirmation_ref": confirmation["confirmation_ref"],
            "confirmed_by": confirmation["authority_class"],
            "confirmed_at": confirmed_at,
        }
    )
    for field in REQUIREMENT_CONFIRMATION_FIELDS:
        if field not in fields:
            fields.append(field)
    binding_sha = payload_sha256(_requirement_binding_payload(row))
    receipt: dict[str, object] = {
        "protocol_id": "adco.requirement-confirmation",
        "receipt_version": "1.1",
        "requirement_id": requirement_id,
        "requirement_binding_sha256": binding_sha,
        "source_event_id": source_event_id,
        "evidence_ref": selected_ref,
        "evidence_sha256": chunk.sha256,
        "confirmation_ref": confirmation["confirmation_ref"],
        "confirmation_id": confirmation["confirmation_id"],
        "confirmation_source_event_sha256": confirmation["source_event_sha256"],
        "confirmation_evidence_path": confirmation["evidence_path"],
        "confirmation_evidence_sha256": confirmation["evidence_sha256"],
        "authority_class": confirmation["authority_class"],
        "confirmed_by": confirmation["authority_class"],
        "confirmed_at": confirmed_at,
    }
    confirmations = _optional_json_list(project, REQUIREMENT_CONFIRMATIONS_REL)
    confirmations = [
        item for item in confirmations if item.get("requirement_id") != requirement_id
    ]
    confirmations.append(receipt)
    confirmations.sort(key=lambda item: str(item.get("requirement_id", "")))

    # The CSV row is the commit point. An interrupted pre-write can leave only
    # an unused receipt; it can never make an unconfirmed row authoritative.
    confirmation_path = _write_json(
        project,
        project / REQUIREMENT_CONFIRMATIONS_REL,
        confirmations,
    )
    atomic_write_bytes(project, requirements_path, _csv_bytes(fields, rows))
    return RequirementConfirmationResult(
        requirement_id=requirement_id,
        path=confirmation_path,
        receipt=receipt,
    )


def _requirement_authority(
    project: Path,
    snapshot: dict[str, object],
    requirement: dict[str, object],
) -> dict[str, object]:
    status = str(requirement.get("status", "")).strip().casefold()
    owner = str(requirement.get("owner", "")).strip().casefold()
    source_event_id = str(requirement.get("source_event_id", "")).strip()
    requirement_id = str(requirement.get("requirement_id", "")).strip()
    evidence_ref = _requirement_evidence_ref(requirement)
    confirmation_ref = str(requirement.get("confirmation_ref", "")).strip()
    confirmed_by = str(requirement.get("confirmed_by", "")).strip()
    confirmed_at = str(requirement.get("confirmed_at", "")).strip()
    try:
        confidence = float(requirement.get("confidence", ""))
    except (TypeError, ValueError):
        confidence = None

    source_ids = {
        str(item.get("source_event_id", "")).strip()
        for item in snapshot.get("source_events", [])
        if isinstance(item, dict)
    }
    evidence = {
        str(item.get("chunk_id", "")).strip(): item
        for item in snapshot.get("evidence", [])
        if isinstance(item, dict)
    }
    linked_chunk = evidence.get(evidence_ref)
    binding_sha = payload_sha256(_requirement_binding_payload(requirement))
    try:
        confirmation_event = _typed_confirmation_event(
            project,
            confirmation_ref,
            expected_semantics=REQUIREMENT_CONFIRMATION_SEMANTICS,
            required_requirements={requirement_id},
            required_artifacts=set(),
        )
    except (OSError, ValueError):
        confirmation_event = None
    confirmation = next(
        (
            item
            for item in snapshot.get("requirement_confirmations", [])
            if isinstance(item, dict)
            and item.get("protocol_id") == "adco.requirement-confirmation"
            and item.get("receipt_version") == "1.1"
            and item.get("requirement_id") == requirement_id
            and item.get("requirement_binding_sha256") == binding_sha
            and item.get("source_event_id") == source_event_id
            and item.get("evidence_ref") == evidence_ref
            and item.get("confirmation_ref") == confirmation_ref
            and item.get("confirmed_by") == confirmed_by
            and item.get("confirmed_at") == confirmed_at
            and isinstance(linked_chunk, dict)
            and item.get("evidence_sha256") == linked_chunk.get("sha256")
            and isinstance(confirmation_event, dict)
            and item.get("confirmation_id")
            == confirmation_event.get("confirmation_id")
            and item.get("confirmation_source_event_sha256")
            == confirmation_event.get("source_event_sha256")
            and item.get("confirmation_evidence_path")
            == confirmation_event.get("evidence_path")
            and item.get("confirmation_evidence_sha256")
            == confirmation_event.get("evidence_sha256")
            and item.get("authority_class")
            == confirmation_event.get("authority_class")
        ),
        None,
    )
    authoritative = bool(
        status in CONFIRMED_REQUIREMENT_STATUSES
        and owner in {"client", "operator"}
        and source_event_id in source_ids
        and isinstance(linked_chunk, dict)
        and linked_chunk.get("source_event_id") == source_event_id
        and isinstance(confirmation_event, dict)
        and confirmed_by == confirmation_event.get("authority_class")
        and confirmed_at == confirmation_event.get("received_at")
        and confirmed_at
        and confirmation is not None
    )
    reason = (
        "workflow-confirmed requirement bound to source evidence and an exact typed authority event"
        if authoritative
        else "requirement authority is not workflow-confirmed against source evidence and a typed authority event"
    )
    return {
        "authoritative": authoritative,
        "status": status or "missing",
        "owner": owner or "missing",
        "source_event_id": source_event_id or "missing",
        "evidence_ref": evidence_ref or "missing",
        "confirmation_ref": confirmation_ref or "missing",
        "confirmed_by": confirmed_by or "missing",
        "confirmed_at": confirmed_at or "missing",
        "confirmation_receipt": "matched" if confirmation is not None else "missing_or_stale",
        "confidence": confidence,
        "reason": reason,
    }


def _hard_requirement_clauses(statement: str) -> list[str]:
    clauses = [
        item.strip(" ：:，,。.；;()（）")
        for item in re.split(r"[；;。\n]+", statement)
    ]
    return [item for item in clauses if item]


def _extract_hard_constraints(
    project: Path, snapshot: dict[str, object]
) -> list[dict[str, object]]:
    requirements = snapshot.get("requirements")
    if not isinstance(requirements, list):
        return []
    constraints: list[dict[str, object]] = []
    for index, requirement in enumerate(requirements, start=1):
        if not isinstance(requirement, dict):
            continue
        statement = str(requirement.get("statement", "")).strip()
        if not statement:
            continue
        requirement_id = str(requirement.get("requirement_id", "")).strip() or f"REQ-{index:03d}"
        authority = _requirement_authority(project, snapshot, requirement)
        used_ids: set[str] = set()
        for clause_index, clause in enumerate(_hard_requirement_clauses(statement), start=1):
            extracted: list[tuple[str, object]] = []
            runtime_max = _first_number(RUNTIME_MAX_PATTERNS, clause)
            if runtime_max is not None:
                extracted.append(("runtime_max_seconds", runtime_max))
            cast_max = _first_number(CAST_MAX_PATTERNS, clause)
            if cast_max is not None:
                extracted.append(("cast_max", cast_max))
            locations = _allowed_locations(clause)
            if locations:
                extracted.append(("location_allowlist", locations))
            if PRODUCT_EXPOSURE_PROHIBITED_PATTERN.search(clause):
                extracted.append(("product_exposure_required", False))
            elif PRODUCT_EXPOSURE_PATTERN.search(clause):
                extracted.append(("product_exposure_required", True))
            claims = _prohibited_claims(clause)
            if claims:
                extracted.append(("prohibited_claims", claims))

            needs_manual_review = bool(
                (HARD_REQUIREMENT_PATTERN.search(clause) and not extracted)
                or ONE_DAY_SHOOT_PATTERN.search(clause)
                or NO_FABRICATED_DATA_PATTERN.search(clause)
            )
            if needs_manual_review:
                extracted.append(("manual_review", clause))

            for kind, value in extracted:
                base_id = f"{requirement_id}:{kind}"
                constraint_id = base_id
                if constraint_id in used_ids:
                    constraint_id = f"{requirement_id}:clause-{clause_index}:{kind}"
                used_ids.add(constraint_id)
                constraints.append(
                    {
                        "constraint_id": constraint_id,
                        "requirement_id": requirement_id,
                        "kind": kind,
                        "value": value,
                        "statement": clause,
                        "authority": authority,
                    }
                )
    return constraints


def _requested_direction_count(requirements: object) -> int | None:
    if not isinstance(requirements, list):
        return None
    values: list[int] = []
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        statement = str(requirement.get("statement", ""))
        for pattern in DIRECTION_COUNT_PATTERNS:
            match = pattern.search(statement)
            if match and (parsed := _number_value(match.group("value"))) is not None:
                if 1 <= parsed <= 6:
                    values.append(parsed)
                break
    unique = list(dict.fromkeys(values))
    if len(unique) > 1:
        raise ValueError(
            "conflicting explicit creative direction counts in current requirements: "
            + ", ".join(str(item) for item in unique)
        )
    return unique[0] if unique else None


def _critic_requested(requirements: object) -> bool:
    return bool(
        isinstance(requirements, list)
        and any(
            isinstance(requirement, dict)
            and CRITIC_REQUEST_PATTERN.search(str(requirement.get("statement", "")))
            and not CRITIC_NEGATION_PATTERN.search(str(requirement.get("statement", "")))
            for requirement in requirements
        )
    )


def _verified_brief(
    project: Path,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    manifest_path = project / BRIEF_MANIFEST_REL
    if not manifest_path.exists():
        raise ValueError("creative brief manifest is missing; run creative-brief first")
    manifest = _read_json(project, manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("creative brief manifest must be a JSON object")
    if (
        manifest.get("protocol_id") != "adco.creative-brief-manifest"
        or manifest.get("manifest_version") != "1.0"
    ):
        raise ValueError("creative brief manifest protocol/version is invalid")
    artifacts = manifest.get("artifacts")
    expected = {relative.as_posix() for relative in BRIEF_ARTIFACT_RELS}
    if not isinstance(artifacts, dict) or set(artifacts) != expected:
        raise ValueError("creative brief manifest artifact set is incomplete or unexpected")

    parsed: dict[Path, object] = {}
    for relative in BRIEF_ARTIFACT_RELS:
        entry = artifacts.get(relative.as_posix())
        if not isinstance(entry, dict) or set(entry) != {"sha256", "byte_length"}:
            raise ValueError(f"creative brief manifest entry is invalid: {relative}")
        data = read_project_bytes(project, project / relative)
        if entry.get("sha256") != hashlib.sha256(data).hexdigest():
            raise ValueError(f"creative brief artifact hash mismatch: {relative}")
        if entry.get("byte_length") != len(data):
            raise ValueError(f"creative brief artifact length mismatch: {relative}")
        try:
            parsed[relative] = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ValueError(f"creative brief artifact is invalid JSON: {relative}: {exc}") from exc

    snapshot = parsed[BRIEF_SNAPSHOT_REL]
    contract = parsed[BRIEF_CONTRACT_REL]
    if not isinstance(snapshot, dict) or not isinstance(contract, dict):
        raise ValueError("creative brief snapshot and contract must be JSON objects")
    stored_sha = str(snapshot.get("brief_snapshot_sha256", ""))
    unhashed = dict(snapshot)
    unhashed.pop("brief_snapshot_sha256", None)
    recomputed_sha = payload_sha256(unhashed)
    if not stored_sha or stored_sha != recomputed_sha:
        raise ValueError("creative brief snapshot self-hash mismatch")
    if manifest.get("brief_snapshot_sha256") != stored_sha:
        raise ValueError("creative brief manifest is bound to a different snapshot")
    if contract.get("brief_snapshot_sha256") != stored_sha:
        raise ValueError("creative brief contract is bound to a different snapshot")
    current_sha = str(_current_snapshot(project).get("brief_snapshot_sha256", ""))
    if current_sha != stored_sha:
        raise ValueError(
            "creative brief is stale against current evidence/facts/requirements/gaps; run creative-brief again"
        )
    return snapshot, contract, manifest


def create_creative_brief(project: Path) -> CreativeBriefResult:
    snapshot = _current_snapshot(project)
    snapshot_sha = str(snapshot["brief_snapshot_sha256"])
    evidence_refs = [
        str(item.get("chunk_id"))
        for item in snapshot["evidence"]
        if isinstance(item, dict) and item.get("chunk_id")
    ]
    open_gaps = _open_gaps(snapshot)
    hard_constraints = _extract_hard_constraints(project, snapshot)
    requested_direction_count = _requested_direction_count(snapshot["requirements"])
    critic_required_by_brief = _critic_requested(snapshot["requirements"])
    candidate_schema = copy.deepcopy(CREATIVE_CANDIDATE_SCHEMA)
    if requested_direction_count is not None:
        direction_schema = candidate_schema["properties"]["directions"]
        assert isinstance(direction_schema, dict)
        direction_schema["minItems"] = requested_direction_count
        direction_schema["maxItems"] = requested_direction_count
    contract = {
        "protocol_id": "adco.creative-brief-contract",
        "contract_version": "1.1",
        "brief_snapshot_sha256": snapshot_sha,
        "evidence_refs": evidence_refs,
        "confirmed_facts": [
            fact
            for fact in snapshot["facts"]
            if isinstance(fact, dict) and fact.get("state") == "present"
        ],
        "requirements": snapshot["requirements"],
        "hard_constraints": hard_constraints,
        "open_evidence_gaps": open_gaps,
        "candidate_contract": {
            "requested_direction_count": requested_direction_count,
            "allowed_direction_count_range": [1, 6],
            "direction_count_policy": "match_explicit_request_else_smallest_sufficient_set",
            "critic_required_by_brief": critic_required_by_brief,
            "critic_policy": "only_when_explicit_or_consequential_decision_boundary",
            "mechanism_deduplication_required": True,
            "every_direction_requires_evidence_refs": True,
            "structure_pass_is_not_creative_pass": True,
        },
    }
    request = {
        "protocol_id": "adco.creative-generation-request",
        "request_version": "1.1",
        "model_role": "GPT-5.6 Sol creative reasoning",
        "brief_snapshot_sha256": snapshot_sha,
        "contract_path": BRIEF_CONTRACT_REL.as_posix(),
        "candidate_schema_path": CANDIDATE_SCHEMA_REL.as_posix(),
        "hard_constraints": hard_constraints,
        "instructions": [
            (
                f"Generate exactly {requested_direction_count} genuinely distinct direction(s), as requested."
                if requested_direction_count is not None
                else "Generate the smallest sufficient set of genuinely distinct directions; one strong direction is valid."
            ),
            "Differentiate creative mechanism, not only name or wording.",
            "Bind every direction to evidence_refs from the snapshot.",
            "Treat every authoritative hard_constraint as mandatory; keep unconfirmed or manual_review constraints unresolved and do not import until reviewed. Evidence refs alone never prove compliance.",
            "Populate runtime_seconds, cast_count, locations, product_exposure, and claims as machine-checkable fields; keep prose consistent with them.",
            "Do not introduce a location or sub-location outside a location_allowlist, and do not use any prohibited_claim.",
            (
                "Run an independent Critic because the brief explicitly requests it."
                if critic_required_by_brief
                else "Do not add an independent Critic unless a consequential decision boundary or explicit request requires it."
            ),
            "Do not claim structural validity as creative quality approval.",
        ],
    }
    artifact_payloads: dict[Path, object] = {
        BRIEF_SNAPSHOT_REL: snapshot,
        BRIEF_CONTRACT_REL: contract,
        CANDIDATE_SCHEMA_REL: candidate_schema,
        GENERATION_REQUEST_REL: request,
        OPEN_GAPS_REL: {
            "brief_snapshot_sha256": snapshot_sha,
            "open_evidence_gaps": open_gaps,
        },
    }
    artifact_bytes = {
        relative: persisted_json_bytes(payload)
        for relative, payload in artifact_payloads.items()
    }
    manifest: dict[str, object] = {
        "protocol_id": "adco.creative-brief-manifest",
        "manifest_version": "1.0",
        "brief_snapshot_sha256": snapshot_sha,
        "artifacts": {
            relative.as_posix(): {
                "sha256": hashlib.sha256(data).hexdigest(),
                "byte_length": len(data),
            }
            for relative, data in artifact_bytes.items()
        },
    }
    paths = [
        atomic_write_bytes(project, project / relative, artifact_bytes[relative])
        for relative in BRIEF_ARTIFACT_RELS
    ]
    # The manifest is the brief commit point and is replaced only after every
    # member has been durably written.
    paths.append(_write_json(project, project / BRIEF_MANIFEST_REL, manifest))
    _verified_brief(project)
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
    if payload.get("candidate_version") != "1.1":
        errors.append("candidate_version must be 1.1")
    try:
        snapshot, contract_payload, _manifest = _verified_brief(project)
        current_snapshot_sha = str(snapshot.get("brief_snapshot_sha256", ""))
    except ValueError as exc:
        errors.append(str(exc))
        current_snapshot_sha = ""
        contract_payload = {}
    if payload.get("brief_snapshot_sha256") != current_snapshot_sha:
        errors.append("brief_snapshot_sha256 does not match the current creative brief")
    directions = payload.get("directions")
    requested_direction_count: int | None = None
    try:
        raw_requested = contract_payload.get("candidate_contract", {}).get(
            "requested_direction_count"
        )
        if raw_requested is not None and (
            not isinstance(raw_requested, int)
            or isinstance(raw_requested, bool)
            or not 1 <= raw_requested <= 6
        ):
            errors.append("creative brief requested_direction_count is invalid")
        elif isinstance(raw_requested, int):
            requested_direction_count = raw_requested
    except AttributeError:
        errors.append("creative brief candidate_contract is invalid")
    if not isinstance(directions, list) or not 1 <= len(directions) <= 6:
        errors.append("creative-import requires 1-6 directions")
        return errors, warnings
    if (
        requested_direction_count is not None
        and len(directions) != requested_direction_count
    ):
        errors.append(
            "creative-import direction count must match requested_direction_count="
            f"{requested_direction_count}"
        )
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
        for field in CREATIVE_NARRATIVE_FIELDS:
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
        runtime_seconds = direction.get("runtime_seconds")
        if (
            not isinstance(runtime_seconds, int)
            or isinstance(runtime_seconds, bool)
            or not 1 <= runtime_seconds <= 3600
        ):
            errors.append(f"directions[{index}].runtime_seconds must be an integer in 1..3600")
        cast_count = direction.get("cast_count")
        if (
            not isinstance(cast_count, int)
            or isinstance(cast_count, bool)
            or not 0 <= cast_count <= 100
        ):
            errors.append(f"directions[{index}].cast_count must be an integer in 0..100")
        locations = direction.get("locations")
        if (
            not isinstance(locations, list)
            or not locations
            or len(locations) != len(set(locations))
            or not all(isinstance(item, str) and item.strip() for item in locations)
        ):
            errors.append(f"directions[{index}].locations must be non-empty unique strings")
        product_exposure = direction.get("product_exposure")
        if (
            not isinstance(product_exposure, dict)
            or set(product_exposure) != {"physical_product_visible", "description"}
            or not isinstance(product_exposure.get("physical_product_visible"), bool)
            or not isinstance(product_exposure.get("description"), str)
            or not product_exposure.get("description", "").strip()
        ):
            errors.append(
                f"directions[{index}].product_exposure must declare visibility and description"
            )
        claims = direction.get("claims")
        if (
            not isinstance(claims, list)
            or len(claims) != len(set(claims))
            or not all(isinstance(item, str) and item.strip() for item in claims)
        ):
            errors.append(f"directions[{index}].claims must be unique non-empty strings")
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


def validate_creative_candidate(
    project: Path, payload: object
) -> tuple[list[str], list[str]]:
    """Public scoped-validator entrypoint for the current candidate contract."""
    return _candidate_validation_errors(project, payload)


def _candidate_version_path(project: Path, exact_bytes: bytes) -> Path:
    current = project / CURRENT_CANDIDATE_REL
    if current.exists() and read_project_bytes(project, current) == exact_bytes:
        directory = project / CREATIVE_ROOT / "candidates"
        if directory.exists():
            safe_project_path(project, directory / ".sentinel", create_parent=False)
        matching = [
            path
            for path in sorted(
                directory.glob("candidate_v*.json") if directory.exists() else []
            )
            if path.is_file() and read_project_bytes(project, path) == exact_bytes
        ]
        if matching:
            return matching[-1]
    directory = project / CREATIVE_ROOT / "candidates"
    safe_project_path(project, directory / ".sentinel", create_parent=True)
    versions = [
        int(match.group(1))
        for path in directory.glob("candidate_v*.json")
        if path.is_file()
        and not path.is_symlink()
        and (match := re.fullmatch(r"candidate_v(\d+)\.json", path.name))
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
- runtime seconds: {raw['runtime_seconds']}
- cast count: {raw['cast_count']}
- locations: {'; '.join(str(item) for item in raw['locations'])}
- physical product visible: {raw['product_exposure']['physical_product_visible']}
- product exposure: {raw['product_exposure']['description']}
- claims: {'; '.join(str(item) for item in raw['claims']) or 'none'}
- evidence refs: {evidence}
"""
        )
    return """# Imported Creative Candidates

status: imported_for_internal_review
visibility: internal_only
artifact_role: evidence_bound_model_generated_candidates

These directions were imported through `adco creative-import`. ADCO validates
structure, declared hard constraints, and traceability. Independent creative
judgment is added only when the decision boundary requires it.

""" + "\n".join(sections)


def _render_option_matrix(payload: dict[str, object]) -> bytes:
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
    handle = io.StringIO(newline="")
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
                    "notes": "candidate_schema=1.1",
            }
        )
    return handle.getvalue().encode("utf-8")


def _constraint_confirmation_artifacts(
    payload: dict[str, object], direction_id: str, constraint_id: str
) -> set[str]:
    return {
        f"candidate_payload_sha256:{payload_sha256(payload)}",
        f"brief_snapshot_sha256:{payload.get('brief_snapshot_sha256', '')}",
        f"direction_id:{direction_id}",
        f"constraint_id:{constraint_id}",
    }


def _constraint_resolution_map(
    project: Path,
    payload: dict[str, object],
    constraints: list[dict[str, object]],
) -> dict[tuple[str, str], dict[str, object]]:
    candidate_digest = payload_sha256(payload)
    snapshot_sha = str(payload.get("brief_snapshot_sha256", ""))
    constraints_by_id = {
        str(item.get("constraint_id", "")): item
        for item in constraints
        if str(item.get("constraint_id", ""))
    }
    applicable: dict[tuple[str, str], dict[str, object]] = {}
    for item in _optional_json_list(project, CONSTRAINT_RESOLUTIONS_REL):
        direction_id = str(item.get("direction_id", ""))
        constraint_id = str(item.get("constraint_id", ""))
        decision = str(item.get("decision", ""))
        constraint = constraints_by_id.get(constraint_id)
        if constraint is None or decision not in CONSTRAINT_CONFIRMATION_SEMANTICS:
            continue
        requirement_id = str(constraint.get("requirement_id", ""))
        try:
            confirmation = _typed_confirmation_event(
                project,
                str(item.get("confirmation_ref", "")),
                expected_semantics={CONSTRAINT_CONFIRMATION_SEMANTICS[decision]},
                required_requirements={requirement_id},
                required_artifacts=_constraint_confirmation_artifacts(
                    payload, direction_id, constraint_id
                ),
            )
        except (OSError, ValueError):
            continue
        if (
            item.get("protocol_id") == "adco.creative-constraint-resolution"
            and item.get("resolution_version") == "1.1"
            and item.get("candidate_payload_sha256") == candidate_digest
            and item.get("brief_snapshot_sha256") == snapshot_sha
            and item.get("decision") == decision
            and direction_id
            and constraint_id
            and item.get("reviewed_by") == confirmation["authority_class"]
            and item.get("reviewed_at") == confirmation["received_at"]
            and item.get("confirmation_id") == confirmation["confirmation_id"]
            and item.get("confirmation_source_event_sha256")
            == confirmation["source_event_sha256"]
            and item.get("confirmation_evidence_path")
            == confirmation["evidence_path"]
            and item.get("confirmation_evidence_sha256")
            == confirmation["evidence_sha256"]
            and str(item.get("note", "")).strip()
        ):
            applicable[(direction_id, constraint_id)] = item
    return applicable


def resolve_creative_constraint(
    project: Path,
    candidate_file: Path,
    *,
    direction_id: str,
    constraint_id: str,
    confirmation_ref: str,
    decision: str,
    note: str,
) -> ConstraintResolutionResult:
    """Record a typed authority decision for one non-deterministic constraint."""
    if decision not in {"approved", "rejected"}:
        raise ValueError("decision must be approved or rejected")
    if not note.strip():
        raise ValueError("a non-empty human review note is required")
    try:
        payload = json.loads(candidate_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read creative candidate: {exc}") from exc
    errors, _warnings = _candidate_validation_errors(project, payload)
    if errors:
        raise ValueError("creative candidate validation failed: " + "; ".join(errors[:20]))
    assert isinstance(payload, dict)
    directions = payload.get("directions")
    assert isinstance(directions, list)
    raw = next(
        (
            item
            for item in directions
            if isinstance(item, dict) and item.get("direction_id") == direction_id
        ),
        None,
    )
    if raw is None:
        raise ValueError(f"direction_id is not present in candidate: {direction_id}")
    snapshot, _contract, _manifest = _verified_brief(project)
    constraint = next(
        (
            item
            for item in _extract_hard_constraints(project, snapshot)
            if item.get("constraint_id") == constraint_id
        ),
        None,
    )
    if constraint is None:
        raise ValueError(f"constraint_id is not present in current brief: {constraint_id}")
    unresolved = _evaluate_hard_constraint(raw, constraint, None)
    if unresolved["status"] != "REVIEW_REQUIRED":
        raise ValueError(
            "human resolution is allowed only for REVIEW_REQUIRED checks; "
            f"current deterministic status is {unresolved['status']}"
        )
    requirement_id = str(constraint.get("requirement_id", ""))
    confirmation = _typed_confirmation_event(
        project,
        confirmation_ref,
        expected_semantics={CONSTRAINT_CONFIRMATION_SEMANTICS[decision]},
        required_requirements={requirement_id},
        required_artifacts=_constraint_confirmation_artifacts(
            payload, direction_id, constraint_id
        ),
    )
    resolution: dict[str, object] = {
        "protocol_id": "adco.creative-constraint-resolution",
        "resolution_version": "1.1",
        "brief_snapshot_sha256": payload["brief_snapshot_sha256"],
        "candidate_payload_sha256": payload_sha256(payload),
        "direction_id": direction_id,
        "constraint_id": constraint_id,
        "decision": decision,
        "confirmation_ref": confirmation["confirmation_ref"],
        "confirmation_id": confirmation["confirmation_id"],
        "confirmation_source_event_sha256": confirmation["source_event_sha256"],
        "confirmation_evidence_path": confirmation["evidence_path"],
        "confirmation_evidence_sha256": confirmation["evidence_sha256"],
        "reviewed_by": confirmation["authority_class"],
        "reviewed_at": confirmation["received_at"],
        "note": note.strip(),
    }
    records = _optional_json_list(project, CONSTRAINT_RESOLUTIONS_REL)
    records = [
        item
        for item in records
        if not (
            item.get("brief_snapshot_sha256") == payload["brief_snapshot_sha256"]
            and item.get("candidate_payload_sha256") == payload_sha256(payload)
            and item.get("direction_id") == direction_id
            and item.get("constraint_id") == constraint_id
        )
    ]
    records.append(resolution)
    records.sort(
        key=lambda item: (
            str(item.get("brief_snapshot_sha256", "")),
            str(item.get("candidate_payload_sha256", "")),
            str(item.get("direction_id", "")),
            str(item.get("constraint_id", "")),
        )
    )
    path = _write_json(project, project / CONSTRAINT_RESOLUTIONS_REL, records)
    return ConstraintResolutionResult(
        constraint_id=constraint_id,
        direction_id=direction_id,
        path=path,
        resolution=resolution,
    )


def _candidate_hard_constraint_blockers(
    project: Path, payload: dict[str, object]
) -> list[str]:
    try:
        snapshot, _contract, _manifest = _verified_brief(project)
    except ValueError as exc:
        return [str(exc)]
    constraints = _extract_hard_constraints(project, snapshot)
    resolutions = _constraint_resolution_map(project, payload, constraints)
    blockers: list[str] = []
    directions = payload.get("directions")
    assert isinstance(directions, list)
    for raw in directions:
        assert isinstance(raw, dict)
        adherence, checks = _brief_adherence(raw, constraints, resolutions)
        if adherence["status"] not in {"FAIL", "REVIEW_REQUIRED"}:
            continue
        direction_id = str(raw.get("direction_id", "unknown-direction"))
        unresolved = [
            f"{constraint_id}={result['status']} ({result['reason']})"
            for constraint_id, result in checks.items()
            if result["status"] in {"FAIL", "REVIEW_REQUIRED"}
        ]
        blockers.append(
            f"{direction_id}: hard-constraint adherence {adherence['status']} "
            f"({', '.join(unresolved)})"
        )
    return blockers


def import_creative_candidate(project: Path, candidate_file: Path) -> CreativeImportResult:
    try:
        payload = json.loads(candidate_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read creative candidate: {exc}") from exc
    errors, warnings = _candidate_validation_errors(project, payload)
    if errors:
        raise ValueError("creative candidate validation failed: " + "; ".join(errors[:20]))
    assert isinstance(payload, dict)
    hard_constraint_blockers = _candidate_hard_constraint_blockers(project, payload)
    if hard_constraint_blockers:
        raise ValueError(
            "creative candidate hard-constraint validation failed before persistence: "
            + "; ".join(hard_constraint_blockers[:20])
        )
    semantic_digest = payload_sha256(payload)
    exact_bytes = persisted_json_bytes(payload)
    candidate_path = _candidate_version_path(project, exact_bytes)
    current_path = project / CURRENT_CANDIDATE_REL
    if not candidate_path.exists():
        atomic_write_bytes(project, candidate_path, exact_bytes)
    if read_project_bytes(project, candidate_path) != exact_bytes:
        raise ValueError("persisted creative candidate bytes do not match import payload")
    candidate_digest = hashlib.sha256(exact_bytes).hexdigest()
    directions_path = project / CREATIVE_DIRECTIONS_REL
    directions_bytes = _render_directions(payload).encode("utf-8")
    matrix_path = project / OPTION_MATRIX_REL
    matrix_bytes = _render_option_matrix(payload)
    manifest_bytes = read_project_bytes(project, project / BRIEF_MANIFEST_REL)
    receipt = {
        "protocol_id": "adco.creative-candidate-import",
        "receipt_version": "1.1",
        "candidate_path": candidate_path.relative_to(project).as_posix(),
        "candidate_sha256": candidate_digest,
        "candidate_payload_sha256": semantic_digest,
        "candidate_byte_length": len(exact_bytes),
        "current_candidate_sha256": candidate_digest,
        "brief_snapshot_sha256": payload["brief_snapshot_sha256"],
        "brief_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "creative_directions_sha256": hashlib.sha256(directions_bytes).hexdigest(),
        "option_matrix_sha256": hashlib.sha256(matrix_bytes).hexdigest(),
        "direction_count": len(payload["directions"]),
        "warnings": warnings,
        "structure_validation": "PASS",
        "hard_constraint_validation": "PASS",
        "creative_quality": "NOT_EVALUATED",
        "imported_at": now_iso(),
    }
    receipt_path = project / CANDIDATE_IMPORT_RECEIPT_REL

    # Version and derived views are prepared first. The receipt is committed
    # next and current_candidate.json is the final atomic pointer switch. A
    # crash can therefore produce a detectable receipt/current mismatch, never
    # a new current candidate accepted under an old receipt.
    atomic_write_bytes(project, directions_path, directions_bytes)
    atomic_write_bytes(project, matrix_path, matrix_bytes)
    _write_json(project, receipt_path, receipt)
    atomic_write_bytes(project, current_path, exact_bytes)
    if read_project_bytes(project, current_path) != exact_bytes:
        raise ValueError("current creative candidate bytes do not match versioned candidate")
    return CreativeImportResult(
        candidate_path=candidate_path,
        current_path=current_path,
        receipt_path=receipt_path,
        directions_path=directions_path,
        matrix_path=matrix_path,
        candidate_sha256=candidate_digest,
        direction_count=len(payload["directions"]),
        warnings=warnings,
    )


def _verified_import(
    project: Path,
) -> tuple[dict[str, object], dict[str, object], Path]:
    current_path = project / CURRENT_CANDIDATE_REL
    receipt_path = project / CANDIDATE_IMPORT_RECEIPT_REL
    if not current_path.exists():
        raise ValueError("current creative candidate is missing; run creative-import first")
    if not receipt_path.exists():
        raise ValueError("creative candidate import receipt is missing; run creative-import again")
    current_bytes = read_project_bytes(project, current_path)
    receipt = _read_json(project, receipt_path)
    if not isinstance(receipt, dict):
        raise ValueError("creative candidate import receipt must be a JSON object")
    if (
        receipt.get("protocol_id") != "adco.creative-candidate-import"
        or receipt.get("receipt_version") != "1.1"
    ):
        raise ValueError("creative candidate import receipt protocol/version is invalid")
    raw_candidate_path = str(receipt.get("candidate_path", ""))
    if not re.fullmatch(
        r"AD-creative/creative/candidates/candidate_v\d{3,}\.json",
        raw_candidate_path,
    ):
        raise ValueError("creative candidate import receipt candidate_path is invalid")
    candidate_path = project / Path(raw_candidate_path)
    candidate_bytes = read_project_bytes(project, candidate_path)
    candidate_sha = hashlib.sha256(candidate_bytes).hexdigest()
    current_sha = hashlib.sha256(current_bytes).hexdigest()
    if current_bytes != candidate_bytes:
        raise ValueError("current creative candidate bytes do not match receipt version")
    if receipt.get("candidate_sha256") != candidate_sha:
        raise ValueError("creative candidate version hash does not match import receipt")
    if receipt.get("current_candidate_sha256") != current_sha:
        raise ValueError("current creative candidate hash does not match import receipt")
    if receipt.get("candidate_byte_length") != len(candidate_bytes):
        raise ValueError("creative candidate byte length does not match import receipt")
    try:
        payload = json.loads(current_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError(f"current creative candidate is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("current creative candidate must be a JSON object")
    if receipt.get("candidate_payload_sha256") != payload_sha256(payload):
        raise ValueError("creative candidate semantic hash does not match import receipt")
    if receipt.get("brief_snapshot_sha256") != payload.get("brief_snapshot_sha256"):
        raise ValueError("creative candidate snapshot does not match import receipt")
    directions = payload.get("directions")
    if not isinstance(directions, list) or receipt.get("direction_count") != len(directions):
        raise ValueError("creative candidate direction count does not match import receipt")

    _snapshot, _contract, _manifest = _verified_brief(project)
    manifest_bytes = read_project_bytes(project, project / BRIEF_MANIFEST_REL)
    if receipt.get("brief_manifest_sha256") != hashlib.sha256(manifest_bytes).hexdigest():
        raise ValueError("creative candidate import receipt is bound to a different brief manifest")
    directions_bytes = read_project_bytes(project, project / CREATIVE_DIRECTIONS_REL)
    matrix_bytes = read_project_bytes(project, project / OPTION_MATRIX_REL)
    if directions_bytes != _render_directions(payload).encode("utf-8"):
        raise ValueError("creative directions view is not derived from the current candidate")
    if matrix_bytes != _render_option_matrix(payload):
        raise ValueError("creative option matrix is not derived from the current candidate")
    if receipt.get("creative_directions_sha256") != hashlib.sha256(directions_bytes).hexdigest():
        raise ValueError("creative directions view does not match import receipt")
    if receipt.get("option_matrix_sha256") != hashlib.sha256(matrix_bytes).hexdigest():
        raise ValueError("creative option matrix does not match import receipt")
    return payload, receipt, candidate_path


GENERIC_CREATIVE_PATTERN = re.compile(
    r"unlock|elevate|game changer|next level|seamless|innovative|empower|reimagine|breakthrough|重新定义|引爆|破圈|赋能|无限可能",
    re.I,
)


def _status_map(status: str, reason: str) -> dict[str, str]:
    return {"status": status, "reason": reason}


RUNTIME_TOTAL_PATTERNS = (
    re.compile(
        r"(?:成片|全片|总时长|片长|影片时长|视频时长|完整(?:视频|短片)|"
        r"total\s+(?:runtime|duration)|(?:video|film)\s+(?:runtime|duration))"
        r"\s*(?:为|是|控制为|控制在|:|：|=)?\s*"
        r"(?P<value>\d{1,3})\s*(?:秒|s(?:ec(?:ond)?s?)?\b)",
        re.I,
    ),
    re.compile(
        r"(?P<value>\d{1,3})\s*(?:秒|s(?:ec(?:ond)?s?)?\b)\s*"
        r"(?:的)?(?:竖屏|横屏|vertical|horizontal)?\s*"
        r"(?:成片|视频|短片|版本|film|video|cut)",
        re.I,
    ),
)
CAST_TOTAL_PATTERNS = (
    re.compile(
        r"(?:共|总计|总共|一共|全片|整片|仅|只有|总演员数(?:为)?|"
        r"total\s+cast(?:\s+is)?|exactly|only)\s*"
        r"(?P<value>\d{1,2}|[一二两三四五六七八九十])\s*"
        r"(?:位|名|个)?\s*(?:演员|人物|角色|人|朋友|actors?|people|cast\s+members?)",
        re.I,
    ),
    re.compile(
        r"(?:演员|人物|角色|cast(?:\s+count)?)\s*(?:共|总计|总共|为|是|:|：|=)\s*"
        r"(?P<value>\d{1,2}|[一二两三四五六七八九十])\s*"
        r"(?:位|名|个)?(?:演员|人物|角色|人|actors?|people|cast\s+members?)?",
        re.I,
    ),
)
PRODUCT_VISUAL_PATTERN = re.compile(
    r"产品|商品|实物|包装|瓶身|罐身|瓶装|罐装|"
    r"\b(?:physical|actual|real)\s+product\b|\bpackaging\b|\bbottle\b|"
    r"\b(?:beverage|drink|aluminum|branded|mori\s+spark)\s+can\b|"
    r"\bcan\s+(?:body|label|packaging|close[ -]?up)\b",
    re.I,
)
ENGLISH_PRODUCT_EXPOSURE_PAIR_PATTERN = re.compile(
    r"(?:show|showing|shown|hold|holding|held|open|opening|opened|drink|drinking)"
    r"\s+(?:the\s+)?(?:physical\s+|actual\s+|real\s+)?"
    r"(?:product|packaging|bottle|can)\b|"
    r"\b(?:product|packaging|bottle|can)\s+(?:is\s+|remains\s+)?"
    r"(?:visible|shown|held|opened|on[ -]?screen|in\s+(?:a\s+)?close[ -]?up)\b",
    re.I,
)
PRODUCT_EXPOSURE_ACTION_PATTERN = re.compile(
    r"露出|出镜|展示|可见|特写|拿起|取出|开瓶|开罐|饮用|喝|"
    r"on[ -]?screen|visible|close[ -]?up|show|hold|open|drink",
    re.I,
)
PRODUCT_EXPOSURE_NEGATION_PATTERN = re.compile(
    r"(?:产品|商品|实物|包装|瓶身|罐身).{0,10}(?:不|未|没有|无需).{0,8}"
    r"(?:露出|出镜|展示|可见|出现)|"
    r"(?:不|未|没有|无需).{0,8}(?:露出|出镜|展示|出现).{0,10}"
    r"(?:产品|商品|实物|包装|瓶身|罐身)|"
    r"(?:without|no)\s+(?:physical\s+)?(?:product|packaging|bottle|can)\b|"
    r"(?:product|packaging|bottle|can).{0,18}\b(?:not|never)\b.{0,10}"
    r"(?:visible|shown|on[ -]?screen)",
    re.I,
)
GENERIC_LOCATION_PATTERN = re.compile(
    r"(?:在|于|到|进入|来到|回到|转场(?:到|至)?|切(?:换)?到|从)\s*"
    r"(?P<zh>[^，。；;,.\n]{1,24}?(?:馆|店|场|室|房|厅|街|路|台|园|门口|站|车内))"
    r"|\b(?:at|in|into|to|from)\s+(?:the\s+)?"
    r"(?P<en>(?:[a-z][a-z'-]*\s+){0,4}(?:museum|gallery|library|school|"
    r"store|shop|bar|restaurant|office|bedroom|kitchen|rooftop|park|station))\b",
    re.I,
)
CLAIM_VARIANT_PATTERNS: tuple[tuple[re.Pattern[str], re.Pattern[str]], ...] = (
    (
        re.compile(r"睡眠|助眠|安眠|好眠|sleep", re.I),
        re.compile(r"睡眠|助眠|安眠|好眠|一夜好眠|sleep|sleeping|restful\s+night", re.I),
    ),
    (
        re.compile(r"醒酒|解酒|清醒|sobering|sober", re.I),
        re.compile(
            r"醒酒|解酒|快速清醒|清醒社交|保持清醒|头脑清醒|"
            r"clear[ -]?headed(?:\s+sociali[sz]ing)?|"
            r"sober(?:ing|\s+up|\s+sociali[sz]ing)",
            re.I,
        ),
    ),
    (
        re.compile(r"减肥|减重|瘦身|weight", re.I),
        re.compile(r"减肥|减重|瘦身|燃脂|weight[ -]?loss|lose\s+weight", re.I),
    ),
    (
        re.compile(r"健康|health", re.I),
        re.compile(
            r"改善健康|更健康|健康功效|低负担社交|轻负担社交|"
            r"health(?:y|ier)?\s+(?:benefit|choice)|"
            r"wellness\s+choice|low[ -]?burden\s+sociali[sz]ing",
            re.I,
        ),
    ),
    (
        re.compile(r"医疗|医学|medical", re.I),
        re.compile(r"医疗|医学|治疗|治愈|疗效|medical|treat(?:s|ment)?|cure", re.I),
    ),
)


def _direction_text(raw: dict[str, object], fields: Iterable[str] | None = None) -> str:
    selected = fields or (
        field for field in CREATIVE_NARRATIVE_FIELDS if field != "evidence_refs"
    )
    return " ".join(str(raw.get(field, "")) for field in selected)


def _normalized_phrase(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.casefold())


def _claim_is_negated(text: str, start: int) -> bool:
    prefix = text[max(0, start - 64) : start]
    prefix = re.split(r"[。；;,.，!?！？\n]", prefix)[-1]
    prefix = re.split(r"(?:但是|但|然而|不过|却|\bbut\b|\bhowever\b)", prefix, flags=re.I)[-1]
    direct = re.search(
            r"(?:不得|不能|禁止|避免|不(?:出现|涉及|包含|提及|宣称|声称|使用|作|做)|"
            r"未(?:出现|涉及|包含|提及|宣称|声称|使用)|没有|无|"
            r"must\s+not(?:\s+(?:claim|state|promise|suggest|use|include|make))?|"
            r"do(?:es)?\s+not(?:\s+(?:claim|state|promise|suggest|use|include|make))?|"
            r"don['’]t(?:\s+(?:claim|state|promise|suggest|use|include|make))?|"
            r"doesn['’]t(?:\s+(?:claim|state|promise|suggest|use|include|make))?|"
            r"without(?:\s+(?:making|any))?|avoid(?:s|ed|ing)?|"
            r"(?<!\w)no\b|(?<!\w)not\b)\s*(?:(?:a|an|the|任何|相关|关于|这类|该类|直接|明确|的|"
            r"any|related|claimed|explicit|such|the)\s*)*$",
            prefix,
            re.I,
        )
    coordinated = re.search(
        r"(?:不得|不能|禁止|避免|不(?:出现|涉及|包含|提及|宣称|声称|使用)|"
        r"must\s+not|do(?:es)?\s+not|don['’]t|doesn['’]t|without|avoid)"
        r"[^。；;,.，!?！？\n]{1,48}(?:或|和|与|及|\band\b|\bor\b)\s*$",
        prefix,
        re.I,
    )
    return bool(direct or coordinated)


def _claim_patterns(claim: str) -> list[re.Pattern[str]]:
    patterns = [re.compile(re.escape(claim), re.I)]
    for category, variants in CLAIM_VARIANT_PATTERNS:
        if category.search(claim):
            patterns.append(variants)
    return patterns


def _explicit_product_visibility(text: str) -> bool:
    """Require a physical-product noun and visual action in one local clause."""
    for clause in re.split(r"[。；;.!?！？\n]+", text):
        if ENGLISH_PRODUCT_EXPOSURE_PAIR_PATTERN.search(clause):
            return True
        entities = [
            match
            for match in PRODUCT_VISUAL_PATTERN.finditer(clause)
            if not re.match(
                r"\s*(?:策略|定位|概念|路线|思路|规划|文案|strategy|positioning|concept)",
                clause[match.end() :],
                re.I,
            )
        ]
        actions = list(PRODUCT_EXPOSURE_ACTION_PATTERN.finditer(clause))
        if any(
            abs((entity.start() + entity.end()) - (action.start() + action.end()))
            <= 96
            for entity in entities
            for action in actions
        ):
            return True
    return False


def _residual_location_mentions(text: str, allowed: list[str]) -> list[str]:
    residual = text
    for item in sorted(allowed, key=len, reverse=True):
        residual = re.sub(re.escape(item), " ", residual, flags=re.I)
    mentions = [
        marker
        for marker in LOCATION_MARKERS
        if marker.casefold() in residual.casefold()
    ]
    mentions.extend(
        next(value for value in match.groups() if value)
        for match in GENERIC_LOCATION_PATTERN.finditer(residual)
    )
    return sorted(set(item.strip() for item in mentions if item.strip()))


def _evaluate_hard_constraint(
    raw: dict[str, object],
    constraint: dict[str, object],
    resolution: dict[str, object] | None = None,
) -> dict[str, str]:
    kind = str(constraint["kind"])
    value = constraint["value"]
    authority = constraint.get("authority")
    if isinstance(authority, dict) and authority.get("authoritative") is not True:
        return _status_map(
            "REVIEW_REQUIRED",
            "unconfirmed requirement authority: "
            f"status={authority.get('status')}; owner={authority.get('owner')}; "
            f"source_event_id={authority.get('source_event_id')}; "
            f"confidence={authority.get('confidence')}",
        )
    if kind == "manual_review":
        if resolution is not None:
            approved = resolution.get("decision") == "approved"
            return _status_map(
                "PASS" if approved else "FAIL",
                "human resolution "
                f"{resolution.get('decision')} by {resolution.get('reviewed_by')}: "
                f"{resolution.get('note')}",
            )
        return _status_map(
            "REVIEW_REQUIRED",
            f"explicit hard requirement has no deterministic checker: {value}",
        )
    combined = _direction_text(raw)
    if kind == "runtime_max_seconds":
        declared = raw.get("runtime_seconds")
        if not isinstance(declared, int) or isinstance(declared, bool):
            return _status_map("REVIEW_REQUIRED", "runtime_seconds is not declared")
        limit = int(value)
        mentions = [
            int(match.group("value"))
            for pattern in RUNTIME_TOTAL_PATTERNS
            for match in pattern.finditer(combined)
        ]
        inconsistent = [item for item in mentions if item != declared]
        return _status_map(
            "FAIL" if declared > limit or inconsistent else "PASS",
            f"runtime_seconds={declared}; prose_mentions={mentions}; max_seconds={limit}; inconsistent={inconsistent}",
        )
    if kind == "cast_max":
        declared = raw.get("cast_count")
        if not isinstance(declared, int) or isinstance(declared, bool):
            return _status_map("REVIEW_REQUIRED", "cast_count is not declared")
        mentions = [
            parsed
            for pattern in CAST_TOTAL_PATTERNS
            for match in pattern.finditer(combined)
            if (parsed := _number_value(match.group("value"))) is not None
        ]
        limit = int(value)
        inconsistent = [item for item in mentions if item != declared]
        return _status_map(
            "FAIL" if declared > limit or inconsistent else "PASS",
            f"cast_count={declared}; prose_mentions={mentions}; max_cast={limit}; inconsistent={inconsistent}",
        )
    if kind == "location_allowlist":
        allowed = [str(item) for item in value] if isinstance(value, list) else []
        declared = raw.get("locations")
        if not isinstance(declared, list) or not declared:
            return _status_map("REVIEW_REQUIRED", "locations are not declared")
        allowed_normalized = {_normalized_phrase(item) for item in allowed}
        disallowed_declared = [
            str(item)
            for item in declared
            if _normalized_phrase(str(item)) not in allowed_normalized
        ]
        residual_mentions = _residual_location_mentions(combined, allowed)
        if disallowed_declared or residual_mentions:
            return _status_map(
                "FAIL",
                f"disallowed_declared={disallowed_declared}; residual_prose_mentions={residual_mentions}; allowed={allowed}",
            )
        return _status_map(
            "PASS",
            f"declared_locations={declared}; all exactly allowed; no residual location marker found",
        )
    if kind == "product_exposure_required":
        exposure = raw.get("product_exposure")
        expected_visible = bool(value)
        if not isinstance(exposure, dict):
            return _status_map("REVIEW_REQUIRED", "product_exposure is not declared")
        if exposure.get("physical_product_visible") is not expected_visible:
            return _status_map(
                "FAIL",
                f"physical_product_visible must be {expected_visible}",
            )
        visual_text = _direction_text(
            raw,
            ("key_visual", "story_or_behavior", "channel_execution"),
        )
        exposure_text = f"{exposure.get('description', '')} {visual_text}"
        if expected_visible and PRODUCT_EXPOSURE_NEGATION_PATTERN.search(exposure_text):
            return _status_map("FAIL", "product exposure is explicitly negated in structured description or prose")
        visible = _explicit_product_visibility(exposure_text)
        if not expected_visible:
            return _status_map(
                "FAIL" if visible else "PASS",
                (
                    "product exposure is present despite the prohibition"
                    if visible
                    else "physical product exposure is explicitly disabled and no visible product action was found"
                ),
            )
        return _status_map(
            "PASS" if visible else "REVIEW_REQUIRED",
            (
                "physical product and visible on-screen action are explicit"
                if visible
                else "physical product exposure is not explicit in visual, story, or channel execution"
            ),
        )
    if kind == "prohibited_claims":
        narrative_claim_text = _direction_text(
            raw,
            (
                "name",
                "human_tension",
                "single_minded_proposition",
                "creative_mechanism",
                "key_visual",
                "story_or_behavior",
                "product_role",
                "channel_execution",
            ),
        )
        declared_claims = raw.get("claims")
        if not isinstance(declared_claims, list):
            return _status_map("REVIEW_REQUIRED", "claims are not declared")
        claim_text = " ".join(str(item) for item in declared_claims) + " " + narrative_claim_text
        claims = [str(item) for item in value] if isinstance(value, list) else []
        violations: list[str] = []
        for claim in claims:
            for pattern in _claim_patterns(claim):
                if any(
                    not _claim_is_negated(claim_text, match.start())
                    for match in pattern.finditer(claim_text)
                ):
                    violations.append(claim)
                    break
        return _status_map(
            "FAIL" if violations else "PASS",
            f"prohibited_claims_present={sorted(set(violations))}",
        )
    return _status_map("REVIEW_REQUIRED", f"unsupported hard constraint kind: {kind}")


def _brief_adherence(
    raw: dict[str, object],
    constraints: list[dict[str, object]],
    resolutions: dict[tuple[str, str], dict[str, object]] | None = None,
) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    if not constraints:
        return (
            _status_map(
                "NOT_APPLICABLE",
                "no machine-readable hard constraints were extracted; evidence traceability is reported separately",
            ),
            {},
        )
    direction_id = str(raw.get("direction_id", ""))
    resolutions = resolutions or {}
    checks = {}
    for constraint in constraints:
        constraint_id = str(constraint["constraint_id"])
        checks[constraint_id] = _evaluate_hard_constraint(
            raw,
            constraint,
            resolutions.get((direction_id, constraint_id)),
        )
    failed = [key for key, result in checks.items() if result["status"] == "FAIL"]
    unresolved = [
        key for key, result in checks.items() if result["status"] == "REVIEW_REQUIRED"
    ]
    if failed:
        status = "FAIL"
    elif unresolved:
        status = "REVIEW_REQUIRED"
    else:
        status = "PASS"
    return (
        _status_map(
            status,
            f"checked={len(checks)}; failed={failed}; review_required={unresolved}",
        ),
        checks,
    )


def review_creative_candidate(
    project: Path,
    *,
    independent_critic_required: bool = False,
) -> CreativeReviewResult:
    path = project / CURRENT_CANDIDATE_REL
    payload, import_receipt, candidate_path = _verified_import(project)
    errors, import_warnings = _candidate_validation_errors(project, payload)
    if errors:
        raise ValueError("current creative candidate is invalid: " + "; ".join(errors[:20]))
    directions = payload["directions"]
    assert isinstance(directions, list)
    snapshot, _contract, _manifest = _verified_brief(project)
    hard_constraints = _extract_hard_constraints(project, snapshot)
    resolutions = _constraint_resolution_map(project, payload, hard_constraints)
    receipt: dict[str, object] = {
        "protocol_id": "adco.creative-critic-receipt",
        "receipt_version": "1.0",
        "candidate_sha256": hashlib.sha256(read_project_bytes(project, path)).hexdigest(),
        "candidate_payload_sha256": payload_sha256(payload),
        "candidate_version_path": candidate_path.relative_to(project).as_posix(),
        "candidate_import_receipt_sha256": hashlib.sha256(
            read_project_bytes(project, project / CANDIDATE_IMPORT_RECEIPT_REL)
        ).hexdigest(),
        "candidate_imported_at": import_receipt.get("imported_at"),
        "brief_snapshot_sha256": payload["brief_snapshot_sha256"],
        "review_kind": "deterministic_structure_semantic_and_language_lint",
        "hard_constraints": hard_constraints,
        "evidence_traceability": {},
        "brief_adherence": {},
        "brief_constraint_checks": {},
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
        receipt["evidence_traceability"][direction_id] = _status_map(
            "PROVENANCE_ONLY" if refs else "FAIL",
            (
                f"evidence_refs={len(refs)}; refs exist, but semantic claim support is not verified by this lint"
                if refs
                else "no evidence_refs"
            ),
        )
        adherence, constraint_checks = _brief_adherence(
            raw,
            hard_constraints,
            resolutions,
        )
        receipt["brief_adherence"][direction_id] = adherence
        receipt["brief_constraint_checks"][direction_id] = constraint_checks
        if adherence["status"] in {"FAIL", "REVIEW_REQUIRED"}:
            blocking.append(
                f"{direction_id}: hard-constraint adherence {adherence['status'].lower()}"
            )
        insight = str(raw["human_tension"])
        insight_ok = len(insight.strip()) >= 15 and not GENERIC_CREATIVE_PATTERN.search(insight)
        receipt["insight_quality"][direction_id] = _status_map(
            "LINT_PASS" if insight_ok else "REVIEW_REQUIRED",
            "human tension is concrete" if insight_ok else "human tension is thin or generic",
        )
        if not insight_ok:
            warnings.append(f"{direction_id}: insight quality requires human review")
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
                (
                    "Independent Critic must replace the brand and test whether the mechanism still fully works."
                    if independent_critic_required
                    else "A human reviewer should replace the brand and test whether the mechanism still fully works."
                )
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
    receipt["independent_critic_required"] = independent_critic_required
    receipt["creative_quality"] = "NOT_APPROVED_BY_DETERMINISTIC_LINT"
    receipt["verdict"] = (
        "BLOCKED"
        if blocking
        else "STRUCTURE_PASS_REQUIRES_INDEPENDENT_CRITIC"
        if independent_critic_required
        else "STRUCTURE_PASS_HUMAN_JUDGMENT_REQUIRED"
    )
    receipt["reviewed_at"] = now_iso()
    receipt_path = (
        _write_json(project, project / CRITIC_RECEIPT_REL, receipt)
        if independent_critic_required
        else None
    )
    return CreativeReviewResult(
        status="BLOCKED" if blocking else "PARTIAL_PASS",
        receipt_path=receipt_path,
        receipt=receipt,
        blocking_issues=blocking,
        warnings=sorted(set(warnings)),
    )
