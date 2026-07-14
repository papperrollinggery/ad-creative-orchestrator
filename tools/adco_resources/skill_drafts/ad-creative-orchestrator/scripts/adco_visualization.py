#!/usr/bin/env python3
"""Validate and render ADCO chat-native OpenAI Visualization specs."""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import html
import json
import re
import tempfile
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = SKILL_ROOT / "assets" / "visualizations"
FIXTURE_ROOT = SKILL_ROOT / "fixtures" / "chat-visualization"
SCHEMA_PATH = SKILL_ROOT / "schemas" / "chat-visualization-spec.schema.json"
WRITEBACK_SCHEMA_PATH = SKILL_ROOT / "schemas" / "chat-visualization-writeback.schema.json"
REGISTRY_PATH = ASSET_ROOT / "surface-registry.json"
CSS_PATH = ASSET_ROOT / "decision-surface.css"
JS_PATH = ASSET_ROOT / "decision-surface.js"
CONTRACT = "adco.chat-visualization@1.0"
PHASES = [f"P{i}" for i in range(9)]
PHASE_LABELS = {
    "P0": "资料与目标",
    "P1": "提案框架",
    "P2": "方向确认",
    "P3": "创意与素材",
    "P4": "提案制作",
    "P5": "内容与视觉检查",
    "P6": "交付包检查",
    "P7": "发送准备",
    "P8": "反馈与下一版",
}
SURFACE_KINDS = {
    "current-status",
    "phase-logic",
    "blocking-decision",
    "option-comparison",
    "asset-review",
    "ppt-slide-review",
    "feedback-impact",
}
ACTION_KINDS = {
    "submit-selection",
    "request-revision",
    "register-feedback",
    "request-recheck",
    "inspect-detail",
}
FORBIDDEN_CLAIMS = {"approval", "readiness", "send", "completion", "global-install"}
LIFECYCLES = {"current", "candidate", "superseded", "stale", "archived", "rejected", "pending"}
ASSET_CLASSIFICATIONS = {"real-candidate", "illustrative-placeholder"}
ASSET_SOURCE_STATUSES = {"verified", "pending", "not-applicable"}
ASSET_AUTHORIZATION_STATUSES = {"confirmed", "pending", "not-applicable"}
ASSET_CHANNEL_FIT_STATUSES = {"verified", "pending", "not-applicable"}
ASSET_VISIBLE_VALUES = {
    "real-candidate": "真实候选素材",
    "illustrative-placeholder": "演示占位图",
    "source:verified": "来源已确认",
    "source:pending": "来源待确认",
    "source:not-applicable": "不适用",
    "authorization:confirmed": "授权已确认",
    "authorization:pending": "授权待确认",
    "authorization:not-applicable": "不适用",
    "channel:verified": "渠道适配已检查",
    "channel:pending": "渠道适配待检查",
    "channel:not-applicable": "不适用",
}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA_RE = re.compile(r"^[a-f0-9]{64}$")
SOURCE_RE = re.compile(r"^([a-z0-9]+(?:-[a-z0-9]+)*)#(/.*)$")
NETWORK_TOKENS = ("fetch(", "XMLHttpRequest", "WebSocket", "http://", "https://")
FRONTSTAGE_FORBIDDEN = (
    "artifact_id", "sha256", "hash", "gate", "receipt", "writeback", "validator", "source truth", "source_truth",
    "authority", "evidence binding", "control-plane", "current_truth.md", "version_map.csv",
    "artifact_index.csv", "回执", "控制面", "证据绑定", "证据锁", "哈希",
    "校验", "写入", "重读", "p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8",
)


class VisualizationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualizationError(f"cannot load JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualizationError("spec root must be an object")
    return value


def _is_nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def frontstage_term_errors(values: list[Any], context: str = "customer-visible content") -> list[str]:
    lowered = "\n".join(str(value) for value in values).lower()
    return [f"{context} contains backstage term: {token}" for token in FRONTSTAGE_FORBIDDEN if token in lowered]


def validate_spec(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "contract", "view_id", "execution_context", "controller", "phase", "surface",
        "source_truth", "presentation", "interactions", "write_boundary", "fallback",
    }
    missing = sorted(required - set(document))
    if missing:
        errors.append("missing required keys: " + ", ".join(missing))
        return errors
    if document.get("contract") != CONTRACT:
        errors.append(f"contract must be {CONTRACT}")
    if not SLUG_RE.fullmatch(str(document.get("view_id", ""))):
        errors.append("view_id must be lowercase hyphenated ASCII")
    if document.get("phase") not in PHASES:
        errors.append("phase must be P0-P8")

    context = document.get("execution_context")
    controller = document.get("controller") if isinstance(document.get("controller"), dict) else {}
    if context not in {"standalone_chat", "orchestrated_provider"}:
        errors.append("execution_context must be standalone_chat or orchestrated_provider")
    if controller.get("surface_owner") != "ad-creative-orchestrator":
        errors.append("controller.surface_owner must be ad-creative-orchestrator")
    if context == "standalone_chat" and controller.get("user_facing") is not True:
        errors.append("standalone_chat controller must be user-facing")
    if context == "orchestrated_provider" and controller.get("user_facing") is not False:
        errors.append("orchestrated_provider must remain provider-hidden")

    surface = document.get("surface") if isinstance(document.get("surface"), dict) else {}
    kind = surface.get("kind")
    if kind not in SURFACE_KINDS:
        errors.append("surface.kind is not registered")
    for key in ("title", "summary", "question"):
        if not _is_nonempty(surface.get(key)):
            errors.append(f"surface.{key} must be non-empty")

    truth = document.get("source_truth") if isinstance(document.get("source_truth"), dict) else {}
    current_version = truth.get("current_version")
    if not _is_nonempty(truth.get("project_id")) or not _is_nonempty(current_version):
        errors.append("source_truth requires project_id and current_version")
    artifacts = truth.get("artifacts") if isinstance(truth.get("artifacts"), list) else []
    if not artifacts:
        errors.append("source_truth.artifacts must not be empty")
    artifact_ids: set[str] = set()
    current_count = 0
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            errors.append(f"artifact {index} must be an object")
            continue
        artifact_id = artifact.get("artifact_id")
        if not SLUG_RE.fullmatch(str(artifact_id or "")):
            errors.append(f"artifact {index} has invalid artifact_id")
        elif artifact_id in artifact_ids:
            errors.append(f"duplicate artifact_id: {artifact_id}")
        else:
            artifact_ids.add(artifact_id)
        path = artifact.get("path")
        if not _is_nonempty(path) or Path(str(path)).is_absolute() or ".." in Path(str(path)).parts:
            errors.append(f"artifact {artifact_id or index} path must be project-relative and traversal-free")
        if not _is_nonempty(artifact.get("version")):
            errors.append(f"artifact {artifact_id or index} requires version")
        if not SHA_RE.fullmatch(str(artifact.get("sha256", ""))):
            errors.append(f"artifact {artifact_id or index} requires lowercase SHA-256")
        if artifact.get("lifecycle") not in LIFECYCLES:
            errors.append(f"artifact {artifact_id or index} has invalid lifecycle")
        if artifact.get("lifecycle") == "current" and artifact.get("version") == current_version:
            current_count += 1
    if artifacts and current_count < 1:
        errors.append("at least one artifact must bind current_version with lifecycle current")

    presentation = document.get("presentation") if isinstance(document.get("presentation"), dict) else {}
    fields = presentation.get("fields") if isinstance(presentation.get("fields"), list) else []
    if len(fields) < 2:
        errors.append("presentation.fields needs at least two visible fields")
    for index, field in enumerate(fields):
        if not isinstance(field, dict):
            errors.append(f"field {index} must be an object")
            continue
        provenance = field.get("provenance")
        source_ref = field.get("source_ref")
        if provenance == "source-bound":
            if not _valid_source_ref(source_ref, artifact_ids):
                errors.append(f"field {field.get('id', index)} has invalid source binding")
        elif provenance == "presentation-only":
            if source_ref is not None:
                errors.append(f"field {field.get('id', index)} presentation-only source_ref must be null")
        else:
            errors.append(f"field {field.get('id', index)} has invalid provenance")

    options = presentation.get("options") if isinstance(presentation.get("options"), list) else []
    if len(options) > 3:
        errors.append("presentation.options must contain at most three options")
    if kind == "option-comparison" and len(options) not in {2, 3}:
        errors.append("option-comparison requires two or three options")
    option_ids: set[str] = set()
    for index, option in enumerate(options):
        if not isinstance(option, dict):
            errors.append(f"option {index} must be an object")
            continue
        option_id = option.get("id")
        if not SLUG_RE.fullmatch(str(option_id or "")) or option_id in option_ids:
            errors.append(f"option {index} has invalid or duplicate id")
        else:
            option_ids.add(option_id)
        refs = option.get("source_refs") if isinstance(option.get("source_refs"), list) else []
        if not refs or any(not _valid_source_ref(ref, artifact_ids) for ref in refs):
            errors.append(f"option {option_id or index} requires valid source_refs")
        for key in ("label", "summary", "tradeoff"):
            if not _is_nonempty(option.get(key)):
                errors.append(f"option {option_id or index} requires {key}")
    recommendation = presentation.get("recommendation")
    if recommendation is not None:
        if not isinstance(recommendation, dict) or recommendation.get("option_id") not in option_ids:
            errors.append("recommendation must reference an option in this view")
        elif not _is_nonempty(recommendation.get("reason")):
            errors.append("recommendation requires a reason")
    quantitative = presentation.get("quantitative_evidence", [])
    if not isinstance(quantitative, list):
        errors.append("quantitative_evidence must be an optional list")
    else:
        for index, evidence in enumerate(quantitative):
            if not isinstance(evidence, dict) or not isinstance(evidence.get("value"), (int, float)):
                errors.append(f"quantitative evidence {index} requires a numeric value")
            elif not _valid_source_ref(evidence.get("source_ref"), artifact_ids):
                errors.append(f"quantitative evidence {index} requires a reviewed source binding")
    previews = presentation.get("previews", [])
    asset_review_artifact: dict[str, Any] | None = None
    asset_review_usable = False
    if not isinstance(previews, list) or len(previews) > 4:
        errors.append("previews must be an optional list with at most four items")
    else:
        for index, preview in enumerate(previews):
            if not isinstance(preview, dict) or preview.get("artifact_id") not in artifact_ids:
                errors.append(f"preview {index} requires a source artifact")
                continue
            for key in ("label", "alt", "caption"):
                if not _is_nonempty(preview.get(key)):
                    errors.append(f"preview {index} requires {key}")
            annotations = preview.get("annotations")
            if not isinstance(annotations, list) or len(annotations) > 4:
                errors.append(f"preview {index} annotations must be a list with at most four items")
            else:
                for annotation in annotations:
                    if not isinstance(annotation, dict) or not _is_nonempty(annotation.get("region")) or not _is_nonempty(annotation.get("note")):
                        errors.append(f"preview {index} annotations require region and note")

    if kind == "asset-review" and context == "standalone_chat" and controller.get("user_facing") is True:
        if len(previews) != 1:
            errors.append("asset-review requires exactly one inspected preview")
        artifact_by_id = {
            item.get("artifact_id"): item for item in artifacts if isinstance(item, dict)
        }
        if len(previews) == 1 and isinstance(previews[0], dict):
            candidate = artifact_by_id.get(previews[0].get("artifact_id"))
            if isinstance(candidate, dict):
                asset_review_artifact = candidate
        if asset_review_artifact is not None:
            classification = asset_review_artifact.get("review_classification")
            source_status = asset_review_artifact.get("source_status")
            authorization_status = asset_review_artifact.get("authorization_status")
            channel_fit_status = asset_review_artifact.get("channel_fit_status")
            if classification not in ASSET_CLASSIFICATIONS:
                errors.append("asset-review artifact requires review_classification")
            if source_status not in ASSET_SOURCE_STATUSES:
                errors.append("asset-review artifact requires source_status")
            if authorization_status not in ASSET_AUTHORIZATION_STATUSES:
                errors.append("asset-review artifact requires authorization_status")
            if channel_fit_status not in ASSET_CHANNEL_FIT_STATUSES:
                errors.append("asset-review artifact requires channel_fit_status")

            if classification == "illustrative-placeholder":
                if any(status != "not-applicable" for status in (source_status, authorization_status, channel_fit_status)):
                    errors.append("illustrative placeholder statuses must be not-applicable")
            elif classification == "real-candidate" and any(
                status == "not-applicable" for status in (source_status, authorization_status, channel_fit_status)
            ):
                errors.append("real candidate statuses cannot be not-applicable")

            evidence_requirements = (
                ("source_status", source_status, "verified", "source_evidence_ref"),
                ("authorization_status", authorization_status, "confirmed", "authorization_evidence_ref"),
                ("channel_fit_status", channel_fit_status, "verified", "channel_fit_evidence_ref"),
            )
            evidence_ready = True
            for status_name, status, ready_status, ref_name in evidence_requirements:
                ref = asset_review_artifact.get(ref_name)
                ref_match = SOURCE_RE.fullmatch(str(ref or ""))
                ref_artifact = artifact_by_id.get(ref_match.group(1)) if ref_match else None
                valid_external_ref = bool(
                    _valid_source_ref(ref, artifact_ids)
                    and ref_match
                    and ref_match.group(1) != asset_review_artifact.get("artifact_id")
                    and isinstance(ref_artifact, dict)
                    and ref_artifact.get("lifecycle") == "current"
                    and ref_artifact.get("version") == current_version
                )
                if status == ready_status:
                    if not valid_external_ref:
                        errors.append(f"asset-review {status_name} requires external evidence binding")
                        evidence_ready = False
                elif ref is not None:
                    errors.append(f"asset-review {ref_name} must be null until its status is confirmed")
                    evidence_ready = False

            field_values = {
                item.get("id"): str(item.get("value", ""))
                for item in fields if isinstance(item, dict)
            }
            expected = {
                "asset-status": ASSET_VISIBLE_VALUES.get(str(classification)),
                "source-status": ASSET_VISIBLE_VALUES.get(f"source:{source_status}"),
                "authorization-status": ASSET_VISIBLE_VALUES.get(f"authorization:{authorization_status}"),
                "channel-fit": ASSET_VISIBLE_VALUES.get(f"channel:{channel_fit_status}"),
            }
            for field_id, expected_value in expected.items():
                if expected_value is not None and field_values.get(field_id) != expected_value:
                    errors.append(f"asset-review field {field_id} must match structured asset status")

            usable = (
                classification == "real-candidate"
                and source_status == "verified"
                and authorization_status == "confirmed"
                and channel_fit_status == "verified"
                and evidence_ready
            )
            asset_review_usable = usable
            expected_availability = "可进入使用确认" if usable else "暂不能确认使用"
            if field_values.get("availability") != expected_availability:
                errors.append("asset-review field availability must match source, authorization and channel status")

    interactions = document.get("interactions") if isinstance(document.get("interactions"), dict) else {}
    actions = interactions.get("actions") if isinstance(interactions.get("actions"), list) else []
    if not 1 <= len(actions) <= 2:
        errors.append("interactions.actions must contain one or two actions")
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            errors.append(f"action {index} must be an object")
            continue
        if action.get("kind") not in ACTION_KINDS:
            errors.append(f"action {index} has invalid kind")
        for key in ("id", "label", "target_gate", "conversation_intent"):
            if not _is_nonempty(action.get(key)):
                errors.append(f"action {index} requires {key}")
        intent = str(action.get("conversation_intent", "")).lower()
        if any(token in intent for token in ("直接批准", "直接发送", "标记完成", "全局安装")):
            errors.append(f"action {index} attempts a forbidden authoritative operation")
    if kind == "blocking-decision" and not 2 <= len(options) <= 3:
        errors.append("blocking-decision requires two or three explicit options")
    if (
        kind == "asset-review"
        and context == "standalone_chat"
        and controller.get("user_facing") is True
        and asset_review_artifact is not None
        and not asset_review_usable
        and any(action.get("kind") == "submit-selection" for action in actions if isinstance(action, dict))
    ):
        errors.append("asset without complete evidence cannot offer a use-selection action")

    boundary = document.get("write_boundary") if isinstance(document.get("write_boundary"), dict) else {}
    if boundary.get("component_writes_authoritative_state") is not False:
        errors.append("component must not write authoritative state")
    if boundary.get("conversation_intent_only") is not True:
        errors.append("component actions must be conversation intent only")
    if boundary.get("write_owner") != "ad-creative-orchestrator":
        errors.append("write owner must be ad-creative-orchestrator")
    if boundary.get("revalidation_command") != "adco validate <project>":
        errors.append("revalidation_command must be adco validate <project>")
    if set(boundary.get("forbidden_claims", [])) != FORBIDDEN_CLAIMS:
        errors.append("forbidden_claims must include approval/readiness/send/completion/global-install")

    fallback = document.get("fallback") if isinstance(document.get("fallback"), dict) else {}
    if not _is_nonempty(fallback.get("summary")) or not _is_nonempty(fallback.get("decision_prompt")):
        errors.append("fallback requires summary and decision_prompt")
    if fallback.get("decision_prompt") != surface.get("question"):
        errors.append("fallback decision_prompt must preserve the surface question")
    table = fallback.get("table") if isinstance(fallback.get("table"), dict) else {}
    headers = table.get("headers") if isinstance(table.get("headers"), list) else []
    rows = table.get("rows") if isinstance(table.get("rows"), list) else []
    if len(headers) < 2 or not rows or any(not isinstance(row, list) or len(row) != len(headers) for row in rows):
        errors.append("fallback table must be complete and rectangular")
    mermaid = fallback.get("mermaid")
    if not _is_nonempty(mermaid) or not str(mermaid).lstrip().startswith(("flowchart", "graph")):
        errors.append("fallback mermaid must contain a flowchart or graph")
    visible_values: list[str] = [
        str(surface.get("title", "")), str(surface.get("summary", "")), str(surface.get("question", "")),
        str(fallback.get("summary", "")), str(fallback.get("decision_prompt", "")), str(mermaid or ""),
    ]
    visible_values.extend(str(item) for item in headers)
    visible_values.extend(str(cell) for row in rows if isinstance(row, list) for cell in row)
    for field in fields:
        if isinstance(field, dict):
            visible_values.extend((str(field.get("label", "")), str(field.get("value", ""))))
    for option in options:
        if isinstance(option, dict):
            visible_values.extend(str(option.get(key, "")) for key in ("label", "summary", "tradeoff"))
    if isinstance(recommendation, dict):
        visible_values.append(str(recommendation.get("reason", "")))
    visible_values.extend(str(item.get("effect", "")) for item in presentation.get("downstream_effects", []) if isinstance(item, dict))
    visible_values.extend(str(item.get("conversation_intent", "")) for item in actions if isinstance(item, dict))
    visible_values.extend(str(item.get("label", "")) for item in actions if isinstance(item, dict))
    for preview in previews if isinstance(previews, list) else []:
        if isinstance(preview, dict):
            visible_values.extend(str(preview.get(key, "")) for key in ("label", "alt", "caption"))
            for annotation in preview.get("annotations", []):
                if isinstance(annotation, dict):
                    visible_values.extend((str(annotation.get("region", "")), str(annotation.get("note", ""))))
    if context == "standalone_chat" and controller.get("user_facing") is True:
        errors.extend(frontstage_term_errors(visible_values))
    return errors


def _valid_source_ref(value: Any, artifact_ids: set[str]) -> bool:
    if not isinstance(value, str):
        return False
    match = SOURCE_RE.fullmatch(value)
    return bool(match and match.group(1) in artifact_ids)


def escape(value: Any) -> str:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return html.escape(str(value), quote=True)


def safe_inline_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace(
        "&", "\\u0026"
    ).replace("<", "\\u003c").replace(">", "\\u003e")


def verify_physical_artifacts(
    document: dict[str, Any], project_root: Path, artifact_ids: set[str] | None = None
) -> tuple[dict[str, Path], list[str]]:
    root = project_root.expanduser().resolve()
    verified: dict[str, Path] = {}
    errors: list[str] = []
    for artifact in document["source_truth"]["artifacts"]:
        artifact_id = artifact["artifact_id"]
        if artifact_ids is not None and artifact_id not in artifact_ids:
            continue
        candidate = (root / artifact["path"]).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            errors.append(f"artifact {artifact_id} escapes project root")
            continue
        if not candidate.is_file():
            errors.append(f"artifact {artifact_id} is missing")
            continue
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if digest != artifact["sha256"]:
            errors.append(f"artifact {artifact_id} physical SHA-256 mismatch")
            continue
        verified[artifact_id] = candidate
    return verified, errors


def image_data_uri(path: Path) -> str:
    suffix = path.suffix.lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".svg": "image/svg+xml"}.get(suffix)
    if not mime:
        raise VisualizationError(f"preview format is not supported: {suffix}")
    raw = path.read_bytes()
    if suffix == ".svg":
        lowered = raw.lower()
        if any(token in lowered for token in (b"<script", b"onload=", b"javascript:", b'href="http', b"href='http")):
            raise VisualizationError("SVG preview contains active or external content")
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


