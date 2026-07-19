"""Version negotiation and scoped validation for Specialist Exchange v2.

The v2 provider contract intentionally excludes ADCO-owned workflow state.  Exchange
identity, descriptor provenance, host scope baselines, and adoption decisions remain
in ADCO's local exchange index and adoption records.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Iterable


PROTOCOL_ID = "adco.specialist-exchange"
CONTROLLER_CONTRACT_VERSIONS = ("2.0", "1.0")
V2_CONTRACT_VERSION = "2.0"
V2_EXECUTION_MODE = "inline"
V2_RECEIPT_STATUSES = {"completed", "needs_user", "blocked", "failed"}
OUTER_READINESS_KEYS = {
    "client_ready",
    "control_plane_updated",
    "final_delivery_ready",
    "ppt_ready",
    "project_complete",
    "send_ready",
}
NESTED_DISPATCH_KEYS = {
    "nested_dispatch",
    "nested_dispatch_allowed",
    "nested_dispatch_used",
}


def _version_key(version: str) -> tuple[int, int]:
    parts = version.split(".")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError(f"invalid specialist contract version: {version}")
    return int(parts[0]), int(parts[1])


def negotiate_contract_version(
    descriptor: dict[str, object],
    *,
    controller_versions: Iterable[str] = CONTROLLER_CONTRACT_VERSIONS,
) -> str:
    """Return the numerically highest contract version supported by both sides."""
    advertised = descriptor.get("supported_contract_versions")
    if not isinstance(advertised, list) or not advertised:
        raise ValueError("descriptor supported_contract_versions missing")
    provider_versions: set[str] = set()
    for raw_version in advertised:
        if not isinstance(raw_version, str):
            raise ValueError("descriptor contract versions must be strings")
        _version_key(raw_version)
        provider_versions.add(raw_version)
    controller = set(controller_versions)
    common = provider_versions & controller
    if not common:
        raise ValueError("descriptor has no contract version supported by ADCO")
    return max(common, key=_version_key)


def _walk_keys(value: object, *, prefix: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}"
            yield path, str(key)
            yield from _walk_keys(item, prefix=path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_keys(item, prefix=f"{prefix}[{index}]")


def v2_boundary_errors(payload: object, *, message_type: str) -> list[str]:
    """Reject v2 authority leakage that cannot be expressed by the JSON schema."""
    if not isinstance(payload, dict):
        return [f"v2 {message_type} must be an object"]
    errors: list[str] = []
    if payload.get("protocol_id") != PROTOCOL_ID:
        errors.append(f"v2 {message_type} protocol_id mismatch")
    if payload.get("contract_version") != V2_CONTRACT_VERSION:
        errors.append(f"v2 {message_type} contract_version mismatch")
    for path, key in _walk_keys(payload):
        if key in NESTED_DISPATCH_KEYS:
            errors.append(f"v2 {message_type} nested dispatch field is forbidden: {path}")
        if message_type == "receipt" and key in OUTER_READINESS_KEYS:
            errors.append(f"v2 receipt outer readiness claim is forbidden: {path}")
    if message_type == "handoff" and payload.get("execution_mode") != V2_EXECUTION_MODE:
        errors.append("v2 handoff execution_mode must be inline")
    return errors


def build_v2_handoff(
    *,
    task: str,
    brief_snapshot: str,
    locked_decisions: list[dict[str, object]],
    requested_outputs: list[dict[str, object]],
    quality_targets: list[str],
    execution_mode: str = V2_EXECUTION_MODE,
) -> dict[str, object]:
    """Build the minimal provider-facing v2 handoff contract."""
    if execution_mode != V2_EXECUTION_MODE:
        raise ValueError("specialist exchange v2 forbids nested or delegated execution")
    handoff: dict[str, object] = {
        "protocol_id": PROTOCOL_ID,
        "contract_version": V2_CONTRACT_VERSION,
        "task": task.strip(),
        "brief_snapshot": brief_snapshot,
        "locked_decisions": locked_decisions,
        "requested_outputs": requested_outputs,
        "quality_targets": list(dict.fromkeys(quality_targets)),
        "execution_mode": V2_EXECUTION_MODE,
    }
    errors = v2_boundary_errors(handoff, message_type="handoff")
    if errors:
        raise ValueError("; ".join(errors))
    return handoff


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_digest(files: dict[str, str]) -> str:
    canonical = json.dumps(files, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _has_symlink_component(project: Path, raw_path: str) -> bool:
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


def contained_project_path(project: Path, raw_path: str, label: str) -> Path:
    if not raw_path or "\\" in raw_path:
        raise ValueError(f"{label} must be a non-empty POSIX project-relative path")
    candidate = Path(raw_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{label} must be project-relative")
    if _has_symlink_component(project, raw_path):
        raise ValueError(f"{label} must not use a symlink path")
    root = project.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes project scope") from exc
    return resolved


def _requested_output_map(handoff: dict[str, object]) -> dict[str, dict[str, object]]:
    requested = handoff.get("requested_outputs")
    if not isinstance(requested, list):
        return {}
    result: dict[str, dict[str, object]] = {}
    for item in requested:
        if not isinstance(item, dict):
            continue
        output_id = str(item.get("output_id", ""))
        if output_id:
            result[output_id] = item
    return result


def validate_v2_receipt_outputs(
    project: Path,
    handoff: dict[str, object],
    receipt: dict[str, object],
) -> tuple[dict[str, tuple[dict[str, object], Path]], list[str]]:
    """Validate only v2 output path/hash/type, domain QA, and requested scope."""
    errors = v2_boundary_errors(receipt, message_type="receipt")
    status = str(receipt.get("status", ""))
    if status not in V2_RECEIPT_STATUSES:
        errors.append("v2 receipt status is invalid")
    domain_qa = receipt.get("domain_qa")
    if not isinstance(domain_qa, dict):
        errors.append("v2 receipt domain_qa is missing")
    requested = _requested_output_map(handoff)
    outputs = receipt.get("outputs")
    if not isinstance(outputs, list):
        return {}, [*errors, "v2 receipt outputs is missing"]
    if status == "completed" and not outputs:
        errors.append("completed v2 receipt has no outputs")

    output_by_id: dict[str, tuple[dict[str, object], Path]] = {}
    seen_paths: set[str] = set()
    seen_inodes: set[tuple[int, int]] = set()
    for item in outputs:
        if not isinstance(item, dict):
            errors.append("v2 receipt contains an invalid output entry")
            continue
        output_id = str(item.get("output_id", ""))
        if not output_id or output_id in output_by_id:
            errors.append(f"v2 receipt output_id is missing or duplicated: {output_id}")
            continue
        request = requested.get(output_id)
        if request is None:
            errors.append(f"v2 receipt returned an unrequested output: {output_id}")
            continue
        output_type = str(item.get("type", ""))
        if output_type != str(request.get("type", "")):
            errors.append(f"v2 receipt output type mismatch: {output_id}")
        raw_path = str(item.get("path", ""))
        try:
            output_path = contained_project_path(project, raw_path, f"v2 output {output_id}")
            output_root = contained_project_path(
                project,
                str(request.get("path_root", "")),
                f"v2 output root {output_id}",
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if output_path != output_root and output_root not in output_path.parents:
            errors.append(f"v2 receipt output is outside requested scope: {output_id}")
            continue
        if raw_path in seen_paths:
            errors.append(f"v2 receipt output path is duplicated: {raw_path}")
            continue
        seen_paths.add(raw_path)
        if not output_path.is_file():
            errors.append(f"v2 receipt output is missing: {output_id}")
            continue
        stat = output_path.stat()
        physical_id = (stat.st_dev, stat.st_ino)
        if stat.st_size == 0 or stat.st_nlink != 1:
            errors.append(f"v2 receipt output must be non-empty and not hardlinked: {output_id}")
        if physical_id in seen_inodes:
            errors.append(f"v2 receipt output physical file is reused: {output_id}")
        seen_inodes.add(physical_id)
        if file_sha256(output_path) != str(item.get("sha256", "")):
            errors.append(f"v2 receipt output hash mismatch: {output_id}")
        output_by_id[output_id] = (item, output_path)

    if status == "completed" and set(output_by_id) != set(requested):
        missing = sorted(set(requested) - set(output_by_id))
        if missing:
            errors.append("completed v2 receipt is missing requested outputs: " + ",".join(missing))
    return output_by_id, errors


def _load_json_object(path: Path, label: str) -> tuple[dict[str, object] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"{label} is invalid JSON: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"{label} must be an object"]
    return payload, []


def _baseline_errors(project: Path, row: dict[str, str]) -> list[str]:
    errors: list[str] = []
    try:
        path = contained_project_path(
            project, row.get("baseline_path", ""), "v2 host scope baseline"
        )
    except ValueError as exc:
        return [str(exc)]
    if not path.is_file() or file_sha256(path) != row.get("baseline_sha256", ""):
        return ["v2 host scope baseline is missing or stale"]
    baseline, load_errors = _load_json_object(path, "v2 host scope baseline")
    errors.extend(load_errors)
    if baseline is None:
        return errors
    if baseline.get("handoff_id") != row.get("handoff_id"):
        errors.append("v2 host scope baseline handoff_id mismatch")
    if baseline.get("contract_version") != V2_CONTRACT_VERSION:
        errors.append("v2 host scope baseline contract_version mismatch")
    files = baseline.get("files")
    if not isinstance(files, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in files.items()
    ):
        errors.append("v2 host scope baseline file manifest is invalid")
    elif baseline.get("manifest_sha256") != manifest_digest(files):
        errors.append("v2 host scope baseline manifest hash mismatch")
    return errors


def validate_v2_exchange_row(project: Path, row: dict[str, str]) -> list[str]:
    """Full-project validator for one persisted v2 exchange index row."""
    from specialist_schema_validation import specialist_schema_errors

    errors: list[str] = []
    handoff_id = row.get("handoff_id", "")
    if not handoff_id:
        errors.append("v2 exchange row is missing handoff_id")
    for field in ["exchange_id", "work_id", "provider_id", "profile_id"]:
        if not row.get(field):
            errors.append(f"v2 exchange {handoff_id} is missing {field}")
    if row.get("attempt") != "1":
        errors.append(f"v2 exchange {handoff_id} attempt must be 1")
    if row.get("contract_version") != V2_CONTRACT_VERSION:
        errors.append(f"v2 exchange {handoff_id} contract version mismatch")
    if row.get("execution_mode") != V2_EXECUTION_MODE:
        errors.append(f"v2 exchange {handoff_id} execution mode must be inline")
    if row.get("lane_id") or row.get("thread_id"):
        errors.append(f"v2 exchange {handoff_id} must not bind nested dispatch state")
    if row.get("compatibility_status") != "compatible":
        errors.append(f"v2 exchange {handoff_id} descriptor is not compatible")

    try:
        handoff_path = contained_project_path(
            project, row.get("handoff_path", ""), f"v2 exchange {handoff_id} handoff"
        )
    except ValueError as exc:
        return [*errors, str(exc)]
    if not handoff_path.is_file():
        return [*errors, f"v2 exchange {handoff_id} handoff is missing"]
    if file_sha256(handoff_path) != row.get("handoff_sha256"):
        errors.append(f"v2 exchange {handoff_id} handoff hash mismatch")
    handoff, load_errors = _load_json_object(handoff_path, f"v2 exchange {handoff_id} handoff")
    errors.extend(load_errors)
    if handoff is None:
        return errors
    errors.extend(
        f"v2 exchange {handoff_id} handoff schema: {item}"
        for item in specialist_schema_errors("handoff", handoff, schema_version="2.0")
    )
    errors.extend(v2_boundary_errors(handoff, message_type="handoff"))
    errors.extend(_baseline_errors(project, row))

    descriptor_sha = row.get("descriptor_sha256", "")
    if not descriptor_sha:
        errors.append(f"v2 exchange {handoff_id} descriptor hash is missing")
    else:
        descriptor_path = (
            project
            / "AD-creative/orchestrator/specialist_exchange/descriptors"
            / f"descriptor_{descriptor_sha}.json"
        )
        descriptor, descriptor_errors = _load_json_object(
            descriptor_path, f"v2 exchange {handoff_id} descriptor"
        )
        errors.extend(descriptor_errors)
        if descriptor is not None:
            canonical = json.dumps(descriptor, ensure_ascii=False, sort_keys=True).encode("utf-8")
            if hashlib.sha256(canonical).hexdigest() != descriptor_sha:
                errors.append(f"v2 exchange {handoff_id} descriptor hash mismatch")
            errors.extend(
                f"v2 exchange {handoff_id} descriptor schema: {item}"
                for item in specialist_schema_errors(
                    "descriptor", descriptor, schema_version="2.0"
                )
            )
            try:
                negotiated = negotiate_contract_version(descriptor)
            except ValueError as exc:
                errors.append(str(exc))
            else:
                if negotiated != V2_CONTRACT_VERSION:
                    errors.append(f"v2 exchange {handoff_id} was not highest common version")
            provider = descriptor.get("provider")
            if not isinstance(provider, dict) or str(provider.get("id", "")) != row.get(
                "provider_id"
            ):
                errors.append(f"v2 exchange {handoff_id} provider identity mismatch")
            profiles = descriptor.get("profiles")
            profile_ids = {
                str(item.get("profile_id", ""))
                for item in profiles
                if isinstance(item, dict)
            } if isinstance(profiles, list) else set()
            if row.get("profile_id") not in profile_ids:
                errors.append(f"v2 exchange {handoff_id} profile identity mismatch")

    receipt_sha = row.get("receipt_sha256", "")
    receipt: dict[str, object] | None = None
    output_by_id: dict[str, tuple[dict[str, object], Path]] = {}
    if receipt_sha:
        try:
            receipt_path = contained_project_path(
                project, row.get("receipt_path", ""), f"v2 exchange {handoff_id} receipt"
            )
        except ValueError as exc:
            errors.append(str(exc))
        else:
            if not receipt_path.is_file() or file_sha256(receipt_path) != receipt_sha:
                errors.append(f"v2 exchange {handoff_id} receipt is missing or stale")
            else:
                stat = receipt_path.stat()
                if stat.st_size == 0 or stat.st_nlink != 1:
                    errors.append(
                        f"v2 exchange {handoff_id} receipt must be non-empty and not hardlinked"
                    )
                receipt, receipt_errors = _load_json_object(
                    receipt_path, f"v2 exchange {handoff_id} receipt"
                )
                errors.extend(receipt_errors)
                if receipt is not None:
                    errors.extend(
                        f"v2 exchange {handoff_id} receipt schema: {item}"
                        for item in specialist_schema_errors(
                            "receipt", receipt, schema_version="2.0"
                        )
                    )
                    output_by_id, output_errors = validate_v2_receipt_outputs(
                        project, handoff, receipt
                    )
                    errors.extend(output_errors)
                    if receipt.get("status") != row.get("outcome"):
                        errors.append(f"v2 exchange {handoff_id} receipt status mismatch")

    decision = row.get("adoption_decision", "")
    if decision:
        if decision not in {"adopt", "partial_adopt", "reject", "defer"}:
            errors.append(f"v2 exchange {handoff_id} adoption decision is invalid")
        try:
            adoption_path = contained_project_path(
                project,
                row.get("adoption_path", ""),
                f"v2 exchange {handoff_id} adoption",
            )
        except ValueError as exc:
            errors.append(str(exc))
        else:
            if not adoption_path.is_file() or file_sha256(adoption_path) != row.get(
                "adoption_sha256", ""
            ):
                errors.append(f"v2 exchange {handoff_id} adoption is missing or stale")
            else:
                adoption, adoption_errors = _load_json_object(
                    adoption_path, f"v2 exchange {handoff_id} adoption"
                )
                errors.extend(adoption_errors)
                if adoption is not None:
                    expected = {
                        "protocol_id": "adco.specialist-adoption",
                        "version": "1.0",
                        "contract_version": "2.0",
                        "handoff_id": handoff_id,
                        "receipt_sha256": receipt_sha,
                        "decision_owner": "adco",
                        "decision": decision,
                    }
                    for key, value in expected.items():
                        if adoption.get(key) != value:
                            errors.append(f"v2 exchange {handoff_id} adoption {key} mismatch")
                    adopted_outputs = adoption.get("adopted_outputs")
                    if not isinstance(adopted_outputs, list):
                        errors.append(f"v2 exchange {handoff_id} adoption outputs are invalid")
                    else:
                        for item in adopted_outputs:
                            if not isinstance(item, dict):
                                errors.append(f"v2 exchange {handoff_id} adoption output is invalid")
                                continue
                            try:
                                target = contained_project_path(
                                    project,
                                    str(item.get("target_path", "")),
                                    f"v2 exchange {handoff_id} adoption target",
                                )
                            except ValueError as exc:
                                errors.append(str(exc))
                                continue
                            if not target.is_file() or file_sha256(target) != item.get("sha256"):
                                errors.append(
                                    f"v2 exchange {handoff_id} adoption target is missing or stale"
                                )
                            output_id = str(item.get("output_id", ""))
                            source_output = output_by_id.get(output_id)
                            if (
                                source_output is None
                                or item.get("sha256") != source_output[0].get("sha256")
                                or item.get("type") != source_output[0].get("type")
                            ):
                                errors.append(
                                    f"v2 exchange {handoff_id} adoption output binding mismatch: {output_id}"
                                )
                    proof = adoption.get("host_scope_proof")
                    if not isinstance(proof, dict):
                        errors.append(f"v2 exchange {handoff_id} host scope proof is missing")
                    else:
                        if proof.get("baseline_path") != row.get("baseline_path"):
                            errors.append(
                                f"v2 exchange {handoff_id} host scope baseline path mismatch"
                            )
                        if proof.get("baseline_sha256") != row.get("baseline_sha256"):
                            errors.append(
                                f"v2 exchange {handoff_id} host scope baseline hash mismatch"
                            )
                        if proof.get("baseline_manifest_sha256") != proof.get(
                            "observed_manifest_sha256"
                        ) or proof.get("changed_paths") != []:
                            errors.append(
                                f"v2 exchange {handoff_id} host scope proof reports changes"
                            )
                    status = str(receipt.get("status", "")) if receipt else ""
                    if decision == "adopt" and status != "completed":
                        errors.append(
                            f"v2 exchange {handoff_id} full adoption requires completed status"
                        )
                    if decision in {"adopt", "partial_adopt"} and status in {
                        "blocked",
                        "failed",
                    }:
                        errors.append(
                            f"v2 exchange {handoff_id} blocked or failed receipt was adopted"
                        )
    return errors


def current_scope_manifest(project: Path, *, excluded_roots: list[str]) -> dict[str, str]:
    """Build the same host-scope manifest used by the controller baseline."""
    roots = [root.strip().rstrip("/") for root in excluded_roots if root.strip()]
    files: dict[str, str] = {}
    for path in sorted(project.rglob("*")):
        rel = path.relative_to(project).as_posix()
        if rel == ".git" or rel.startswith(".git/"):
            continue
        if any(rel == root or rel.startswith(root + "/") for root in roots):
            continue
        if path.is_symlink():
            files[rel] = "symlink:" + os.readlink(path)
        elif path.is_file():
            files[rel] = file_sha256(path)
    return files
