#!/usr/bin/env python3
"""Validate and render ADCO chat-native OpenAI Visualization specs."""

from __future__ import annotations

import argparse
import base64
import copy
import csv
import hashlib
import html
import json
import re
import tempfile
from dataclasses import dataclass
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
CREATIVE_REVIEW_KINDS = {
    "preserve": "保留",
    "revise": "调整",
    "recheck": "待真实素材复查",
}
CHANNEL_REVIEW_STATUSES = {
    "verified-fit": "已适配",
    "preserve-direction": "构图可延续",
    "reframe": "需要重构",
    "recheck": "待真实素材复查",
}
CREATIVE_REVIEW_SCOPES = {
    "composition-principle", "person", "product", "emotion", "packaging", "crop", "usage-readiness",
}
CREATIVE_REVIEW_BASES = {"composition-reading", "placeholder-limitation", "real-file-observation"}
CHANNEL_ASSESSMENT_BASES = {"creative-direction-only", "real-candidate-check"}
CURRENT_VERSION_STATUSES = {"draft", "internal_review", "ready", "active", "current"}
PLACEHOLDER_FORBIDDEN_CLAIMS = (
    "可直接使用", "可以直接使用", "可确认使用", "已获授权", "授权已确认", "渠道适配已检查",
    "已经证明", "已证明", "ready to use", "approved for use", "licensed for use",
)
ASSET_ACTION_SCOPE_KINDS = {
    "creative-revision": {"request-revision", "register-feedback"},
    "creative-recheck": {"request-recheck"},
    "asset-use-selection": {"submit-selection"},
}
ASSET_REVIEW_FOCUS = {
    "asset-role": "画面任务", "reference-boundary": "参考边界", "customer-moment": "消费者时刻",
    "product-proof": "产品证明", "brand-memory": "品牌记忆", "region-findings": "画面区域判断",
    "channel-placement": "渠道落位", "source-and-authorization": "来源与使用授权",
}
ASSET_ACTION_FORBIDDEN = (
    "approve", "mark complete", "complete project", "批准", "标记完成", "完成项目", "全局安装",
)
ASSET_EXTERNAL_OPERATION_RE = re.compile(
    r"(?ix)(?:\b(?:send|deliver|delivery|publish|upload|release|distribute|share|handoff|hand[ -]?over|ship)\b"
    r"|交付|发送|发给|提交给|递交|移交|分享|发布|上线|投放|上传|寄给|传给)"
)
ASSET_GENERIC_ACTION_LABELS = {"继续", "确认", "下一步", "continue", "confirm", "next"}
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
UNRESOLVED = object()


class VisualizationError(Exception):
    pass


@dataclass(frozen=True)
class VerifiedArtifact:
    """Immutable bytes captured by the same read that passed SHA verification."""

    path: Path
    data: bytes


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
    errors: list[str] = []
    for token in FRONTSTAGE_FORBIDDEN:
        if re.fullmatch(r"[a-z0-9_. -]+", token):
            found = re.search(
                rf"(?<![a-z0-9_]){re.escape(token)}(?![a-z0-9_])",
                lowered,
            )
        else:
            found = token in lowered
        if found:
            errors.append(f"{context} contains backstage term: {token}")
    return errors


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
    binding_mode = truth.get("binding_mode")
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
    artifact_by_id = {
        item.get("artifact_id"): item for item in artifacts if isinstance(item, dict)
    }

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
    creative_review = presentation.get("creative_review")
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
                        continue
                    annotation_kind = annotation.get("kind")
                    if annotation_kind is not None and annotation_kind not in CREATIVE_REVIEW_KINDS:
                        errors.append(f"preview {index} annotation has invalid creative review kind")
                    if annotation.get("scope") is not None and annotation.get("scope") not in CREATIVE_REVIEW_SCOPES:
                        errors.append(f"preview {index} annotation has invalid creative review scope")
                    if annotation.get("basis") is not None and annotation.get("basis") not in CREATIVE_REVIEW_BASES:
                        errors.append(f"preview {index} annotation has invalid creative review basis")
                    anchor = annotation.get("anchor")
                    if anchor is not None:
                        valid_anchor = (
                            isinstance(anchor, dict)
                            and isinstance(anchor.get("x"), (int, float))
                            and isinstance(anchor.get("y"), (int, float))
                            and not isinstance(anchor.get("x"), bool)
                            and not isinstance(anchor.get("y"), bool)
                            and 0 <= anchor["x"] <= 100
                            and 0 <= anchor["y"] <= 100
                        )
                        if not valid_anchor:
                            errors.append(f"preview {index} annotation anchor must use 0-100 x/y coordinates")

    if kind == "asset-review" and context == "standalone_chat" and controller.get("user_facing") is True:
        if not isinstance(creative_review, dict):
            errors.append("asset-review requires ADCO creative_review context")
        else:
            for lens_name in ("asset_role", "reference_boundary", "customer_moment", "product_proof", "brand_memory"):
                lens = creative_review.get(lens_name)
                if not isinstance(lens, dict) or not _is_nonempty(lens.get("label")) or not _is_nonempty(lens.get("value")):
                    errors.append(f"creative_review {lens_name} requires a visible label and value")
                    continue
                provenance = lens.get("provenance")
                source_ref = lens.get("source_ref")
                if provenance != "source-bound":
                    errors.append(f"creative_review {lens_name} must be source-bound")
                elif not _valid_current_source_ref(source_ref, artifact_by_id, current_version):
                    errors.append(f"creative_review {lens_name} requires a current-version source binding")
            channel_plan = creative_review.get("channel_plan")
            if not isinstance(channel_plan, list) or not 1 <= len(channel_plan) <= 4:
                errors.append("creative_review channel_plan requires one to four target placements")
            else:
                for index, placement in enumerate(channel_plan):
                    if not isinstance(placement, dict):
                        errors.append(f"creative_review channel placement {index} must be an object")
                        continue
                    if not all(_is_nonempty(placement.get(key)) for key in ("channel", "format", "note")):
                        errors.append(f"creative_review channel placement {index} is incomplete")
                    if placement.get("format") not in {"16:9", "4:5", "1:1", "9:16"}:
                        errors.append(f"creative_review channel placement {index} has unsupported format")
                    if placement.get("status") not in CHANNEL_REVIEW_STATUSES:
                        errors.append(f"creative_review channel placement {index} has invalid status")
                    if placement.get("assessment_basis") not in CHANNEL_ASSESSMENT_BASES:
                        errors.append(f"creative_review channel placement {index} has invalid assessment basis")
                    if not _valid_current_source_ref(placement.get("source_ref"), artifact_by_id, current_version):
                        errors.append(f"creative_review channel placement {index} requires a current-version source binding")
        if len(previews) != 1:
            errors.append("asset-review requires exactly one inspected preview")
        elif isinstance(previews[0], dict):
            annotations = previews[0].get("annotations")
            if not isinstance(annotations, list) or not annotations:
                errors.append("asset-review requires at least one region-level creative judgment")
            else:
                for annotation in annotations:
                    if not isinstance(annotation, dict):
                        continue
                    if annotation.get("kind") not in CREATIVE_REVIEW_KINDS:
                        errors.append("asset-review annotations must classify preserve, revise, or recheck")
                    if annotation.get("scope") not in CREATIVE_REVIEW_SCOPES:
                        errors.append("asset-review annotations require a structured review scope")
                    if annotation.get("basis") not in CREATIVE_REVIEW_BASES:
                        errors.append("asset-review annotations require a structured evidence basis")
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
                if binding_mode != "fixture-placeholder":
                    errors.append("illustrative placeholder requires fixture-placeholder truth binding")
                if any(status != "not-applicable" for status in (source_status, authorization_status, channel_fit_status)):
                    errors.append("illustrative placeholder statuses must be not-applicable")
            elif classification == "real-candidate" and any(
                status == "not-applicable" for status in (source_status, authorization_status, channel_fit_status)
            ):
                errors.append("real candidate statuses cannot be not-applicable")
            elif classification == "real-candidate" and binding_mode != "adco-control-plane":
                errors.append("real candidate requires ADCO control-plane truth binding")

            if len(previews) == 1 and isinstance(previews[0], dict):
                for annotation in previews[0].get("annotations", []):
                    if not isinstance(annotation, dict):
                        continue
                    if classification == "illustrative-placeholder":
                        if annotation.get("kind") == "preserve" and (
                            annotation.get("scope") != "composition-principle"
                            or annotation.get("basis") != "composition-reading"
                        ):
                            errors.append("placeholder can preserve only a composition principle")
                        if annotation.get("scope") != "composition-principle" and annotation.get("kind") == "preserve":
                            errors.append("placeholder cannot preserve person, product, emotion, packaging, crop, or readiness")
                        if annotation.get("kind") in {"revise", "recheck"} and annotation.get("basis") != "placeholder-limitation":
                            errors.append("placeholder revise/recheck findings must state their placeholder limitation")
                        claim_text = f'{annotation.get("region", "")} {annotation.get("note", "")}'.lower()
                        if any(token in claim_text for token in PLACEHOLDER_FORBIDDEN_CLAIMS):
                            errors.append("placeholder finding makes a forbidden production-use claim")
                    elif classification == "real-candidate" and annotation.get("basis") != "real-file-observation":
                        errors.append("real candidate findings must be based on the inspected real file")
            channel_plan = creative_review.get("channel_plan", []) if isinstance(creative_review, dict) else []
            if classification == "illustrative-placeholder" and any(
                item.get("assessment_basis") != "creative-direction-only" or item.get("status") == "verified-fit"
                for item in channel_plan if isinstance(item, dict)
            ):
                errors.append("placeholder channel plan can describe direction only, not verified fit")
            if classification == "real-candidate" and any(
                item.get("assessment_basis") != "real-candidate-check"
                for item in channel_plan if isinstance(item, dict)
            ):
                errors.append("real candidate channel plan must be based on the inspected real file")

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
                and bool(channel_plan)
                and all(item.get("status") == "verified-fit" for item in channel_plan if isinstance(item, dict))
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
        if kind == "asset-review" and context == "standalone_chat" and controller.get("user_facing") is True:
            review_scope = action.get("review_scope")
            review_focus = action.get("review_focus")
            if review_scope not in ASSET_ACTION_SCOPE_KINDS or action.get("kind") not in ASSET_ACTION_SCOPE_KINDS.get(review_scope, set()):
                errors.append(f"asset-review action {index} has an invalid creative review scope")
            if (
                not isinstance(review_focus, list) or len(review_focus) < 2
                or len(set(review_focus)) != len(review_focus)
                or any(item not in ASSET_REVIEW_FOCUS for item in review_focus)
            ):
                errors.append(f"asset-review action {index} requires two or more ADCO review focuses")
            label = str(action.get("label", "")).strip().lower()
            action_text = f'{label} {action.get("conversation_intent", "")}'.lower()
            if label in ASSET_GENERIC_ACTION_LABELS:
                errors.append(f"asset-review action {index} label is too generic")
            if any(token in action_text for token in ASSET_ACTION_FORBIDDEN):
                errors.append(f"asset-review action {index} attempts approval, external send, publish, upload, completion, or install")
            if ASSET_EXTERNAL_OPERATION_RE.search(action_text):
                errors.append(f"asset-review action {index} requests an external delivery or publication outside the review capability")
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
    if isinstance(creative_review, dict):
        for lens_name in ("asset_role", "reference_boundary", "customer_moment", "product_proof", "brand_memory"):
            lens = creative_review.get(lens_name)
            if isinstance(lens, dict):
                visible_values.extend((str(lens.get("label", "")), str(lens.get("value", ""))))
        for placement in creative_review.get("channel_plan", []):
            if isinstance(placement, dict):
                visible_values.extend((str(placement.get("channel", "")), str(placement.get("format", "")), str(placement.get("note", ""))))
    if context == "standalone_chat" and controller.get("user_facing") is True:
        errors.extend(frontstage_term_errors(visible_values))
    return errors