def render_phase_rail(current_phase: str) -> str:
    current = PHASES.index(current_phase)
    items = []
    for index, phase in enumerate(PHASES):
        classes = ["adco-phase", "text-small"]
        attr = ""
        if index < current:
            classes.append("is-done")
            attr = f' aria-label="{escape(PHASE_LABELS[phase])}，已完成"'
        elif index == current:
            classes.append("is-current")
            attr = f' aria-current="step" aria-label="{escape(PHASE_LABELS[phase])}，当前阶段"'
        else:
            attr = f' aria-label="{escape(PHASE_LABELS[phase])}，尚未开始"'
        items.append(f'<li class="{" ".join(classes)}"{attr}>{escape(PHASE_LABELS[phase])}</li>')
    return '<ol class="adco-phase-rail" aria-label="项目进度">' + "".join(items) + "</ol>"


def render_fields(document: dict[str, Any]) -> str:
    fields = []
    for field in document["presentation"]["fields"]:
        fields.append(
            '<div class="adco-field">'
            f'<dt class="text-small text-muted">{escape(field["label"])}</dt>'
            f'<dd>{escape(field.get("value", ""))}</dd></div>'
        )
    return '<dl class="adco-fields">' + "".join(fields) + "</dl>"


def render_previews(document: dict[str, Any], verified_artifacts: dict[str, Path]) -> str:
    previews = document["presentation"].get("previews", [])
    if not previews:
        return ""
    figures = []
    artifact_by_id = {item["artifact_id"]: item for item in document["source_truth"]["artifacts"]}
    for preview in previews:
        path = verified_artifacts.get(preview["artifact_id"])
        if path is None:
            raise VisualizationError(f"preview artifact is not physically verified: {preview['artifact_id']}")
        notes = "".join(
            f'<li><strong>{escape(item["region"])}</strong>：{escape(item["note"])}</li>'
            for item in preview["annotations"]
        )
        annotation_html = '<ul class="adco-annotations">' + notes + "</ul>" if notes else ""
        artifact = artifact_by_id[preview["artifact_id"]]
        classification_label = ASSET_VISIBLE_VALUES.get(str(artifact.get("review_classification")))
        classification_html = (
            f'<span class="viz-badge adco-preview-status">{escape(classification_label)}</span>'
            if classification_label else ""
        )
        figures.append(
            '<figure class="adco-preview">'
            f'{classification_html}'
            f'<img src="{image_data_uri(path)}" alt="{escape(preview["alt"])}">'
            f'<figcaption><strong>{escape(preview["label"])}</strong> · {escape(preview["caption"])}</figcaption>'
            f'{annotation_html}'
            '</figure>'
        )
    return '<div class="adco-preview-grid">' + "".join(figures) + "</div>"


