#!/usr/bin/env python3
"""Fail-fast structural checks for the packaged specialist exchange schemas."""

from __future__ import annotations

import json
import re
from pathlib import Path

from runtime_paths import source_root


SOURCE_ROOT = source_root()
ROOT = SOURCE_ROOT or Path(__file__).resolve().parent
SCHEMA_ROOT = (
    ROOT / "tools/adco_resources/contracts/specialist_exchange/v1"
    if SOURCE_ROOT
    else ROOT / "adco_resources/contracts/specialist_exchange/v1"
)
SCHEMA_NAMES = ("descriptor", "handoff", "receipt", "adoption")
RESERVED_CLAIMS = {
    "client_ready",
    "ppt_ready",
    "final_delivery_ready",
    "send_ready",
    "project_complete",
    "control_plane_updated",
}


def load_schema(name: str) -> dict[str, object]:
    path = SCHEMA_ROOT / f"{name}.schema.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"schema must be a JSON object: {path}")
    if payload.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise AssertionError(f"schema draft drift: {path}")
    if payload.get("$id") != f"adco.specialist-exchange/{name}/1.0":
        raise AssertionError(f"schema id drift: {path}")
    return payload


def required_set(schema: dict[str, object]) -> set[str]:
    required = schema.get("required")
    if not isinstance(required, list) or not all(
        isinstance(item, str) for item in required
    ):
        raise AssertionError("schema required must be a string array")
    return set(required)


def object_at(schema: dict[str, object], *keys: str) -> dict[str, object]:
    value: object = schema
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            raise AssertionError("schema path missing: " + ".".join(keys))
        value = value[key]
    if not isinstance(value, dict):
        raise AssertionError("schema path is not an object: " + ".".join(keys))
    return value


def object_at_or_none(
    schema: dict[str, object], *keys: str
) -> dict[str, object] | None:
    value: object = schema
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value if isinstance(value, dict) else None


def check_relative_path_safety(schema: dict[str, object], name: str) -> None:
    pattern = object_at(schema, "$defs", "relativePath").get("pattern")
    if not isinstance(pattern, str):
        raise AssertionError(f"{name} relative path pattern is missing")
    if re.fullmatch(pattern, "AD-creative/workspaces/output.md") is None:
        raise AssertionError(f"{name} rejects a valid POSIX relative path")
    if re.fullmatch(pattern, "AD-creative\\workspaces\\output.md") is not None:
        raise AssertionError(f"{name} must reject backslash protocol paths")


def check_descriptor(schema: dict[str, object]) -> None:
    pattern = object_at(schema, "properties", "descriptor_version").get("pattern")
    if (
        not isinstance(pattern, str)
        or not re.fullmatch(pattern, "1.17")
        or re.fullmatch(pattern, "2.0")
    ):
        raise AssertionError("descriptor_version must accept only the 1.x line")
    supported = object_at(schema, "properties", "supported_contract_versions")
    if supported.get("contains") != {"const": "1.0"}:
        raise AssertionError("descriptor must advertise specialist contract 1.0")
    authority = object_at(schema, "$defs", "profile", "properties", "authority")
    expected_authority = {
        "client_interaction",
        "artifact_adoption",
        "client_readiness",
        "final_export",
        "nested_dispatch",
    }
    if required_set(authority) != expected_authority:
        raise AssertionError("descriptor authority keys drifted")
    properties = object_at(authority, "properties")
    if any(properties[key] != {"const": False} for key in expected_authority):
        raise AssertionError("descriptor authority must remain false")
    if authority.get("additionalProperties") != {"const": False}:
        raise AssertionError("new descriptor authority keys must also remain false")
    extension = object_at(schema, "$defs", "profile", "properties", "receipt_extension")
    if required_set(extension) != {"id", "version", "required"}:
        raise AssertionError("descriptor receipt extension negotiation drifted")
    generation_modes = object_at(
        schema, "$defs", "profile", "properties", "generation_modes"
    )
    if generation_modes.get("minItems") != 1 or generation_modes.get(
        "uniqueItems"
    ) is not True:
        raise AssertionError("descriptor generation mode negotiation is incomplete")
    if object_at(generation_modes, "items").get("enum") != [
        "prompt_only",
        "real_media",
    ]:
        raise AssertionError("descriptor generation mode values drifted")