def _valid_source_ref(value: Any, artifact_ids: set[str]) -> bool:
    if not isinstance(value, str):
        return False
    match = SOURCE_RE.fullmatch(value)
    return bool(match and match.group(1) in artifact_ids)


def _valid_current_source_ref(
    value: Any, artifact_by_id: dict[str, dict[str, Any]], current_version: Any
) -> bool:
    if not isinstance(value, str):
        return False
    match = SOURCE_RE.fullmatch(value)
    artifact = artifact_by_id.get(match.group(1)) if match else None
    return bool(
        isinstance(artifact, dict)
        and artifact.get("lifecycle") == "current"
        and artifact.get("version") == current_version
    )


def escape(value: Any) -> str:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return html.escape(str(value), quote=True)


def safe_inline_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace(
        "&", "\\u0026"
    ).replace("<", "\\u003c").replace(">", "\\u003e")


def mermaid_label(value: Any) -> str:
    """Keep derived customer-facing labels inert inside Mermaid node syntax."""
    return re.sub(r'[\[\]{}()"<>`|]', " ", str(value)).replace("\n", " ").strip()


def verify_physical_artifacts(
    document: dict[str, Any], project_root: Path, artifact_ids: set[str] | None = None
) -> tuple[dict[str, VerifiedArtifact], list[str]]:
    root = project_root.expanduser().resolve()
    verified: dict[str, VerifiedArtifact] = {}
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
        try:
            data = candidate.read_bytes()
        except OSError:
            errors.append(f"artifact {artifact_id} cannot be read")
            continue
        digest = hashlib.sha256(data).hexdigest()
        if digest != artifact["sha256"]:
            errors.append(f"artifact {artifact_id} physical SHA-256 mismatch")
            continue
        verified[artifact_id] = VerifiedArtifact(path=candidate, data=data)
    return verified, errors


def _resolve_json_pointer(root: Any, pointer: str) -> tuple[bool, Any]:
    if not pointer.startswith("/"):
        return False, None
    current = root
    for raw_token in pointer[1:].split("/"):
        if re.search(r"~(?![01])", raw_token):
            return False, None
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                return False, None
            current = current[token]
        elif isinstance(current, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", token):
                return False, None
            index = int(token)
            if index >= len(current):
                return False, None
            current = current[index]
        else:
            return False, None
    return True, current


def _read_csv_records(path: Path) -> tuple[list[dict[str, str]], str | None]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle)), None
    except OSError as exc:
        return [], str(exc)


def _current_version_truth_values(text: str) -> dict[str, str] | None:
    matches = list(re.finditer(
        r"(?ims)^##[ \t]+Current Version Truth[ \t]*\n(.*?)(?=^##[ \t]+|\Z)", text
    ))
    if len(matches) != 1:
        return None
    return {
        key: value.strip()
        for key, value in re.findall(r"(?m)^[ \t]*([a-z0-9_]+)[ \t]*:[ \t]*(.*)$", matches[0].group(1))
    }