def render_options(document: dict[str, Any]) -> str:
    options = document["presentation"].get("options", [])
    if not options:
        return ""
    recommendation = document["presentation"].get("recommendation") or {}
    selected_id = recommendation.get("option_id") or options[0]["id"]
    selected = next((item for item in options if item["id"] == selected_id), options[0])
    buttons = []
    for option in options:
        buttons.append(
            f'<button type="button" class="btn viz-tile" data-adco-option="{escape(option["id"])}" '
            f'aria-pressed="{str(option["id"] == selected_id).lower()}">'
            f'{escape(option["label"])}</button>'
        )
    return (
        '<div class="viz-grid adco-choice-grid" role="group">' + "".join(buttons) + "</div>"
        f'<div class="card adco-choice-detail" data-adco-detail aria-live="polite">{escape(selected["label"])}：'
        f'{escape(selected["summary"])}；权衡：{escape(selected["tradeoff"])}</div>'
    )


def render_fragment(document: dict[str, Any], verified_artifacts: dict[str, Path] | None = None) -> str:
    errors = validate_spec(document)
    if errors:
        raise VisualizationError("invalid spec: " + "; ".join(errors))
    if document["execution_context"] != "standalone_chat" or not document["controller"]["user_facing"]:
        raise VisualizationError("orchestrated_provider specs are provider-hidden and cannot render directly")
    verified_artifacts = verified_artifacts or {}
    digest = hashlib.sha256(json.dumps(document, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    root_id = f"adco-view-{digest}"
    data_id = f"adco-data-{digest}"
    css = CSS_PATH.read_text(encoding="utf-8").strip()
    script = JS_PATH.read_text(encoding="utf-8").replace("__ROOT_ID__", root_id).replace("__DATA_ID__", data_id).strip()
    effects = "".join(
        f'<span class="viz-badge">{escape(PHASE_LABELS.get(item["phase"], item["phase"]))}：{escape(item["effect"])}</span>'
        for item in document["presentation"].get("downstream_effects", [])
    )
    actions = "".join(
        f'<button type="button" class="btn{" btn-primary" if index == 0 else ""}" '
        f'data-adco-action="{escape(action["id"])}">{escape(action["label"])}</button>'
        for index, action in enumerate(document["interactions"]["actions"])
    )
    recommendation = document["presentation"].get("recommendation")
    recommendation_text = "暂不预选"
    if recommendation:
        recommended = next(item for item in document["presentation"]["options"] if item["id"] == recommendation["option_id"])
        recommendation_text = f'{recommended["label"]}：{recommendation["reason"]}'
    elif document["surface"]["kind"] == "asset-review":
        preview_ids = {item["artifact_id"] for item in document["presentation"].get("previews", [])}
        asset = next(
            (item for item in document["source_truth"]["artifacts"] if item["artifact_id"] in preview_ids),
            {},
        )
        if asset.get("review_classification") == "illustrative-placeholder":
            recommendation_text = "先取得真实候选素材"
        elif (
            asset.get("source_status") == "verified"
            and asset.get("authorization_status") == "confirmed"
            and asset.get("channel_fit_status") == "verified"
        ):
            recommendation_text = "条件齐全，等待你的选择"
        else:
            recommendation_text = "先补齐待确认条件"
    client_payload = {
        "presentation": {
            "options": [
                {key: option[key] for key in ("id", "label", "summary", "tradeoff")}
                for option in document["presentation"].get("options", [])
            ],
            "recommendation": document["presentation"].get("recommendation"),
        },
        "interactions": {
            "actions": [
                {key: action[key] for key in ("id", "label", "conversation_intent")}
                for action in document["interactions"]["actions"]
            ]
        },
    }
    phase_visual = render_phase_rail(document["phase"]) if document["surface"]["kind"] in {"current-status", "phase-logic"} else ""
    return (
        f'<div id="{root_id}" data-adco-visual="1">\n<style>\n{css}\n</style>\n'
        f'{phase_visual}\n'
        '<dl class="adco-summary">'
        f'<div class="adco-field"><dt class="text-small text-muted">当前阶段</dt><dd>{escape(PHASE_LABELS[document["phase"]])}</dd></div>'
        f'<div class="adco-field"><dt class="text-small text-muted">专业建议</dt><dd>{escape(recommendation_text)}</dd></div>'
        '</dl>\n'
        f'{render_previews(document, verified_artifacts)}\n'
        f'{render_fields(document)}\n'
        f'<p class="adco-question"><strong>需要你决定：</strong>{escape(document["surface"]["question"])}</p>\n'
        f'{render_options(document)}\n<div class="adco-impact"><span class="text-small text-muted">接下来</span>{effects}</div>\n'
        f'<div class="viz-row adco-actions">{actions}</div>\n'
        '<div class="adco-status text-small" data-adco-status role="status">'
        '提交后我会先确认这是最新内容，再告诉你已记录什么和下一步。</div>\n'
        f'<script type="application/json" id="{data_id}">{safe_inline_json(client_payload)}</script>\n'
        f'<script>\n{script}\n</script>\n</div>\n'
    )


def validate_output_path(path: Path, test_output: bool) -> None:
    if path.suffix != ".html" or not SLUG_RE.fullmatch(path.stem):
        raise VisualizationError("output must be a lowercase hyphenated .html filename")
    if not test_output:
        parts = path.expanduser().resolve().parts
        if ".codex" not in parts or "visualizations" not in parts:
            raise VisualizationError("production output must be inside .codex/visualizations")


def write_fragment(
    document: dict[str, Any], output: Path, test_output: bool, force: bool, project_root: Path | None = None
) -> None:
    validate_output_path(output, test_output)
    if output.exists() and not force:
        raise VisualizationError(f"refusing to overwrite existing output: {output}")
    previews = document["presentation"].get("previews", [])
    if not test_output and project_root is None:
        raise VisualizationError("production render requires --project-root for physical source verification")
    verified: dict[str, Path] = {}
    if project_root is not None:
        required_ids = None if not test_output else {item["artifact_id"] for item in previews}
        verified, physical_errors = verify_physical_artifacts(document, project_root, required_ids)
        if physical_errors:
            raise VisualizationError("; ".join(physical_errors))
    elif previews:
        raise VisualizationError("preview render requires --project-root")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_fragment(document, verified), encoding="utf-8")


def render_fallback(document: dict[str, Any]) -> str:
    fallback = document["fallback"]
    headers = fallback["table"]["headers"]
    rows = fallback["table"]["rows"]
    divider = ["---"] * len(headers)
    lines = [
        f"### {document['surface']['title']}",
        "",
        fallback["summary"],
        "",
        "| " + " | ".join(str(item) for item in headers) + " |",
        "| " + " | ".join(divider) + " |",
    ]
    lines.extend("| " + " | ".join(str(item) for item in row) + " |" for row in rows)
    lines.extend(["", "```mermaid", fallback["mermaid"], "```", "", f"**请确认：** {fallback['decision_prompt']}"])
    return "\n".join(lines)


def canonical_sha256(document: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def load_source_spec_from_receipt(receipt: dict[str, Any], receipt_path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    source = receipt.get("source_spec") if isinstance(receipt.get("source_spec"), dict) else {}
    raw_path = source.get("path")
    if not _is_nonempty(raw_path):
        return None, ["source_spec.path is required"]
    source_path = Path(str(raw_path))
    if not source_path.is_absolute():
        source_path = receipt_path.parent / source_path
    try:
        document = load_json(source_path.resolve())
    except VisualizationError as exc:
        return None, [f"cannot load source spec: {exc}"]
    errors.extend(validate_spec(document))
    if canonical_sha256(document) != source.get("sha256"):
        errors.append("source spec hash is stale")
    return document, errors


def validate_writeback(
    receipt: dict[str, Any], receipt_path: Path, project_root: Path | None = None
) -> list[str]:
    errors: list[str] = []
    if receipt.get("contract") != "adco.chat-visualization-writeback@1.0":
        errors.append("writeback contract mismatch")
    source_document, source_errors = load_source_spec_from_receipt(receipt, receipt_path)
    errors.extend(source_errors)
    source = receipt.get("source_spec") if isinstance(receipt.get("source_spec"), dict) else {}
    intent = receipt.get("intent") if isinstance(receipt.get("intent"), dict) else {}
    result = receipt.get("controller_result") if isinstance(receipt.get("controller_result"), dict) else {}
    authority = receipt.get("authority") if isinstance(receipt.get("authority"), dict) else {}
    if source_document:
        if source.get("view_id") != source_document.get("view_id"):
            errors.append("writeback view_id does not match source spec")
        source_gate = source_document["interactions"]["actions"][0]["target_gate"]
        if source.get("current_gate") != source_gate or result.get("current_gate") != source_gate:
            errors.append("writeback current gate does not match source spec")
        action_ids = {item["id"] for item in source_document["interactions"]["actions"]}
        if intent.get("action_id") not in action_ids:
            errors.append("writeback action_id does not match source spec")
        option_ids = {item["id"] for item in source_document["presentation"].get("options", [])}
        selected = intent.get("selected_option_id")
        if selected is not None and selected not in option_ids:
            errors.append("writeback selected option does not match source spec")
        if option_ids and selected is None and intent.get("action_id") != "request-revision":
            errors.append("writeback must identify the selected option")
    if not _is_nonempty(intent.get("human_readable_intent")):
        errors.append("writeback requires human-readable conversation intent")
    if authority.get("visual_action_wrote_state") is not False:
        errors.append("visual action must not write authoritative state")
    if authority.get("controller_revalidated_source") is not True:
        errors.append("controller must revalidate the source")
    if authority.get("artifact_hashes_verified") is not True:
        errors.append("controller must verify artifact hashes")
    if result.get("validation_status") not in {"PASS", "FAIL"}:
        errors.append("controller validation status must be PASS or FAIL")
    if not _is_nonempty(result.get("recorded_change")):
        errors.append("controller result requires recorded_change")
    artifact_results = receipt.get("artifact_results") if isinstance(receipt.get("artifact_results"), list) else []
    if not artifact_results:
        errors.append("writeback requires artifact_results")
    for index, artifact in enumerate(artifact_results):
        if not isinstance(artifact, dict) or not SHA_RE.fullmatch(str(artifact.get("sha256", ""))):
            errors.append(f"writeback artifact {index} requires SHA-256")
        elif Path(str(artifact.get("path", ""))).is_absolute() or ".." in Path(str(artifact.get("path", ""))).parts:
            errors.append(f"writeback artifact {index} path must be project-relative")
        if artifact.get("result") not in {"created", "updated", "stale", "preserved"}:
            errors.append(f"writeback artifact {index} has invalid result")
    confirmation = receipt.get("confirmation") if isinstance(receipt.get("confirmation"), dict) else {}
    for key in ("decision", "artifact_status", "downstream_effect", "next_visible_stage"):
        if not _is_nonempty(confirmation.get(key)):
            errors.append(f"confirmation requires {key}")
    errors.extend(frontstage_term_errors(list(confirmation.values()), "customer-visible confirmation"))
    if project_root is not None:
        if source_document is not None:
            _, physical_errors = verify_physical_artifacts(source_document, project_root)
            errors.extend(physical_errors)
        root = project_root.expanduser().resolve()
        for index, artifact in enumerate(artifact_results):
            candidate = (root / str(artifact.get("path", ""))).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                errors.append(f"writeback artifact {index} escapes project root")
                continue
            if not candidate.is_file():
                errors.append(f"writeback artifact {index} is missing")
                continue
            if hashlib.sha256(candidate.read_bytes()).hexdigest() != artifact.get("sha256"):
                errors.append(f"writeback artifact {index} physical SHA-256 mismatch")
    return errors


def render_confirmation(
    receipt: dict[str, Any], receipt_path: Path, project_root: Path | None = None
) -> str:
    errors = validate_writeback(receipt, receipt_path, project_root)
    if errors:
        raise VisualizationError("invalid writeback: " + "; ".join(errors))
    confirmation = receipt["confirmation"]
    css = CSS_PATH.read_text(encoding="utf-8").strip()
    rows = []
    labels = {
        "decision": "已记录你的选择",
        "artifact_status": "内容更新",
        "downstream_effect": "需要重新检查",
        "next_visible_stage": "下一步",
    }
    for key, label in labels.items():
        rows.append(
            '<div class="adco-field"><dt class="text-small text-muted">'
            f'{escape(label)}</dt><dd>{escape(confirmation[key])}</dd></div>'
        )
    return (
        '<div data-adco-visual="confirmation" aria-label="选择记录结果">'
        f'<style>\n{css}\n</style>'
        '<dl class="adco-fields">' + "".join(rows) + "</dl></div>\n"
    )


def registry_errors() -> list[str]:
    registry = load_json(REGISTRY_PATH)
    errors: list[str] = []
    if registry.get("spec_contract") != CONTRACT:
        errors.append("registry contract mismatch")
    surfaces = registry.get("surfaces") if isinstance(registry.get("surfaces"), list) else []
    found = {item.get("kind") for item in surfaces if isinstance(item, dict)}
    if found != SURFACE_KINDS:
        errors.append("registry must contain all seven ADCO surface kinds exactly once")
    for surface in surfaces:
        if len(surface.get("minimum_visible_fields", [])) < 4:
            errors.append(f"registry surface {surface.get('kind')} has insufficient visible fields")
        if surface.get("preferred_visual") == "dashboard":
            errors.append(f"registry surface {surface.get('kind')} attempts a dashboard")
    return errors


def self_test() -> list[str]:
    failures = registry_errors()
    manifest = load_json(FIXTURE_ROOT / "manifest.json")
    for filename in manifest.get("valid", []):
        document = load_json(FIXTURE_ROOT / filename)
        errors = validate_spec(document)
        if errors:
            failures.append(f"{filename}: expected PASS, got {errors}")
    for item in manifest.get("invalid", []):
        errors = validate_spec(load_json(FIXTURE_ROOT / item["file"]))
        joined = "\n".join(errors)
        if item["expected_error"] not in joined:
            failures.append(f"{item['file']}: expected {item['expected_error']!r}, got {joined!r}")
    with tempfile.TemporaryDirectory(prefix="adco-visualization-") as temp_dir:
        for filename in manifest.get("render", []):
            document = load_json(FIXTURE_ROOT / filename)
            output = Path(temp_dir) / filename.replace(".json", ".html")
            try:
                preview_items = document["presentation"].get("previews", [])
                write_fragment(
                    document,
                    output,
                    test_output=True,
                    force=False,
                    project_root=SKILL_ROOT if preview_items else None,
                )
            except VisualizationError as exc:
                failures.append(f"{filename}: render failed: {exc}")
                continue
            text = output.read_text(encoding="utf-8")
            for forbidden in ("<!doctype", "<html", "<head", "<body") + NETWORK_TOKENS:
                if forbidden in text:
                    failures.append(f"{filename}: rendered forbidden token {forbidden}")
            if "sendFollowUpMessage" not in text or "确认这是最新内容" not in text:
                failures.append(f"{filename}: missing follow-up/revalidation boundary")
            visible = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.IGNORECASE)
            visible = re.sub(r"<style[\s\S]*?</style>", "", visible, flags=re.IGNORECASE).lower()
            visible = re.sub(r"<[^>]+>", " ", visible)
            for token in FRONTSTAGE_FORBIDDEN:
                if token in visible:
                    failures.append(f"{filename}: customer-visible fragment contains backstage term {token}")
            payload_match = re.search(r'<script type="application/json"[^>]*>(.*?)</script>', text, flags=re.DOTALL)
            if not payload_match or any(token in payload_match.group(1) for token in ('"sha256"', '"path"', '"target_gate"', '"write_boundary"')):
                failures.append(f"{filename}: client payload contains backstage fields")
    provider = load_json(FIXTURE_ROOT / "valid-orchestrated-provider.json")
    try:
        render_fragment(provider)
        failures.append("orchestrated_provider rendered directly")
    except VisualizationError as exc:
        if "provider-hidden" not in str(exc):
            failures.append(f"orchestrated_provider rejected for wrong reason: {exc}")
    hostile = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-current-status.json"))
    hostile["presentation"]["fields"][0]["value"] = '</script><script>window.__adcoInjected=true</script><img src=x onerror=alert(1)>'
    hostile_html = render_fragment(hostile)
    if "</script><script>window.__adcoInjected" in hostile_html or "<img src=x" in hostile_html:
        failures.append("hostile value escaped HTML/JSON boundaries")
    if "&lt;/script&gt;" not in hostile_html:
        failures.append("hostile value lacks static escaping evidence")
    backstage_action = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-current-status.json"))
    backstage_action["interactions"]["actions"][0]["label"] = "写入 Gate 回执"
    if not any("customer-visible content contains backstage term" in item for item in validate_spec(backstage_action)):
        failures.append("action label backstage terminology was not rejected")
    physical = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-current-status.json"))
    physical["source_truth"]["artifacts"] = [{
        "artifact_id": "physical-fixture",
        "path": "fixtures/chat-visualization/hero-asset-preview.svg",
        "version": "v12",
        "sha256": "0" * 64,
        "lifecycle": "current",
    }]
    _, physical_errors = verify_physical_artifacts(physical, SKILL_ROOT)
    if not any("physical SHA-256 mismatch" in item for item in physical_errors):
        failures.append("physical artifact hash mismatch was not rejected")
    real_candidate = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-asset-review.json"))
    real_artifact = real_candidate["source_truth"]["artifacts"][0]
    real_artifact.update({
        "review_classification": "real-candidate",
        "source_status": "verified",
        "authorization_status": "confirmed",
        "channel_fit_status": "verified",
        "source_evidence_ref": "source-record#/row/source",
        "authorization_evidence_ref": "authorization-record#/row/authorization",
        "channel_fit_evidence_ref": "channel-record#/row/channel-fit",
    })
    support_files = (
        ("source-record", "fixtures/chat-visualization/manifest.json"),
        ("authorization-record", "fixtures/chat-visualization/valid-current-status.json"),
        ("channel-record", "fixtures/chat-visualization/valid-feedback-impact.json"),
    )
    for artifact_id, relative_path in support_files:
        physical_path = SKILL_ROOT / relative_path
        real_candidate["source_truth"]["artifacts"].append({
            "artifact_id": artifact_id,
            "path": relative_path,
            "version": "v12",
            "sha256": hashlib.sha256(physical_path.read_bytes()).hexdigest(),
            "lifecycle": "current",
        })
    real_values = {
        "asset-status": "真实候选素材",
        "source-status": "来源已确认",
        "authorization-status": "授权已确认",
        "channel-fit": "渠道适配已检查",
        "availability": "可进入使用确认",
    }
    for field in real_candidate["presentation"]["fields"]:
        field["value"] = real_values[field["id"]]
    real_errors = validate_spec(real_candidate)
    if real_errors:
        failures.append(f"fully verified real candidate was rejected: {real_errors}")
    optimistic_candidate = copy.deepcopy(real_candidate)
    optimistic_asset = optimistic_candidate["source_truth"]["artifacts"][0]
    optimistic_asset["authorization_status"] = "pending"
    optimistic_asset["authorization_evidence_ref"] = None
    for field in optimistic_candidate["presentation"]["fields"]:
        if field["id"] == "authorization-status":
            field["value"] = "授权待确认"
        elif field["id"] == "availability":
            field["value"] = "暂不能确认使用"
    optimistic_candidate["interactions"]["actions"][0].update({"kind": "submit-selection", "label": "确认使用"})
    if not any("cannot offer a use-selection action" in item for item in validate_spec(optimistic_candidate)):
        failures.append("real candidate with pending authorization offered a use-selection action")
    placeholder_source = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-asset-review.json"))
    placeholder_asset = placeholder_source["source_truth"]["artifacts"][0]
    placeholder_asset["source_status"] = "verified"
    placeholder_asset["source_evidence_ref"] = "source-record#/row/source"
    placeholder_source["source_truth"]["artifacts"].append(copy.deepcopy(real_candidate["source_truth"]["artifacts"][1]))
    for field in placeholder_source["presentation"]["fields"]:
        if field["id"] == "source-status":
            field["value"] = "来源已确认"
    if not any("placeholder statuses must be not-applicable" in item for item in validate_spec(placeholder_source)):
        failures.append("illustrative placeholder claimed a verified formal source")
    ppt_document = load_json(FIXTURE_ROOT / "valid-ppt-slide-review.json")
    _, ppt_physical_errors = verify_physical_artifacts(ppt_document, SKILL_ROOT)
    if ppt_physical_errors:
        failures.append(f"PPT formal physical verification failed: {ppt_physical_errors}")
    schema = load_json(SCHEMA_PATH)
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        failures.append("schema is not draft 2020-12")
    if not schema.get("allOf"):
        failures.append("schema lacks asset-review conditional requirements")
    artifact_schema = schema.get("$defs", {}).get("artifact", {})
    for key in ("source_evidence_ref", "authorization_evidence_ref", "channel_fit_evidence_ref"):
        if key not in artifact_schema.get("properties", {}):
            failures.append(f"schema lacks asset evidence field: {key}")
    writeback_schema = load_json(WRITEBACK_SCHEMA_PATH)
    if writeback_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        failures.append("writeback schema is not draft 2020-12")
    valid_receipt_path = FIXTURE_ROOT / "valid-writeback-receipt.json"
    valid_receipt = load_json(valid_receipt_path)
    receipt_errors = validate_writeback(valid_receipt, valid_receipt_path)
    if receipt_errors:
        failures.append(f"valid writeback receipt failed: {receipt_errors}")
    else:
        echo = render_confirmation(valid_receipt, valid_receipt_path)
        for forbidden in ("<button", "sendFollowUpMessage", "data-adco-action", "<script"):
            if forbidden in echo:
                failures.append(f"confirmation echo contains action token {forbidden}")
        if "<style>" not in echo or ".adco-fields" not in echo:
            failures.append("confirmation echo is missing self-contained visualization styles")
        hostile_receipt = copy.deepcopy(valid_receipt)
        hostile_receipt["confirmation"]["decision"] = "Gate P4 回执 hash"
        if not any("customer-visible confirmation contains backstage term" in item for item in validate_writeback(hostile_receipt, valid_receipt_path)):
            failures.append("confirmation backstage terminology was not rejected")
    stale_path = FIXTURE_ROOT / "invalid-writeback-stale-source.json"
    stale_errors = validate_writeback(load_json(stale_path), stale_path)
    if "source spec hash is stale" not in "\n".join(stale_errors):
        failures.append("stale writeback source was not rejected")
    css = CSS_PATH.read_text(encoding="utf-8")
    for forbidden_css in (".card {", ".btn {", ".btn-primary {", "#fff", "#ffffff", "font-family:", "border-radius: 0.9rem"):
        if forbidden_css in css:
            failures.append(f"visual CSS overrides host-owned styling: {forbidden_css}")
    representative = render_fragment(load_json(FIXTURE_ROOT / "valid-option-comparison.json"))
    if document_title := load_json(FIXTURE_ROOT / "valid-option-comparison.json")["surface"]["title"]:
        visible = re.sub(r"<script[\s\S]*?</script>", "", representative, flags=re.IGNORECASE)
        visible = re.sub(r"<style[\s\S]*?</style>", "", visible, flags=re.IGNORECASE)
        if document_title in visible:
            failures.append("fragment repeats the response title inside the visualization")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("spec")
    validate_parser.add_argument("--project-root")
    fallback_parser = subparsers.add_parser("render-fallback")
    fallback_parser.add_argument("spec")
    render_parser = subparsers.add_parser("render-html")
    render_parser.add_argument("spec")
    render_parser.add_argument("--output", required=True)
    render_parser.add_argument("--test-output", action="store_true")
    render_parser.add_argument("--force", action="store_true")
    render_parser.add_argument("--project-root")
    writeback_parser = subparsers.add_parser("validate-writeback")
    writeback_parser.add_argument("receipt")
    writeback_parser.add_argument("--project-root")
    confirmation_parser = subparsers.add_parser("render-confirmation")
    confirmation_parser.add_argument("receipt")
    confirmation_parser.add_argument("--output", required=True)
    confirmation_parser.add_argument("--test-output", action="store_true")
    confirmation_parser.add_argument("--force", action="store_true")
    confirmation_parser.add_argument("--project-root")
    subparsers.add_parser("self-test")
    args = parser.parse_args()

    if args.command == "self-test":
        failures = self_test()
        print(f"ADCO_CHAT_VISUALIZATION_SELF_TEST: {'PASS' if not failures else 'FAIL'}")
        for failure in failures:
            print(f"- {failure}")
        return 0 if not failures else 1

    if args.command in {"validate-writeback", "render-confirmation"}:
        receipt_path = Path(args.receipt)
        if not receipt_path.is_absolute():
            receipt_path = SKILL_ROOT / receipt_path
        try:
            receipt = load_json(receipt_path)
            project_root = Path(args.project_root) if args.project_root else None
            errors = validate_writeback(receipt, receipt_path, project_root)
            if errors:
                raise VisualizationError("; ".join(errors))
            if args.command == "validate-writeback":
                print("ADCO_CHAT_VISUALIZATION_WRITEBACK: PASS")
                print(f"physical_sources: {'VERIFIED' if project_root else 'NOT_CHECKED'}")
            else:
                output = Path(args.output).expanduser()
                validate_output_path(output, args.test_output)
                if not args.test_output and project_root is None:
                    raise VisualizationError("production confirmation requires --project-root for physical verification")
                if output.exists() and not args.force:
                    raise VisualizationError(f"refusing to overwrite existing output: {output}")
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(render_confirmation(receipt, receipt_path, project_root), encoding="utf-8")
                print("ADCO_CHAT_VISUALIZATION_CONFIRMATION: PASS")
                print(output.resolve())
                print(f'::codex-inline-vis{{file="{output.name}"}}')
        except VisualizationError as exc:
            print(f"ADCO_CHAT_VISUALIZATION_WRITEBACK: FAIL\n- {exc}")
            return 1
        return 0

    spec_path = Path(args.spec)
    if not spec_path.is_absolute():
        spec_path = SKILL_ROOT / spec_path
    try:
        document = load_json(spec_path)
        errors = validate_spec(document)
        if errors:
            raise VisualizationError("; ".join(errors))
        if args.command == "validate":
            if args.project_root:
                _, physical_errors = verify_physical_artifacts(document, Path(args.project_root))
                if physical_errors:
                    raise VisualizationError("; ".join(physical_errors))
            print("ADCO_CHAT_VISUALIZATION_SPEC: PASS")
            print(f"view_id: {document['view_id']}")
            print(f"physical_sources: {'VERIFIED' if args.project_root else 'NOT_CHECKED'}")
        elif args.command == "render-fallback":
            print(render_fallback(document))
        else:
            output = Path(args.output).expanduser()
            project_root = Path(args.project_root) if args.project_root else None
            write_fragment(document, output, args.test_output, args.force, project_root)
            print("ADCO_CHAT_VISUALIZATION_RENDER: PASS")
            print(output.resolve())
            print(f'::codex-inline-vis{{file="{output.name}"}}')
    except VisualizationError as exc:
        print(f"ADCO_CHAT_VISUALIZATION: FAIL\n- {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