def check_handoff(schema: dict[str, object]) -> None:
    check_relative_path_safety(schema, "handoff")
    required = {
        "provider_id",
        "descriptor_ref",
        "task",
        "source_truth",
        "execution",
        "scope",
        "acceptance",
    }
    if not required.issubset(required_set(schema)):
        raise AssertionError("handoff identity or scope binding is incomplete")
    execution = object_at(schema, "$defs", "execution")
    if not {"lane_id", "lane_run_id", "thread_id", "nested_dispatch_allowed"}.issubset(
        required_set(execution)
    ):
        raise AssertionError("handoff thread binding is incomplete")
    if (
        object_at(execution, "properties", "nested_dispatch_allowed").get("const")
        is not False
    ):
        raise AssertionError("handoff must forbid nested dispatch")
    scope = object_at(schema, "$defs", "scope")
    if "host_baseline" not in required_set(scope):
        raise AssertionError("handoff host baseline is not required")
    write_scope = object_at(scope, "properties", "write")
    if write_scope.get("minItems") != 1:
        raise AssertionError("handoff write scope must support receipt-only read_only mode")
    baseline = object_at(scope, "properties", "host_baseline")
    if required_set(baseline) != {"path", "sha256", "manifest_sha256"}:
        raise AssertionError("handoff host baseline hash binding drifted")
    acceptance = object_at(schema, "properties", "acceptance")
    if "required_receipt_extensions" not in required_set(acceptance):
        raise AssertionError("handoff required receipt extension list is missing")
    rules = schema.get("allOf")
    if not isinstance(rules, list):
        raise AssertionError("handoff conditional safety rules are missing")
    read_only_rule = next(
        (
            rule
            for rule in rules
            if isinstance(rule, dict)
            and (object_at_or_none(
                rule,
                "if",
                "properties",
                "execution",
                "properties",
                "workspace_mode",
            ) or {}).get("const")
            == "read_only"
        ),
        None,
    )
    if read_only_rule is None:
        raise AssertionError("read_only handoff scope conditional is missing")
    read_only_write = object_at(
        read_only_rule, "then", "properties", "scope", "properties", "write"
    )
    writable_write = object_at(
        read_only_rule, "else", "properties", "scope", "properties", "write"
    )
    if read_only_write.get("minItems") != 1 or read_only_write.get("maxItems") != 1:
        raise AssertionError("read_only handoff must grant exactly one write path")
    if writable_write.get("minItems") != 2:
        raise AssertionError("writable handoff must grant output root plus receipt")
    authorization_rule = next(
        (
            rule
            for rule in rules
            if isinstance(rule, dict)
            and (object_at_or_none(
                rule,
                "if",
                "properties",
                "authorization",
                "properties",
                "generation_mode",
            ) or {}).get("const")
            == "prompt_only"
        ),
        None,
    )
    if authorization_rule is None:
        raise AssertionError("generation authorization conditional is missing")
    prompt_only = object_at(
        authorization_rule, "then", "properties", "authorization", "properties"
    )
    real_media = object_at(
        authorization_rule, "else", "properties", "authorization", "properties"
    )
    if prompt_only.get("authorized") != {"const": False} or prompt_only.get(
        "authorization_ref"
    ) != {"type": "null"}:
        raise AssertionError("prompt_only authorization must remain disabled")
    if (
        real_media.get("generation_mode") != {"const": "real_media"}
        or real_media.get("authorized") != {"const": True}
        or real_media.get("authorization_ref") != {"$ref": "#/$defs/relativePath"}
    ):
        raise AssertionError("real_media authorization binding is incomplete")


def check_receipt(schema: dict[str, object]) -> None:
    check_relative_path_safety(schema, "receipt")
    required = required_set(schema)
    if not {
        "descriptor_sha256",
        "handoff_sha256",
        "claims",
        "extensions",
    }.issubset(required):
        raise AssertionError("receipt identity/hash/extension binding is incomplete")
    claims = object_at(schema, "properties", "claims")
    if required_set(claims) != RESERVED_CLAIMS:
        raise AssertionError("receipt reserved claims drifted")
    claim_properties = object_at(claims, "properties")
    if any(claim_properties[key] != {"const": False} for key in RESERVED_CLAIMS):
        raise AssertionError("receipt reserved claims must remain false")
    if claims.get("additionalProperties") is not False:
        raise AssertionError("receipt claim escalation must be schema-invalid")
    open_questions = object_at(schema, "properties", "open_questions")
    if open_questions.get("uniqueItems") is not True:
        raise AssertionError("receipt open question objects must be unique")
    evidence = object_at(schema, "$defs", "executionEvidence")
    if (
        object_at(evidence, "properties", "nested_dispatch_used").get("const")
        is not False
    ):
        raise AssertionError("receipt must prove nested dispatch was not used")
    if object_at(evidence, "properties", "out_of_scope_writes").get("maxItems") != 0:
        raise AssertionError("receipt out-of-scope writes must be empty")
    output = object_at(schema, "$defs", "outputArtifact")
    expected_output = {
        "provider_artifact_id",
        "kind",
        "version",
        "path",
        "sha256",
        "visibility",
        "source_input_ids",
    }
    if required_set(output) != expected_output:
        raise AssertionError("receipt output contract drifted")
    if (
        object_at(output, "properties", "visibility").get("const")
        != "internal_only"
    ):
        raise AssertionError("specialist outputs must remain internal-only")


def check_adoption(schema: dict[str, object]) -> None:
    check_relative_path_safety(schema, "adoption")
    if not {"host_scope_proof", "thread_reconciliation_ref"}.issubset(
        required_set(schema)
    ):
        raise AssertionError("adoption host proof or Thread reconciliation is missing")
    if object_at(schema, "properties", "decision_owner").get("const") != "adco":
        raise AssertionError("ADCO must remain the adoption decision owner")
    proof = object_at(schema, "$defs", "hostScopeProof")
    expected_proof = {
        "baseline_path",
        "baseline_sha256",
        "baseline_manifest_sha256",
        "observed_manifest_sha256",
        "changed_paths",
    }
    if required_set(proof) != expected_proof:
        raise AssertionError("adoption host scope proof drifted")
    if object_at(proof, "properties", "changed_paths").get("maxItems") != 0:
        raise AssertionError("adoption cannot close over host-scope changes")
    thread_ref = object_at(schema, "$defs", "threadReconciliationRef")
    expected_thread_ref = {
        "lane_id",
        "lane_run_id",
        "thread_id",
        "receipt_path",
        "receipt_sha256",
        "dispatch_receipt_path",
        "dispatch_receipt_sha256",
        "registry_sha256",
        "scope_proof_path",
        "scope_proof_sha256",
        "archived_at",
        "cleanup_action",
    }
    if required_set(thread_ref) != expected_thread_ref:
        raise AssertionError("adoption Thread reconciliation proof drifted")


def main() -> int:
    schemas = {name: load_schema(name) for name in SCHEMA_NAMES}
    check_descriptor(schemas["descriptor"])
    check_handoff(schemas["handoff"])
    check_receipt(schemas["receipt"])
    check_adoption(schemas["adoption"])
    print("SPECIALIST_SCHEMA_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