def validate_adco_control_plane_binding(
    document: dict[str, Any], project_root: Path | None, verified_artifacts: dict[str, VerifiedArtifact],
    json_records: dict[str, dict[str, Any]],
) -> list[str]:
    if document["source_truth"].get("binding_mode") != "adco-control-plane":
        return []
    if project_root is None:
        return ["real-candidate review requires a project root for ADCO control-plane binding"]
    root = project_root.expanduser().resolve()
    control = root / "AD-creative/orchestrator"
    errors: list[str] = []
    required_paths = {
        "project": control / "project.yml",
        "truth": control / "current_truth.md",
        "versions": control / "version_map.csv",
        "artifacts": control / "artifact_index.csv",
        "sources": control / "source_events.csv",
        "gates": control / "gate_log.csv",
        "authorizations": root / "AD-creative/visual_assets/asset_authorizations.csv",
    }
    for label, path in required_paths.items():
        if not path.is_file():
            errors.append(f"ADCO control-plane binding is missing {label}")
    if errors:
        return errors

    project_text = required_paths["project"].read_text(encoding="utf-8")
    name_match = re.search(r"(?m)^[ \t]+name:[ \t]*(.*)$", project_text)
    project_name = (name_match.group(1).strip().strip('"\'') if name_match else "")
    if not project_name or project_name != document["source_truth"]["project_id"]:
        errors.append("ADCO project name does not match visualization project_id")

    truth_values = _current_version_truth_values(required_paths["truth"].read_text(encoding="utf-8"))
    current_version = document["source_truth"]["current_version"]
    if truth_values is None or truth_values.get("current_version_id") != current_version:
        errors.append("ADCO current_truth does not match visualization current_version")

    versions, version_error = _read_csv_records(required_paths["versions"])
    artifacts, artifact_error = _read_csv_records(required_paths["artifacts"])
    sources, source_error = _read_csv_records(required_paths["sources"])
    gates, gate_error = _read_csv_records(required_paths["gates"])
    authorizations, authorization_error = _read_csv_records(required_paths["authorizations"])
    for label, issue in (
        ("version_map", version_error), ("artifact_index", artifact_error), ("source_events", source_error),
        ("gate_log", gate_error), ("asset_authorizations", authorization_error),
    ):
        if issue:
            errors.append(f"ADCO {label} cannot be read")
    if errors:
        return errors

    version_matches = [row for row in versions if row.get("version_id", "").strip() == current_version]
    if len(version_matches) != 1 or version_matches[0].get("status", "").strip().lower() not in CURRENT_VERSION_STATUSES:
        errors.append("ADCO version_map lacks one current-view row for visualization current_version")
    elif truth_values and truth_values.get("version_map_status") and (
        truth_values["version_map_status"].lower() != version_matches[0].get("status", "").strip().lower()
    ):
        errors.append("ADCO current_truth and version_map status disagree")

    for spec_artifact in document["source_truth"]["artifacts"]:
        matches = [row for row in artifacts if row.get("artifact_id", "").strip() == spec_artifact["artifact_id"]]
        if len(matches) != 1:
            errors.append(f"ADCO artifact_index does not uniquely register {spec_artifact['artifact_id']}")
            continue
        row = matches[0]
        lifecycle = (row.get("lifecycle_state") or row.get("status") or "").strip().lower()
        if (
            row.get("path", "").strip() != spec_artifact["path"]
            or row.get("version", "").strip() != spec_artifact["version"]
            or row.get("sha256", "").strip() != spec_artifact["sha256"]
            or lifecycle not in {"active", "current", "registered", "ready"}
        ):
            errors.append(f"ADCO artifact_index binding is stale or mismatched for {spec_artifact['artifact_id']}")

    preview_id = document["presentation"]["previews"][0]["artifact_id"]
    preview = next(item for item in document["source_truth"]["artifacts"] if item["artifact_id"] == preview_id)
    source_record = next((record for record in json_records.values() if record.get("contract") == "adco.asset-source-record@1.0"), None)
    if isinstance(source_record, dict):
        source_event_id = source_record.get("source_event_id")
        matches = [row for row in sources if row.get("source_event_id", "").strip() == source_event_id]
        if len(matches) != 1 or (
            preview_id not in matches[0].get("affects_artifacts", "")
            and preview["path"] not in matches[0].get("file_paths", "")
        ):
            errors.append("asset source record is not backed by a registered source event")

    authorization_record = next((record for record in json_records.values() if record.get("contract") == "adco.asset-authorization-record@1.0"), None)
    if isinstance(authorization_record, dict):
        authorization_id = authorization_record.get("authorization_id")
        matches = [row for row in authorizations if row.get("authorization_id", "").strip() == authorization_id]
        valid = False
        if len(matches) == 1:
            row = matches[0]
            evidence_ref = row.get("evidence_ref", "").strip()
            evidence_ok = False
            confirmation_match = re.fullmatch(
                r"(?:user_confirmation|client_confirmation):([A-Za-z0-9._-]+)", evidence_ref
            )
            if confirmation_match:
                confirmation_id = confirmation_match.group(1)
                confirmation_rows = [
                    item for item in sources if item.get("source_event_id", "").strip() == confirmation_id
                ]
                if len(confirmation_rows) == 1:
                    confirmation = confirmation_rows[0]
                    confirmation_type = confirmation.get("source_type", "").strip().lower()
                    semantics = confirmation.get("declared_semantics", "").strip().lower()
                    trust = confirmation.get("trust_level", "").strip().lower()
                    owner = confirmation.get("source_owner", "").strip().lower()
                    expected_owner = "user" if evidence_ref.startswith("user_confirmation:") else "client"
                    expected_type = f"{expected_owner}_confirmation"
                    expected_trust = f"{expected_owner}_confirmed"
                    evidence_ok = (
                        confirmation_type == expected_type
                        and semantics == "direct_use_authorization"
                        and trust == expected_trust
                        and bool(confirmation.get("received_at", "").strip())
                        and owner == expected_owner
                        and row.get("approved_by", "").strip().lower() == expected_owner
                        and (
                            preview_id in confirmation.get("affects_artifacts", "")
                            or preview["path"] in confirmation.get("file_paths", "")
                        )
                    )
            valid = (
                row.get("asset_id", "").strip() == preview_id
                and row.get("asset_sha256", "").strip() == preview["sha256"]
                and row.get("approval_scope", "").strip().lower() in {"client_review", "client_delivery", "client_visible"}
                and row.get("status", "").strip().lower() == "approved"
                and not row.get("revoked_at", "").strip()
                and row.get("approved_by", "").strip().lower() in {"user", "client"}
                and bool(row.get("approved_at", "").strip())
                and evidence_ok
            )
        if not valid:
            errors.append("asset authorization record is not backed by current registered human/client authorization")

    channel_record = next((record for record in json_records.values() if record.get("contract") == "adco.asset-channel-fit-record@1.0"), None)
    if isinstance(channel_record, dict):
        gate_run_id = channel_record.get("gate_run_id")
        matches = [row for row in gates if row.get("gate_run_id", "").strip() == gate_run_id]
        if len(matches) != 1 or (
            matches[0].get("status", "").strip().upper() not in {"PASS", "PASSED"}
            or matches[0].get("target_sha256", "").strip() != preview["sha256"]
            or preview_id not in matches[0].get("checked_artifacts", "")
        ):
            errors.append("asset channel-fit record is not backed by a current exact-asset Gate run")
    return errors


