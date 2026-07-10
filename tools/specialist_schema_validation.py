#!/usr/bin/env python3
"""Validate specialist exchange payloads against the packaged canonical schemas."""

from __future__ import annotations

import json
import hashlib
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime_paths import packaged_assets_root, source_root


SCHEMA_NAMES = {"descriptor", "handoff", "receipt", "adoption"}
GENERATION_AUTHORIZATION_PROTOCOL = "adco.specialist-generation-authorization"
GENERATION_AUTHORIZATION_VERSION = "1.0"
SPECIALIST_CONTROL_ROOT = Path("AD-creative/orchestrator/specialist_exchange")


def specialist_schema_path(name: str) -> Path:
    if name not in SCHEMA_NAMES:
        raise ValueError(f"unknown specialist schema: {name}")
    root = source_root()
    asset_root = root / "tools/adco_resources" if root else packaged_assets_root()
    return asset_root / "contracts/specialist_exchange/v1" / f"{name}.schema.json"


def load_specialist_schema(name: str) -> dict[str, object]:
    path = specialist_schema_path(name)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load canonical specialist schema {name}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"canonical specialist schema is not an object: {name}")
    return payload


def _path_has_symlink_component(project: Path, raw_path: str) -> bool:
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


def specialist_generation_authorization_errors(
    project: Path,
    *,
    authorization: object,
    work_id: str,
    profile_id: str,
    input_artifact_ids: list[str],
    expected_output_kinds: list[str],
) -> list[str]:
    if not isinstance(authorization, dict):
        return ["authorization must be an object"]
    generation_mode = str(authorization.get("generation_mode", ""))
    authorized = authorization.get("authorized")
    raw_ref = authorization.get("authorization_ref")
    if generation_mode not in {"prompt_only", "real_media"}:
        return [
            "generation_mode must be one of prompt_only or real_media"
        ]
    if generation_mode == "prompt_only":
        if authorized is not False or raw_ref not in {None, ""}:
            return [
                "prompt_only handoff must keep authorized=false and authorization_ref=null"
            ]
        return []
    errors: list[str] = []
    if authorized is not True:
        errors.append("real media generation requires authorized=true")
    if not isinstance(raw_ref, str) or not raw_ref.strip():
        errors.append("real media generation requires authorization_ref")
        return errors
    if "\\" in raw_ref:
        errors.append("generation authorization_ref must use POSIX path separators")
        return errors
    candidate = Path(raw_ref)
    if candidate.is_absolute() or ".." in Path(raw_ref.replace("\\", "/")).parts:
        errors.append("generation authorization_ref must be project-relative")
        return errors
    if _path_has_symlink_component(project, raw_ref):
        errors.append("generation authorization_ref must not use a symlink")
        return errors
    root = project.resolve()
    evidence_path = (root / candidate).resolve()
    try:
        evidence_path.relative_to(root)
    except ValueError:
        errors.append("generation authorization_ref escapes project scope")
        return errors
    if not evidence_path.is_file():
        errors.append("generation authorization evidence file is missing")
        return errors
    stat = evidence_path.stat()
    if stat.st_size == 0 or stat.st_nlink != 1:
        errors.append(
            "generation authorization evidence must be non-empty and not hardlinked"
        )
        return errors
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"generation authorization evidence is invalid JSON: {exc}")
        return errors
    if not isinstance(evidence, dict):
        errors.append("generation authorization evidence must be an object")
        return errors
    expected = {
        "protocol_id": GENERATION_AUTHORIZATION_PROTOCOL,
        "version": GENERATION_AUTHORIZATION_VERSION,
        "message_type": "generation_authorization",
        "work_id": work_id,
        "profile_id": profile_id,
        "generation_mode": generation_mode,
        "authorized": True,
        "decision": "authorized",
    }
    for key, value in expected.items():
        if evidence.get(key) != value:
            errors.append(f"generation authorization {key} mismatch")
    authorization_id = str(evidence.get("authorization_id", ""))
    if not re.fullmatch(
        r"^(?!.*\.\.)[A-Za-z0-9][A-Za-z0-9._-]{0,127}$", authorization_id
    ):
        errors.append("generation authorization authorization_id is invalid")
    authorized_by = str(evidence.get("authorized_by", "")).strip()
    if authorized_by.lower() in {
        "",
        "automation",
        "worker",
        "specialist",
        "dircreative",
        "ad_creative_operator",
    }:
        errors.append("generation authorization requires a human/controller authorizer")
    authorized_at = str(evidence.get("authorized_at", ""))
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        authorized_at,
    ):
        errors.append("generation authorization authorized_at must be RFC3339")
    else:
        try:
            parsed = datetime.fromisoformat(authorized_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append("generation authorization authorized_at is invalid")
        else:
            if parsed.tzinfo is None:
                errors.append("generation authorization authorized_at needs timezone")
    evidence_ref = str(evidence.get("evidence_ref", ""))
    if not evidence_ref.startswith(("user_confirmation:", "client_confirmation:")):
        errors.append(
            "generation authorization evidence_ref must bind user/client confirmation"
        )
    scope = evidence.get("scope")
    if not isinstance(scope, dict):
        errors.append("generation authorization scope must be an object")
    else:
        for key, expected_values in [
            ("input_artifact_ids", input_artifact_ids),
            ("expected_output_kinds", expected_output_kinds),
        ]:
            actual = scope.get(key)
            if (
                not isinstance(actual, list)
                or not all(isinstance(item, str) and item for item in actual)
                or len(actual) != len(set(actual))
                or set(actual) != set(expected_values)
            ):
                errors.append(f"generation authorization scope.{key} mismatch")
    return errors


def specialist_control_plane_errors(
    project: Path, rows: list[dict[str, str]]
) -> list[str]:
    root = project.resolve()
    control_root = root / SPECIALIST_CONTROL_ROOT
    allowed = {
        (SPECIALIST_CONTROL_ROOT / "exchange_index.csv").as_posix(),
        (SPECIALIST_CONTROL_ROOT / ".exchange.lock").as_posix(),
    }
    descriptor_shas: set[str] = set()
    errors: list[str] = []
    for row in rows:
        for field in ["handoff_path", "baseline_path", "adoption_path"]:
            raw_path = (row.get(field) or "").strip()
            if not raw_path:
                continue
            if "\\" in raw_path or _path_has_symlink_component(project, raw_path):
                errors.append(f"specialist control {field} uses an unsafe path: {raw_path}")
                continue
            candidate = (root / raw_path).resolve()
            try:
                candidate.relative_to(control_root)
            except ValueError:
                errors.append(f"specialist control {field} is outside control root: {raw_path}")
                continue
            allowed.add(candidate.relative_to(root).as_posix())
        descriptor_sha = (row.get("descriptor_sha256") or "").strip()
        if descriptor_sha:
            descriptor_shas.add(descriptor_sha)
            allowed.add(
                (
                    SPECIALIST_CONTROL_ROOT
                    / "descriptors"
                    / f"descriptor_{descriptor_sha}.json"
                ).as_posix()
            )

    if control_root.exists():
        for path in control_root.rglob("*"):
            if not path.is_file() and not path.is_symlink():
                continue
            rel = path.relative_to(root).as_posix()
            if rel not in allowed:
                errors.append(f"unexpected specialist control-plane file: {rel}")
                continue
            if path.is_symlink():
                errors.append(f"specialist control-plane file must not be symlink: {rel}")
                continue
            if path.stat().st_nlink != 1:
                errors.append(f"specialist control-plane file must not be hardlinked: {rel}")
            if rel == (SPECIALIST_CONTROL_ROOT / ".exchange.lock").as_posix() and path.stat().st_size != 0:
                errors.append("specialist exchange lock file must remain empty")

    for descriptor_sha in descriptor_shas:
        descriptor_path = (
            control_root / "descriptors" / f"descriptor_{descriptor_sha}.json"
        )
        if not descriptor_path.is_file():
            errors.append(
                f"specialist descriptor snapshot missing: descriptor_{descriptor_sha}.json"
            )
            continue
        try:
            descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            errors.append(
                f"specialist descriptor snapshot invalid: descriptor_{descriptor_sha}.json"
            )
            continue
        canonical = json.dumps(
            descriptor, ensure_ascii=False, sort_keys=True
        ).encode("utf-8")
        if hashlib.sha256(canonical).hexdigest() != descriptor_sha:
            errors.append(
                f"specialist descriptor snapshot hash mismatch: descriptor_{descriptor_sha}.json"
            )
    return errors


def _json_type_matches(value: object, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return False


def _resolve_ref(root: dict[str, object], ref: str) -> dict[str, object]:
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported external specialist schema ref: {ref}")
    value: object = root
    for raw_part in ref[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"unresolved specialist schema ref: {ref}")
        value = value[part]
    if not isinstance(value, dict):
        raise ValueError(f"specialist schema ref is not an object: {ref}")
    return value


def _canonical_item(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _path(parent: str, key: object) -> str:
    return f"{parent}[{key}]" if isinstance(key, int) else f"{parent}.{key}"


def _builtin_errors(
    value: object,
    schema: dict[str, object],
    root: dict[str, object],
    path: str,
) -> list[str]:
    errors: list[str] = []
    ref = schema.get("$ref")
    if isinstance(ref, str):
        return _builtin_errors(value, _resolve_ref(root, ref), root, path)

    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        alternatives = [
            _builtin_errors(value, item, root, path)
            for item in any_of
            if isinstance(item, dict)
        ]
        if not alternatives or all(items for items in alternatives):
            detail = min(alternatives, key=len)[0] if alternatives else "no valid branch"
            errors.append(f"{path}: anyOf failed ({detail})")
            return errors

    all_of = schema.get("allOf")
    if isinstance(all_of, list):
        for item in all_of:
            if isinstance(item, dict):
                errors.extend(_builtin_errors(value, item, root, path))

    condition = schema.get("if")
    if isinstance(condition, dict):
        matched = not _builtin_errors(value, condition, root, path)
        branch = schema.get("then" if matched else "else")
        if isinstance(branch, dict):
            errors.extend(_builtin_errors(value, branch, root, path))

    expected_type = schema.get("type")
    if isinstance(expected_type, str):
        expected_types = [expected_type]
    elif isinstance(expected_type, list):
        expected_types = [item for item in expected_type if isinstance(item, str)]
    else:
        expected_types = []
    if expected_types and not any(
        _json_type_matches(value, item) for item in expected_types
    ):
        errors.append(f"{path}: expected type {'|'.join(expected_types)}")
        return errors

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: value does not match const")
    enum = schema.get("enum")
    if isinstance(enum, list) and value not in enum:
        errors.append(f"{path}: value is not in enum")

    if isinstance(value, dict):
        required = schema.get("required")
        if isinstance(required, list):
            for key in required:
                if isinstance(key, str) and key not in value:
                    errors.append(f"{path}: missing required property {key}")
        properties = schema.get("properties")
        property_map = properties if isinstance(properties, dict) else {}
        for key, item_value in value.items():
            item_schema = property_map.get(key)
            if isinstance(item_schema, dict):
                errors.extend(
                    _builtin_errors(item_value, item_schema, root, _path(path, key))
                )
                continue
            additional = schema.get("additionalProperties", True)
            if additional is False:
                errors.append(f"{path}: additional property not allowed: {key}")
            elif isinstance(additional, dict):
                errors.extend(
                    _builtin_errors(item_value, additional, root, _path(path, key))
                )

    if isinstance(value, list):
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{path}: expected at least {min_items} items")
        if isinstance(max_items, int) and len(value) > max_items:
            errors.append(f"{path}: expected at most {max_items} items")
        if schema.get("uniqueItems") is True:
            canonical_items = [_canonical_item(item) for item in value]
            if len(canonical_items) != len(set(canonical_items)):
                errors.append(f"{path}: items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(
                    _builtin_errors(item, item_schema, root, _path(path, index))
                )
        contains = schema.get("contains")
        if isinstance(contains, dict):
            match_count = sum(
                1 for item in value if not _builtin_errors(item, contains, root, path)
            )
            minimum = schema.get("minContains", 1)
            if isinstance(minimum, int) and match_count < minimum:
                errors.append(f"{path}: contains matched {match_count}, expected {minimum}")

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append(f"{path}: string is shorter than {min_length}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            errors.append(f"{path}: string does not match pattern")
        if schema.get("format") == "date-time":
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path}: invalid date-time")
            else:
                if not re.fullmatch(
                    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
                    value,
                ) or parsed.tzinfo is None:
                    errors.append(f"{path}: date-time must be RFC3339 with timezone")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, (int, float)) and value < minimum:
            errors.append(f"{path}: number is below minimum {minimum}")
        if isinstance(maximum, (int, float)) and value > maximum:
            errors.append(f"{path}: number is above maximum {maximum}")
    return errors


def specialist_schema_errors(
    name: str,
    payload: object,
    *,
    force_builtin: bool = False,
) -> list[str]:
    schema = load_specialist_schema(name)
    if not force_builtin and not os.environ.get("ADCO_FORCE_BUILTIN_SCHEMA_VALIDATOR"):
        try:
            from jsonschema import Draft202012Validator, FormatChecker
        except ImportError:
            pass
        else:
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            return [
                f"{'.'.join(str(item) for item in error.absolute_path) or '$'}: {error.message}"
                for error in sorted(
                    validator.iter_errors(payload),
                    key=lambda item: [str(part) for part in item.absolute_path],
                )
            ]
    return _builtin_errors(payload, schema, schema, "$")


def validate_specialist_payload(name: str, payload: object) -> None:
    errors = specialist_schema_errors(name, payload)
    if errors:
        raise ValueError(
            f"{name} schema validation failed: " + "; ".join(errors[:12])
        )
