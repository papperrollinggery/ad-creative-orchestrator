"""Lightweight default `adco run` orchestration with measurable phases."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Callable

from adco_core.ingestion import material_files
from adco_core.incremental_validation import run_incremental_validation


class RunPreflightError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def preflight_material_inputs(
    project: Path,
    materials: list[Path],
    max_total_chars: int,
) -> None:
    """Validate all runtime inputs before ADCO creates or changes project files."""
    if int(max_total_chars) <= 0:
        raise RunPreflightError(
            "invalid_character_budget",
            "max_total_chars must be greater than zero",
        )
    if project.is_symlink():
        raise RunPreflightError(
            "unsafe_project_symlink",
            "project root must not be a symlink",
        )
    for managed in (project / "AD-creative", project / ".adco-local"):
        if managed.is_symlink():
            raise RunPreflightError(
                "unsafe_project_symlink",
                f"managed project path must not be a symlink: {managed.name}",
            )

    project_root = project.resolve()
    for material in materials:
        label = material.name or "<material>"
        if material.is_symlink():
            raise RunPreflightError(
                "unsafe_material_symlink",
                f"material must not be a symlink: {label}",
            )
        if not material.exists():
            raise RunPreflightError(
                "material_not_found",
                f"material not found: {label}",
            )
        if not material.is_file() and not material.is_dir():
            raise RunPreflightError(
                "unsupported_material",
                f"material must be a regular file or directory: {label}",
            )
        material_root = material.resolve()
        try:
            project_relative = material_root.relative_to(project_root)
        except ValueError:
            project_relative = None
        try:
            material_contains_project = project_root.relative_to(material_root)
        except ValueError:
            material_contains_project = None
        if project_relative == Path() or (
            project_relative is not None
            and project_relative.parts
            and project_relative.parts[0] == "AD-creative"
        ) or material_contains_project is not None:
            raise RunPreflightError(
                "recursive_project_material",
                (
                    "material must not be the project root, a parent containing the "
                    f"project, or the managed AD-creative tree: {label}"
                ),
            )
        try:
            supported = material_files(material)
        except ValueError as exc:
            raise RunPreflightError(
                "unsafe_material_symlink",
                f"material tree contains a symlink: {label}",
            ) from exc
        if not supported:
            raise RunPreflightError(
                "empty_or_unsupported_material",
                f"material contains no supported files: {label}",
            )
        if not any(path.stat().st_size > 0 for path in supported):
            raise RunPreflightError(
                "empty_material",
                f"material contains no non-empty supported files: {label}",
            )


def _elapsed_ms(started: float) -> int:
    return round((perf_counter() - started) * 1000)


def execute_lightweight_run(
    project: Path,
    *,
    materials: list[Path],
    goal: str,
    max_total_chars: int,
    ensure_project: Callable[[Path], tuple[int, int]],
    register_materials: Callable[[Path, list[Path], str], list[str]],
    ensure_intake_work: Callable[[Path, list[str], str], str] | None,
    perform_intake: Callable[..., dict[str, int]],
    render_handoff: Callable[[Path, str, list[str]], dict[str, object]],
    render_dashboard: Callable[..., Path],
    render_optional_dashboard: bool = False,
) -> dict[str, object]:
    preflight_material_inputs(project, materials, max_total_chars)
    total_started = perf_counter()
    write_started = perf_counter()
    created, skipped = ensure_project(project)
    source_ids = register_materials(project, materials, goal) if materials else []
    if ensure_intake_work is not None and (source_ids or goal):
        ensure_intake_work(project, source_ids, goal)
    setup_write_ms = _elapsed_ms(write_started)

    if source_ids:
        intake_stats = perform_intake(
            project,
            source_ids,
            goal,
            max_total_chars=max_total_chars,
        )
    else:
        intake_stats = {
            "requirements": 0,
            "gaps": 0,
            "materials": 0,
            "characters_read": 0,
            "evidence_chunks": 0,
            "over_budget_files": 0,
            "parser_errors": 0,
            "facts": 0,
            "parse_ms": 0,
            "fact_analysis_ms": 0,
            "write_ms": 0,
        }

    handoff_started = perf_counter()
    intake_summary = render_handoff(project, goal, source_ids)
    intake_summary["artifact_role"] = "intake_summary_not_creative_output"
    handoff_write_ms = _elapsed_ms(handoff_started)

    dashboard = None
    dashboard_ms = 0
    if render_optional_dashboard:
        dashboard_started = perf_counter()
        dashboard = render_dashboard(
            project,
            validation_errors=[],
            validation_status="SCOPED_PENDING",
        )
        dashboard_ms = _elapsed_ms(dashboard_started)

    changed_paths: list[str] = [
        "AD-creative/orchestrator/source_events.csv",
        "AD-creative/orchestrator/evidence_chunks.jsonl",
        "AD-creative/orchestrator/fact_inventory.jsonl",
        "AD-creative/orchestrator/requirements.csv",
        "AD-creative/orchestrator/gaps.csv",
    ] if source_ids else []
    validation = run_incremental_validation(
        project,
        changed_artifact_ids=[
            "ART-AUTO-EVIDENCE-CHUNKS",
            "ART-AUTO-FACT-INVENTORY",
            "ART-AUTO-REQUIREMENTS",
            "ART-AUTO-GAPS",
        ] if source_ids else [],
        changed_file_paths=changed_paths,
    )
    timings = {
        "parse_ms": int(intake_stats.get("parse_ms", 0)),
        "fact_analysis_ms": int(intake_stats.get("fact_analysis_ms", 0)),
        "write_ms": (
            setup_write_ms
            + int(intake_stats.get("write_ms", 0))
            + handoff_write_ms
        ),
        "dashboard_ms": dashboard_ms,
        "validation_ms": validation.validation_ms,
        "total_ms": _elapsed_ms(total_started),
    }
    return {
        "project": str(project),
        "created_files": created,
        "skipped_existing_files": skipped,
        "registered_sources": len(source_ids),
        "source_ids": source_ids,
        "intake": intake_stats,
        "intake_summary": intake_summary,
        # Backward-compatible JSON alias. Human-readable CLI output uses the
        # accurate INTAKE_SUMMARY label.
        "content_answer": intake_summary,
        "dashboard": str(dashboard) if dashboard else "",
        "dashboard_render_count": int(dashboard is not None),
        "council_run_count": 0,
        "specialist_handoff_count": 0,
        "ppt_auto_generated": 0,
        "client_pack_run_count": 0,
        "full_validation_run_count": 0,
        "incremental_validation": validation.as_dict(),
        "timings": timings,
        "next_command": f"adco next {project}",
    }