def validate_asset_physical_bindings(
    document: dict[str, Any], verified_artifacts: dict[str, VerifiedArtifact], project_root: Path | None = None,
) -> list[str]:
    if document.get("surface", {}).get("kind") != "asset-review":
        return []
    errors: list[str] = []
    truth = document["source_truth"]
    current_version = truth["current_version"]
    artifacts = {item["artifact_id"]: item for item in truth["artifacts"]}
    preview_id = document["presentation"]["previews"][0]["artifact_id"]
    preview_artifact = artifacts[preview_id]
    json_cache: dict[str, dict[str, Any]] = {}

    def resolve(ref: Any, context: str) -> tuple[dict[str, Any] | None, Any]:
        match = SOURCE_RE.fullmatch(str(ref or ""))
        if not match:
            errors.append(f"{context} has an invalid source reference")
            return None, UNRESOLVED
        artifact_id, pointer = match.groups()
        artifact = artifacts.get(artifact_id)
        if not isinstance(artifact, dict) or artifact.get("lifecycle") != "current" or artifact.get("version") != current_version:
            errors.append(f"{context} must reference a current-version artifact")
            return None, UNRESOLVED
        verified = verified_artifacts.get(artifact_id)
        if verified is None:
            errors.append(f"{context} source artifact was not physically verified")
            return None, UNRESOLVED
        if verified.path.suffix.lower() != ".json":
            errors.append(f"{context} must reference a structured JSON record")
            return None, UNRESOLVED
        if artifact_id not in json_cache:
            try:
                record = json.loads(verified.data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                errors.append(f"{context} structured source cannot be read")
                return None, UNRESOLVED
            if not isinstance(record, dict):
                errors.append(f"{context} structured source must be an object")
                return None, UNRESOLVED
            json_cache[artifact_id] = record
        record = json_cache[artifact_id]
        if record.get("project") != truth.get("project_id") or record.get("version") != current_version:
            errors.append(f"{context} structured source does not match the declared project and version")
        found, value = _resolve_json_pointer(record, pointer)
        if not found:
            errors.append(f"{context} source pointer does not exist")
            return record, UNRESOLVED
        return record, value

    review = document["presentation"].get("creative_review")
    if isinstance(review, dict):
        for lens_name in ("asset_role", "reference_boundary", "customer_moment", "product_proof", "brand_memory"):
            lens = review.get(lens_name)
            if not isinstance(lens, dict):
                continue
            _, bound_value = resolve(lens.get("source_ref"), f"creative_review {lens_name}")
            if bound_value is not UNRESOLVED and bound_value != lens.get("value"):
                errors.append(f"creative_review {lens_name} visible value does not match its source")
        for index, placement in enumerate(review.get("channel_plan", [])):
            if not isinstance(placement, dict):
                continue
            _, bound_value = resolve(placement.get("source_ref"), f"creative_review channel placement {index}")
            if bound_value is not UNRESOLVED:
                expected = {key: placement.get(key) for key in ("channel", "format", "status", "assessment_basis", "note")}
                if not isinstance(bound_value, dict) or any(bound_value.get(key) != value for key, value in expected.items()):
                    errors.append(f"creative_review channel placement {index} does not match its source")

    evidence_contracts = (
        ("source_status", "verified", "source_evidence_ref", "adco.asset-source-record@1.0"),
        ("authorization_status", "confirmed", "authorization_evidence_ref", "adco.asset-authorization-record@1.0"),
        ("channel_fit_status", "verified", "channel_fit_evidence_ref", "adco.asset-channel-fit-record@1.0"),
    )
    for status_name, ready_status, ref_name, contract in evidence_contracts:
        if preview_artifact.get(status_name) != ready_status:
            continue
        record, bound_value = resolve(preview_artifact.get(ref_name), f"asset-review {status_name}")
        if record is None:
            continue
        if record.get("contract") != contract:
            errors.append(f"asset-review {status_name} references the wrong evidence contract")
        if record.get("asset_id") != preview_id or record.get("asset_sha256") != preview_artifact.get("sha256"):
            errors.append(f"asset-review {status_name} evidence does not bind the inspected asset")
        if bound_value != ready_status:
            errors.append(f"asset-review {status_name} evidence does not confirm the claimed status")
        if status_name == "source_status":
            if not all(_is_nonempty(record.get(key)) for key in ("source_platform", "source_location")):
                errors.append("asset-review source evidence lacks provenance details")
        elif status_name == "authorization_status":
            if record.get("scope") != "direct-client-use" or not all(
                _is_nonempty(record.get(key)) for key in ("authorized_by", "authorized_at")
            ):
                errors.append("asset-review authorization evidence lacks direct-use scope and authorization details")
        else:
            targets = record.get("targets")
            if not isinstance(targets, list) or not targets or any(
                not isinstance(item, dict)
                or not _is_nonempty(item.get("channel"))
                or item.get("format") not in {"16:9", "4:5", "1:1", "9:16"}
                or item.get("fit_status") != "verified"
                for item in targets
            ):
                errors.append("asset-review channel evidence lacks verified named targets")
            elif isinstance(review, dict):
                covered = {(item["channel"], item["format"]) for item in targets}
                required = {(item["channel"], item["format"]) for item in review.get("channel_plan", [])}
                if not required.issubset(covered):
                    errors.append("asset-review channel evidence does not cover every displayed target placement")
    if truth.get("binding_mode") == "fixture-placeholder":
        if any(
            record.get("project") != truth.get("project_id") or record.get("version") != current_version
            for record in json_cache.values()
        ):
            errors.append("fixture placeholder records do not match declared project and version")
    errors.extend(validate_adco_control_plane_binding(document, project_root, verified_artifacts, json_cache))
    return errors


def image_data_uri(artifact: VerifiedArtifact) -> str:
    suffix = artifact.path.suffix.lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".svg": "image/svg+xml"}.get(suffix)
    if not mime:
        raise VisualizationError(f"preview format is not supported: {suffix}")
    raw = artifact.data
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


def render_previews(document: dict[str, Any], verified_artifacts: dict[str, VerifiedArtifact]) -> str:
    previews = document["presentation"].get("previews", [])
    if not previews:
        return ""
    figures = []
    artifact_by_id = {item["artifact_id"]: item for item in document["source_truth"]["artifacts"]}
    for preview in previews:
        verified = verified_artifacts.get(preview["artifact_id"])
        if verified is None:
            raise VisualizationError(f"preview artifact is not physically verified: {preview['artifact_id']}")
        findings = []
        hotspots = []
        for index, item in enumerate(preview["annotations"], start=1):
            kind = item.get("kind", "recheck")
            kind_label = CREATIVE_REVIEW_KINDS.get(kind, "复查")
            finding_id = f'adco-{preview["artifact_id"]}-finding-{index}'
            findings.append(
                f'<li id="{finding_id}" class="adco-finding is-{escape(kind)}" data-adco-finding="{index}">'
                f'<span class="adco-finding-index text-small" aria-hidden="true">{index}</span>'
                f'<div><span class="text-small adco-finding-kind">{escape(kind_label)}</span>'
                f'<strong>{escape(item["region"])}</strong><p>{escape(item["note"])}</p></div></li>'
            )
            anchor = item.get("anchor")
            if isinstance(anchor, dict):
                hotspots.append(
                    f'<button type="button" class="btn adco-hotspot" aria-pressed="false" '
                    f'data-adco-hotspot="{index}" aria-controls="{finding_id}" '
                    f'aria-label="查看画面判断 {index}：{escape(kind_label)}，{escape(item["region"])}" '
                    f'style="--adco-x:{float(anchor["x"]):g}%;--adco-y:{float(anchor["y"]):g}%">{index}</button>'
                )
        location_hint = "点击画面标记定位" if hotspots else "按画面区域阅读"
        annotation_html = (
            '<section class="adco-review-findings" aria-label="画面判断">'
            f'<div class="adco-section-heading"><span>画面判断</span><span class="text-small text-muted">{location_hint}</span></div>'
            '<ol class="adco-findings">' + "".join(findings) + "</ol></section>"
            if findings else ""
        )
        artifact = artifact_by_id[preview["artifact_id"]]
        classification_label = ASSET_VISIBLE_VALUES.get(str(artifact.get("review_classification")))
        classification_html = (
            f'<span class="viz-badge adco-preview-status">{escape(classification_label)}</span>'
            if classification_label else ""
        )
        figures.append(
            '<div class="adco-preview-layout"><figure class="adco-preview">'
            f'{classification_html}<div class="adco-image-stage">'
            f'<img src="{image_data_uri(verified)}" alt="{escape(preview["alt"])}">'
            f'{"".join(hotspots)}</div>'
            f'<figcaption><strong>{escape(preview["label"])}</strong> · {escape(preview["caption"])}</figcaption>'
            f'</figure>{annotation_html}</div>'
        )
    return '<div class="adco-preview-grid">' + "".join(figures) + "</div>"


