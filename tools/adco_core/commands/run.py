"""Lightweight default `adco run` orchestration with measurable phases."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Callable

from adco_core.incremental_validation import run_incremental_validation


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
    content_answer = render_handoff(project, goal, source_ids)
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
        "content_answer": content_answer,
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
