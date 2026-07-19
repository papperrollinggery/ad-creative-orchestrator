#!/usr/bin/env python3
"""Regression checks for neutral ADCO specialist exchange v1."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Callable

from adco_core.specialist_exchange import (
    negotiate_contract_version,
    v2_boundary_errors,
)
from ad_creative_operator import (
    DIRCREATIVE_PROFILE_ID,
    adopt_specialist_receipt,
    create_specialist_handoff,
    ensure_delivery_project,
    file_sha256,
    read_csv_rows,
    reconcile_thread_receipt,
    record_thread_dispatch,
    render_thread_execution_plan,
    specialist_manifest_digest,
    write_csv_rows,
    write_json_object,
)
from specialist_schema_validation import specialist_schema_errors
from validate_project import validate


def descriptor_payload() -> dict[str, object]:
    return {
        "protocol_id": "adco.specialist-exchange",
        "message_type": "descriptor",
        "descriptor_version": "1.0",
        "supported_contract_versions": ["1.0"],
        "provider": {"id": "dircreative", "display_name": "DIRcreative"},
        "profiles": [
            {
                "profile_id": DIRCREATIVE_PROFILE_ID,
                "capabilities": [
                    "film.story_package",
                    "film.treatment",
                    "workflow.needs_user_return",
                    "workflow.bounded_retry",
                ],
                "execution_modes": ["inline", "codex_thread", "external_handoff"],
                "workspace_modes": ["isolated_workspace", "worktree", "read_only"],
                "authority": {
                    "client_interaction": False,
                    "artifact_adoption": False,
                    "client_readiness": False,
                    "final_export": False,
                    "nested_dispatch": False,
                },
            }
        ],
    }


def descriptor_payload_v2() -> dict[str, object]:
    payload = descriptor_payload()
    payload["descriptor_version"] = "2.0"
    payload["supported_contract_versions"] = ["1.0", "2.0"]
    return payload


def media_descriptor_payload() -> dict[str, object]:
    return {
        "protocol_id": "adco.specialist-exchange",
        "message_type": "descriptor",
        "descriptor_version": "1.0",
        "supported_contract_versions": ["1.0"],
        "provider": {"id": "neutral-media", "display_name": "Neutral Media"},
        "profiles": [
            {
                "profile_id": "neutral.media-generation",
                "capabilities": ["film.story_package"],
                "execution_modes": ["inline", "external_handoff"],
                "workspace_modes": ["isolated_workspace", "worktree"],
                "generation_modes": ["prompt_only", "real_media"],
                "authority": {
                    "client_interaction": False,
                    "artifact_adoption": False,
                    "client_readiness": False,
                    "final_export": False,
                    "nested_dispatch": False,
                },
            }
        ],
    }


def add_input_artifact(project: Path) -> tuple[str, Path]:
    artifact_id = "ART-INPUT-001"
    source = project / "AD-creative/proposal_architecture/specialist_input.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("Client-approved facts and internal story brief.", encoding="utf-8")
    work_path = project / "AD-creative/orchestrator/work_items.csv"
    work_fields, work_rows = read_csv_rows(work_path)
    work_rows.append(
        {
            "work_id": "WORK-SPX-001",
            "stage": "specialist_handoff",
            "title": "DIRcreative story package",
            "objective": "Create a bounded internal story package.",
            "owner_agent": "Main Controller",
            "status": "ready",
            "priority": "high",
            "input_refs": artifact_id,
            "output_artifacts": "",
            "linked_requirements": "",
            "linked_source_events": "",
            "linked_references": "",
            "linked_assets": "",
            "linked_slides": "",
            "blocked_by": "",
            "gate_required": "creative-quality-gate",
            "client_visibility": "internal_only",
            "created_at": "2026-07-05T00:00:00Z",
            "updated_at": "2026-07-05T00:00:00Z",
            "supersedes_work_id": "",
        }
    )
    write_csv_rows(work_path, work_fields, work_rows)
    path = project / "AD-creative/orchestrator/artifact_index.csv"
    fields, rows = read_csv_rows(path)
    rows.append(
        {
            "artifact_id": artifact_id,
            "artifact_type": "proposal_structure",
            "path": str(source.relative_to(project)),
            "stage": "proposal_architecture",
            "version": "v001",
            "status": "done",
            "visibility": "internal_only",
            "source_event_ids": "",
            "linked_requirements": "",
            "linked_work_items": "WORK-SPX-001",
            "linked_references": "",
            "linked_assets": "",
            "gate_status": "PASS",
            "supersedes_artifact_id": "",
            "created_at": "2026-07-05T00:00:00Z",
            "updated_at": "2026-07-05T00:00:00Z",
            "sha256": file_sha256(source),
            "size_bytes": str(source.stat().st_size),
            "derived_from_artifact_id": "",
            "derived_from_sha256": "",
        }
    )
    write_csv_rows(path, fields, rows)
    return artifact_id, source


def make_receipt(
    project: Path,
    handoff: dict[str, object],
    *,
    claims_override: dict[str, bool] | None = None,
    outcome: str = "completed",
    open_questions: list[dict[str, str]] | None = None,
    execution_mode: str = "inline",
    thread_id: str | None = None,
    include_output: bool = True,
) -> tuple[Path, Path | None]:
    scope = handoff["scope"]
    assert isinstance(scope, dict)
    output: Path | None = None
    output_artifacts: list[dict[str, object]] = []
    if include_output:
        output_roots = [
            str(item)
            for item in scope["write"]
            if str(item) != str(scope["receipt_path"])
        ]
        assert output_roots, "writable receipt fixture requires an output root"
        output_root = project / output_roots[0]
        output_root.mkdir(parents=True, exist_ok=True)
        output = output_root / "story.md"
        output.write_text(
            "A bounded story package produced by the specialist.", encoding="utf-8"
        )
    source_truth = handoff["source_truth"]
    assert isinstance(source_truth, dict)
    receipt_path = project / str(scope["receipt_path"])
    _, exchange_rows = read_csv_rows(
        project / "AD-creative/orchestrator/specialist_exchange/exchange_index.csv"
    )
    exchange_row = next(
        row for row in exchange_rows if row.get("handoff_id") == handoff["handoff_id"]
    )
    descriptor_ref = handoff.get("descriptor_ref")
    acceptance = handoff.get("acceptance")
    assert isinstance(acceptance, dict)
    extensions = [
        {"id": item["id"], "version": item["version"], "payload": {}}
        for item in acceptance.get("required_receipt_extensions", [])
    ]
    claims = {
        "client_ready": False,
        "ppt_ready": False,
        "final_delivery_ready": False,
        "send_ready": False,
        "project_complete": False,
        "control_plane_updated": False,
    }
    claims.update(claims_override or {})
    if output is not None:
        output_artifacts.append(
            {
                "provider_artifact_id": "DIR-STORY-001",
                "kind": "film.story_package",
                "version": "1",
                "path": str(output.relative_to(project)),
                "sha256": file_sha256(output),
                "visibility": "internal_only",
                "source_input_ids": [source_truth["artifacts"][0]["artifact_id"]],
            }
        )
    receipt = {
        "protocol_id": "adco.specialist-exchange",
        "contract_version": "1.0",
        "message_type": "receipt",
        "receipt_id": "SPR-001",
        "exchange_id": handoff["exchange_id"],
        "handoff_id": handoff["handoff_id"],
        "work_id": handoff["work_id"],
        "provider_id": handoff["provider_id"],
        "profile_id": handoff["profile_id"],
        "descriptor_sha256": descriptor_ref["sha256"] if isinstance(descriptor_ref, dict) else "",
        "handoff_sha256": exchange_row["handoff_sha256"],
        "outcome": outcome,
        "stage_gate": {"type": "story", "status": "pass", "decision_owner": "worker"},
        "consumed_inputs": [
            {
                "artifact_id": item["artifact_id"],
                "version": item["version"],
                "sha256": item["sha256"],
            }
            for item in source_truth["artifacts"]
        ],
        "output_artifacts": output_artifacts,
        "qa": {"status": "pass", "checks": [], "limitations": []},
        "open_questions": open_questions or [],
        "specialist_recommendation": "adopt_for_adco_gate",
        "execution_evidence": {
            "mode": execution_mode,
            "thread_id": thread_id,
            "nested_dispatch_used": False,
            "out_of_scope_writes": [],
        },
        "claims": claims,
        "extensions": extensions,
    }
    write_json_object(receipt_path, receipt)
    return receipt_path, output


def create_inline_exchange(
    project: Path,
    *,
    descriptor_data: dict[str, object] | None = None,
    expected_output_kinds: list[str] | None = None,
) -> tuple[dict[str, object], Path, Path]:
    artifact_id, _ = add_input_artifact(project)
    descriptor = project / "descriptor.json"
    write_json_object(descriptor, descriptor_data or descriptor_payload())
    handoff, handoff_path = create_specialist_handoff(
        project,
        work_id="WORK-SPX-001",
        profile_id=DIRCREATIVE_PROFILE_ID,
        objective="Create a bounded internal film story package.",
        input_artifact_ids=[artifact_id],
        expected_output_kinds=expected_output_kinds or ["film.story_package"],
        required_capabilities=[],
        descriptor_path=descriptor,
        execution_mode="inline",
        workspace_mode="isolated_workspace",
    )
    receipt_path, _ = make_receipt(project, handoff)
    return handoff, handoff_path, receipt_path


def mutate_json(path: Path, mutate: Callable[[dict[str, object]], None]) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    mutate(payload)
    write_json_object(path, payload)


def assert_adoption_error(
    project: Path,
    handoff_path: Path,
    receipt_path: Path,
    expected: str,
    *,
    target: str = "AD-creative/film/rejected.md",
) -> None:
    try:
        adopt_specialist_receipt(
            project,
            handoff_path=handoff_path,
            receipt_path=receipt_path,
            decision="adopt",
            reason="negative protocol fixture",
            output_mappings={"DIR-STORY-001": target},
            dry_run=True,
        )
    except (ValueError, FileExistsError) as exc:
        assert expected in str(exc), str(exc)
    else:
        raise AssertionError(f"specialist adoption should fail with {expected}")


def test_positive_inline_dircreative_exchange() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-spx-positive-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        artifact_id, _ = add_input_artifact(project)
        descriptor = project / "descriptor.json"
        write_json_object(descriptor, descriptor_payload())
        handoff, handoff_path = create_specialist_handoff(
            project,
            work_id="WORK-SPX-001",
            profile_id=DIRCREATIVE_PROFILE_ID,
            objective="Create a story package without changing ADCO control files.",
            input_artifact_ids=[artifact_id],
            expected_output_kinds=["film.story_package"],
            required_capabilities=["film.story_package"],
            descriptor_path=descriptor,
            execution_mode="inline",
            workspace_mode="isolated_workspace",
        )
        assert handoff["descriptor_ref"]
        assert handoff["execution"]["thread_id"] is None
        assert handoff["execution"]["nested_dispatch_allowed"] is False
        receipt_path, _ = make_receipt(project, handoff)
        adoption, adoption_path = adopt_specialist_receipt(
            project,
            handoff_path=handoff_path,
            receipt_path=receipt_path,
            decision="adopt",
            reason="Story package matches the handoff and remains internal.",
            output_mappings={"DIR-STORY-001": "AD-creative/film/adopted_story_v001.md"},
        )
        assert adoption_path and adoption_path.exists()
        assert adoption["decision_owner"] == "adco"
        assert (project / "AD-creative/film/adopted_story_v001.md").exists()
        errors, _ = validate(project)
        assert errors == [], errors


def test_unverified_descriptor_and_authority_escalation_are_blocked() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-spx-negative-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        artifact_id, _ = add_input_artifact(project)
        handoff, handoff_path = create_specialist_handoff(
            project,
            work_id="WORK-SPX-001",
            profile_id=DIRCREATIVE_PROFILE_ID,
            objective="Manual unverified handoff draft.",
            input_artifact_ids=[artifact_id],
            expected_output_kinds=["film.story_package"],
            required_capabilities=["film.story_package"],
            descriptor_path=None,
            execution_mode="inline",
            workspace_mode="isolated_workspace",
        )
        receipt_path, _ = make_receipt(project, handoff)
        try:
            adopt_specialist_receipt(
                project,
                handoff_path=handoff_path,
                receipt_path=receipt_path,
                decision="adopt",
                reason="must fail without descriptor",
                output_mappings={"DIR-STORY-001": "AD-creative/film/unverified.md"},
            )
        except ValueError as exc:
            assert "unverified specialist descriptor" in str(exc)
        else:
            raise AssertionError("unverified descriptor must not be adopted")
        assert not (project / "AD-creative/film/unverified.md").exists()

        receipt_path, _ = make_receipt(
            project,
            handoff,
            claims_override={
                "client_ready": True,
                "ppt_ready": False,
                "final_delivery_ready": False,
            },
        )
        try:
            adopt_specialist_receipt(
                project,
                handoff_path=handoff_path,
                receipt_path=receipt_path,
                decision="reject",
                reason="authority escalation",
                output_mappings={},
            )
        except ValueError as exc:
            assert "authority escalation" in str(exc)
        else:
            raise AssertionError("provider client_ready claim must be rejected")


def test_needs_user_requires_questions_and_cannot_advance() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-spx-needs-user-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        artifact_id, _ = add_input_artifact(project)
        descriptor = project / "descriptor.json"
        write_json_object(descriptor, descriptor_payload())
        handoff, handoff_path = create_specialist_handoff(
            project,
            work_id="WORK-SPX-001",
            profile_id=DIRCREATIVE_PROFILE_ID,
            objective="Return a structured client question if duration is missing.",
            input_artifact_ids=[artifact_id],
            expected_output_kinds=["film.story_package"],
            required_capabilities=["workflow.needs_user_return"],
            descriptor_path=descriptor,
            execution_mode="inline",
            workspace_mode="isolated_workspace",
        )
        receipt_path, _ = make_receipt(project, handoff, outcome="needs_user")
        try:
            adopt_specialist_receipt(
                project,
                handoff_path=handoff_path,
                receipt_path=receipt_path,
                decision="partial_adopt",
                reason="missing question",
                output_mappings={"DIR-STORY-001": "AD-creative/film/needs_user.md"},
                dry_run=True,
            )
        except ValueError as exc:
            assert "lacks open_questions" in str(exc)
        else:
            raise AssertionError("needs_user without questions must fail")

        receipt_path, _ = make_receipt(
            project,
            handoff,
            outcome="needs_user",
            open_questions=[
                {"id": "Q-DUPLICATE", "question": "Confirm film duration."},
                {"id": "Q-DUPLICATE", "question": "Confirm product format."},
            ],
        )
        try:
            adopt_specialist_receipt(
                project,
                handoff_path=handoff_path,
                receipt_path=receipt_path,
                decision="defer",
                reason="Duplicate question IDs cannot be routed safely.",
                output_mappings={},
                dry_run=True,
            )
        except ValueError as exc:
            assert "duplicate question id" in str(exc), str(exc)
        else:
            raise AssertionError("needs_user duplicate question IDs must fail")

        receipt_path, _ = make_receipt(
            project,
            handoff,
            outcome="needs_user",
            open_questions=[{"id": "Q-1", "question": "Confirm film duration."}],
        )
        adoption, path = adopt_specialist_receipt(
            project,
            handoff_path=handoff_path,
            receipt_path=receipt_path,
            decision="partial_adopt",
            reason="Keep internal draft while waiting for duration.",
            output_mappings={"DIR-STORY-001": "AD-creative/film/needs_user.md"},
            dry_run=True,
        )
        assert path is None
        assert adoption["gate_effect"]["advance_allowed"] is False


def test_specialist_identifiers_and_adoption_paths_cannot_escape() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-spx-paths-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        artifact_id, _ = add_input_artifact(project)
        descriptor_data = descriptor_payload()
        provider = descriptor_data["provider"]
        assert isinstance(provider, dict)
        provider["id"] = "../../../../outside-provider"
        descriptor = project / "descriptor.json"
        write_json_object(descriptor, descriptor_data)
        try:
            create_specialist_handoff(
                project,
                work_id="WORK-SPX-001",
                profile_id=DIRCREATIVE_PROFILE_ID,
                objective="Reject unsafe provider id.",
                input_artifact_ids=[artifact_id],
                expected_output_kinds=["film.story_package"],
                required_capabilities=[],
                descriptor_path=descriptor,
                execution_mode="inline",
                workspace_mode="isolated_workspace",
            )
        except ValueError as exc:
            assert "safe protocol token" in str(exc)
        else:
            raise AssertionError("unsafe provider id must be rejected")

        try:
            create_specialist_handoff(
                project,
                work_id="../../outside-work",
                profile_id=DIRCREATIVE_PROFILE_ID,
                objective="Reject unsafe work id.",
                input_artifact_ids=[artifact_id],
                expected_output_kinds=["film.story_package"],
                required_capabilities=[],
                descriptor_path=None,
                execution_mode="inline",
                workspace_mode="isolated_workspace",
            )
        except ValueError as exc:
            assert "safe protocol token" in str(exc)
        else:
            raise AssertionError("unsafe work id must be rejected")

    for target in [
        "./AD-creative/orchestrator/injected.md",
        "AD-creative/film/../orchestrator/injected.md",
        "./05_最终交付_FinalDelivery/injected.md",
    ]:
        with tempfile.TemporaryDirectory(prefix="adco-spx-target-") as raw:
            project = Path(raw)
            ensure_delivery_project(project)
            _, handoff_path, receipt_path = create_inline_exchange(project)
            assert_adoption_error(
                project,
                handoff_path,
                receipt_path,
                "forbidden control/final scope",
                target=target,
            )

    with tempfile.TemporaryDirectory(prefix="adco-spx-symlink-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        outside = project.parent
        (project / "AD-creative/escape-link").symlink_to(outside, target_is_directory=True)
        _, handoff_path, receipt_path = create_inline_exchange(project)
        assert_adoption_error(
            project,
            handoff_path,
            receipt_path,
            "escapes project scope",
            target="AD-creative/escape-link/injected.md",
        )


def test_specialist_receipt_identity_authority_and_output_contract_are_bound() -> None:
    cases: list[tuple[str, Callable[[dict[str, object]], None], str]] = [
        (
            "provider",
            lambda payload: payload.__setitem__("provider_id", "other-provider"),
            "provider_id mismatch",
        ),
        (
            "descriptor",
            lambda payload: payload.__setitem__("descriptor_sha256", "0" * 64),
            "descriptor_sha256 mismatch",
        ),
        (
            "handoff",
            lambda payload: payload.__setitem__("handoff_sha256", "0" * 64),
            "handoff_sha256 mismatch",
        ),
        (
            "kind",
            lambda payload: payload["output_artifacts"][0].__setitem__(
                "kind", "film.unrequested"
            ),
            "unexpected specialist output kind",
        ),
        (
            "claim",
            lambda payload: payload["claims"].__setitem__("send_ready", True),
            "authority escalation",
        ),
    ]
    for label, mutator, expected in cases:
        with tempfile.TemporaryDirectory(prefix=f"adco-spx-bind-{label}-") as raw:
            project = Path(raw)
            ensure_delivery_project(project)
            _, handoff_path, receipt_path = create_inline_exchange(project)
            mutate_json(receipt_path, mutator)
            assert_adoption_error(
                project, handoff_path, receipt_path, expected
            )


def test_specialist_outputs_reject_aliases_and_physical_reuse() -> None:
    for alias_kind, expected in [
        ("symlink", "symlink path"),
        ("hardlink", "not hardlinked"),
        ("backslash_symlink", "POSIX path separators"),
    ]:
        with tempfile.TemporaryDirectory(prefix=f"adco-spx-{alias_kind}-") as raw:
            project = Path(raw)
            ensure_delivery_project(project)
            _, handoff_path, receipt_path = create_inline_exchange(project)
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            outputs = receipt["output_artifacts"]
            assert isinstance(outputs, list) and isinstance(outputs[0], dict)
            source = project / str(outputs[0]["path"])
            alias = source.with_name(
                "story\\alias.md"
                if alias_kind == "backslash_symlink"
                else f"story-{alias_kind}.md"
            )
            if alias_kind == "symlink":
                alias.symlink_to(source)
            elif alias_kind == "hardlink":
                os.link(source, alias)
            else:
                alias.symlink_to(source)
            outputs[0]["path"] = str(alias.relative_to(project))
            write_json_object(receipt_path, receipt)
            assert_adoption_error(
                project,
                handoff_path,
                receipt_path,
                expected,
                target=f"AD-creative/film/{alias_kind}.md",
            )

    with tempfile.TemporaryDirectory(prefix="adco-spx-physical-reuse-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        _, handoff_path, receipt_path = create_inline_exchange(
            project,
            expected_output_kinds=["film.story_package", "film.treatment"],
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        outputs = receipt["output_artifacts"]
        assert isinstance(outputs, list) and isinstance(outputs[0], dict)
        second = dict(outputs[0])
        second.update(
            {
                "provider_artifact_id": "DIR-TREATMENT-001",
                "kind": "film.treatment",
                "path": "./" + str(outputs[0]["path"]),
            }
        )
        outputs.append(second)
        write_json_object(receipt_path, receipt)
        try:
            adopt_specialist_receipt(
                project,
                handoff_path=handoff_path,
                receipt_path=receipt_path,
                decision="adopt",
                reason="One physical file cannot satisfy two output identities.",
                output_mappings={
                    "DIR-STORY-001": "AD-creative/film/story.md",
                    "DIR-TREATMENT-001": "AD-creative/film/treatment.md",
                },
                dry_run=True,
            )
        except ValueError as exc:
            assert "duplicate specialist output path" in str(exc), str(exc)
        else:
            raise AssertionError("canonical path/physical output reuse must fail")

    with tempfile.TemporaryDirectory(prefix="adco-spx-duplicate-kind-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        _, handoff_path, receipt_path = create_inline_exchange(
            project,
            expected_output_kinds=["film.story_package", "film.treatment"],
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        outputs = receipt["output_artifacts"]
        assert isinstance(outputs, list) and isinstance(outputs[0], dict)
        first_path = project / str(outputs[0]["path"])
        second_path = first_path.with_name("second-story.md")
        second_path.write_text("A distinct file with a reused kind.", encoding="utf-8")
        second = dict(outputs[0])
        second.update(
            {
                "provider_artifact_id": "DIR-STORY-002",
                "path": str(second_path.relative_to(project)),
                "sha256": file_sha256(second_path),
            }
        )
        outputs.append(second)
        write_json_object(receipt_path, receipt)
        assert_adoption_error(
            project,
            handoff_path,
            receipt_path,
            "duplicate specialist output kind",
        )


def test_generation_authorization_is_structured_and_baseline_bound() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-spx-generation-auth-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        artifact_id, _ = add_input_artifact(project)
        descriptor = project / "descriptor.json"
        write_json_object(descriptor, descriptor_payload())
        try:
            create_specialist_handoff(
                project,
                work_id="WORK-SPX-001",
                profile_id=DIRCREATIVE_PROFILE_ID,
                objective="Generate a real internal media artifact.",
                input_artifact_ids=[artifact_id],
                expected_output_kinds=["film.story_package"],
                required_capabilities=["film.story_package"],
                descriptor_path=descriptor,
                execution_mode="inline",
                workspace_mode="isolated_workspace",
                generation_mode="real_media",
                generation_authorized=True,
                authorization_ref="AD-creative/visual_assets/missing-authorization.json",
            )
        except ValueError as exc:
            assert "authorization evidence file is missing" in str(exc), str(exc)
        else:
            raise AssertionError("missing generation authorization must fail")

        try:
            create_specialist_handoff(
                project,
                work_id="WORK-SPX-001",
                profile_id=DIRCREATIVE_PROFILE_ID,
                objective="Reject an unknown generation mode.",
                input_artifact_ids=[artifact_id],
                expected_output_kinds=["film.story_package"],
                required_capabilities=["film.story_package"],
                descriptor_path=descriptor,
                execution_mode="inline",
                workspace_mode="isolated_workspace",
                generation_mode="automatic_magic",
                generation_authorized=True,
                authorization_ref="AD-creative/visual_assets/missing-authorization.json",
            )
        except ValueError as exc:
            assert "generation_mode" in str(exc), str(exc)
        else:
            raise AssertionError("unknown generation_mode must fail")

        authorization_path = (
            project
            / "AD-creative/visual_assets/generation_authorizations/AUTH-SPX-001.json"
        )
        mismatched_authorization = {
            "protocol_id": "adco.specialist-generation-authorization",
            "version": "1.0",
            "message_type": "generation_authorization",
            "authorization_id": "AUTH-SPX-001",
            "work_id": "WORK-WRONG",
            "profile_id": DIRCREATIVE_PROFILE_ID,
            "generation_mode": "real_media",
            "authorized": True,
            "decision": "authorized",
            "authorized_by": "Main Controller",
            "authorized_at": "2026-07-10T10:00:00+08:00",
            "evidence_ref": "user_confirmation:019f47f9",
            "scope": {
                "input_artifact_ids": [artifact_id],
                "expected_output_kinds": ["film.story_package"],
            },
        }
        write_json_object(authorization_path, mismatched_authorization)
        try:
            create_specialist_handoff(
                project,
                work_id="WORK-SPX-001",
                profile_id=DIRCREATIVE_PROFILE_ID,
                objective="Reject authorization evidence for another work item.",
                input_artifact_ids=[artifact_id],
                expected_output_kinds=["film.story_package"],
                required_capabilities=["film.story_package"],
                descriptor_path=descriptor,
                execution_mode="inline",
                workspace_mode="isolated_workspace",
                generation_mode="real_media",
                generation_authorized=True,
                authorization_ref=str(authorization_path.relative_to(project)),
            )
        except ValueError as exc:
            assert "authorization work_id mismatch" in str(exc), str(exc)
        else:
            raise AssertionError("mismatched generation authorization must fail")

        write_json_object(
            authorization_path,
            {
                "protocol_id": "adco.specialist-generation-authorization",
                "version": "1.0",
                "message_type": "generation_authorization",
                "authorization_id": "AUTH-SPX-001",
                "work_id": "WORK-SPX-001",
                "profile_id": DIRCREATIVE_PROFILE_ID,
                "generation_mode": "real_media",
                "authorized": True,
                "decision": "authorized",
                "authorized_by": "Main Controller",
                "authorized_at": "2026-07-10T10:00:00+08:00",
                "evidence_ref": "user_confirmation:019f47f9",
                "scope": {
                    "input_artifact_ids": [artifact_id],
                    "expected_output_kinds": ["film.story_package"],
                },
            },
        )
        try:
            create_specialist_handoff(
                project,
                work_id="WORK-SPX-001",
                profile_id=DIRCREATIVE_PROFILE_ID,
                objective="DIRcreative v1 must remain prompt-only.",
                input_artifact_ids=[artifact_id],
                expected_output_kinds=["film.story_package"],
                required_capabilities=["film.story_package"],
                descriptor_path=descriptor,
                execution_mode="inline",
                workspace_mode="isolated_workspace",
                generation_mode="real_media",
                generation_authorized=True,
                authorization_ref=str(authorization_path.relative_to(project)),
            )
        except ValueError as exc:
            assert "does not support generation_mode" in str(exc), str(exc)
        else:
            raise AssertionError("DIRcreative v1 real_media handoff must fail")

        media_profile_id = "neutral.media-generation"
        mutate_json(
            authorization_path,
            lambda payload: payload.__setitem__("profile_id", media_profile_id),
        )
        media_descriptor = project / "media-descriptor.json"
        write_json_object(media_descriptor, media_descriptor_payload())
        handoff, handoff_path = create_specialist_handoff(
            project,
            work_id="WORK-SPX-001",
            profile_id=media_profile_id,
            objective="Generate a real internal media artifact with explicit approval.",
            input_artifact_ids=[artifact_id],
            expected_output_kinds=["film.story_package"],
            required_capabilities=["film.story_package"],
            descriptor_path=media_descriptor,
            execution_mode="inline",
            workspace_mode="isolated_workspace",
            generation_mode="real_media",
            generation_authorized=True,
            authorization_ref=str(authorization_path.relative_to(project)),
        )
        authorization = handoff["authorization"]
        assert isinstance(authorization, dict)
        assert authorization["generation_mode"] == "real_media"
        receipt_path, _ = make_receipt(project, handoff)
        mutate_json(
            authorization_path,
            lambda payload: payload.__setitem__("authorized_by", "Changed Controller"),
        )
        assert_adoption_error(
            project,
            handoff_path,
            receipt_path,
            "not bound by the host baseline",
        )
        mutate_json(
            authorization_path,
            lambda payload: payload.__setitem__("authorized_by", "Main Controller"),
        )
        _, adoption_path = adopt_specialist_receipt(
            project,
            handoff_path=handoff_path,
            receipt_path=receipt_path,
            decision="adopt",
            reason="Persist a valid real-media exchange before rebind tamper.",
            output_mappings={
                "DIR-STORY-001": "AD-creative/film/authorized_story_v001.md"
            },
        )
        assert adoption_path is not None
        mutate_json(
            authorization_path,
            lambda payload: payload.__setitem__("authorized_by", "Changed Controller"),
        )
        scope = handoff["scope"]
        assert isinstance(scope, dict)
        baseline_ref = scope["host_baseline"]
        assert isinstance(baseline_ref, dict)
        original_baseline_path = project / str(baseline_ref["path"])
        fake_baseline = json.loads(original_baseline_path.read_text(encoding="utf-8"))
        baseline_files = fake_baseline["files"]
        assert isinstance(baseline_files, dict)
        authorization_rel = str(authorization_path.relative_to(project))
        baseline_files[authorization_rel] = file_sha256(authorization_path)
        fake_baseline["manifest_sha256"] = specialist_manifest_digest(
            {str(key): str(value) for key, value in baseline_files.items()}
        )
        fake_baseline_path = (
            project / "AD-creative/visual_assets/fake-specialist-baseline.json"
        )
        write_json_object(fake_baseline_path, fake_baseline)
        rebound_handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        rebound_scope = rebound_handoff["scope"]
        assert isinstance(rebound_scope, dict)
        rebound_scope["host_baseline"] = {
            "path": str(fake_baseline_path.relative_to(project)),
            "sha256": file_sha256(fake_baseline_path),
            "manifest_sha256": fake_baseline["manifest_sha256"],
        }
        write_json_object(handoff_path, rebound_handoff)
        index_path = (
            project / "AD-creative/orchestrator/specialist_exchange/exchange_index.csv"
        )
        index_fields, index_rows = read_csv_rows(index_path)
        index_rows[0]["handoff_sha256"] = file_sha256(handoff_path)
        write_csv_rows(index_path, index_fields, index_rows)
        errors, _ = validate(project)
        assert any("handoff baseline path mismatch" in error for error in errors), errors
        assert any("receipt handoff hash mismatch" in error for error in errors), errors


def test_read_only_handoff_roundtrips_receipt_only() -> None:
    cases = [
        (
            "needs_user",
            "defer",
            [
                {
                    "id": "Q-READ-ONLY-1",
                    "question": "Which client lock must be resolved first?",
                }
            ],
        ),
        ("blocked", "defer", []),
        ("failed", "reject", []),
    ]
    for outcome, decision, questions in cases:
        with tempfile.TemporaryDirectory(
            prefix=f"adco-spx-read-only-{outcome}-"
        ) as raw:
            project = Path(raw)
            ensure_delivery_project(project)
            artifact_id, _ = add_input_artifact(project)
            descriptor = project / "descriptor.json"
            write_json_object(descriptor, descriptor_payload())
            handoff, handoff_path = create_specialist_handoff(
                project,
                work_id="WORK-SPX-001",
                profile_id=DIRCREATIVE_PROFILE_ID,
                objective="Return a receipt without writable output scope.",
                input_artifact_ids=[artifact_id],
                expected_output_kinds=["film.story_package"],
                required_capabilities=["workflow.needs_user_return"],
                descriptor_path=descriptor,
                execution_mode="inline",
                workspace_mode="read_only",
            )
            scope = handoff["scope"]
            assert isinstance(scope, dict)
            assert scope["write"] == [scope["receipt_path"]]
            receipt_path, output = make_receipt(
                project,
                handoff,
                outcome=outcome,
                open_questions=questions,
                include_output=False,
            )
            assert output is None
            if outcome == "needs_user":
                exchange_lock = (
                    project
                    / "AD-creative/orchestrator/specialist_exchange/.exchange.lock"
                )
                exchange_lock.write_text("provider mutation", encoding="utf-8")
                try:
                    adopt_specialist_receipt(
                        project,
                        handoff_path=handoff_path,
                        receipt_path=receipt_path,
                        decision=decision,
                        reason="Mutated exchange lock must fail.",
                        output_mappings={},
                        dry_run=True,
                    )
                except ValueError as exc:
                    assert "lock file must remain empty" in str(exc), str(exc)
                else:
                    raise AssertionError("mutated exchange lock must fail")
                exchange_lock.write_text("", encoding="utf-8")

                exchange_index = (
                    project
                    / "AD-creative/orchestrator/specialist_exchange/exchange_index.csv"
                )
                index_fields, index_rows = read_csv_rows(exchange_index)
                original_created_at = index_rows[0]["created_at"]
                index_rows[0]["created_at"] = "2026-07-10T00:00:00Z"
                write_csv_rows(exchange_index, index_fields, index_rows)
                try:
                    adopt_specialist_receipt(
                        project,
                        handoff_path=handoff_path,
                        receipt_path=receipt_path,
                        decision=decision,
                        reason="Mutated exchange index must fail.",
                        output_mappings={},
                        dry_run=True,
                    )
                except ValueError as exc:
                    assert "timestamp binding mismatch" in str(exc), str(exc)
                else:
                    raise AssertionError("mutated exchange index must fail")
                index_rows[0]["created_at"] = original_created_at
                write_csv_rows(exchange_index, index_fields, index_rows)

                unexpected_control = (
                    project
                    / "AD-creative/orchestrator/specialist_exchange/provider-unreported-control-write.json"
                )
                write_json_object(unexpected_control, {})
                try:
                    adopt_specialist_receipt(
                        project,
                        handoff_path=handoff_path,
                        receipt_path=receipt_path,
                        decision=decision,
                        reason="Unreported specialist control write must fail.",
                        output_mappings={},
                        dry_run=True,
                    )
                except ValueError as exc:
                    assert "unexpected specialist control-plane file" in str(exc), str(exc)
                else:
                    raise AssertionError("unreported specialist control write must fail")
                unexpected_control.unlink()
                try:
                    adopt_specialist_receipt(
                        project,
                        handoff_path=handoff_path,
                        receipt_path=receipt_path,
                        decision=decision,
                        reason="Reject fabricated mapping in read-only mode.",
                        output_mappings={
                            "DIR-STORY-001": "AD-creative/film/invalid.md"
                        },
                        dry_run=True,
                    )
                except ValueError as exc:
                    assert "reject/defer adoption must not map" in str(exc), str(exc)
                else:
                    raise AssertionError("read-only return must reject output mappings")

            adoption, adoption_path = adopt_specialist_receipt(
                project,
                handoff_path=handoff_path,
                receipt_path=receipt_path,
                decision=decision,
                reason=f"Close receipt-only {outcome} without adopting output.",
                output_mappings={},
            )
            assert adoption_path and adoption_path.exists()
            assert adoption["adopted_outputs"] == []
            assert adoption["gate_effect"]["advance_allowed"] is False
            errors, _ = validate(project)
            assert errors == [], errors
            if outcome == "needs_user":
                exchange_lock = (
                    project
                    / "AD-creative/orchestrator/specialist_exchange/.exchange.lock"
                )
                exchange_lock.write_text("provider mutation", encoding="utf-8")
                errors, _ = validate(project)
                assert any("lock file must remain empty" in error for error in errors), errors
                exchange_lock.write_text("", encoding="utf-8")
                errors, _ = validate(project)
                assert errors == [], errors

                exchange_index = (
                    project
                    / "AD-creative/orchestrator/specialist_exchange/exchange_index.csv"
                )
                index_fields, index_rows = read_csv_rows(exchange_index)
                original_created_at = index_rows[0]["created_at"]
                index_rows[0]["created_at"] = "2026-07-10T00:00:00Z"
                write_csv_rows(exchange_index, index_fields, index_rows)
                errors, _ = validate(project)
                assert any("index timestamp binding mismatch" in error for error in errors), errors
                index_rows[0]["created_at"] = original_created_at
                write_csv_rows(exchange_index, index_fields, index_rows)
                errors, _ = validate(project)
                assert errors == [], errors

                unexpected_control = (
                    project
                    / "AD-creative/orchestrator/specialist_exchange/provider-unreported-control-write.json"
                )
                write_json_object(unexpected_control, {})
                errors, _ = validate(project)
                assert any(
                    "unexpected specialist control-plane file" in error
                    for error in errors
                ), errors
                unexpected_control.unlink()
                errors, _ = validate(project)
                assert errors == [], errors
                receipt_bytes = receipt_path.read_bytes()
                control_alias = (
                    project
                    / "AD-creative/orchestrator/specialist_exchange/provider-control-write.json"
                )
                control_alias.write_bytes(receipt_bytes)
                receipt_path.unlink()
                os.link(control_alias, receipt_path)
                errors, _ = validate(project)
                assert any(
                    "receipt must be non-empty and not hardlinked" in error
                    for error in errors
                ), errors
                receipt_path.unlink()
                control_alias.unlink()
                receipt_path.write_bytes(receipt_bytes)
                errors, _ = validate(project)
                assert errors == [], errors
                tampered_adoption = json.loads(
                    adoption_path.read_text(encoding="utf-8")
                )
                tampered_adoption["decision"] = "adopt"
                tampered_adoption["gate_effect"]["advance_allowed"] = True
                write_json_object(adoption_path, tampered_adoption)
                errors, _ = validate(project)
                assert any("adoption hash mismatch" in error for error in errors), errors
                index_path = (
                    project
                    / "AD-creative/orchestrator/specialist_exchange/exchange_index.csv"
                )
                index_fields, index_rows = read_csv_rows(index_path)
                index_rows[0]["adoption_sha256"] = file_sha256(adoption_path)
                write_csv_rows(index_path, index_fields, index_rows)
                errors, _ = validate(project)
                assert any(
                    "adoption decision mismatch" in error for error in errors
                ), errors
                assert any(
                    "adoption gate advance mismatch" in error for error in errors
                ), errors


def test_receipt_path_rejects_symlink_and_hardlink_aliases() -> None:
    for alias_kind, expected in [
        ("symlink", "non-symlink POSIX"),
        ("hardlink", "not hardlinked"),
    ]:
        with tempfile.TemporaryDirectory(
            prefix=f"adco-spx-receipt-{alias_kind}-"
        ) as raw:
            project = Path(raw)
            ensure_delivery_project(project)
            artifact_id, _ = add_input_artifact(project)
            descriptor = project / "descriptor.json"
            write_json_object(descriptor, descriptor_payload())
            handoff, handoff_path = create_specialist_handoff(
                project,
                work_id="WORK-SPX-001",
                profile_id=DIRCREATIVE_PROFILE_ID,
                objective="Return one receipt-only question.",
                input_artifact_ids=[artifact_id],
                expected_output_kinds=["film.story_package"],
                required_capabilities=["workflow.needs_user_return"],
                descriptor_path=descriptor,
                execution_mode="inline",
                workspace_mode="read_only",
            )
            receipt_path, _ = make_receipt(
                project,
                handoff,
                outcome="needs_user",
                open_questions=[
                    {"id": "Q-RECEIPT-1", "question": "Confirm the locked choice."}
                ],
                include_output=False,
            )
            receipt_bytes = receipt_path.read_bytes()
            control_alias = (
                project
                / "AD-creative/orchestrator/specialist_exchange/provider-control-write.json"
            )
            control_alias.write_bytes(receipt_bytes)
            receipt_path.unlink()
            if alias_kind == "symlink":
                receipt_path.symlink_to(control_alias)
            else:
                os.link(control_alias, receipt_path)
            try:
                adopt_specialist_receipt(
                    project,
                    handoff_path=handoff_path,
                    receipt_path=receipt_path,
                    decision="defer",
                    reason="Receipt inode alias must be rejected.",
                    output_mappings={},
                    dry_run=True,
                )
            except ValueError as exc:
                assert expected in str(exc), str(exc)
            else:
                raise AssertionError(f"{alias_kind} receipt alias must fail")


def test_runtime_and_project_validator_enforce_canonical_specialist_schemas() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-spx-schema-runtime-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        _, handoff_path, receipt_path = create_inline_exchange(project)
        valid_handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        valid_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        assert specialist_schema_errors(
            "descriptor", descriptor_payload(), force_builtin=True
        ) == []
        assert specialist_schema_errors(
            "handoff", valid_handoff, force_builtin=True
        ) == []
        assert specialist_schema_errors(
            "receipt", valid_receipt, force_builtin=True
        ) == []

        def break_receipt(payload: dict[str, object]) -> None:
            payload.pop("receipt_id", None)
            payload["specialist_recommendation"] = ""
            outputs = payload.get("output_artifacts")
            assert isinstance(outputs, list) and isinstance(outputs[0], dict)
            outputs[0]["version"] = ""

        mutate_json(receipt_path, break_receipt)
        invalid_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
        assert specialist_schema_errors(
            "receipt", invalid_payload, force_builtin=True
        ), "stdlib fallback must execute the canonical receipt schema"
        assert_adoption_error(
            project,
            handoff_path,
            receipt_path,
            "receipt schema validation failed",
        )

    with tempfile.TemporaryDirectory(prefix="adco-spx-schema-project-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        _, handoff_path, receipt_path = create_inline_exchange(project)
        _, adoption_path = adopt_specialist_receipt(
            project,
            handoff_path=handoff_path,
            receipt_path=receipt_path,
            decision="adopt",
            reason="Create a valid baseline before tamper checks.",
            output_mappings={
                "DIR-STORY-001": "AD-creative/film/schema_baseline_v001.md"
            },
        )
        assert adoption_path is not None
        valid_adoption = json.loads(adoption_path.read_text(encoding="utf-8"))
        assert specialist_schema_errors(
            "adoption", valid_adoption, force_builtin=True
        ) == []
        invalid_time_adoption = {**valid_adoption, "created_at": "2026-07-05 00:00:00"}
        assert any(
            "RFC3339" in issue
            for issue in specialist_schema_errors(
                "adoption", invalid_time_adoption, force_builtin=True
            )
        )
        mutate_json(receipt_path, lambda payload: payload.pop("receipt_id", None))
        mutate_json(adoption_path, lambda payload: payload.pop("decision_owner", None))
        errors, _ = validate(project)
        assert any(
            "receipt schema" in error and "receipt_id" in error for error in errors
        ), errors
        assert any(
            "adoption schema" in error and "decision_owner" in error
            for error in errors
        ), errors

    with tempfile.TemporaryDirectory(prefix="adco-spx-semantic-rebind-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        _, handoff_path, receipt_path = create_inline_exchange(project)
        _, adoption_path = adopt_specialist_receipt(
            project,
            handoff_path=handoff_path,
            receipt_path=receipt_path,
            decision="adopt",
            reason="Create a valid baseline before semantic rebind tamper.",
            output_mappings={
                "DIR-STORY-001": "AD-creative/film/semantic_baseline_v001.md"
            },
        )
        assert adoption_path is not None
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        outputs = receipt["output_artifacts"]
        assert isinstance(outputs, list) and isinstance(outputs[0], dict)
        source = project / str(outputs[0]["path"])
        alias = source.with_name("semantic-rebound-symlink.md")
        alias.symlink_to(source)
        outputs[0]["path"] = str(alias.relative_to(project))
        write_json_object(receipt_path, receipt)
        rebound_sha = file_sha256(receipt_path)
        index_path = (
            project / "AD-creative/orchestrator/specialist_exchange/exchange_index.csv"
        )
        index_fields, index_rows = read_csv_rows(index_path)
        index_rows[0]["receipt_sha256"] = rebound_sha
        write_csv_rows(index_path, index_fields, index_rows)
        adoption = json.loads(adoption_path.read_text(encoding="utf-8"))
        adoption["receipt_sha256"] = rebound_sha
        write_json_object(adoption_path, adoption)
        errors, _ = validate(project)
        assert any(
            "receipt semantics" in error and "symlink path" in error
            for error in errors
        ), errors


def test_descriptor_evolution_and_required_receipt_extension_are_negotiated() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-spx-extension-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        descriptor = descriptor_payload()
        descriptor["descriptor_version"] = "1.1"
        profiles = descriptor["profiles"]
        assert isinstance(profiles, list) and isinstance(profiles[0], dict)
        profiles[0]["receipt_extension"] = {
            "id": "dircreative.domain-delivery",
            "version": "1.0",
            "required": True,
        }
        handoff, handoff_path, receipt_path = create_inline_exchange(
            project, descriptor_data=descriptor
        )
        acceptance = handoff["acceptance"]
        assert isinstance(acceptance, dict)
        assert acceptance["required_receipt_extensions"] == [
            {"id": "dircreative.domain-delivery", "version": "1.0"}
        ]
        adoption, path = adopt_specialist_receipt(
            project,
            handoff_path=handoff_path,
            receipt_path=receipt_path,
            decision="adopt",
            reason="required DIR extension was negotiated by id/version",
            output_mappings={"DIR-STORY-001": "AD-creative/film/extension.md"},
            dry_run=True,
        )
        assert path is None
        assert adoption["gate_effect"]["advance_allowed"] is True

        mutate_json(receipt_path, lambda payload: payload.__setitem__("extensions", []))
        assert_adoption_error(
            project,
            handoff_path,
            receipt_path,
            "required receipt extension missing",
            target="AD-creative/film/missing-extension.md",
        )


def test_host_scope_manifest_detects_unreported_control_plane_write() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-spx-host-proof-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        _, handoff_path, receipt_path = create_inline_exchange(project)
        truth_path = project / "AD-creative/orchestrator/current_truth.md"
        truth_path.write_text(
            truth_path.read_text(encoding="utf-8") + "\nunreported specialist mutation\n",
            encoding="utf-8",
        )
        assert_adoption_error(
            project,
            handoff_path,
            receipt_path,
            "out_of_scope_changes",
        )


def test_codex_thread_specialist_exchange_requires_host_reconciliation() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-spx-codex-thread-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        artifact_id, _ = add_input_artifact(project)
        render_thread_execution_plan(
            project,
            goal_id="GOAL-SPX-CODEX-THREAD",
            work_id="WORK-SPX-001",
            title="DIRcreative bounded specialist lane",
            objective="Bind DIRcreative output to one real Thread and host proof.",
            roles=["film_director"],
        )
        _, registry = read_csv_rows(
            project / "AD-creative/orchestrator/thread_registry.csv"
        )
        lane = next(row for row in registry if row["work_id"] == "WORK-SPX-001")
        lane_id = lane["lane_id"]
        thread_id = "019f7777-8888-7999-8aaa-bbbbbbbbbbbb"
        record_thread_dispatch(
            project,
            lane_id=lane_id,
            work_id="WORK-SPX-001",
            real_thread_id=thread_id,
            title_action="dispatcher_set",
            title_verified_at="2026-07-05T00:00:00Z",
            dispatch_evidence="read_thread title and id matched DIR specialist fixture",
            dispatch_status="dispatched",
            absolute_deadline_at="2026-07-05T00:10:00Z",
        )
        descriptor = project / "descriptor.json"
        write_json_object(descriptor, descriptor_payload())
        handoff, handoff_path = create_specialist_handoff(
            project,
            work_id="WORK-SPX-001",
            profile_id=DIRCREATIVE_PROFILE_ID,
            objective="Create an internal film story package.",
            input_artifact_ids=[artifact_id],
            expected_output_kinds=["film.story_package"],
            required_capabilities=["film.story_package"],
            descriptor_path=descriptor,
            execution_mode="codex_thread",
            workspace_mode="isolated_workspace",
            lane_id=lane_id,
        )
        receipt_path, _ = make_receipt(
            project,
            handoff,
            execution_mode="codex_thread",
            thread_id=thread_id,
        )

        assert_adoption_error(
            project,
            handoff_path,
            receipt_path,
            "codex_thread receipt is not host-received",
            target="AD-creative/film/unreconciled.md",
        )
        reconciliation = reconcile_thread_receipt(
            project,
            lane_id=lane_id,
            work_id="WORK-SPX-001",
            receipt_path_value=str(receipt_path.relative_to(project)),
            adoption_decision="ADOPT",
            rejection_reason="",
            reconciled_at="2026-07-05T00:05:00Z",
            cleanup_action="archived_after_receipt_reconcile",
            archived_at="2026-07-05T00:05:10Z",
        )
        assert reconciliation["status"] == "reconciled", reconciliation
        adoption, adoption_path = adopt_specialist_receipt(
            project,
            handoff_path=handoff_path,
            receipt_path=receipt_path,
            decision="adopt",
            reason="Host identity, scope, validation, and cleanup proof are complete.",
            output_mappings={
                "DIR-STORY-001": "AD-creative/film/adopted_thread_story_v001.md"
            },
        )
        assert adoption_path and adoption_path.exists()
        assert adoption["thread_reconciliation_ref"]["thread_id"] == thread_id
        errors, _ = validate(project)
        assert errors == [], errors


def test_v2_negotiation_handoff_receipt_and_independent_adoption() -> None:
    with tempfile.TemporaryDirectory(prefix="adco-spx-v2-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        artifact_id, _ = add_input_artifact(project)
        descriptor_data = descriptor_payload_v2()
        assert negotiate_contract_version(descriptor_data) == "2.0"
        descriptor = project / "descriptor-v2.json"
        write_json_object(descriptor, descriptor_data)
        handoff, handoff_path = create_specialist_handoff(
            project,
            work_id="WORK-SPX-001",
            profile_id=DIRCREATIVE_PROFILE_ID,
            objective="Create a bounded internal v2 story package.",
            input_artifact_ids=[artifact_id],
            expected_output_kinds=["film.story_package"],
            required_capabilities=[],
            descriptor_path=descriptor,
            execution_mode="inline",
            workspace_mode="isolated_workspace",
        )
        assert set(handoff) == {
            "protocol_id",
            "contract_version",
            "task",
            "brief_snapshot",
            "locked_decisions",
            "requested_outputs",
            "quality_targets",
            "execution_mode",
        }
        assert handoff["contract_version"] == "2.0"
        assert handoff["execution_mode"] == "inline"
        assert not specialist_schema_errors("handoff", handoff, force_builtin=True)
        request = handoff["requested_outputs"][0]
        assert isinstance(request, dict)
        output = project / str(request["path_root"]) / "story.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("Evidence-bound v2 story package.", encoding="utf-8")
        _, exchange_rows = read_csv_rows(
            project / "AD-creative/orchestrator/specialist_exchange/exchange_index.csv"
        )
        row = exchange_rows[0]
        assert row["contract_version"] == "2.0"
        assert row["execution_mode"] == "inline"
        assert not row["thread_id"]
        receipt_path = project / row["receipt_path"]
        receipt = {
            "protocol_id": "adco.specialist-exchange",
            "contract_version": "2.0",
            "status": "completed",
            "outputs": [
                {
                    "output_id": request["output_id"],
                    "type": request["type"],
                    "path": output.relative_to(project).as_posix(),
                    "sha256": file_sha256(output),
                }
            ],
            "domain_qa": {
                "status": "pass",
                "checks": ["provider-domain-continuity"],
                "limitations": [],
            },
            "open_questions": [],
        }
        write_json_object(receipt_path, receipt)
        adoption, adoption_path = adopt_specialist_receipt(
            project,
            handoff_path=handoff_path,
            receipt_path=receipt_path,
            decision="adopt",
            reason="v2 domain QA passed and output bindings match.",
            output_mappings={
                str(request["output_id"]): "AD-creative/film/adopted_v2_story.md"
            },
        )
        assert adoption_path and adoption_path.is_file()
        assert adoption["protocol_id"] == "adco.specialist-adoption"
        assert adoption["decision_owner"] == "adco"
        assert adoption["adco_validation"] == [
            "path",
            "hash",
            "type",
            "domain_qa",
            "scope",
        ]
        errors, _ = validate(project)
        assert not errors, errors


def test_v2_falls_back_to_v1_and_rejects_nested_dispatch() -> None:
    assert negotiate_contract_version(descriptor_payload()) == "1.0"
    with tempfile.TemporaryDirectory(prefix="adco-spx-v2-nested-") as raw:
        project = Path(raw)
        ensure_delivery_project(project)
        artifact_id, _ = add_input_artifact(project)
        descriptor = project / "descriptor-v2.json"
        write_json_object(descriptor, descriptor_payload_v2())
        try:
            create_specialist_handoff(
                project,
                work_id="WORK-SPX-001",
                profile_id=DIRCREATIVE_PROFILE_ID,
                objective="This must remain inline.",
                input_artifact_ids=[artifact_id],
                expected_output_kinds=["film.story_package"],
                required_capabilities=[],
                descriptor_path=descriptor,
                execution_mode="external_handoff",
                workspace_mode="isolated_workspace",
            )
        except ValueError as exc:
            assert "inline" in str(exc)
        else:
            raise AssertionError("v2 nested/delegated execution must fail")


def test_v2_receipt_rejects_outer_readiness_claims() -> None:
    receipt = {
        "protocol_id": "adco.specialist-exchange",
        "contract_version": "2.0",
        "status": "completed",
        "outputs": [
            {
                "output_id": "OUT-01",
                "type": "film.story_package",
                "path": "AD-creative/workspaces/output.md",
                "sha256": "0" * 64,
            }
        ],
        "domain_qa": {"status": "pass", "checks": [], "limitations": []},
        "open_questions": [],
        "project_complete": False,
    }
    schema_errors = specialist_schema_errors("receipt", receipt, force_builtin=True)
    assert any("additional property" in item for item in schema_errors), schema_errors
    boundary_errors = v2_boundary_errors(receipt, message_type="receipt")
    assert any("outer readiness" in item for item in boundary_errors), boundary_errors


def main() -> int:
    test_positive_inline_dircreative_exchange()
    test_unverified_descriptor_and_authority_escalation_are_blocked()
    test_needs_user_requires_questions_and_cannot_advance()
    test_specialist_identifiers_and_adoption_paths_cannot_escape()
    test_specialist_receipt_identity_authority_and_output_contract_are_bound()
    test_specialist_outputs_reject_aliases_and_physical_reuse()
    test_generation_authorization_is_structured_and_baseline_bound()
    test_read_only_handoff_roundtrips_receipt_only()
    test_receipt_path_rejects_symlink_and_hardlink_aliases()
    test_runtime_and_project_validator_enforce_canonical_specialist_schemas()
    test_descriptor_evolution_and_required_receipt_extension_are_negotiated()
    test_host_scope_manifest_detects_unreported_control_plane_write()
    test_codex_thread_specialist_exchange_requires_host_reconciliation()
    test_v2_negotiation_handoff_receipt_and_independent_adoption()
    test_v2_falls_back_to_v1_and_rejects_nested_dispatch()
    test_v2_receipt_rejects_outer_readiness_claims()
    print("TEST_SPECIALIST_EXCHANGE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