def render_creative_review(document: dict[str, Any]) -> str:
    review = document["presentation"].get("creative_review")
    if not isinstance(review, dict):
        return ""
    role = review["asset_role"]
    reference_boundary = review["reference_boundary"]
    lenses = [review["customer_moment"], review["product_proof"], review["brand_memory"]]
    lens_html = "".join(
        '<div class="adco-creative-lens">'
        f'<span class="text-small text-muted">{escape(item["label"])}</span>'
        f'<strong>{escape(item["value"])}</strong></div>'
        for item in lenses
    )
    return (
        '<section class="adco-creative-brief" aria-label="广告创意任务">'
        '<div class="adco-role-callout"><span class="text-small">这张图在方案里的任务</span>'
        '<div class="adco-role-copy">'
        f'<strong>{escape(role["value"])}</strong>'
        f'<span class="text-small text-muted">参考边界：{escape(reference_boundary["value"])}</span></div></div>'
        f'<div class="adco-creative-lenses">{lens_html}</div></section>'
    )


def render_channel_plan(document: dict[str, Any]) -> str:
    review = document["presentation"].get("creative_review")
    if not isinstance(review, dict):
        return ""
    ratio_classes = {"16:9": "is-wide", "4:5": "is-portrait", "1:1": "is-square", "9:16": "is-vertical"}
    cards = []
    for item in review["channel_plan"]:
        status = item["status"]
        cards.append(
            '<article class="adco-channel-card">'
            f'<div class="adco-ratio-frame {ratio_classes[item["format"]]}" aria-hidden="true">'
            '<span></span><i></i></div>'
            '<div class="adco-channel-copy">'
            f'<div><strong>{escape(item["channel"])}</strong><span>{escape(item["format"])}</span></div>'
            f'<span class="adco-channel-status text-small">{escape(CHANNEL_REVIEW_STATUSES[status])}</span>'
            f'<p class="text-small">{escape(item["note"])}</p></div></article>'
        )
    return (
        '<section class="adco-channel-plan" aria-label="渠道落位">'
        '<div class="adco-section-heading"><span>渠道落位</span><span class="text-small text-muted">同一创意方向，不等于同一裁切</span></div>'
        f'<div class="adco-channel-grid">{"".join(cards)}</div></section>'
    )


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


def render_fragment(
    document: dict[str, Any], verified_artifacts: dict[str, VerifiedArtifact] | None = None,
    project_root: Path | None = None,
) -> str:
    errors = validate_spec(document)
    if errors:
        raise VisualizationError("invalid spec: " + "; ".join(errors))
    if document["execution_context"] != "standalone_chat" or not document["controller"]["user_facing"]:
        raise VisualizationError("orchestrated_provider specs are provider-hidden and cannot render directly")
    verified_artifacts = verified_artifacts or {}
    binding_errors = validate_asset_physical_bindings(document, verified_artifacts, project_root)
    if binding_errors:
        raise VisualizationError("invalid physical bindings: " + "; ".join(binding_errors))
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
            annotations = document["presentation"].get("previews", [{}])[0].get("annotations", [])
            preserves_composition = any(
                item.get("kind") == "preserve" and item.get("scope") == "composition-principle"
                for item in annotations if isinstance(item, dict)
            )
            recommendation_text = (
                "保留构图方向，替换演示素材" if preserves_composition
                else "重新建立创意方向，并替换演示素材"
            )
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
                {key: action[key] for key in ("id", "label", "conversation_intent", "review_focus") if key in action}
                for action in document["interactions"]["actions"]
            ]
        },
    }
    phase_visual = render_phase_rail(document["phase"]) if document["surface"]["kind"] in {"current-status", "phase-logic"} else ""
    if document["surface"]["kind"] == "asset-review":
        body = (
            '<section class="adco-asset-verdict" aria-label="当前创意判断">'
            '<div><span class="text-small">当前创意判断</span>'
            f'<strong>{escape(recommendation_text)}</strong></div>'
            f'<span class="viz-badge">{escape(PHASE_LABELS[document["phase"]])}</span></section>\n'
            f'{render_creative_review(document)}\n'
            f'{render_previews(document, verified_artifacts)}\n'
            f'{render_channel_plan(document)}\n'
            '<section class="adco-use-conditions" aria-label="使用前提">'
            '<div class="adco-section-heading"><span>使用前提</span><span class="text-small text-muted">创意判断与素材可用性分开看</span></div>'
            f'{render_fields(document)}</section>\n'
        )
    else:
        body = (
            f'{phase_visual}\n'
            '<dl class="adco-summary">'
            f'<div class="adco-field"><dt class="text-small text-muted">当前阶段</dt><dd>{escape(PHASE_LABELS[document["phase"]])}</dd></div>'
            f'<div class="adco-field"><dt class="text-small text-muted">专业建议</dt><dd>{escape(recommendation_text)}</dd></div>'
            '</dl>\n'
            f'{render_previews(document, verified_artifacts)}\n'
            f'{render_fields(document)}\n'
        )
    return (
        f'<div id="{root_id}" data-adco-visual="1">\n<style>\n{css}\n</style>\n'
        f'{body}'
        f'{render_options(document)}\n<div class="adco-impact"><span class="text-small text-muted">接下来</span>{effects}</div>\n'
        f'<div class="viz-row adco-actions">{actions}</div>\n'
        '<div class="adco-status text-small" data-adco-status role="status">'
        '尚未提交任何选择。</div>\n'
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
    verified: dict[str, VerifiedArtifact] = {}
    if project_root is not None:
        required_ids = None if (not test_output or document["surface"]["kind"] == "asset-review") else {
            item["artifact_id"] for item in previews
        }
        verified, physical_errors = verify_physical_artifacts(document, project_root, required_ids)
        if physical_errors:
            raise VisualizationError("; ".join(physical_errors))
    elif previews:
        raise VisualizationError("preview render requires --project-root")
    output.parent.mkdir(parents=True, exist_ok=True)
    fragment = render_fragment(document, verified, project_root)
    if len(fragment.encode("utf-8")) >= 2_000_000:
        raise VisualizationError("rendered fragment exceeds the 2 MB OpenAI Visualization limit; use a registered preview derivative")
    output.write_text(fragment, encoding="utf-8")


def render_fallback(document: dict[str, Any]) -> str:
    if document["surface"]["kind"] == "asset-review":
        review = document["presentation"]["creative_review"]
        preview_id = document["presentation"]["previews"][0]["artifact_id"]
        artifact = next(item for item in document["source_truth"]["artifacts"] if item["artifact_id"] == preview_id)
        fields = {item["id"]: item["value"] for item in document["presentation"]["fields"]}
        summary = (
            "当前画面是演示占位图；只能讨论构图原则，人物、产品、情绪、包装和裁切必须在真实候选素材上复查。"
            if artifact.get("review_classification") == "illustrative-placeholder"
            else f"当前真实候选素材的使用结论：{fields['availability']}。"
        )
        headers = ["画面任务", "消费者时刻", "产品证明", "品牌记忆", "当前结论"]
        rows = [[
            review["asset_role"]["value"], review["customer_moment"]["value"],
            review["product_proof"]["value"], review["brand_memory"]["value"], fields["availability"],
        ]]
        channel_nodes = "\n".join(
            f'  A --> C{index}["{mermaid_label(item["channel"])} {mermaid_label(item["format"])}: '
            f'{mermaid_label(CHANNEL_REVIEW_STATUSES[item["status"]])}"]'
            for index, item in enumerate(review["channel_plan"], start=1)
        )
        fallback = {
            "summary": summary,
            "table": {"headers": headers, "rows": rows},
            "mermaid": "flowchart LR\n  A[广告创意任务] --> B[画面判断]\n" + channel_nodes,
            "decision_prompt": document["surface"]["question"],
        }
    else:
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
        actions = source_document["interactions"]["actions"]
        action_matches = [item for item in actions if item["id"] == intent.get("action_id")]
        if len(action_matches) != 1:
            errors.append("writeback action_id does not match source spec")
        else:
            action_gate = action_matches[0]["target_gate"]
            if source.get("current_gate") != action_gate or result.get("current_gate") != action_gate:
                errors.append("writeback current gate does not match selected source action")
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
            verified_sources, physical_errors = verify_physical_artifacts(source_document, project_root)
            errors.extend(physical_errors)
            if not physical_errors:
                errors.extend(validate_asset_physical_bindings(source_document, verified_sources, project_root))
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
        "artifact_status": "将保留",
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
            if "sendFollowUpMessage" not in text or "请先确认我看到的是最新内容" not in text:
                failures.append(f"{filename}: missing follow-up/revalidation boundary")
            visible = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.IGNORECASE)
            visible = re.sub(r"<style[\s\S]*?</style>", "", visible, flags=re.IGNORECASE).lower()
            visible = re.sub(r"<[^>]+>", " ", visible)
            failures.extend(frontstage_term_errors([visible], filename))
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
    if frontstage_term_errors(["Investigate the idea, then navigate the options."]):
        failures.append("frontstage term filter matched gate inside an ordinary English word")
    unsafe_second_action = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-asset-review.json"))
    unsafe_second_action["interactions"]["actions"][1].update({
        "label": "Send now", "conversation_intent": "Send now to the client",
    })
    if not any("action 1 requests an external delivery" in item for item in validate_spec(unsafe_second_action)):
        failures.append("second asset-review action bypassed the external-send policy")
    for label, intent in (
        ("立刻交付客户", "请把这张图立刻交付给客户"),
        ("Deliver to customer", "Deliver this visual to the customer immediately"),
    ):
        delivery_action = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-asset-review.json"))
        delivery_action["interactions"]["actions"][1].update({"label": label, "conversation_intent": intent})
        if not any("requests an external delivery" in item for item in validate_spec(delivery_action)):
            failures.append(f"external delivery intent bypassed review-only action capability: {label}")
    generic_action = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-asset-review.json"))
    generic_action["interactions"]["actions"][1]["label"] = "继续"
    if not any("label is too generic" in item for item in validate_spec(generic_action)):
        failures.append("generic asset-review action label was accepted")
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
    with tempfile.TemporaryDirectory(prefix="adco-verified-bytes-") as byte_temp:
        byte_root = Path(byte_temp)
        relative = "preview.svg"
        original = b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>'
        replacement = b'<svg xmlns="http://www.w3.org/2000/svg"><circle r="1"/></svg>'
        (byte_root / relative).write_bytes(original)
        immutable_document = copy.deepcopy(physical)
        immutable_document["source_truth"]["artifacts"][0].update({
            "path": relative,
            "sha256": hashlib.sha256(original).hexdigest(),
        })
        immutable_verified, immutable_errors = verify_physical_artifacts(
            immutable_document, byte_root
        )
        (byte_root / relative).write_bytes(replacement)
        if immutable_errors:
            failures.append(f"immutable byte fixture failed verification: {immutable_errors}")
        else:
            uri = image_data_uri(immutable_verified["physical-fixture"])
            if base64.b64encode(original).decode("ascii") not in uri:
                failures.append("render did not retain the exact bytes that passed SHA verification")
            if base64.b64encode(replacement).decode("ascii") in uri:
                failures.append("render re-read a replaced file after SHA verification")
    real_candidate = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-asset-review.json"))
    real_candidate["source_truth"]["binding_mode"] = "adco-control-plane"
    real_artifact = real_candidate["source_truth"]["artifacts"][0]
    real_artifact.update({
        "review_classification": "real-candidate",
        "source_status": "verified",
        "authorization_status": "confirmed",
        "channel_fit_status": "verified",
        "source_evidence_ref": "source-record#/source_status",
        "authorization_evidence_ref": "authorization-record#/authorization_status",
        "channel_fit_evidence_ref": "channel-record#/channel_fit_status",
    })
    real_brief_path = "fixtures/chat-visualization/hero-real-review-brief.json"
    real_brief = load_json(SKILL_ROOT / real_brief_path)
    brief_artifact = real_candidate["source_truth"]["artifacts"][1]
    brief_artifact.update({
        "path": real_brief_path,
        "sha256": hashlib.sha256((SKILL_ROOT / real_brief_path).read_bytes()).hexdigest(),
    })
    for lens_name, source_key in (
        ("asset_role", "asset_role"), ("reference_boundary", "reference_role"),
        ("customer_moment", "customer_moment"), ("product_proof", "product_proof"),
        ("brand_memory", "brand_memory"),
    ):
        lens = real_candidate["presentation"]["creative_review"][lens_name]
        lens.update({"value": real_brief[source_key], "source_ref": f"hero-review-brief#/{source_key}"})
    real_candidate["presentation"]["creative_review"]["channel_plan"] = [
        {**placement, "source_ref": f"hero-review-brief#/channel_plan/{index}"}
        for index, placement in enumerate(real_brief["channel_plan"])
    ]
    for annotation in real_candidate["presentation"]["previews"][0]["annotations"]:
        annotation["basis"] = "real-file-observation"
    support_files = (
        ("source-record", "fixtures/chat-visualization/hero-source-record.json"),
        ("authorization-record", "fixtures/chat-visualization/hero-authorization-record.json"),
        ("channel-record", "fixtures/chat-visualization/hero-channel-fit-record.json"),
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
    with tempfile.TemporaryDirectory(prefix="adco-real-candidate-") as real_temp:
        project_root = Path(real_temp)
        for artifact in real_candidate["source_truth"]["artifacts"]:
            source = SKILL_ROOT / artifact["path"]
            destination = project_root / artifact["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
        control = project_root / "AD-creative/orchestrator"
        visual_assets = project_root / "AD-creative/visual_assets"
        control.mkdir(parents=True, exist_ok=True)
        visual_assets.mkdir(parents=True, exist_ok=True)
        (control / "project.yml").write_text("project:\n  name: campaign-summer\n", encoding="utf-8")
        (control / "current_truth.md").write_text(
            "## Current Version Truth\ncurrent_version_id: v12\nversion_map_status: current\n", encoding="utf-8"
        )
        (control / "version_map.csv").write_text("version_id,status\nv12,current\n", encoding="utf-8")
        artifact_rows = ["artifact_id,path,version,sha256,lifecycle_state"] + [
            f'{item["artifact_id"]},{item["path"]},{item["version"]},{item["sha256"]},active'
            for item in real_candidate["source_truth"]["artifacts"]
        ]
        (control / "artifact_index.csv").write_text("\n".join(artifact_rows) + "\n", encoding="utf-8")
        (control / "source_events.csv").write_text(
            "source_event_id,received_at,source_owner,source_type,declared_semantics,file_paths,trust_level,affects_artifacts\n"
            "SRC-FIXTURE-001,2026-07-14T00:00:00Z,fixture-human,asset_source,registration,"
            "fixtures/chat-visualization/hero-asset-preview.svg,high,hero-visual\n"
            "CONF-FIXTURE-001,2026-07-14T00:00:00Z,user,user_confirmation,direct_use_authorization,"
            "fixtures/chat-visualization/hero-asset-preview.svg,user_confirmed,hero-visual\n",
            encoding="utf-8",
        )
        (control / "gate_log.csv").write_text(
            "gate_run_id,status,target_sha256,checked_artifacts\n"
            f'GATE-FIXTURE-001,PASS,{real_artifact["sha256"]},hero-visual\n', encoding="utf-8",
        )
        (visual_assets / "asset_authorizations.csv").write_text(
            "authorization_id,asset_id,asset_sha256,approval_scope,status,approved_by,approved_at,evidence_ref,revoked_at\n"
            f'AUTH-FIXTURE-001,hero-visual,{real_artifact["sha256"]},client_visible,approved,user,'
            "2026-07-14T00:00:00Z,user_confirmation:CONF-FIXTURE-001,\n",
            encoding="utf-8",
        )
        real_verified, real_physical_errors = verify_physical_artifacts(real_candidate, project_root)
        real_errors = validate_spec(real_candidate) + real_physical_errors
        if not real_physical_errors:
            real_errors.extend(validate_asset_physical_bindings(real_candidate, real_verified, project_root))
        if real_errors:
            failures.append(f"fully verified real candidate was rejected: {real_errors}")
        incomplete_channel = copy.deepcopy(real_candidate)
        incomplete_channel["presentation"]["creative_review"]["channel_plan"][1]["status"] = "reframe"
        incomplete_channel["presentation"]["creative_review"]["channel_plan"][1]["note"] = "需要重新构图。"
        if not any("availability must match" in item for item in validate_spec(incomplete_channel)):
            failures.append("real candidate with an unresolved channel placement remained usable")
        stale_current = copy.deepcopy(real_candidate)
        (control / "current_truth.md").write_text(
            "## Current Version Truth\ncurrent_version_id: v11\nversion_map_status: current\n", encoding="utf-8"
        )
        if not any(
            "current_truth does not match" in item
            for item in validate_asset_physical_bindings(stale_current, real_verified, project_root)
        ):
            failures.append("real candidate accepted a mismatched ADCO current truth")
        (control / "current_truth.md").write_text(
            "## Current Version Truth\ncurrent_version_id: v12\nversion_map_status: current\n", encoding="utf-8"
        )
        authorization_path = visual_assets / "asset_authorizations.csv"
        valid_authorization_csv = authorization_path.read_text(encoding="utf-8")
        for forged_identity in ("automation", "review-bot", "service-account", "Alex Example"):
            authorization_path.write_text(
                valid_authorization_csv.replace(",user,2026", f",{forged_identity},2026"),
                encoding="utf-8",
            )
            if not any(
                "human/client authorization" in item
                for item in validate_asset_physical_bindings(real_candidate, real_verified, project_root)
            ):
                failures.append(f"free-text authorization identity was accepted: {forged_identity}")
        authorization_path.write_text(valid_authorization_csv, encoding="utf-8")
        authorization_path.write_text(
            valid_authorization_csv.replace("user_confirmation:CONF-FIXTURE-001", "user_confirmation:not-registered"),
            encoding="utf-8",
        )
        if not any(
            "human/client authorization" in item
            for item in validate_asset_physical_bindings(real_candidate, real_verified, project_root)
        ):
            failures.append("unregistered user_confirmation prefix was accepted as authorization")
        authorization_path.write_text(valid_authorization_csv, encoding="utf-8")
        source_events_path = control / "source_events.csv"
        valid_source_events_csv = source_events_path.read_text(encoding="utf-8")
        source_events_path.write_text(
            valid_source_events_csv.replace(",user,user_confirmation,", ",review-bot,user_confirmation,"),
            encoding="utf-8",
        )
        if not any(
            "human/client authorization" in item
            for item in validate_asset_physical_bindings(real_candidate, real_verified, project_root)
        ):
            failures.append("automation-owned confirmation row was accepted as human authority")
        source_events_path.write_text(valid_source_events_csv, encoding="utf-8")
        authorization_path.write_text(
            valid_authorization_csv.replace(
                "user_confirmation:CONF-FIXTURE-001", "fixtures/chat-visualization/hero-authorization-record.json"
            ),
            encoding="utf-8",
        )
        if not any(
            "human/client authorization" in item
            for item in validate_asset_physical_bindings(real_candidate, real_verified, project_root)
        ):
            failures.append("project-local evidence file self-authorized client use")
        authorization_path.write_text(valid_authorization_csv, encoding="utf-8")
        gate_path = control / "gate_log.csv"
        valid_gate_csv = gate_path.read_text(encoding="utf-8")
        gate_path.write_text(valid_gate_csv.replace(real_artifact["sha256"], "0" * 64), encoding="utf-8")
        if not any(
            "current exact-asset Gate run" in item
            for item in validate_asset_physical_bindings(real_candidate, real_verified, project_root)
        ):
            failures.append("channel fit accepted a Gate run for another asset")
        gate_path.write_text(valid_gate_csv, encoding="utf-8")
        irrelevant_evidence = copy.deepcopy(real_candidate)
        irrelevant_evidence["source_truth"]["artifacts"][0]["source_evidence_ref"] = "hero-review-brief#/asset_role"
        if not any("wrong evidence contract" in item for item in validate_asset_physical_bindings(irrelevant_evidence, real_verified, project_root)):
            failures.append("unrelated current artifact was accepted as source evidence")
        missing_evidence_pointer = copy.deepcopy(real_candidate)
        missing_evidence_pointer["source_truth"]["artifacts"][0]["source_evidence_ref"] = "source-record#/missing"
        if not any("source pointer does not exist" in item for item in validate_asset_physical_bindings(missing_evidence_pointer, real_verified, project_root)):
            failures.append("nonexistent source evidence pointer was accepted")
        null_evidence = copy.deepcopy(real_candidate)
        null_evidence["source_truth"]["artifacts"][0]["source_evidence_ref"] = "source-record#/optional_null"
        source_path = project_root / "fixtures/chat-visualization/hero-source-record.json"
        null_record = load_json(source_path)
        null_record["optional_null"] = None
        source_path.write_text(json.dumps(null_record, ensure_ascii=False), encoding="utf-8")
        null_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        source_artifact = next(item for item in null_evidence["source_truth"]["artifacts"] if item["artifact_id"] == "source-record")
        source_artifact["sha256"] = null_hash
        artifact_index_path = control / "artifact_index.csv"
        artifact_index_path.write_text(
            artifact_index_path.read_text(encoding="utf-8").replace(
                next(item for item in real_candidate["source_truth"]["artifacts"] if item["artifact_id"] == "source-record")["sha256"],
                null_hash,
            ),
            encoding="utf-8",
        )
        null_verified, null_physical = verify_physical_artifacts(null_evidence, project_root)
        null_errors = null_physical or validate_asset_physical_bindings(null_evidence, null_verified, project_root)
        if not any("does not confirm the claimed status" in item for item in null_errors):
            failures.append("JSON null evidence bypassed exact status comparison")
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
    placeholder_asset["source_evidence_ref"] = "source-record#/source_status"
    source_support = next(
        item for item in real_candidate["source_truth"]["artifacts"] if item["artifact_id"] == "source-record"
    )
    placeholder_source["source_truth"]["artifacts"].append(copy.deepcopy(source_support))
    for field in placeholder_source["presentation"]["fields"]:
        if field["id"] == "source-status":
            field["value"] = "来源已确认"
    if not any("placeholder statuses must be not-applicable" in item for item in validate_spec(placeholder_source)):
        failures.append("illustrative placeholder claimed a verified formal source")
    false_preserve = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-asset-review.json"))
    false_preserve["presentation"]["previews"][0]["annotations"][0].update({
        "scope": "product", "basis": "composition-reading",
    })
    if not any("placeholder can preserve only a composition principle" in item for item in validate_spec(false_preserve)):
        failures.append("placeholder preserved a product claim from illustrative content")
    missing_creative_review = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-asset-review.json"))
    missing_creative_review["presentation"].pop("creative_review")
    if not any("requires ADCO creative_review context" in item for item in validate_spec(missing_creative_review)):
        failures.append("generic asset status card passed without ADCO creative review context")
    presentation_only_lens = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-asset-review.json"))
    presentation_only_lens["presentation"]["creative_review"]["customer_moment"].update({
        "provenance": "presentation-only", "source_ref": None,
    })
    if not any("customer_moment must be source-bound" in item for item in validate_spec(presentation_only_lens)):
        failures.append("core ADCO creative lens accepted presentation-only provenance")
    stale_creative_source = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-asset-review.json"))
    stale_creative_source["source_truth"]["artifacts"][1]["lifecycle"] = "stale"
    if not any("requires a current-version source binding" in item for item in validate_spec(stale_creative_source)):
        failures.append("ADCO creative review accepted a stale source artifact")
    wrong_version_creative_source = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-asset-review.json"))
    wrong_version_creative_source["source_truth"]["artifacts"][1]["version"] = "v11"
    if not any("requires a current-version source binding" in item for item in validate_spec(wrong_version_creative_source)):
        failures.append("ADCO creative review accepted a wrong-version source artifact")
    invalid_channel_binding = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-asset-review.json"))
    invalid_channel_binding["presentation"]["creative_review"]["channel_plan"][0]["source_ref"] = "missing-brief#/channel"
    if not any("channel placement 0 requires a current-version source binding" in item for item in validate_spec(invalid_channel_binding)):
        failures.append("ADCO channel plan passed without current project binding")
    creative_base = load_json(FIXTURE_ROOT / "valid-asset-review.json")
    creative_verified, creative_physical_errors = verify_physical_artifacts(creative_base, SKILL_ROOT)
    if creative_physical_errors:
        failures.append(f"ADCO creative fixture physical verification failed: {creative_physical_errors}")
    else:
        nonexistent_pointer = copy.deepcopy(creative_base)
        nonexistent_pointer["presentation"]["creative_review"]["customer_moment"]["source_ref"] = "hero-review-brief#/not/present"
        if not any("source pointer does not exist" in item for item in validate_asset_physical_bindings(nonexistent_pointer, creative_verified)):
            failures.append("ADCO creative review accepted a nonexistent JSON pointer")
        mismatched_value = copy.deepcopy(creative_base)
        mismatched_value["presentation"]["creative_review"]["customer_moment"]["value"] = "fabricated moment"
        if not any("visible value does not match its source" in item for item in validate_asset_physical_bindings(mismatched_value, creative_verified)):
            failures.append("ADCO creative review accepted a fabricated visible value")
        no_anchor = copy.deepcopy(creative_base)
        for annotation in no_anchor["presentation"]["previews"][0]["annotations"]:
            annotation.pop("anchor", None)
        try:
            no_anchor_html = render_fragment(no_anchor, creative_verified, SKILL_ROOT)
        except VisualizationError as exc:
            failures.append(f"valid region-list review without hotspots failed to render: {exc}")
        else:
            if "按画面区域阅读" not in no_anchor_html or 'class="btn adco-hotspot"' in no_anchor_html:
                failures.append("no-anchor review did not provide the accessible region-list mode")
        fragment_html = render_fragment(creative_base, creative_verified, SKILL_ROOT)
        visible_fragment = re.sub(r"<script[\s\S]*?</script>", "", fragment_html, flags=re.IGNORECASE)
        visible_fragment = re.sub(r"<style[\s\S]*?</style>", "", visible_fragment, flags=re.IGNORECASE)
        if creative_base["surface"]["summary"] in visible_fragment or creative_base["surface"]["question"] in visible_fragment:
            failures.append("asset fragment duplicates the response summary or decision question")
        with tempfile.TemporaryDirectory(prefix="adco-large-preview-") as large_temp:
            large_root = Path(large_temp)
            oversized = copy.deepcopy(creative_base)
            large_relative = "fixtures/chat-visualization/oversized-preview.svg"
            large_path = large_root / large_relative
            large_path.parent.mkdir(parents=True, exist_ok=True)
            large_path.write_bytes(
                b'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="9"><rect width="16" height="9"/>'
                + b" " * 1_600_000 + b"</svg>"
            )
            oversized_artifact = oversized["source_truth"]["artifacts"][0]
            oversized_artifact.update({
                "path": large_relative,
                "sha256": hashlib.sha256(large_path.read_bytes()).hexdigest(),
            })
            brief_source = SKILL_ROOT / oversized["source_truth"]["artifacts"][1]["path"]
            brief_destination = large_root / oversized["source_truth"]["artifacts"][1]["path"]
            brief_destination.parent.mkdir(parents=True, exist_ok=True)
            brief_destination.write_bytes(brief_source.read_bytes())
            try:
                write_fragment(
                    oversized, large_root / "oversized-preview.html", test_output=True,
                    force=False, project_root=large_root,
                )
                failures.append("oversized OpenAI Visualization fragment was written")
            except VisualizationError as exc:
                if "exceeds the 2 MB" not in str(exc):
                    failures.append(f"oversized fragment failed for the wrong reason: {exc}")
    unclassified_finding = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-asset-review.json"))
    unclassified_finding["presentation"]["previews"][0]["annotations"][0].pop("kind")
    if not any("annotations must classify" in item for item in validate_spec(unclassified_finding)):
        failures.append("asset review finding passed without preserve/revise/recheck classification")
    boolean_anchor = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-asset-review.json"))
    boolean_anchor["presentation"]["previews"][0]["annotations"][0]["anchor"]["x"] = True
    if not any("anchor must use 0-100" in item for item in validate_spec(boolean_anchor)):
        failures.append("asset review hotspot accepted a boolean coordinate")
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
    if "creativeReview" not in schema.get("$defs", {}):
        failures.append("schema lacks ADCO creative review contract")
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
        for label in ("已记录你的选择", "将保留", "需要重新检查", "下一步"):
            if label not in echo:
                failures.append(f"confirmation echo is missing required user-facing section: {label}")
        hostile_receipt = copy.deepcopy(valid_receipt)
        hostile_receipt["confirmation"]["decision"] = "Gate P4 回执 hash"
        if not any("customer-visible confirmation contains backstage term" in item for item in validate_writeback(hostile_receipt, valid_receipt_path)):
            failures.append("confirmation backstage terminology was not rejected")
        with tempfile.TemporaryDirectory(prefix="adco-writeback-action-") as action_temp:
            action_root = Path(action_temp)
            action_spec = copy.deepcopy(load_json(FIXTURE_ROOT / "valid-option-comparison.json"))
            action_spec["interactions"]["actions"][1]["target_gate"] = "creative-revision-gate"
            action_spec_path = action_root / "source.json"
            action_spec_path.write_text(json.dumps(action_spec, ensure_ascii=False), encoding="utf-8")
            second_action_receipt = copy.deepcopy(valid_receipt)
            second_action_receipt["source_spec"].update({
                "path": "source.json",
                "sha256": canonical_sha256(action_spec),
                "current_gate": "creative-revision-gate",
            })
            second_action_receipt["intent"].update({
                "action_id": "request-revision",
                "selected_option_id": None,
                "human_readable_intent": "用户要求修改创意路线。",
            })
            second_action_receipt["controller_result"]["current_gate"] = "creative-revision-gate"
            receipt_path = action_root / "receipt.json"
            receipt_path.write_text(json.dumps(second_action_receipt, ensure_ascii=False), encoding="utf-8")
            second_action_errors = validate_writeback(second_action_receipt, receipt_path)
            if second_action_errors:
                failures.append(f"second action writeback was rejected: {second_action_errors}")
            wrong_gate_receipt = copy.deepcopy(second_action_receipt)
            wrong_gate_receipt["source_spec"]["current_gate"] = "creative-route-gate"
            if not any(
                "current gate does not match selected source action" in item
                for item in validate_writeback(wrong_gate_receipt, receipt_path)
            ):
                failures.append("second action writeback accepted the first action's Gate")
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
    fallback_parser.add_argument("--project-root")
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
                verified_sources, physical_errors = verify_physical_artifacts(document, Path(args.project_root))
                if physical_errors:
                    raise VisualizationError("; ".join(physical_errors))
                binding_errors = validate_asset_physical_bindings(document, verified_sources, Path(args.project_root))
                if binding_errors:
                    raise VisualizationError("; ".join(binding_errors))
            print("ADCO_CHAT_VISUALIZATION_SPEC: PASS")
            print(f"view_id: {document['view_id']}")
            print(f"physical_sources: {'VERIFIED' if args.project_root else 'NOT_CHECKED'}")
        elif args.command == "render-fallback":
            if document["surface"]["kind"] == "asset-review":
                if not args.project_root:
                    raise VisualizationError("asset-review fallback requires --project-root for current physical bindings")
                fallback_verified, fallback_physical_errors = verify_physical_artifacts(document, Path(args.project_root))
                if fallback_physical_errors:
                    raise VisualizationError("; ".join(fallback_physical_errors))
                fallback_binding_errors = validate_asset_physical_bindings(
                    document, fallback_verified, Path(args.project_root)
                )
                if fallback_binding_errors:
                    raise VisualizationError("; ".join(fallback_binding_errors))
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
