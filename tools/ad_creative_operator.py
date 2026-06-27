#!/usr/bin/env python3
"""Non-developer operation surface for Ad Creative Orchestrator projects."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import importlib.metadata as metadata
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True

from init_project import agents_policy_status, copy_template
from runtime_paths import repo_or_module_root, skill_draft_dir, source_root, template_root
from validate_project import current_truth_value, validate, validate_client_delivery_readiness


REPO_ROOT = repo_or_module_root()
TEMPLATE_ROOT = template_root()
SKILL_DRAFT_DIR = skill_draft_dir()
PACKAGE_NAME = "ad-creative-orchestrator"
FALLBACK_VERSION = "0.1.0"
DEFAULT_SKILL_INSTALL_DIR = Path.home() / ".codex/skills/ad-creative-orchestrator"
DASHBOARD_REL = Path("AD-creative/handoff/操作台.html")
COUNCIL_REPORT_REL = Path("AD-creative/gates/THREE-COUNCIL-READINESS_report.md")
GOAL_PLAN_TEMPLATE_REL = Path("AD-creative/orchestrator/goal_iteration_plan_template.md")
GOAL_ITERATIONS_REL = Path("AD-creative/orchestrator/goal_iterations")
SUPPORT_BUNDLE_REL = Path("AD-creative/handoff/support_bundle.md")
SAMPLE_MATERIAL_REL = Path("00_项目资料_ProjectMaterials/01_客户资料_ClientMaterials/sample_brief.md")
DEFAULT_DEMO_PROJECT = Path(tempfile.gettempdir()) / "adco-demo"
SAMPLE_GOAL = "用内置样例跑通品牌深度研究与图片功能双泳道，生成可审计的本地操作台。"
SAMPLE_BRIEF = """# Sample Creative Brief

项目：NOVA Trail 户外功能饮料新品广告创意样例

客户希望输出一版广告创意提案，用于内部评审。
品牌深度研究需要先梳理品牌主张、目标人群、竞品参考边界和不可复制项。
图片功能需要规划关键视觉、产品露出、AI 生成图边界、asset slot 和 visual QA。
本轮交付需要包含可编辑 PPT 结构、参考证据链、图片资产清单和客户追问。
客户明确不要使用未经授权 logo、真实品牌包装、不可追溯参考截图或客户可见 AI 图。
产品素材暂缺产品高清图、包装图、字体和官方视觉规范。
参考方向希望偏真实户外、清爽补给、清晨山路、手持产品、轻运动人群。
PPT 需要保留文本可编辑，客户稿发送前必须经过 Gate。
"""
ID_SUFFIX_PATTERN = re.compile(r"(\d+)$")
CLIENT_OWNER_PATTERN = re.compile(r"客户|不要")
CONFIRMATION_HEADER_CELLS = {"ID", "---"}
CLIENT_VISIBLE_VALUES = {"client_visible", "client_visible_ready", "sent"}
PASS_GATE_VALUES = {"pass", "passed"}
CLIENT_REVIEW_ASSET_STATUSES = {"selected", "approved", "done"}
GENERATED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
ACTIVE_ASSET_STATUSES = {"registered", "selected", "approved", "done"}
SELECTED_ASSET_STATUSES = {"selected", "approved", "done"}
CREATIVE_PRODUCTION_KINDS = {"moodboard", "ads", "shots"}
GOAL_PHASES = ("P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7")
GOAL_PHASE_NAMES = {
    "P0": "Intake 与事实基线",
    "P1": "研究计划与图片策略",
    "P2": "证据包与资产槽位",
    "P3": "策略方向与图片任务 PRD",
    "P4": "内部原型与图片探索",
    "P5": "视觉审核与客户审阅包",
    "P6": "PPT / 最终交付 Gate",
    "P7": "反馈合并与复用沉淀",
}
GOAL_PHASE_GATE_HINTS = {
    "P0": ("intake", "brief", "project_readiness"),
    "P1": ("research_plan", "reference_research"),
    "P2": ("reference_research", "visual_plan"),
    "P3": ("creative", "image_job", "proposal_architecture"),
    "P4": ("visual_review", "internal_prototype"),
    "P5": ("client_review", "visual_review"),
    "P6": ("ppt_gate", "final_delivery"),
    "P7": ("feedback", "skill_mining"),
}
VISUAL_RISK_PATTERNS = {
    "contact sheet",
    "low-quality collage",
    "collage",
    "placeholder-only",
    "fake logo",
    "假 logo",
    "假logo",
}
VISUAL_RISK_PATTERN = re.compile(
    "|".join(re.escape(pattern) for pattern in sorted(VISUAL_RISK_PATTERNS, key=len, reverse=True))
)
CREATIVE_PROPOSAL_ARTIFACTS = [
    (
        "ART-AUTO-CREATIVE-DIRECTIONS",
        "creative_directions",
        Path("AD-creative/creative/creative_directions.md"),
    ),
    (
        "ART-AUTO-CREATIVE-OPTION-MATRIX",
        "creative_option_matrix",
        Path("AD-creative/creative/option_matrix.csv"),
    ),
    (
        "ART-AUTO-PROPOSAL-STRUCTURE",
        "proposal_structure",
        Path("AD-creative/proposal_architecture/proposal_structure.md"),
    ),
    (
        "ART-AUTO-SLIDE-SPEC",
        "slide_spec",
        Path("AD-creative/client_review/slide_spec.md"),
    ),
]
CREATIVE_PROPOSAL_REQUIRED_LABELS = [
    "business problem",
    "client real objective",
    "target audience",
    "behavior barrier",
    "consumer insight",
    "feature to benefit",
    "brand/category/competitor notes",
    "strategy path",
    "creative proposition",
    "core message",
    "key visual/action",
    "title/use case",
    "risk",
    "why choose",
    "proposal outline",
]
GENERIC_CREATIVE_PATTERNS = [
    "unlock",
    "elevate",
    "game changer",
    "next level",
    "seamless",
    "innovative",
    "empower",
    "reimagine",
    "breakthrough",
    "bold new",
    "打造全新体验",
    "重新定义",
    "引爆",
    "破圈",
    "赋能",
    "焕新",
    "不止于",
    "美好生活",
    "无限可能",
]
GENERIC_CREATIVE_PATTERN = re.compile(
    "|".join(re.escape(pattern) for pattern in sorted(GENERIC_CREATIVE_PATTERNS, key=len, reverse=True)),
    re.IGNORECASE,
)
CASE_CLAIM_PATTERN = re.compile(
    r"case study|案例|campaign proved|proven by|according to|数据显示|行业报告|竞品证明|参考案例",
    re.IGNORECASE,
)
INTERNAL_LANGUAGE_PATTERN = re.compile(
    r"prompt|thread|worker|lane|subagent|codex|worktree|执行线程|工作线程|提示词|子代理|泳道|lane plan",
    re.IGNORECASE,
)
CHATBOT_RESIDUE_PATTERN = re.compile(
    r"hope this helps|let me know|would you like|want me to|of course[!,]|certainly[!,]|"
    r"\bhere (?:is|are) (?:a|an|the)\b|"
    r"希望这对.{0,8}有帮助|请告诉我|您想要|当然[！!]|一定[！!]",
    re.IGNORECASE,
)
VAGUE_AUTHORITY_PATTERN = re.compile(
    r"industry reports?|experts? (?:argue|believe|say|suggest)|observers? (?:have )?(?:cited|noted|say)|"
    r"some critics argue|studies show|data shows|leading experts?|"
    r"行业报告|专家(?:认为|指出|表示)|观察者(?:指出|认为)|一些批评者|数据显示|多方(?:认为|指出)",
    re.IGNORECASE,
)
EXAGGERATED_SIGNIFICANCE_PATTERN = re.compile(
    r"stands as|serves as|testament to|pivotal moment|crucial role|key role|marks a shift|"
    r"broader trend|evolving landscape|lasting impact|transformative|game-changing|"
    r"标志着|见证了|是.+证明|关键(?:性)?(?:时刻|转折|作用)|至关重要|深远影响|"
    r"不断演变的格局|变革性|重塑(?:行业|市场|格局)",
    re.IGNORECASE,
)
NOT_ONLY_BUT_PATTERN = re.compile(
    r"not only .{0,120} but|not just .{0,120} (?:but|it'?s)|not merely .{0,120} but|"
    r"不仅.{0,80}而且|不止于.{0,80}(?:更是|而是)|不只是.{0,80}(?:更是|而是)",
    re.IGNORECASE,
)
GENERIC_AI_VOCABULARY_PATTERN = re.compile(
    r"additionally|align with|crucial|delve|enduring|enhance|foster(?:ing)?|highlight(?:ing)?|"
    r"interplay|intricate|landscape|pivotal|showcase|tapestry|testament|underscore|valuable|vibrant|"
    r"此外|至关重要|深入探讨|彰显|凸显|赋能|焕新|无缝|沉浸式|多维|格局|"
    r"重要抓手|有力抓手|强势助推|生态闭环",
    re.IGNORECASE,
)
CLIENT_WRITING_RISK_CODES = {
    "CHATBOT_RESIDUE": CHATBOT_RESIDUE_PATTERN,
    "VAGUE_AUTHORITY_CLAIM": VAGUE_AUTHORITY_PATTERN,
    "EXAGGERATED_SIGNIFICANCE": EXAGGERATED_SIGNIFICANCE_PATTERN,
    "FORMULAIC_NOT_ONLY_BUT": NOT_ONLY_BUT_PATTERN,
}
PROFILE_SUBJECT_FIELDS = [
    "subject_id",
    "subject_type",
    "name",
    "role_or_title",
    "organization",
    "source_event_ids",
    "first_seen_at",
    "last_seen_at",
    "profile_status",
    "influence_level",
    "decision_power",
    "traits",
    "needs",
    "preferences",
    "concerns",
    "notes",
]
PROFILE_VOICE_FIELDS = [
    "voice_id",
    "source_event_id",
    "file_path",
    "speaker",
    "utterance",
    "need_signal",
    "preference_signal",
    "concern_signal",
    "decision_signal",
    "influence_level",
    "decision_power",
    "evidence_quote",
    "confidence",
    "status",
]
PROFILE_INSIGHT_FIELDS = [
    "insight_id",
    "subject_id",
    "subject_type",
    "source_event_id",
    "file_path",
    "insight_type",
    "statement",
    "evidence_quote",
    "confidence",
    "status",
    "priority",
    "linked_requirement_ids",
    "supersedes_insight_id",
    "created_at",
    "updated_at",
]
PROFILE_CONFLICT_FIELDS = [
    "conflict_id",
    "topic",
    "source_event_ids",
    "subject_ids",
    "conflict_summary",
    "recommended_resolution",
    "status",
    "confidence",
    "evidence_quotes",
    "created_at",
    "updated_at",
]
PROFILE_STATUS_VALUES = {"candidate", "confirmed", "conflicted", "deprecated"}
PROFILE_SUBJECT_TYPES = {"participant", "brand", "company", "client_group"}
PROFILE_DECISION_LEVELS = {"high", "medium", "low", "unknown"}
PROFILE_SOURCE_LABELS = {
    "项目",
    "品牌",
    "产品",
    "参考方向",
    "本轮交付",
    "客户希望",
    "客户明确",
    "背景",
    "目标",
    "交付",
}
SPEAKER_LINE_PATTERN = re.compile(
    r"^(?:\[(?P<bracket>[^\]]{1,28})\]|(?P<label>[\w\u4e00-\u9fff·（）() /-]{1,28}))\s*[：:]\s*(?P<body>.+)$"
)
NEED_SIGNAL_PATTERN = re.compile(r"希望|想要|需要|目标|必须|本轮|交付|要做|要体现|诉求")
PREFERENCE_SIGNAL_PATTERN = re.compile(r"喜欢|偏好|更想|风格|调性|参考方向|年轻|高端|真实|清爽|专业")
CONCERN_SIGNAL_PATTERN = re.compile(r"担心|不要|不能|风险|怕|预算|时间|禁区|不希望|避免|限制")
DECISION_SIGNAL_PATTERN = re.compile(r"拍板|决定|确认|最终|老板|领导|负责人|决策|定下来|可以定|我来定")
BRAND_SIGNAL_PATTERN = re.compile(r"品牌|调性|主张|定位|人群|logo|Logo|包装|视觉规范|产品")
COMPANY_SIGNAL_PATTERN = re.compile(r"公司|团队|集团|部门|内部|统一意见|甲方|客户内部|汇报链路")
CONFLICT_SIGNAL_PATTERN = re.compile(r"分歧|不同意|冲突|但是|不过|有人认为|另一个方向|还没统一|需要统一")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def install_global_skill(target: Path = DEFAULT_SKILL_INSTALL_DIR) -> dict[str, str | bool]:
    source_skill = SKILL_DRAFT_DIR / "SKILL.md"
    if not source_skill.exists():
        raise FileNotFoundError(f"skill draft not found: {source_skill}")
    target = target.expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_skill, target / "SKILL.md")
    source_hash = file_sha256(source_skill)
    target_hash = file_sha256(target / "SKILL.md")
    return {
        "source": str(source_skill),
        "target": str(target / "SKILL.md"),
        "source_hash": source_hash,
        "target_hash": target_hash,
        "match": source_hash == target_hash,
    }


def package_version() -> str:
    try:
        return metadata.version(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        pass

    root = source_root()
    pyproject = root / "pyproject.toml" if root else None
    if pyproject and pyproject.exists():
        try:
            import tomllib

            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            version = data.get("project", {}).get("version")
            if isinstance(version, str) and version:
                return version
        except Exception:
            pass
    return FALLBACK_VERSION


def module_available(name: str) -> tuple[bool, str]:
    try:
        imported = __import__(name)
        return True, str(getattr(imported, "__version__", "available") or "available")
    except Exception as exc:  # noqa: BLE001 - doctor should report exact import problem
        return False, str(exc)


def git_remote_summary() -> tuple[bool, str]:
    root = source_root()
    if not root or not (root / ".git").exists():
        return False, "not_source_git_checkout"
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001 - actionable local diagnostic
        return False, f"git_remote_failed={exc}"
    remote_text = result.stdout.strip()
    if not remote_text:
        return False, "empty"
    return True, remote_text.replace("\n", " | ")


def doctor_report() -> tuple[str, list[str], list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = [
        f"version={package_version()}",
        f"python={sys.version.split()[0]}",
        f"mode={'source' if source_root() else 'installed'}",
        f"runtime_root={REPO_ROOT}",
        f"template_root={TEMPLATE_ROOT}",
        f"skill_draft_dir={SKILL_DRAFT_DIR}",
    ]

    required_template_files = [
        "AD-creative/orchestrator/project.yml",
        "AGENTS.md",
        "AD-creative/orchestrator/requirements.csv",
        "AD-creative/orchestrator/thread_registry.csv",
        "AD-creative/orchestrator/thread_lane_plan_template.md",
        "AD-creative/orchestrator/agency_staff_selection_template.md",
        "AD-creative/agents/role_briefs/README.md",
        "AD-creative/handoff/项目看板.md",
        "AD-creative/gates/adversarial_council_gate_template.md",
    ]
    if not TEMPLATE_ROOT.exists():
        issues.append(f"template root missing: {TEMPLATE_ROOT}")
    else:
        evidence.append("template_root_exists=true")
        for rel_path in required_template_files:
            if not (TEMPLATE_ROOT / rel_path).exists():
                issues.append(f"template file missing: {rel_path}")

    skill_path = SKILL_DRAFT_DIR / "SKILL.md"
    if not skill_path.exists():
        issues.append(f"skill draft missing: {skill_path}")
    else:
        evidence.append(f"skill_draft={skill_path}")

    for module_name in ["PIL", "pptx"]:
        ok, note = module_available(module_name)
        evidence.append(f"module_{module_name}={note if ok else 'missing'}")
        if not ok:
            warnings.append(f"optional dependency unavailable: {module_name}: {note}")

    has_remote, remote_note = git_remote_summary()
    evidence.append(f"git_remote={remote_note}")
    if not has_remote and remote_note == "empty":
        warnings.append("git remote is not configured; push and GitHub Actions cannot run.")

    status = "PASS" if not issues else "CHECK"
    return status, issues, warnings, evidence


def evidence_map(evidence: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in evidence:
        if "=" in item:
            key, value = item.split("=", 1)
            values[key] = value
    return values


def release_status_payload() -> dict[str, object]:
    doctor_status, issues, warnings, evidence = doctor_report()
    values = evidence_map(evidence)
    mode = values.get("mode", "unknown")
    git_remote = values.get("git_remote", "unknown")
    remote_status = "PASS"
    if git_remote == "empty" or git_remote.startswith("git_remote_failed="):
        remote_status = "CHECK"
    elif git_remote == "not_source_git_checkout":
        remote_status = "NOT_APPLICABLE"

    if issues:
        release_status = "CHECK"
        next_action = "Fix doctor issues, then run make release-check."
    elif mode != "source":
        release_status = "INSTALLED_PACKAGE_OK"
        next_action = "Run adco release-status inside the source checkout before publishing."
    elif git_remote == "empty":
        release_status = "BLOCKED_REMOTE_MISSING"
        next_action = "Configure git remote, push the branch, and verify GitHub Actions."
    elif git_remote.startswith("git_remote_failed="):
        release_status = "CHECK"
        next_action = "Fix git remote diagnostics, then run make release-check."
    else:
        release_status = "READY_FOR_REMOTE_CHECKS"
        next_action = "Run make release-check, push the branch, and verify GitHub Actions."

    return {
        "release_status": release_status,
        "doctor_status": doctor_status,
        "remote_status": remote_status,
        "mode": mode,
        "git_remote": git_remote,
        "verify_command": "make release-check",
        "next_action": next_action,
        "issues": issues,
        "warnings": warnings,
        "evidence": evidence,
    }


def docs_payload() -> dict[str, object]:
    root = source_root()
    docs: list[dict[str, object]] = []
    if root:
        for label, rel_path in [
            ("readme", "README.md"),
            ("install", "docs/operating/install.md"),
            ("adoption_patterns", "docs/operating/adoption_patterns.md"),
            ("release_plan", "docs/operating/open_source_release_plan.md"),
            ("first_run_transcript", "docs/assets/first-run-transcript.md"),
        ]:
            path = root / rel_path
            docs.append({"label": label, "path": str(path), "exists": path.exists()})
    return {
        "mode": "source" if root else "installed",
        "source_root": str(root) if root else None,
        "template_root": str(TEMPLATE_ROOT),
        "skill_draft": str(SKILL_DRAFT_DIR / "SKILL.md"),
        "docs": docs,
        "quickstart": [
            "adco --version",
            "adco doctor",
            "adco release-status",
            "adco quickstart",
            "adco next /tmp/adco-demo",
            "adco profile-analyze /tmp/adco-demo --brand <brand> --company <company>",
            "adco thread-plan /tmp/adco-demo --title ThreadOps --objective 'Coordinate Codex worker threads'",
            "adco hygiene /tmp/adco-demo",
            "adco open-dashboard /tmp/adco-demo --no-open",
            "adco check",
        ],
    }


def sanitized_doctor_evidence(evidence: list[str]) -> list[str]:
    sanitized: list[str] = []
    for item in evidence:
        if item.startswith("git_remote="):
            value = item.split("=", 1)[1]
            if value not in {"empty", "not_source_git_checkout"} and not value.startswith("git_remote_failed="):
                sanitized.append("git_remote=configured")
            else:
                sanitized.append(item)
        elif item.startswith(("runtime_root=", "template_root=", "skill_draft_dir=", "skill_draft=")):
            key, value = item.split("=", 1)
            sanitized.append(f"{key}={Path(value).name if value else value}")
        else:
            sanitized.append(item)
    return sanitized


def support_table(project: Path, rel_path: str, columns: list[str], limit: int = 5) -> list[str]:
    _, rows = read_csv_rows(project / rel_path)
    lines: list[str] = []
    for row in rows[-limit:]:
        values = [f"{column}={row.get(column, '')}" for column in columns if row.get(column, "")]
        lines.append("- " + " | ".join(values) if values else "- row_present")
    return lines or ["- none"]


def render_support_bundle(project: Path) -> Path:
    counts = read_counts(project)
    errors, validate_stats = validate(project)
    doctor_status, doctor_issues, doctor_warnings, doctor_evidence = doctor_report()
    dashboard = project / DASHBOARD_REL
    council_report = project / COUNCIL_REPORT_REL
    report = project / SUPPORT_BUNDLE_REL
    lines = [
        "# Support Bundle",
        "",
        "content_policy: sanitized diagnostics only; no client brief text, material body, prompt body, or image content included.",
        f"created_at: {now_iso()}",
        f"project_name: {project.name}",
        f"stage: {project_stage(project)}",
        f"validation: {'PASS' if not errors else 'CHECK'}",
        f"doctor: {doctor_status}",
        "",
        "## Environment",
        "",
        *[f"- {item}" for item in sanitized_doctor_evidence(doctor_evidence)],
        "",
        "## Doctor Warnings",
        "",
        *[f"- {warning}" for warning in doctor_warnings],
        *(["- none"] if not doctor_warnings else []),
        "",
        "## Doctor Issues",
        "",
        *[f"- {issue}" for issue in doctor_issues],
        *(["- none"] if not doctor_issues else []),
        "",
        "## Project Counts",
        "",
        *[f"- {key}: {value}" for key, value in counts.items()],
        "",
        "## Validation Counts",
        "",
        *[f"- {key}: {value}" for key, value in validate_stats.items()],
        "",
        "## Validation Errors",
        "",
        *[f"- {error}" for error in errors],
        *(["- none"] if not errors else []),
        "",
        "## Key Files",
        "",
        f"- dashboard: {'exists' if dashboard.exists() else 'missing'}",
        f"- council_report: {'exists' if council_report.exists() else 'missing'}",
        "",
        "## Latest Gates",
        "",
        *support_table(
            project,
            "AD-creative/orchestrator/gate_log.csv",
            ["gate_id", "stage", "status", "next_state", "created_at", "owner"],
        ),
        "",
        "## Latest Work Items",
        "",
        *support_table(
            project,
            "AD-creative/orchestrator/work_items.csv",
            ["work_id", "stage", "status", "owner", "gate_required", "client_visibility"],
        ),
    ]
    write_text(report, "\n".join(lines))
    return report


def check_global_skill(target: Path = DEFAULT_SKILL_INSTALL_DIR) -> dict[str, str | bool]:
    source_skill = SKILL_DRAFT_DIR / "SKILL.md"
    target_skill = target.expanduser().resolve() / "SKILL.md"
    if not source_skill.exists() or not target_skill.exists():
        return {
            "source": str(source_skill),
            "target": str(target_skill),
            "source_hash": "",
            "target_hash": "",
            "match": False,
        }
    source_hash = file_sha256(source_skill)
    target_hash = file_sha256(target_skill)
    return {
        "source": str(source_skill),
        "target": str(target_skill),
        "source_hash": source_hash,
        "target_hash": target_hash,
        "match": source_hash == target_hash,
    }


def ensure_project(project: Path) -> tuple[int, int]:
    project.mkdir(parents=True, exist_ok=True)
    return copy_template(TEMPLATE_ROOT, project)


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv_rows(path: Path, fieldnames: list[str], rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def append_csv_row(path: Path, row: dict[str, str]) -> None:
    fieldnames, rows = read_csv_rows(path)
    if not fieldnames:
        raise FileNotFoundError(f"CSV header not found: {path}")
    rows.append(row)
    write_csv_rows(path, fieldnames, rows)


def ensure_csv_fields(path: Path, required_fields: list[str]) -> list[str]:
    fieldnames, rows = read_csv_rows(path)
    if not fieldnames:
        raise FileNotFoundError(f"CSV header not found: {path}")
    missing = [field for field in required_fields if field not in fieldnames]
    if missing:
        fieldnames = [*fieldnames, *missing]
        write_csv_rows(path, fieldnames, rows)
    return fieldnames


def update_or_append_csv_row(
    path: Path, key: str, row: dict[str, str], *, replace: bool = True
) -> None:
    fieldnames, rows = read_csv_rows(path)
    if not fieldnames:
        raise FileNotFoundError(f"CSV header not found: {path}")
    for index, existing in enumerate(rows):
        if existing.get(key) == row.get(key):
            if replace:
                rows[index] = row
            break
    else:
        rows.append(row)
    write_csv_rows(path, fieldnames, rows)


def next_id(rows: list[dict[str, str]], key: str, prefix: str) -> str:
    highest = 0
    for row in rows:
        match = ID_SUFFIX_PATTERN.search(row.get(key, ""))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}-{highest + 1:03d}"


def id_allocator(rows: list[dict[str, str]], key: str, prefix: str) -> Callable[[], str]:
    highest = 0
    for row in rows:
        match = ID_SUFFIX_PATTERN.search(row.get(key, ""))
        if match:
            highest = max(highest, int(match.group(1)))

    def allocate() -> str:
        nonlocal highest
        highest += 1
        return f"{prefix}-{highest:03d}"

    return allocate


def safe_rel(project: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(project.resolve()))
    except ValueError:
        return str(path.resolve())


def safe_rel_to(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def codex_generated_images_root() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    return codex_home / "generated_images"


def classify_material(path: Path) -> str:
    marker = str(path).lower()
    if "feedback" in marker or "客户反馈" in marker:
        return "feedback"
    if "director" in marker or "导演" in marker:
        return "director_note"
    if "meeting" in marker or "会议" in marker:
        return "meeting_note"
    if "approval" in marker or "确认" in marker:
        return "approval"
    if "rejection" in marker or "拒绝" in marker:
        return "rejection"
    if "change" in marker or "变更" in marker:
        return "change"
    return "initial"


def append_event(project: Path, payload: dict[str, object]) -> None:
    path = project / "AD-creative/orchestrator/events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def register_materials(project: Path, material_paths: list[Path], goal: str) -> list[str]:
    source_path = project / "AD-creative/orchestrator/source_events.csv"
    _, rows = read_csv_rows(source_path)
    source_ids: list[str] = []
    allocate_source_id = id_allocator(rows, "source_event_id", "SRC")

    for material in material_paths:
        if not material.exists():
            raise FileNotFoundError(f"material not found: {material}")
        source_id = allocate_source_id()
        row = {
            "source_event_id": source_id,
            "received_at": now_iso(),
            "source_owner": "operator",
            "source_type": "folder" if material.is_dir() else "file",
            "declared_semantics": classify_material(material),
            "file_paths": safe_rel(project, material),
            "raw_summary": f"待整理资料：{material.name}",
            "trust_level": "unreviewed",
            "affects_requirements": "unknown",
            "affects_artifacts": "",
            "supersedes_event_ids": "",
            "notes": goal,
        }
        rows.append(row)
        source_ids.append(source_id)
        append_event(
            project,
            {
                "event_id": f"EVT-{source_id}",
                "event_type": "material_registered",
                "created_at": row["received_at"],
                "source_event_id": source_id,
                "material": row["file_paths"],
                "goal": goal,
            },
        )

    if source_ids:
        fieldnames, _ = read_csv_rows(source_path)
        write_csv_rows(source_path, fieldnames, rows)
    return source_ids


def existing_source_ids_for_material(project: Path, material: Path) -> list[str]:
    _, rows = read_csv_rows(project / "AD-creative/orchestrator/source_events.csv")
    material_resolved = material.resolve()
    matches: list[str] = []
    for row in rows:
        raw_path = row.get("file_paths", "")
        path = Path(raw_path)
        if not path.is_absolute():
            path = project / raw_path
        if path.resolve() == material_resolved:
            source_id = row.get("source_event_id", "")
            if source_id:
                matches.append(source_id)
    return matches


def write_sample_brief(project: Path, force: bool = False) -> tuple[Path, str]:
    material = project / SAMPLE_MATERIAL_REL
    if material.exists() and not force:
        return material, "existing"
    write_text(material, SAMPLE_BRIEF)
    return material, "overwritten" if force else "created"


def ensure_intake_work(project: Path, source_ids: list[str], goal: str) -> str:
    work_path = project / "AD-creative/orchestrator/work_items.csv"
    fieldnames, rows = read_csv_rows(work_path)
    for row in rows:
        if row.get("stage") == "intake" and row.get("title") == "需求整理与缺口判断":
            return row.get("work_id", "")

    work_id = next_id(rows, "work_id", "WORK")
    row = {
        "work_id": work_id,
        "stage": "intake",
        "title": "需求整理与缺口判断",
        "objective": goal or "整理客户资料，输出需求、缺口、追问和下一步建议。",
        "owner_agent": "Codex",
        "status": "ready",
        "priority": "high",
        "input_refs": ";".join(source_ids),
        "output_artifacts": "",
        "linked_requirements": "",
        "linked_source_events": ";".join(source_ids),
        "linked_references": "",
        "linked_assets": "",
        "linked_slides": "",
        "blocked_by": "",
        "gate_required": "Brief Gate",
        "client_visibility": "internal_only",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "supersedes_work_id": "",
    }
    rows.append(row)
    write_csv_rows(work_path, fieldnames, rows)
    return work_id


def ensure_profile_work(project: Path, source_ids: list[str], goal: str) -> str:
    work_path = project / "AD-creative/orchestrator/work_items.csv"
    fieldnames, rows = read_csv_rows(work_path)
    for row in rows:
        if row.get("stage") == "intake" and row.get("title") == "会议画像与品牌画像分析":
            row["linked_source_events"] = join_unique_values(row.get("linked_source_events", ""), ";".join(source_ids))
            row["updated_at"] = now_iso()
            write_csv_rows(work_path, fieldnames, rows)
            return row.get("work_id", "")

    work_id = next_id(rows, "work_id", "WORK")
    rows.append(
        {
            "work_id": work_id,
            "stage": "intake",
            "title": "会议画像与品牌画像分析",
            "objective": goal or "分析会议资料中的人物画像、品牌画像、需求权重、决策权和分歧融合路径。",
            "owner_agent": "Codex",
            "status": "ready",
            "priority": "high",
            "input_refs": ";".join(source_ids),
            "output_artifacts": "",
            "linked_requirements": "",
            "linked_source_events": ";".join(source_ids),
            "linked_references": "",
            "linked_assets": "",
            "linked_slides": "",
            "blocked_by": "",
            "gate_required": "Profile Gate",
            "client_visibility": "internal_only",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "supersedes_work_id": "",
        }
    )
    write_csv_rows(work_path, fieldnames, rows)
    return work_id


def ensure_creative_proposal_work(project: Path, work_id: str, source_ids: str, objective: str) -> str:
    work_path = project / "AD-creative/orchestrator/work_items.csv"
    fieldnames, rows = read_csv_rows(work_path)
    if not fieldnames:
        raise FileNotFoundError(f"CSV header not found: {work_path}")
    for row in rows:
        if work_id and row.get("work_id") == work_id:
            row["linked_source_events"] = join_unique_values(row.get("linked_source_events", ""), source_ids)
            row["updated_at"] = now_iso()
            write_csv_rows(work_path, fieldnames, rows)
            return work_id
        if not work_id and row.get("stage") == "creative" and row.get("title") == "内部创意提案草案":
            row["linked_source_events"] = join_unique_values(row.get("linked_source_events", ""), source_ids)
            row["updated_at"] = now_iso()
            write_csv_rows(work_path, fieldnames, rows)
            return row.get("work_id", "")
    new_work_id = work_id or next_id(rows, "work_id", "WORK")
    rows.append(
        {
            "work_id": new_work_id,
            "stage": "creative",
            "title": "内部创意提案草案",
            "objective": objective or "生成可追溯的内部创意提案草案，并在客户可见前通过 creative-quality-gate。",
            "owner_agent": "Codex",
            "status": "ready",
            "priority": "high",
            "input_refs": source_ids,
            "output_artifacts": "ART-AUTO-CREATIVE-DIRECTIONS;ART-AUTO-CREATIVE-OPTION-MATRIX;ART-AUTO-PROPOSAL-STRUCTURE;ART-AUTO-SLIDE-SPEC",
            "linked_requirements": "",
            "linked_source_events": source_ids,
            "linked_references": "",
            "linked_assets": "",
            "linked_slides": "",
            "blocked_by": "",
            "gate_required": "Creative Quality Gate",
            "client_visibility": "internal_only",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "supersedes_work_id": "",
        }
    )
    write_csv_rows(work_path, fieldnames, rows)
    return new_work_id


def read_counts(project: Path) -> dict[str, int]:
    tables = {
        "source_events": "AD-creative/orchestrator/source_events.csv",
        "requirements": "AD-creative/orchestrator/requirements.csv",
        "gaps": "AD-creative/orchestrator/gaps.csv",
        "work_items": "AD-creative/orchestrator/work_items.csv",
        "agent_runs": "AD-creative/orchestrator/agent_runs.csv",
        "artifacts": "AD-creative/orchestrator/artifact_index.csv",
        "gates": "AD-creative/orchestrator/gate_log.csv",
        "references": "AD-creative/references/reference_cards.csv",
        "assets": "AD-creative/visual_assets/asset_manifest.csv",
        "profile_subjects": "AD-creative/orchestrator/profile_knowledge/profile_subjects.csv",
        "profile_insights": "AD-creative/orchestrator/profile_knowledge/profile_insights.csv",
        "profile_conflicts": "AD-creative/orchestrator/profile_knowledge/profile_conflicts.csv",
    }
    counts: dict[str, int] = {}
    for key, rel_path in tables.items():
        _, rows = read_csv_rows(project / rel_path)
        counts[key] = len(rows)
    return counts


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


TEXT_SUFFIXES = {".md", ".txt", ".csv", ".json", ".yml", ".yaml"}
SKIP_MATERIAL_LINES = {"text", "```"}
REQUIREMENT_TRIGGER_PATTERN = re.compile(
    r"项目|客户希望|希望|要求|交付|产品|品牌|方向|关键画面|关键帧|moodboard|参考|PPT|不要|不能|必须|需要|新增要求|客户明确"
)


def material_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() in TEXT_SUFFIXES else []
    if not path.is_dir():
        return []
    files = [
        item
        for item in path.rglob("*")
        if item.is_file() and item.suffix.lower() in TEXT_SUFFIXES and "AD-creative" not in item.parts
    ]
    return sorted(files)


def read_material_text(path: Path, max_chars: int = 12000) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")
    return text[:max_chars]


def clean_material_line(line: str) -> str:
    line = line.strip().strip("|").strip()
    line = re.sub(r"^[-*#>`\s]+", "", line).strip()
    line = re.sub(r"\s+", " ", line)
    return line


def classify_requirement(statement: str) -> tuple[str, str, str]:
    text = statement.lower()
    if any(token in statement for token in ["不要", "禁区", "不能", "未经授权", "假 logo", "假logo"]):
        return "constraint", "high", "client_review"
    if any(token in statement for token in ["交付", "PPT", "ppt", "可编辑", "SlideSpec"]):
        return "delivery", "high", "ppt_gate"
    if any(token in statement for token in ["参考", "moodboard", "视频链接", "摄影参考"]):
        return "research", "high", "reference_research"
    if any(token in statement for token in ["画面", "视觉", "关键帧", "产品", "logo", "人物", "场景", "颜色"]):
        return "visual", "high", "visual_plan"
    if any(token in statement for token in ["方向", "主张", "创意", "情绪", "功能"]):
        return "creative", "high", "creative"
    if "ai" in text or "image" in text:
        return "visual_policy", "medium", "visual_review"
    return "brief", "medium", "intake"


def extract_requirement_statements(materials: list[tuple[Path, str]]) -> list[tuple[Path, str]]:
    candidates: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for path, text in materials:
        for raw_line in text.splitlines():
            line = clean_material_line(raw_line)
            if not line or line in SKIP_MATERIAL_LINES:
                continue
            if len(line) < 6 or len(line) > 180:
                continue
            if not REQUIREMENT_TRIGGER_PATTERN.search(line):
                continue
            normalized = line.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            candidates.append((path, line))
    return candidates[:16]


def gap_templates(requirements: list[dict[str, str]], all_text: str) -> list[dict[str, str]]:
    lowered = all_text.lower()
    gaps: list[dict[str, str]] = []

    def linked_req(*tokens: str) -> str:
        for req in requirements:
            statement = req.get("statement", "")
            if any(token in statement for token in tokens):
                return req.get("requirement_id", "")
        return requirements[0].get("requirement_id", "") if requirements else ""

    if any(token in all_text for token in ["logo", "Logo", "品牌 logo", "品牌规范"]):
        gaps.append(
            {
                "linked_requirement_id": linked_req("logo", "Logo", "品牌"),
                "impact": "blocking",
                "description": "缺少品牌 logo / 字体 / 包装 / 视觉规范，不能进入客户可见稿。",
                "recommended_action": "向客户索取品牌资产包；没有资产前只做内部方向稿。",
                "question_for_client": "请提供品牌 logo、字体、包装或产品露出规范。",
            }
        )
    if any(token in all_text for token in ["产品高清", "产品图", "包装", "实拍", "产品素材"]):
        gaps.append(
            {
                "linked_requirement_id": linked_req("产品", "包装"),
                "impact": "high_impact",
                "description": "缺少产品高清图或实拍素材，产品细节不能准确呈现。",
                "recommended_action": "向客户索取产品高清图、包装图、颜色版本和使用限制。",
                "question_for_client": "是否有产品高清图、包装图、颜色版本和不可改动的产品细节？",
            }
        )
    if any(token in lowered for token in ["ai", "image_gen", "生成图"]) or "AI" in all_text:
        gaps.append(
            {
                "linked_requirement_id": linked_req("AI", "生成图", "视觉"),
                "impact": "high_impact",
                "description": "AI 图客户可见性未锁定。",
                "recommended_action": "默认 internal_only；客户可见前必须单独 Gate。",
                "question_for_client": "AI 生成图是否允许进入客户审阅稿？是否需要标注？",
            }
        )
    else:
        gaps.append(
            {
                "linked_requirement_id": linked_req("视觉", "画面", "关键帧"),
                "impact": "medium",
                "description": "AI 参考图使用边界未声明。",
                "recommended_action": "默认 internal_only，只用于内部方向草图。",
                "question_for_client": "是否允许 AI 参考图用于内部方向草图？",
            }
        )
    if any(token in all_text for token in ["参考", "视频链接", "moodboard", "摄影参考"]):
        gaps.append(
            {
                "linked_requirement_id": linked_req("参考", "视频", "moodboard"),
                "impact": "high_impact",
                "description": "需要公开可追溯参考来源，否则参考包不能客户可见。",
                "recommended_action": "三方议会 PASS 后自动做公开官方/公开视频资料搜索计划。",
                "question_for_client": "是否有客户指定参考片、竞品、禁用参考或必须避开的风格？",
            }
        )
    if any(token in all_text for token in ["PPT", "ppt", "可编辑"]):
        gaps.append(
            {
                "linked_requirement_id": linked_req("PPT", "可编辑", "交付"),
                "impact": "medium",
                "description": "PPT 可编辑性和交付精度未最终确认。",
                "recommended_action": "先做结构和 SlideSpec，PPTX 前跑 PPT Gate。",
                "question_for_client": "本轮需要看结构、关键帧，还是需要接近可发送 PPT？",
            }
        )
    return gaps


def normalize_profile_key(value: str) -> str:
    normalized = re.sub(r"\s+", "", value.strip().lower())
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", normalized)


def stable_profile_id(prefix: str, *parts: str) -> str:
    raw = "|".join(normalize_profile_key(part) for part in parts if part)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10].upper()
    return f"{prefix}-{digest}"


def join_unique_values(*values: str) -> str:
    seen: set[str] = set()
    merged: list[str] = []
    for value in values:
        for item in value.split(";"):
            cleaned = item.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                merged.append(cleaned)
    return ";".join(merged)


def quote_excerpt(value: str, limit: int = 96) -> str:
    cleaned = re.sub(r"\s+", " ", value.strip())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def split_speaker_line(line: str) -> tuple[str, str] | None:
    cleaned = clean_material_line(line)
    match = SPEAKER_LINE_PATTERN.match(cleaned)
    if not match:
        return None
    speaker = (match.group("bracket") or match.group("label") or "").strip()
    utterance = (match.group("body") or "").strip()
    if not speaker or not utterance or speaker in PROFILE_SOURCE_LABELS:
        return None
    if len(utterance) < 4:
        return None
    return speaker, utterance


def collect_source_materials(project: Path, source_ids: list[str]) -> tuple[list[tuple[dict[str, str], Path, str]], list[str]]:
    _, source_rows = read_csv_rows(project / "AD-creative/orchestrator/source_events.csv")
    source_id_set = set(source_ids)
    target_sources = [
        row for row in source_rows if not source_id_set or row.get("source_event_id") in source_id_set
    ]
    materials: list[tuple[dict[str, str], Path, str]] = []
    resolved_source_ids: list[str] = []
    for source in target_sources:
        source_id = source.get("source_event_id", "")
        if source_id:
            resolved_source_ids.append(source_id)
        raw_path = source.get("file_paths", "")
        path = Path(raw_path)
        if raw_path and not path.is_absolute():
            path = project / raw_path
        for file_path in material_files(path):
            materials.append((source, file_path, read_material_text(file_path, max_chars=24000)))
    return materials, resolved_source_ids


def ensure_profile_knowledge_base(project: Path) -> None:
    profile_dir = project / "AD-creative/orchestrator/profile_knowledge"
    profile_dir.mkdir(parents=True, exist_ok=True)
    csv_specs = {
        "profile_subjects.csv": PROFILE_SUBJECT_FIELDS,
        "meeting_voice_map.csv": PROFILE_VOICE_FIELDS,
        "profile_insights.csv": PROFILE_INSIGHT_FIELDS,
        "profile_conflicts.csv": PROFILE_CONFLICT_FIELDS,
    }
    for filename, fields in csv_specs.items():
        path = profile_dir / filename
        if path.exists():
            ensure_csv_fields(path, fields)
        else:
            write_csv_rows(path, fields, [])
    current_truth = profile_dir / "profile_current_truth.md"
    if not current_truth.exists():
        write_text(
            current_truth,
            """# Profile Current Truth

## Participant Profiles
- 暂无会议画像。

## Brand / Company Profiles
- 暂无品牌或公司画像。

## Demand And Decision Map
- 暂无。

## Conflicts
- 暂无。

## Next Confirmation
- 等待会议资料或客户资料输入。
""",
        )


def profile_signal(value: str, pattern: re.Pattern[str]) -> str:
    return "yes" if pattern.search(value) else ""


def profile_insight_types(text: str, *, subject_type: str) -> list[str]:
    insight_types: list[str] = []
    if NEED_SIGNAL_PATTERN.search(text):
        insight_types.append("need")
    if PREFERENCE_SIGNAL_PATTERN.search(text):
        insight_types.append("preference")
    if CONCERN_SIGNAL_PATTERN.search(text):
        insight_types.append("concern")
    if DECISION_SIGNAL_PATTERN.search(text):
        insight_types.append("decision_signal")
    if subject_type == "brand" or BRAND_SIGNAL_PATTERN.search(text):
        insight_types.append("brand_trait")
    if subject_type == "company" or COMPANY_SIGNAL_PATTERN.search(text):
        insight_types.append("company_context")
    return insight_types or ["observation"]


def infer_decision_power(name: str, utterances: list[str]) -> str:
    combined = f"{name}\n" + "\n".join(utterances)
    if DECISION_SIGNAL_PATTERN.search(combined) or re.search(r"老板|CEO|CMO|负责人|总经理|总监|创始人", combined):
        return "high"
    if re.search(r"经理|主管|客户|甲方|品牌", combined):
        return "medium"
    return "unknown"


def infer_influence_level(count: int, total: int, decision_power: str) -> str:
    if decision_power == "high":
        return "high"
    if total <= 0:
        return "unknown"
    share = count / total
    if count >= 4 or share >= 0.35:
        return "high"
    if count >= 2 or share >= 0.15:
        return "medium"
    return "low"


def infer_traits(utterances: list[str]) -> str:
    joined = "\n".join(utterances)
    traits: list[str] = []
    if CONCERN_SIGNAL_PATTERN.search(joined):
        traits.append("谨慎，关注风险边界")
    if DECISION_SIGNAL_PATTERN.search(joined):
        traits.append("会推动拍板或最终确认")
    if BRAND_SIGNAL_PATTERN.search(joined):
        traits.append("重视品牌调性和产品露出")
    if re.search(r"时间|预算|交付|效率|周期", joined):
        traits.append("关注执行效率和交付约束")
    if PREFERENCE_SIGNAL_PATTERN.search(joined):
        traits.append("对风格有明确偏好")
    return "；".join(traits) if traits else "信息不足，需继续观察"


def summarize_signals(utterances: list[str], pattern: re.Pattern[str], fallback: str) -> str:
    matches = [quote_excerpt(item, 60) for item in utterances if pattern.search(item)]
    return "；".join(matches[:3]) if matches else fallback


def profile_subject_row(
    *,
    subject_type: str,
    name: str,
    source_ids: str,
    now: str,
    utterances: list[str],
    total_utterances: int = 0,
    organization: str = "",
    role_or_title: str = "",
) -> dict[str, str]:
    decision_power = infer_decision_power(name, utterances) if subject_type == "participant" else "unknown"
    influence_level = (
        infer_influence_level(len(utterances), total_utterances or len(utterances), decision_power)
        if subject_type == "participant"
        else "unknown"
    )
    return {
        "subject_id": stable_profile_id("PROF", subject_type, name),
        "subject_type": subject_type,
        "name": name,
        "role_or_title": role_or_title,
        "organization": organization,
        "source_event_ids": source_ids,
        "first_seen_at": now,
        "last_seen_at": now,
        "profile_status": "candidate",
        "influence_level": influence_level,
        "decision_power": decision_power,
        "traits": infer_traits(utterances) if utterances else "待补充",
        "needs": summarize_signals(utterances, NEED_SIGNAL_PATTERN, "待补充"),
        "preferences": summarize_signals(utterances, PREFERENCE_SIGNAL_PATTERN, "待补充"),
        "concerns": summarize_signals(utterances, CONCERN_SIGNAL_PATTERN, "待补充"),
        "notes": "由会议/客户资料自动整理；需要人工确认后升级为 confirmed。",
    }


def merge_profile_subject(existing: dict[str, str], incoming: dict[str, str]) -> dict[str, str]:
    merged = dict(existing)
    for key in ["name", "subject_type", "role_or_title", "organization"]:
        if incoming.get(key):
            merged[key] = incoming[key]
    merged["source_event_ids"] = join_unique_values(existing.get("source_event_ids", ""), incoming.get("source_event_ids", ""))
    merged["last_seen_at"] = incoming.get("last_seen_at", existing.get("last_seen_at", ""))
    for key in ["traits", "needs", "preferences", "concerns", "notes"]:
        old = existing.get(key, "")
        new = incoming.get(key, "")
        if old in {"", "待补充", "信息不足，需继续观察"}:
            merged[key] = new
        elif new and new not in old:
            merged[key] = join_unique_values(old.replace("；", ";"), new.replace("；", ";")).replace(";", "；")
    level_order = {"unknown": 0, "low": 1, "medium": 2, "high": 3}
    for key in ["influence_level", "decision_power"]:
        if level_order.get(incoming.get(key, "unknown"), 0) > level_order.get(existing.get(key, "unknown"), 0):
            merged[key] = incoming[key]
    return merged


def profile_priority(insight_type: str) -> str:
    if insight_type in {"decision_signal", "concern"}:
        return "high"
    if insight_type in {"need", "brand_trait", "company_context"}:
        return "medium"
    return "low"


def add_profile_insight(
    rows_by_id: dict[str, dict[str, str]],
    *,
    subject_id: str,
    subject_type: str,
    source_id: str,
    file_path: str,
    insight_type: str,
    statement: str,
    evidence: str,
    now: str,
) -> tuple[int, int]:
    insight_id = stable_profile_id("INS", subject_id, insight_type, statement)
    row = {
        "insight_id": insight_id,
        "subject_id": subject_id,
        "subject_type": subject_type,
        "source_event_id": source_id,
        "file_path": file_path,
        "insight_type": insight_type,
        "statement": statement,
        "evidence_quote": quote_excerpt(evidence),
        "confidence": "0.68" if insight_type in {"need", "preference", "concern", "decision_signal"} else "0.56",
        "status": "candidate",
        "priority": profile_priority(insight_type),
        "linked_requirement_ids": "",
        "supersedes_insight_id": "",
        "created_at": now,
        "updated_at": now,
    }
    if insight_id in rows_by_id:
        existing = rows_by_id[insight_id]
        existing["source_event_id"] = source_id or existing.get("source_event_id", "")
        existing["file_path"] = file_path or existing.get("file_path", "")
        existing["evidence_quote"] = row["evidence_quote"] or existing.get("evidence_quote", "")
        existing["updated_at"] = now
        return 0, 1
    rows_by_id[insight_id] = row
    return 1, 0


def profile_current_truth_content(
    project: Path,
    subjects: list[dict[str, str]],
    insights: list[dict[str, str]],
    conflicts: list[dict[str, str]],
) -> str:
    participant_rows = [row for row in subjects if row.get("subject_type") == "participant"]
    org_rows = [row for row in subjects if row.get("subject_type") in {"brand", "company", "client_group"}]
    top_participants = sorted(
        participant_rows,
        key=lambda row: (
            {"high": 3, "medium": 2, "low": 1}.get(row.get("decision_power", ""), 0),
            {"high": 3, "medium": 2, "low": 1}.get(row.get("influence_level", ""), 0),
        ),
        reverse=True,
    )[:8]
    demand_insights = [row for row in insights if row.get("insight_type") in {"need", "preference", "concern", "decision_signal"}]
    participant_table = "\n".join(
        f"| {md_cell(row.get('name', ''))} | {row.get('influence_level', '')} | {row.get('decision_power', '')} | {md_cell(row.get('needs', ''))} | {md_cell(row.get('concerns', ''))} |"
        for row in top_participants
    ) or "| - | - | - | 暂无 | 暂无 |"
    org_table = "\n".join(
        f"| {md_cell(row.get('subject_type', ''))} | {md_cell(row.get('name', ''))} | {md_cell(row.get('traits', ''))} | {md_cell(row.get('preferences', ''))} |"
        for row in org_rows[:8]
    ) or "| - | - | 暂无 | 暂无 |"
    demand_rows = "\n".join(
        f"- {row.get('insight_type')}: {row.get('statement')}（证据：{row.get('evidence_quote')}）"
        for row in demand_insights[:10]
    ) or "- 暂无"
    conflict_rows = "\n".join(
        f"- {row.get('topic')}: {row.get('conflict_summary')}；建议：{row.get('recommended_resolution')}"
        for row in conflicts[:8]
    ) or "- 暂无显式分歧"
    return f"""# Profile Current Truth

## Project
{project.name}

## Participant Profiles
| 人 | 影响力 | 决策权 | 想要什么 | 担心什么 |
|---|---|---|---|---|
{participant_table}

## Brand / Company Profiles
| 类型 | 名称 | 特点 | 偏好 |
|---|---|---|---|
{org_table}

## Demand And Decision Map
{demand_rows}

## Conflicts
{conflict_rows}

## How To Use
- 先满足高决策权/高影响力人物的明确诉求。
- 有分歧时不要硬合并成一句口号，先列出双方关心点，再给折中方案。
- 证据不足的画像只能作为 candidate，客户确认后再升级为 confirmed。

## Next Confirmation
- 请确认关键发言人姓名/职务、最终拍板人、品牌禁区，以及哪些分歧已经内部统一。
"""


def profile_handoff_content(
    subjects: list[dict[str, str]],
    insights: list[dict[str, str]],
    conflicts: list[dict[str, str]],
) -> str:
    decision_people = [
        row for row in subjects if row.get("subject_type") == "participant" and row.get("decision_power") in {"high", "medium"}
    ][:6]
    decision_rows = "\n".join(
        f"| {md_cell(row.get('name', ''))} | {row.get('decision_power', '')} | {row.get('influence_level', '')} | {md_cell(row.get('traits', ''))} |"
        for row in decision_people
    ) or "| - | - | - | 暂无 |"
    need_rows = "\n".join(
        f"- {row.get('statement')}" for row in insights if row.get("insight_type") in {"need", "preference"}
    ) or "- 暂无明确诉求"
    concern_rows = "\n".join(
        f"- {row.get('statement')}" for row in insights if row.get("insight_type") == "concern"
    ) or "- 暂无明确担心"
    conflict_rows = "\n".join(
        f"- {row.get('conflict_summary')} 建议：{row.get('recommended_resolution')}" for row in conflicts
    ) or "- 暂无显式分歧"
    return f"""# 画像分析简报

## 这次会议看出了什么
{need_rows}

## 谁更需要重点照顾
| 人 | 决策权 | 影响力 | 特点 |
|---|---|---|---|
{decision_rows}

## 他们担心什么
{concern_rows}

## 分歧怎么合
{conflict_rows}

## 下一步怎么用
- 写方案前先看高决策权人物的诉求。
- 研究阶段优先补齐有争议、证据不足、会影响客户拍板的信息。
- 方案里同时照顾品牌特点、公司内部共识和具体发言人的担心点。
"""


def analyze_profiles(
    project: Path,
    *,
    source_ids: list[str] | None = None,
    work_id: str = "",
    goal: str = "",
    brand: str = "",
    company: str = "",
    client: str = "",
) -> dict[str, object]:
    ensure_profile_knowledge_base(project)
    source_ids = source_ids or []
    materials, resolved_source_ids = collect_source_materials(project, source_ids)
    now = now_iso()
    linked_source_ids = ";".join(source_ids or resolved_source_ids)
    profile_dir = project / "AD-creative/orchestrator/profile_knowledge"

    subject_fields, subject_rows = read_csv_rows(profile_dir / "profile_subjects.csv")
    voice_fields, voice_rows = read_csv_rows(profile_dir / "meeting_voice_map.csv")
    insight_fields, insight_rows = read_csv_rows(profile_dir / "profile_insights.csv")
    conflict_fields, conflict_rows = read_csv_rows(profile_dir / "profile_conflicts.csv")
    subjects_by_id = {row.get("subject_id", ""): row for row in subject_rows if row.get("subject_id")}
    voices_by_id = {row.get("voice_id", ""): row for row in voice_rows if row.get("voice_id")}
    insights_by_id = {row.get("insight_id", ""): row for row in insight_rows if row.get("insight_id")}
    conflicts_by_id = {row.get("conflict_id", ""): row for row in conflict_rows if row.get("conflict_id")}

    speaker_utterances: dict[str, list[str]] = {}
    speaker_source_ids: dict[str, str] = {}
    speaker_files: dict[str, str] = {}
    new_voices = 0
    deduped = 0
    new_insights = 0
    updated_insights = 0
    conflict_candidates: list[tuple[str, str, str, str]] = []

    for source, file_path, text in materials:
        source_id = source.get("source_event_id", "")
        rel_file = safe_rel(project, file_path)
        for raw_line in text.splitlines():
            line = clean_material_line(raw_line)
            if not line or len(line) < 4:
                continue
            speaker_line = split_speaker_line(line)
            if speaker_line:
                speaker, utterance = speaker_line
                speaker_utterances.setdefault(speaker, []).append(utterance)
                speaker_source_ids[speaker] = join_unique_values(speaker_source_ids.get(speaker, ""), source_id)
                speaker_files[speaker] = join_unique_values(speaker_files.get(speaker, ""), rel_file)
                voice_id = stable_profile_id("VOICE", source_id, speaker, utterance)
                voice_row = {
                    "voice_id": voice_id,
                    "source_event_id": source_id,
                    "file_path": rel_file,
                    "speaker": speaker,
                    "utterance": utterance,
                    "need_signal": profile_signal(utterance, NEED_SIGNAL_PATTERN),
                    "preference_signal": profile_signal(utterance, PREFERENCE_SIGNAL_PATTERN),
                    "concern_signal": profile_signal(utterance, CONCERN_SIGNAL_PATTERN),
                    "decision_signal": profile_signal(utterance, DECISION_SIGNAL_PATTERN),
                    "influence_level": "",
                    "decision_power": "",
                    "evidence_quote": quote_excerpt(utterance),
                    "confidence": "0.72",
                    "status": "candidate",
                }
                if voice_id in voices_by_id:
                    voices_by_id[voice_id].update(voice_row)
                    deduped += 1
                else:
                    voices_by_id[voice_id] = voice_row
                    new_voices += 1
                if CONFLICT_SIGNAL_PATTERN.search(utterance):
                    conflict_candidates.append((source_id, rel_file, speaker, utterance))
            elif BRAND_SIGNAL_PATTERN.search(line) or COMPANY_SIGNAL_PATTERN.search(line) or CONFLICT_SIGNAL_PATTERN.search(line):
                subject_type = "brand" if BRAND_SIGNAL_PATTERN.search(line) else "company"
                subject_name = brand if subject_type == "brand" and brand else company if company else client or "未命名客户"
                subject_id = stable_profile_id("PROF", subject_type, subject_name)
                if subject_id not in subjects_by_id:
                    subjects_by_id[subject_id] = profile_subject_row(
                        subject_type=subject_type,
                        name=subject_name,
                        source_ids=source_id,
                        now=now,
                        utterances=[line],
                        organization=company or client,
                    )
                else:
                    incoming = profile_subject_row(
                        subject_type=subject_type,
                        name=subject_name,
                        source_ids=source_id,
                        now=now,
                        utterances=[line],
                        organization=company or client,
                    )
                    subjects_by_id[subject_id] = merge_profile_subject(subjects_by_id[subject_id], incoming)
                for insight_type in profile_insight_types(line, subject_type=subject_type):
                    added, updated = add_profile_insight(
                        insights_by_id,
                        subject_id=subject_id,
                        subject_type=subject_type,
                        source_id=source_id,
                        file_path=rel_file,
                        insight_type=insight_type,
                        statement=line,
                        evidence=line,
                        now=now,
                    )
                    new_insights += added
                    updated_insights += updated
                if CONFLICT_SIGNAL_PATTERN.search(line):
                    conflict_candidates.append((source_id, rel_file, subject_name, line))

    total_voice_count = sum(len(items) for items in speaker_utterances.values())
    for speaker, utterances in speaker_utterances.items():
        subject_id = stable_profile_id("PROF", "participant", speaker)
        incoming = profile_subject_row(
            subject_type="participant",
            name=speaker,
            source_ids=speaker_source_ids.get(speaker, linked_source_ids),
            now=now,
            utterances=utterances,
            total_utterances=total_voice_count,
            organization=company or client,
        )
        if subject_id in subjects_by_id:
            subjects_by_id[subject_id] = merge_profile_subject(subjects_by_id[subject_id], incoming)
        else:
            subjects_by_id[subject_id] = incoming
        for voice in voices_by_id.values():
            if voice.get("speaker") == speaker:
                voice["influence_level"] = subjects_by_id[subject_id].get("influence_level", "")
                voice["decision_power"] = subjects_by_id[subject_id].get("decision_power", "")
        for utterance in utterances:
            for insight_type in profile_insight_types(utterance, subject_type="participant"):
                added, updated = add_profile_insight(
                    insights_by_id,
                    subject_id=subject_id,
                    subject_type="participant",
                    source_id=speaker_source_ids.get(speaker, "").split(";")[0],
                    file_path=speaker_files.get(speaker, "").split(";")[0],
                    insight_type=insight_type,
                    statement=utterance,
                    evidence=utterance,
                    now=now,
                )
                new_insights += added
                updated_insights += updated

    for subject_type, name in [("brand", brand), ("company", company), ("client_group", client)]:
        if not name:
            continue
        subject_id = stable_profile_id("PROF", subject_type, name)
        incoming = profile_subject_row(
            subject_type=subject_type,
            name=name,
            source_ids=linked_source_ids,
            now=now,
            utterances=[],
            organization=company if subject_type != "company" else name,
        )
        if subject_id in subjects_by_id:
            subjects_by_id[subject_id] = merge_profile_subject(subjects_by_id[subject_id], incoming)
        else:
            subjects_by_id[subject_id] = incoming

    for source_id, rel_file, speaker, utterance in conflict_candidates:
        conflict_id = stable_profile_id("CONF", source_id, utterance)
        subject_id = stable_profile_id("PROF", "participant", speaker)
        row = {
            "conflict_id": conflict_id,
            "topic": "会议分歧 / 需要统一",
            "source_event_ids": source_id,
            "subject_ids": subject_id if subject_id in subjects_by_id else "",
            "conflict_summary": utterance,
            "recommended_resolution": "先确认最终拍板人；把双方担心点拆成必须满足、可折中、暂缓三类。",
            "status": "candidate",
            "confidence": "0.62",
            "evidence_quotes": quote_excerpt(f"{speaker}: {utterance}"),
            "created_at": now,
            "updated_at": now,
        }
        if conflict_id in conflicts_by_id:
            conflicts_by_id[conflict_id]["updated_at"] = now
            deduped += 1
        else:
            conflicts_by_id[conflict_id] = row

    subjects = sorted(subjects_by_id.values(), key=lambda row: (row.get("subject_type", ""), row.get("name", "")))
    voices = sorted(voices_by_id.values(), key=lambda row: row.get("voice_id", ""))
    insights = sorted(insights_by_id.values(), key=lambda row: (row.get("priority", ""), row.get("insight_id", "")), reverse=True)
    conflicts = sorted(conflicts_by_id.values(), key=lambda row: row.get("conflict_id", ""))
    write_csv_rows(profile_dir / "profile_subjects.csv", subject_fields, subjects)
    write_csv_rows(profile_dir / "meeting_voice_map.csv", voice_fields, voices)
    write_csv_rows(profile_dir / "profile_insights.csv", insight_fields, insights)
    write_csv_rows(profile_dir / "profile_conflicts.csv", conflict_fields, conflicts)

    profile_truth_path = profile_dir / "profile_current_truth.md"
    handoff_path = project / "AD-creative/handoff/画像分析简报.md"
    write_text(profile_truth_path, profile_current_truth_content(project, subjects, insights, conflicts))
    write_text(handoff_path, profile_handoff_content(subjects, insights, conflicts))
    for artifact_id, artifact_type, rel_path in [
        ("ART-AUTO-PROFILE-TRUTH", "profile_current_truth", safe_rel(project, profile_truth_path)),
        ("ART-AUTO-PROFILE-BRIEF", "profile_handoff_brief", safe_rel(project, handoff_path)),
    ]:
        update_artifact(
            project,
            artifact_id,
            artifact_type,
            rel_path,
            "intake",
            source_event_ids=linked_source_ids,
            linked_work_items=work_id,
            gate_status="PARTIAL_PASS",
        )
    append_gate(
        project,
        "GATE-AUTO-PROFILE-001",
        "intake",
        "PARTIAL_PASS",
        "70",
        "ART-AUTO-PROFILE-TRUTH;ART-AUTO-PROFILE-BRIEF",
        "画像均为 candidate，需人工确认关键角色和最终拍板人。",
        "确认关键发言人、决策权、分歧是否已统一。",
        "请确认谁是最终拍板人、哪些画像结论可升级为 confirmed。",
        "research_plan",
        "ad_creative_operator",
    )
    append_event(
        project,
        {
            "event_id": f"EVT-PROFILE-{now}",
            "event_type": "profile_analysis_completed",
            "created_at": now,
            "actor": "ad_creative_operator",
            "source_event_ids": linked_source_ids,
            "goal": goal,
            "subjects": len(subjects),
            "insights": len(insights),
            "conflicts": len(conflicts),
        },
    )
    if work_id:
        work_path = project / "AD-creative/orchestrator/work_items.csv"
        work_fields, work_rows = read_csv_rows(work_path)
        for row in work_rows:
            if row.get("work_id") == work_id:
                row["status"] = "done"
                row["output_artifacts"] = "ART-AUTO-PROFILE-TRUTH;ART-AUTO-PROFILE-BRIEF"
                row["linked_source_events"] = join_unique_values(row.get("linked_source_events", ""), linked_source_ids)
                row["updated_at"] = now
                break
        write_csv_rows(work_path, work_fields, work_rows)
    return {
        "materials": len(materials),
        "subjects": len(subjects),
        "voices": len(voices),
        "insights": len(insights),
        "conflicts": len(conflicts),
        "new_voices": new_voices,
        "new_insights": new_insights,
        "updated_insights": updated_insights,
        "deduped": deduped,
        "profile_current_truth": profile_truth_path,
        "handoff": handoff_path,
        "source_ids": linked_source_ids,
    }


def unique_rows(rows: list[dict[str, str]], key: str) -> set[str]:
    return {row.get(key, "").strip() for row in rows if row.get(key, "").strip()}


def owner_for_statement(statement: str) -> str:
    return "client" if CLIENT_OWNER_PATTERN.search(statement) else "operator"


def first_existing_id(project: Path, rel_path: str, key: str) -> str:
    _, rows = read_csv_rows(project / rel_path)
    for row in rows:
        value = row.get(key, "").strip()
        if value:
            return value
    return ""


def update_artifact(
    project: Path,
    artifact_id: str,
    artifact_type: str,
    rel_path: str,
    stage: str,
    *,
    status: str = "done",
    visibility: str = "internal_only",
    source_event_ids: str = "",
    linked_requirements: str = "",
    linked_work_items: str = "",
    linked_references: str = "",
    linked_assets: str = "",
    gate_status: str = "PASS",
) -> None:
    update_or_append_csv_row(
        project / "AD-creative/orchestrator/artifact_index.csv",
        "artifact_id",
        {
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "path": rel_path,
            "stage": stage,
            "version": "v001",
            "status": status,
            "visibility": visibility,
            "source_event_ids": source_event_ids,
            "linked_requirements": linked_requirements,
            "linked_work_items": linked_work_items,
            "linked_references": linked_references,
            "linked_assets": linked_assets,
            "gate_status": gate_status,
            "supersedes_artifact_id": "",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        },
    )


def append_gate(
    project: Path,
    gate_id: str,
    stage: str,
    status: str,
    score: str,
    checked_artifacts: str,
    blocking_issues: str,
    revision_items: str,
    questions: str,
    next_state: str,
    owner: str,
) -> None:
    update_or_append_csv_row(
        project / "AD-creative/orchestrator/gate_log.csv",
        "gate_id",
        {
            "gate_id": gate_id,
            "stage": stage,
            "status": status,
            "score": score,
            "checked_artifacts": checked_artifacts,
            "blocking_issues": blocking_issues,
            "revision_items": revision_items,
            "questions": questions,
            "next_state": next_state,
            "created_at": now_iso(),
            "owner": owner,
        },
    )


POLLUTION_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
POLLUTION_FILE_SUFFIXES = {".pyc", ".pyo"}
POLLUTION_FILE_NAMES = {".DS_Store"}
THREAD_TERMINAL_STATES = {"archived", "closed", "reconciled", "superseded", "duplicate", "stale"}


def find_pollution_paths(root: Path, limit: int = 80) -> list[str]:
    if not root.exists():
        return []
    findings: list[str] = []
    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.name in POLLUTION_DIR_NAMES or path.name in POLLUTION_FILE_NAMES or path.suffix in POLLUTION_FILE_SUFFIXES:
            findings.append(safe_rel(root, path))
            if len(findings) >= limit:
                break
    return findings


def git_status_for(root: Path) -> tuple[str, list[str], list[str]]:
    try:
        git_root = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "", [], []
    completed = subprocess.run(
        ["git", "-C", git_root, "status", "--short", "--untracked-files=all"],
        check=True,
        text=True,
        capture_output=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    tracked = [line for line in lines if not line.startswith("??")]
    untracked = [line for line in lines if line.startswith("??")]
    return git_root, tracked, untracked


def active_thread_registry_rows(project: Path) -> list[dict[str, str]]:
    _, rows = read_csv_rows(project / "AD-creative/orchestrator/thread_registry.csv")
    active: list[dict[str, str]] = []
    for row in rows:
        thread_id = row.get("thread_id", "").strip()
        archived = row.get("archived", "").strip().lower()
        lifecycle = row.get("lifecycle_state", "").strip().lower()
        if not thread_id or thread_id.startswith("planned:"):
            continue
        if archived in {"true", "yes", "1"} or lifecycle in THREAD_TERMINAL_STATES:
            continue
        active.append(row)
    return active


def workspace_hygiene_report(project: Path) -> dict[str, object]:
    project = project.resolve()
    git_root, tracked, untracked = git_status_for(project)
    pollution = find_pollution_paths(project)
    active_threads = active_thread_registry_rows(project)
    issues: list[str] = []
    if tracked:
        issues.append(f"tracked git changes: {len(tracked)}")
    if untracked:
        issues.append(f"untracked git files: {len(untracked)}")
    if pollution:
        issues.append(f"cache/temp pollution paths: {len(pollution)}")
    if active_threads:
        issues.append(f"active thread registry rows: {len(active_threads)}")
    plan = [
        "把验证和草稿生成放在 /tmp 或 AD-creative/workspaces/<work_id>/，不要写到仓库根目录。",
        "每次大任务结束跑 git status --short --untracked-files=all，并清理 __pycache__ / .pytest_cache / .mypy_cache / .ruff_cache / *.pyc / *.pyo / .DS_Store。",
        "Codex Thread 结果合并后立即归档，并把 cleanup_action / archived 写回 thread_registry.csv。",
        "源码模板和 packaged mirror 必须一起更新，并跑 check_packaged_assets。",
        "用户未要求 commit 前，只报告修改文件；不要 reset、checkout 或删除用户资料。",
    ]
    return {
        "status": "PASS" if not issues else "CHECK",
        "project": str(project),
        "git_root": git_root,
        "tracked_changes": tracked,
        "untracked_files": untracked,
        "pollution_paths": pollution,
        "active_threads": [
            {
                "thread_id": row.get("thread_id", ""),
                "title": row.get("title", ""),
                "role": row.get("role", ""),
                "lifecycle_state": row.get("lifecycle_state", ""),
                "archived": row.get("archived", ""),
            }
            for row in active_threads
        ],
        "issues": issues,
        "plan": plan,
    }


def host_platform(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    if not host:
        return "unknown"
    return host.removeprefix("www.")


def check_url(url: str, timeout: float = 8.0) -> tuple[bool, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        return False, "URL 必须是 https。"
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ad-creative-orchestrator/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            return 200 <= int(status) < 400, f"HTTP {status}"
    except urllib.error.HTTPError as exc:
        if exc.code == 405:
            try:
                fallback = urllib.request.Request(url, headers={"User-Agent": "ad-creative-orchestrator/1.0"})
                with urllib.request.urlopen(fallback, timeout=timeout) as response:
                    status = getattr(response, "status", 200)
                    return 200 <= int(status) < 400, f"HTTP {status}"
            except Exception as fallback_exc:  # noqa: BLE001 - report exact network failure
                return False, str(fallback_exc)
        return False, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 - report exact network failure
        return False, str(exc)


def render_reference_shortlist(project: Path) -> Path:
    _, refs = read_csv_rows(project / "AD-creative/references/reference_cards.csv")
    rows = "\n".join(
        "| {reference_id} | {title} | {platform} | {role} | {url} | {client_visible} |".format(
            **{key: row.get(key, "") for key in [
                "reference_id",
                "title",
                "platform",
                "role",
                "url",
                "client_visible",
            ]}
        )
        for row in refs
    )
    if not rows:
        rows = "| - | 暂无真实参考 | - | - | - | - |"
    path = project / "AD-creative/references/reference_shortlist.md"
    write_text(
        path,
        f"""# Reference Shortlist

status: real_links_registered
visibility: internal_only

| ID | 标题 | 平台 | 角色 | URL | 客户可见 |
| --- | --- | --- | --- | --- | --- |
{rows}

## Rules

- 只登记 https 链接。
- 客户稿引用前仍需确认版权、使用范围和截图来源。
- 未过 Research Gate 的参考只用于内部方向判断。
""",
    )
    return path


def add_reference(
    project: Path,
    url: str,
    title: str,
    role: str,
    reference_type: str,
    *,
    source_owner: str = "official_or_public",
    why_relevant: str = "",
    borrow: str = "",
    do_not_copy: str = "",
    client_visible: str = "false",
    live_check: bool = True,
) -> tuple[str, str]:
    ok, note = check_url(url) if live_check else (True, "live_check_skipped")
    if not ok:
        raise ValueError(f"reference URL check failed: {url}: {note}")
    ref_path = project / "AD-creative/references/reference_cards.csv"
    fields, refs = read_csv_rows(ref_path)
    if not fields:
        raise FileNotFoundError(f"CSV header not found: {ref_path}")
    for row in refs:
        if row.get("url") == url:
            ref_id = row.get("reference_id", "")
            return ref_id, "existing"
    ref_id = next_id(refs, "reference_id", "REF")
    source_id = first_existing_id(project, "AD-creative/orchestrator/source_events.csv", "source_event_id")
    refs.append(
        {
            "reference_id": ref_id,
            "source_event_id": source_id,
            "platform": host_platform(url),
            "url": url,
            "title": title or url,
            "source_owner": source_owner,
            "reference_type": reference_type,
            "role": role,
            "why_relevant": why_relevant,
            "borrow": borrow,
            "do_not_copy": do_not_copy or "不要复制构图、标志、人物或可识别画面；只抽取方向逻辑。",
            "client_visible": client_visible,
            "notes": note,
        }
    )
    write_csv_rows(ref_path, fields, refs)
    shortlist = render_reference_shortlist(project)
    update_artifact(
        project,
        "ART-AUTO-REFERENCE-SHORTLIST",
        "reference_pack",
        safe_rel(project, shortlist),
        "reference_research",
        linked_references=ref_id,
        gate_status="PASS",
    )
    append_gate(
        project,
        "GATE-AUTO-REFERENCE-001",
        "reference_research",
        "PASS",
        "90",
        "ART-AUTO-REFERENCE-SHORTLIST",
        "",
        "客户稿引用前确认版权和截图范围。",
        "",
        "ready_for_internal_creative",
        "ad_creative_operator",
    )
    append_event(
        project,
        {
            "event_id": f"EVT-{ref_id}",
            "event_type": "reference_registered",
            "created_at": now_iso(),
            "reference_id": ref_id,
            "url": url,
            "live_check": note,
        },
    )
    return ref_id, "created"


def compact_evidence(value: str, limit: int = 140) -> str:
    cleaned = re.sub(r"\s+", " ", clean_material_line(value)).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def first_evidence_line(lines: list[tuple[str, str]], patterns: list[str], fallback: str) -> tuple[str, str]:
    regex = re.compile("|".join(re.escape(pattern) for pattern in patterns), re.IGNORECASE)
    for source_id, line in lines:
        if regex.search(line):
            return compact_evidence(line), source_id
    return fallback, ""


def open_question(label: str) -> str:
    return f"TBD - open question: {label}"


def collect_proposal_evidence(project: Path) -> dict[str, object]:
    _, requirement_rows = read_csv_rows(project / "AD-creative/orchestrator/requirements.csv")
    _, gap_rows = read_csv_rows(project / "AD-creative/orchestrator/gaps.csv")
    _, reference_rows = read_csv_rows(project / "AD-creative/references/reference_cards.csv")
    _, profile_insights = read_csv_rows(project / "AD-creative/orchestrator/profile_knowledge/profile_insights.csv")
    source_materials, resolved_source_ids = collect_source_materials(project, [])
    evidence_lines: list[tuple[str, str]] = []
    for requirement in requirement_rows:
        statement = requirement.get("statement", "").strip()
        if statement:
            evidence_lines.append((requirement.get("source_event_id", ""), statement))
    for gap in gap_rows:
        description = gap.get("description", "").strip()
        question = gap.get("question_for_client", "").strip()
        if description:
            evidence_lines.append((gap.get("linked_requirement_id", ""), description))
        if question:
            evidence_lines.append((gap.get("linked_requirement_id", ""), question))
    for source, _, text in source_materials:
        source_id = source.get("source_event_id", "")
        for raw_line in text.splitlines():
            line = clean_material_line(raw_line)
            if 6 <= len(line) <= 180:
                evidence_lines.append((source_id, line))

    business_problem, business_source = first_evidence_line(
        evidence_lines,
        ["问题", "挑战", "新品", "launch", "广告创意", "提案", "内部评审", "交付"],
        open_question("business problem"),
    )
    client_objective, objective_source = first_evidence_line(
        evidence_lines,
        ["客户希望", "目标", "本轮交付", "需要", "PPT", "内部评审", "审阅"],
        open_question("client real objective"),
    )
    audience, audience_source = first_evidence_line(
        evidence_lines,
        ["人群", "用户", "消费者", "轻运动", "户外", "年轻", "audience"],
        open_question("target audience"),
    )
    barrier, barrier_source = first_evidence_line(
        evidence_lines,
        ["担心", "不要", "不能", "缺少", "暂缺", "风险", "障碍", "痛点", "限制"],
        open_question("target behavior barrier"),
    )
    product_feature, feature_source = first_evidence_line(
        evidence_lines,
        ["产品", "功能", "饮料", "包装", "高清图", "补给", "功能饮料", "卖点"],
        open_question("product feature"),
    )
    visual_reference, visual_source = first_evidence_line(
        evidence_lines,
        ["真实户外", "清爽", "清晨", "山路", "手持产品", "关键视觉", "画面", "视觉"],
        open_question("visual/action evidence"),
    )
    insight = open_question("consumer insight")
    insight_source = ""
    for row in profile_insights:
        if row.get("insight_type") in {"need", "preference", "concern", "brand_trait"}:
            insight = compact_evidence(row.get("statement", ""))
            insight_source = row.get("source_event_id", "")
            break
    if insight.startswith("TBD"):
        insight, insight_source = first_evidence_line(
            evidence_lines,
            ["真实", "清爽", "担心", "偏", "希望", "需要", "不要", "轻运动", "户外"],
            open_question("consumer insight"),
        )
    reference_notes = [
        f"{ref.get('reference_id')}: {ref.get('title') or ref.get('url')} ({ref.get('role')})"
        for ref in reference_rows
        if ref.get("reference_id")
    ]
    competitor_notes = "; ".join(reference_notes[:5]) or open_question("brand/category/competitor notes")
    source_ids = ";".join(sorted({item for item in resolved_source_ids if item}))
    return {
        "business_problem": business_problem,
        "business_source": business_source,
        "client_objective": client_objective,
        "objective_source": objective_source,
        "audience": audience,
        "audience_source": audience_source,
        "barrier": barrier,
        "barrier_source": barrier_source,
        "insight": insight,
        "insight_source": insight_source,
        "product_feature": product_feature,
        "feature_source": feature_source,
        "visual_reference": visual_reference,
        "visual_source": visual_source,
        "competitor_notes": competitor_notes,
        "source_ids": source_ids,
        "requirement_ids": ";".join(row.get("requirement_id", "") for row in requirement_rows if row.get("requirement_id")),
        "reference_ids": ";".join(row.get("reference_id", "") for row in reference_rows if row.get("reference_id")),
    }


def proposal_evidence_ref(source: str) -> str:
    return source or "TBD"


def build_creative_direction_rows(context: dict[str, object]) -> list[dict[str, str]]:
    feature = str(context["product_feature"])
    benefit = (
        "把产品从静态卖点翻译成可感知的场景价值。"
        if not feature.startswith("TBD")
        else open_question("communication benefit")
    )
    insight = str(context["insight"])
    visual = str(context["visual_reference"])
    audience = str(context["audience"])
    barrier = str(context["barrier"])
    return [
        {
            "direction_id": "DIR-01",
            "name": "场景补给证明",
            "role": "把产品功能落到真实使用场景",
            "strategy_path": "product_feature_to_behavior_moment",
            "creative_proposition": f"在{audience}最需要补给的时刻，让产品成为动作继续发生的证据。",
            "core_message": f"{feature} -> {benefit}",
            "target_feeling": "真实、清爽、可信",
            "product_feature": feature,
            "communication_benefit": benefit,
            "behavior_barrier": barrier,
            "key_visual_or_action": visual,
            "title_or_use_case": "清晨出发前 / 山路途中 / 手持产品的连续动作",
            "reference_ids": str(context["reference_ids"]),
            "risk": "缺少产品高清图时只能保留 internal_only placeholder。",
            "why_choose": "适合先证明产品如何进入真实行为，不依赖竞品或案例背书。",
            "evidence_refs": ";".join(
                filter(
                    None,
                    [
                        proposal_evidence_ref(str(context["audience_source"])),
                        proposal_evidence_ref(str(context["feature_source"])),
                        proposal_evidence_ref(str(context["visual_source"])),
                    ],
                )
            ),
            "status": "draft",
            "notes": "internal traceable draft",
        },
        {
            "direction_id": "DIR-02",
            "name": "选择理由显性化",
            "role": "把客户目标翻译成可比较的提案路径",
            "strategy_path": "client_objective_to_choice_rationale",
            "creative_proposition": f"围绕客户真实目标：{context['client_objective']}，把每个方向的取舍说清楚。",
            "core_message": "不是口号比拼，而是让客户能判断为什么选这一条。",
            "target_feeling": "清晰、有判断依据、可推进",
            "product_feature": feature,
            "communication_benefit": "让产品利益、执行方式、风险边界能同时被审阅。",
            "behavior_barrier": barrier,
            "key_visual_or_action": "一页对比矩阵 + 每条方向一张关键动作图或 placeholder slot。",
            "title_or_use_case": "内部评审会方向选择页",
            "reference_ids": str(context["reference_ids"]),
            "risk": "如果客户目标证据不足，本方向必须降级为 open question。",
            "why_choose": "适合客户还在内部统一意见时使用。",
            "evidence_refs": proposal_evidence_ref(str(context["objective_source"])),
            "status": "draft",
            "notes": "internal traceable draft",
        },
        {
            "direction_id": "DIR-03",
            "name": "阻力转译",
            "role": "把受众阻力转成创意动作",
            "strategy_path": "audience_barrier_to_execution",
            "creative_proposition": f"承认阻力：{barrier}，用更具体的行动画面降低理解成本。",
            "core_message": f"{insight} -> 看见行动理由。",
            "target_feeling": "直接、具体、少解释",
            "product_feature": feature,
            "communication_benefit": "让受众先理解为什么需要它，再记住产品。",
            "behavior_barrier": barrier,
            "key_visual_or_action": "障碍前后对比：出发前犹豫 / 使用产品 / 继续行动。",
            "title_or_use_case": "受众痛点页或短片第一幕",
            "reference_ids": str(context["reference_ids"]),
            "risk": "若 insight 未被资料支持，只能作为假设方向，不可客户可见。",
            "why_choose": "适合资料里已有明确担心、禁区或使用障碍时推进。",
            "evidence_refs": ";".join(
                filter(
                    None,
                    [
                        proposal_evidence_ref(str(context["barrier_source"])),
                        proposal_evidence_ref(str(context["insight_source"])),
                    ],
                )
            ),
            "status": "draft",
            "notes": "internal traceable draft",
        },
    ]


def render_creative_directions_content(context: dict[str, object], rows: list[dict[str, str]]) -> str:
    overview = "\n".join(
        "| {direction_id} | {name} | {role} | {strategy_path} | {core_message} | {why_choose} |".format(
            **{key: md_cell(row.get(key, "")) for key in [
                "direction_id",
                "name",
                "role",
                "strategy_path",
                "core_message",
                "why_choose",
            ]}
        )
        for row in rows
    )
    detail_sections = "\n\n".join(
        f"""## {row['direction_id']} {row['name']}

- creative proposition: {row['creative_proposition']}
- core message: {row['core_message']}
- key visual/action: {row['key_visual_or_action']}
- title/use case: {row['title_or_use_case']}
- risk: {row['risk']}
- why choose: {row['why_choose']}
- evidence refs: {row['evidence_refs'] or 'TBD'}
"""
        for row in rows
    )
    return f"""# Creative Directions

status: draft
visibility: internal_only
artifact_role: traceable_internal_creative_proposal_draft

## Evidence Boundaries
- Do not fabricate insight, competitors, audience barriers, or case-study facts.
- Missing facts stay as TBD/open questions and must not become client-visible claims.
- Video/storyboard execution goes to dircreative; image/KV/backgrounds go to imagegen or Creative Production; fixed templates go to Template Creator.

## Proposal Inputs
- business problem: {context['business_problem']} [source: {proposal_evidence_ref(str(context['business_source']))}]
- client real objective: {context['client_objective']} [source: {proposal_evidence_ref(str(context['objective_source']))}]
- target audience: {context['audience']} [source: {proposal_evidence_ref(str(context['audience_source']))}]
- behavior barrier: {context['barrier']} [source: {proposal_evidence_ref(str(context['barrier_source']))}]
- consumer insight: {context['insight']} [source: {proposal_evidence_ref(str(context['insight_source']))}]
- feature to benefit: {context['product_feature']} -> {rows[0]['communication_benefit']} [source: {proposal_evidence_ref(str(context['feature_source']))}]
- brand/category/competitor notes: {context['competitor_notes']}
- strategy path: product evidence -> audience barrier -> differentiated direction -> client choice rationale

## Direction Overview

| Direction | Name | Role | Strategy Path | Core Message | Why Choose |
|---|---|---|---|---|---|
{overview}

{detail_sections}
## Open Questions
- Confirm unsupported TBD fields before client-facing use.
- Confirm competitor/category evidence before naming any real competitor.
- Confirm which direction should become a PPT/client review lane.
"""


def render_proposal_structure_content(context: dict[str, object], rows: list[dict[str, str]]) -> str:
    direction_pages = "\n".join(
        f"- {row['direction_id']} {row['name']}: proposition / core message / key visual-action / use case / risk / why choose."
        for row in rows
    )
    return f"""# Proposal Structure

status: draft
visibility: internal_only
artifact_role: traceable_internal_proposal_architecture

## Client Review Goal
client real objective: {context['client_objective']}

## Business Problem
{context['business_problem']}

## Audience And Insight
- target audience: {context['audience']}
- behavior barrier: {context['barrier']}
- consumer insight: {context['insight']}

## Feature To Benefit
- product feature: {context['product_feature']}
- communication benefit: {rows[0]['communication_benefit']}

## Brand/Category/Competitor Notes
{context['competitor_notes']}

## Recommended Page Flow
1. 目标和问题界定
2. 受众与行为阻力
3. 产品功能到传播利益
4. 策略路径
5. 2-3 条创意方向对比
6. 推荐方向与选择理由
7. 风险、缺口、待确认问题

## Direction Pages
{direction_pages}

## Reference Pages
- Only cite registered REF rows or explicit TBD search targets.
- Do not use case-study facts until source evidence exists.

## Visual Asset Slots
- DIR-01 key action frame: internal placeholder until visual-quality-gate.
- DIR-02 matrix/choice slide: editable text first.
- DIR-03 barrier/action contrast: internal placeholder until asset slot is bound.

## Proposal Outline
The PPT/proposal outline must preserve problem, objective, audience, insight, feature-to-benefit, direction choices, visual/action execution, risks, and open questions.

## Open Questions
- Which TBD fields must be confirmed before client review?
- Which visual route should be delegated to imagegen/Creative Production?
- Which video/storyboard route should be delegated to dircreative?
"""


def render_slide_spec_content(rows: list[dict[str, str]]) -> str:
    slide_rows = [
        ("1", "Problem", "Business problem + client real objective", "none", "internal_only"),
        ("2", "Audience Insight", "Target audience + behavior barrier + consumer insight", "none", "internal_only"),
        ("3", "Feature To Benefit", "Product feature translated to communication benefit", "none", "internal_only"),
        ("4", "Direction Matrix", "2-3 differentiated directions with why choose", "none", "internal_only"),
    ]
    for index, row in enumerate(rows, start=5):
        slide_rows.append(
            (
                str(index),
                row["name"],
                f"{row['creative_proposition']} / {row['core_message']} / risk: {row['risk']}",
                f"{row['direction_id']}-KEY-ACTION",
                "internal_only",
            )
        )
    table = "\n".join(
        f"| {num} | {md_cell(purpose)} | {md_cell(content)} | {md_cell(slot)} | {visibility} |"
        for num, purpose, content, slot, visibility in slide_rows
    )
    return f"""# Slide Spec

status: draft
visibility: internal_only
artifact_role: internal_editable_proposal_outline

## Rules

```text
Text must remain editable.
Images must have asset IDs or placeholder IDs.
No internal notes in client-visible slides.
No fake logo or fake case evidence.
Do not treat VALIDATION=PASS as creative quality approval.
```

## Slides

| Slide | Purpose | Content | Asset Slot | Visibility |
|---|---|---|---|---|
{table}
"""


def render_creative_proposal(project: Path, *, work_id: str = "") -> dict[str, object]:
    ensure_project(project)
    context = collect_proposal_evidence(project)
    work_id = ensure_creative_proposal_work(
        project,
        work_id,
        str(context["source_ids"]),
        str(context["client_objective"]),
    )
    rows = build_creative_direction_rows(context)
    creative_path = project / "AD-creative/creative/creative_directions.md"
    matrix_path = project / "AD-creative/creative/option_matrix.csv"
    structure_path = project / "AD-creative/proposal_architecture/proposal_structure.md"
    slide_path = project / "AD-creative/client_review/slide_spec.md"
    write_text(creative_path, render_creative_directions_content(context, rows))
    matrix_fields = [
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
    write_csv_rows(matrix_path, matrix_fields, rows)
    write_text(structure_path, render_proposal_structure_content(context, rows))
    write_text(slide_path, render_slide_spec_content(rows))
    artifact_ids: list[str] = []
    for artifact_id, artifact_type, rel_path in CREATIVE_PROPOSAL_ARTIFACTS:
        artifact_ids.append(artifact_id)
        update_artifact(
            project,
            artifact_id,
            artifact_type,
            str(rel_path),
            "creative",
            visibility="internal_only",
            source_event_ids=str(context["source_ids"]),
            linked_requirements=str(context["requirement_ids"]),
            linked_work_items=work_id,
            linked_references=str(context["reference_ids"]),
            gate_status="NOT_RUN",
        )
    append_event(
        project,
        {
            "event_id": f"EVT-CREATIVE-PROPOSAL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "event_type": "creative_proposal_rendered",
            "created_at": now_iso(),
            "work_id": work_id,
            "artifacts": artifact_ids,
        },
    )
    return {
        "project": str(project),
        "work_id": work_id,
        "artifact_ids": artifact_ids,
        "paths": [str(project / rel_path) for _, _, rel_path in CREATIVE_PROPOSAL_ARTIFACTS],
        "context": context,
    }


def creative_proposal_scan_files(project: Path) -> list[Path]:
    _, artifacts = read_csv_rows(project / "AD-creative/orchestrator/artifact_index.csv")
    paths = [project / rel_path for _, _, rel_path in CREATIVE_PROPOSAL_ARTIFACTS]
    creative_types = {
        "creative_directions",
        "creative_option_matrix",
        "proposal_structure",
        "slide_spec",
        "creative_proposal",
        "proposal_outline",
    }
    for artifact in artifacts:
        if artifact.get("artifact_type", "").strip() in creative_types:
            rel_path = artifact.get("path", "").strip()
            if rel_path:
                paths.append(project / rel_path)
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(path)
    return deduped


def read_proposal_texts(paths: list[Path]) -> tuple[str, list[str]]:
    chunks: list[str] = []
    missing: list[str] = []
    for path in paths:
        if not path.exists():
            missing.append(str(path))
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n\n".join(chunks), missing


def load_direction_rows(project: Path) -> list[dict[str, str]]:
    _, rows = read_csv_rows(project / "AD-creative/creative/option_matrix.csv")
    return [row for row in rows if row.get("direction_id", "").strip()]


def field_is_tbd(value: str) -> bool:
    cleaned = value.strip().lower()
    return cleaned in {"", "tbd", "n/a", "-"} or "tbd" in cleaned or "open question" in cleaned or "待补充" in value or "暂无" in value


def has_supported_case_claim(line: str) -> bool:
    if not CASE_CLAIM_PATTERN.search(line):
        return True
    if re.search(r"不依赖|不是|非|不能|不要|without|not a|not rely|excluded", line, re.IGNORECASE):
        return True
    return bool(re.search(r"\b(REF|SRC|ART)-[A-Z0-9-]+|https://|TBD|open question|待补充", line))


def has_trace_marker(line: str) -> bool:
    return bool(re.search(r"\b(REF|SRC|REQ|ART)-[A-Z0-9-]+|https://|\[source:", line, re.IGNORECASE))


def collect_humanizer_writing_risks(combined_text: str, client_texts: list[tuple[Path, str]], project: Path) -> list[tuple[str, str]]:
    risks: list[tuple[str, str]] = []
    for code, pattern in CLIENT_WRITING_RISK_CODES.items():
        hits: list[str] = []
        for line in combined_text.splitlines():
            if not pattern.search(line):
                continue
            if code == "VAGUE_AUTHORITY_CLAIM" and has_trace_marker(line):
                continue
            hits.append(compact_evidence(line, 120))
        if hits:
            risks.append((code, "; ".join(hits[:3])))

    vocab_hits = [match.group(0) for match in GENERIC_AI_VOCABULARY_PATTERN.finditer(combined_text)]
    unique_vocab_hits = sorted(set(vocab_hits), key=str.lower)
    if len(vocab_hits) >= 4 or len(unique_vocab_hits) >= 3:
        risks.append(("GENERIC_AI_VOCABULARY", ", ".join(unique_vocab_hits[:8])))

    dash_hits = re.findall(r"—|–| -- ", combined_text)
    client_dash_locations = [
        safe_rel(project, path)
        for path, text in client_texts
        if re.search(r"—|–| -- ", text)
    ]
    if len(dash_hits) >= 2:
        risks.append(("DASH_OVERUSE", f"{len(dash_hits)} dash-like separators in proposal text"))
    elif client_dash_locations:
        risks.append(("DASH_OVERUSE", "client-facing dash-like separators: " + ", ".join(client_dash_locations[:4])))
    return risks


def client_facing_scan_paths(project: Path, files: list[Path]) -> list[Path]:
    _, artifacts = read_csv_rows(project / "AD-creative/orchestrator/artifact_index.csv")
    client_paths: set[Path] = set()
    for artifact in artifacts:
        if artifact.get("visibility", "").lower() in CLIENT_VISIBLE_VALUES:
            rel_path = artifact.get("path", "").strip()
            if rel_path:
                client_paths.add((project / rel_path).resolve())
    for path in files:
        if not path.exists() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        head = "\n".join(path.read_text(encoding="utf-8", errors="ignore").splitlines()[:12]).lower()
        if "visibility: client_visible" in head or "visibility: client_visible_ready" in head:
            client_paths.add(path.resolve())
    return sorted(client_paths)


def review_creative_quality(project: Path) -> tuple[str, list[str], Path]:
    files = creative_proposal_scan_files(project)
    for artifact_id, artifact_type, rel_path in CREATIVE_PROPOSAL_ARTIFACTS:
        if (project / rel_path).exists():
            update_artifact(
                project,
                artifact_id,
                artifact_type,
                str(rel_path),
                "creative",
                visibility="internal_only",
                gate_status="NOT_RUN",
            )
    combined_text, missing_files = read_proposal_texts(files)
    lower_text = combined_text.lower()
    direction_rows = load_direction_rows(project)
    issues: list[str] = []
    warnings: list[str] = []
    reason_codes: list[str] = []
    evidence: list[str] = [
        f"scanned_files={len(files)}",
        f"direction_rows={len(direction_rows)}",
    ]

    if missing_files:
        reason_codes.append("MISSING_PROPOSAL_ARTIFACT")
        issues.extend(f"creative proposal artifact missing: {safe_rel(project, Path(path))}" for path in missing_files[:6])
    if len(combined_text.strip()) < 900 or not direction_rows:
        reason_codes.append("EMPTY_SKELETON")
        issues.append("创意/提案文件仍是空骨架或缺少 option_matrix 方向行。")
    for label in CREATIVE_PROPOSAL_REQUIRED_LABELS:
        if label not in lower_text:
            reason_codes.append("MISSING_REQUIRED_FIELD")
            issues.append(f"缺少必要提案字段: {label}")
            break

    insight_lines = [line for line in combined_text.splitlines() if "consumer insight" in line.lower()]
    if not insight_lines or all(field_is_tbd(line) for line in insight_lines):
        reason_codes.append("WEAK_OR_MISSING_INSIGHT")
        issues.append("consumer insight 缺失、过薄或仍是 TBD。")
    feature_lines = [line for line in combined_text.splitlines() if "feature to benefit" in line.lower()]
    if not feature_lines or all(field_is_tbd(line) for line in feature_lines):
        reason_codes.append("NO_PRODUCT_TO_BENEFIT")
        issues.append("缺少产品功能到传播利益的明确翻译。")

    if len(direction_rows) < 2:
        reason_codes.append("TOO_FEW_DIRECTIONS")
        issues.append("创意方向少于 2 条。")
    else:
        signatures = {
            re.sub(
                r"\s+",
                " ",
                " ".join(
                    row.get(field, "").strip().lower()
                    for field in ["strategy_path", "creative_proposition", "core_message", "key_visual_or_action"]
                ),
            )
            for row in direction_rows
        }
        if len(signatures) < len(direction_rows):
            reason_codes.append("UNDIFFERENTIATED_DIRECTIONS")
            issues.append("创意方向之间不可区分，strategy/proposition/message/action 过度重复。")
    if direction_rows and all(field_is_tbd(row.get("key_visual_or_action", "")) for row in direction_rows):
        reason_codes.append("NO_KEY_VISUAL_OR_ACTION")
        issues.append("所有方向都缺少 key visual/actionable execution。")
    if direction_rows and all(field_is_tbd(row.get("why_choose", "")) for row in direction_rows):
        reason_codes.append("NO_CLIENT_CHOICE_RATIONALE")
        issues.append("所有方向都缺少客户选择理由。")
    if direction_rows and any(field_is_tbd(row.get("creative_proposition", "")) for row in direction_rows):
        reason_codes.append("THIN_CREATIVE_PROPOSITION")
        issues.append("至少一条方向的 creative proposition 仍是 TBD。")

    generic_hits = sorted({match.group(0) for match in GENERIC_CREATIVE_PATTERN.finditer(combined_text)})
    if generic_hits:
        reason_codes.append("GENERIC_AI_CLICHE")
        issues.append("提案含泛化口号/AI cliche: " + ", ".join(generic_hits[:8]))

    unsupported_claims = [
        compact_evidence(line, 120)
        for line in combined_text.splitlines()
        if CASE_CLAIM_PATTERN.search(line) and not has_supported_case_claim(line)
    ]
    if unsupported_claims:
        reason_codes.append("UNSUPPORTED_REFERENCE_OR_CASE_CLAIM")
        issues.extend(f"未追溯案例/参考/数据声明: {line}" for line in unsupported_claims[:6])

    client_paths = client_facing_scan_paths(project, files)
    client_texts: list[tuple[Path, str]] = []
    for path in client_paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        client_texts.append((path, text))
        risky = sorted({match.group(0) for match in INTERNAL_LANGUAGE_PATTERN.finditer(text)})
        if risky:
            reason_codes.append("INTERNAL_LANGUAGE_LEAK")
            issues.append(f"client-facing material contains internal language: {safe_rel(project, path)}: {', '.join(risky[:6])}")

    for code, evidence_item in collect_humanizer_writing_risks(combined_text, client_texts, project):
        reason_codes.append(code)
        issues.append(f"humanizer writing risk ({code}): {evidence_item}")

    tbd_count = len(re.findall(r"\bTBD\b|open question|待补充|暂无", combined_text, flags=re.IGNORECASE))
    if tbd_count:
        reason_codes.append("OPEN_EVIDENCE_GAPS")
        warnings.append(f"仍有 {tbd_count} 个 TBD/open question，只能作为内部草案或 PARTIAL。")

    status = "PASS" if not issues and not warnings else "PARTIAL_PASS" if not issues else "BLOCKED"
    status = enforce_adversarial_gate_policy(project, "creative", status, warnings, evidence)
    if status == "PARTIAL_PASS" and "ADVERSARIAL_COUNCIL_MISSING" not in reason_codes and any("反驳性议会" in item for item in warnings):
        reason_codes.append("ADVERSARIAL_COUNCIL_MISSING")

    report_path = project / "AD-creative/gates/GATE-AUTO-CREATIVE-QUALITY-001_report.md"
    issue_text = "\n".join(f"- {issue}" for issue in issues) or "- 无"
    warning_text = "\n".join(f"- {warning}" for warning in warnings) or "- 无"
    reason_text = "\n".join(f"- {code}" for code in sorted(set(reason_codes))) or "- NONE"
    evidence_text = "\n".join(f"- {item}" for item in evidence)
    write_text(
        report_path,
        f"""# Creative Quality Gate

status: {status}
visibility: internal_only
checked_at: {now_iso()}

## Reason Codes

{reason_text}

## Evidence

{evidence_text}

## Blocking Issues

{issue_text}

## Warnings

{warning_text}

## Rules

- Gate checks proposal traceability and completeness, not subjective taste.
- PASS/PARTIAL_PASS/BLOCKED are reason-code based; score alone is never approval.
- Missing facts stay as TBD/open questions and prevent client-ready claims.
- Blocks empty skeletons, generic slogans, weak insight, undifferentiated directions, missing feature-to-benefit, missing key visual/action, missing why-choose, unsupported case/reference claims, internal language leaks, and humanizer writing risks.
- `VALIDATION=PASS` is structural only and never replaces this creative-quality-gate.
""",
    )
    update_artifact(
        project,
        "ART-AUTO-CREATIVE-QUALITY-GATE",
        "creative_quality_gate_report",
        safe_rel(project, report_path),
        "creative",
        status="done" if status != "BLOCKED" else "blocked",
        visibility="internal_only",
        gate_status=status,
    )
    checked_artifacts = ";".join([artifact_id for artifact_id, _, _ in CREATIVE_PROPOSAL_ARTIFACTS] + ["ART-AUTO-CREATIVE-QUALITY-GATE"])
    append_gate(
        project,
        "GATE-AUTO-CREATIVE-QUALITY-001",
        "creative",
        status,
        "90" if status == "PASS" else "65" if status == "PARTIAL_PASS" else "30",
        checked_artifacts,
        ";".join(sorted(set(reason_codes))) if issues else "",
        ";".join(warnings[:8]) or ("修正创意提案后重跑 creative-quality-gate。" if issues else ""),
        "",
        "ready_for_internal_ppt" if status == "PASS" else "resolve_creative_gaps" if status == "PARTIAL_PASS" else "revise_creative_proposal",
        "ad_creative_operator",
    )
    append_event(
        project,
        {
            "event_id": "EVT-AUTO-CREATIVE-QUALITY-GATE",
            "event_type": "creative_quality_gate_run",
            "created_at": now_iso(),
            "status": status,
            "reason_codes": sorted(set(reason_codes)),
            "issues": issues[:12],
            "warnings": warnings[:12],
        },
    )
    return status, issues + warnings, report_path


def review_reference_pack(project: Path, *, live_check: bool = False) -> tuple[str, list[str], Path]:
    _, refs = read_csv_rows(project / "AD-creative/references/reference_cards.csv")
    issues: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = [f"references={len(refs)}", f"live_check={live_check}"]

    if not refs:
        issues.append("参考包为空。")

    for ref in refs:
        ref_id = ref.get("reference_id", "")
        url = ref.get("url", "").strip()
        title = ref.get("title", "").strip()
        source_owner = ref.get("source_owner", "").strip().lower()
        role = ref.get("role", "").strip()
        why_relevant = ref.get("why_relevant", "").strip()
        borrow = ref.get("borrow", "").strip()
        do_not_copy = ref.get("do_not_copy", "").strip()
        client_visible = ref.get("client_visible", "").strip().lower() == "true"

        if not title:
            warnings.append(f"{ref_id} 缺少标题。")
        if not role:
            warnings.append(f"{ref_id} 缺少 role。")
        if not why_relevant:
            warnings.append(f"{ref_id} 缺少 why_relevant。")
        if not borrow:
            warnings.append(f"{ref_id} 缺少 borrow。")
        if not do_not_copy:
            message = f"{ref_id} 缺少 do_not_copy。"
            if client_visible:
                issues.append(message)
            else:
                warnings.append(message)
        if not source_owner or source_owner == "unknown":
            message = f"{ref_id} 来源归属未明确。"
            if client_visible:
                issues.append(message)
            else:
                warnings.append(message)

        if url == "TBD" or not url:
            message = f"{ref_id} 尚未登记真实 https URL。"
            if client_visible:
                issues.append(message)
            else:
                warnings.append(message)
            continue

        if not url.startswith("https://"):
            message = f"{ref_id} 不是 https URL。"
            if client_visible:
                issues.append(message)
            else:
                warnings.append(message)
            continue

        if live_check:
            ok, note = check_url(url)
            evidence.append(f"{ref_id}_live={note}")
            if not ok:
                message = f"{ref_id} live check failed: {note}"
                if client_visible:
                    issues.append(message)
                else:
                    warnings.append(message)

        if client_visible and source_owner in {"research", "ugc", "unknown"}:
            issues.append(f"{ref_id} 客户可见但 source_owner={source_owner}。")

    status = "PASS" if not issues and not warnings else "PARTIAL_PASS" if not issues else "BLOCKED"
    status = enforce_adversarial_gate_policy(
        project, "reference_research", status, warnings, evidence
    )
    report_path = project / "AD-creative/gates/GATE-AUTO-REFERENCE-PACK-001_report.md"
    issue_text = "\n".join(f"- {issue}" for issue in issues) or "- 无"
    warning_text = "\n".join(f"- {warning}" for warning in warnings) or "- 无"
    evidence_text = "\n".join(f"- {item}" for item in evidence)
    write_text(
        report_path,
        f"""# Reference Pack Gate

status: {status}
visibility: internal_only
checked_at: {now_iso()}

## Evidence

{evidence_text}

## Blocking Issues

{issue_text}

## Warnings

{warning_text}

## Rules

- 客户可见参考必须是真实 https URL。
- 客户可见参考必须说明 source_owner、role、why_relevant、borrow、do_not_copy。
- `TBD` 只能作为内部搜索计划，不能进入客户稿引用。
- UGC / research / unknown 不能冒充官方证据。
""",
    )
    update_artifact(
        project,
        "ART-AUTO-REFERENCE-PACK-GATE",
        "reference_pack_gate_report",
        safe_rel(project, report_path),
        "reference_research",
        status="done" if status != "BLOCKED" else "blocked",
        visibility="internal_only",
        linked_references=";".join(ref.get("reference_id", "") for ref in refs if ref.get("reference_id")),
        gate_status=status,
    )
    append_gate(
        project,
        "GATE-AUTO-REFERENCE-PACK-001",
        "reference_research",
        status,
        "90" if status == "PASS" else "65" if status == "PARTIAL_PASS" else "35",
        "ART-AUTO-REFERENCE-PACK-GATE",
        ";".join(issues[:8]),
        ";".join(warnings[:8]) or "补充真实公开参考后重跑 reference-pack-gate。",
        "",
        "ready_for_internal_creative" if status != "BLOCKED" else "fix_reference_pack",
        "ad_creative_operator",
    )
    append_event(
        project,
        {
            "event_id": "EVT-AUTO-REFERENCE-PACK-GATE",
            "event_type": "reference_pack_gate_run",
            "created_at": now_iso(),
            "status": status,
            "issues": issues[:12],
            "warnings": warnings[:12],
        },
    )
    return status, issues + warnings, report_path


def search_plan_files(project: Path, artifacts: list[dict[str, str]]) -> list[Path]:
    paths: list[Path] = []
    for artifact in artifacts:
        artifact_type = artifact.get("artifact_type", "").lower()
        rel_path = artifact.get("path", "").strip()
        if artifact_type == "search_plan" and rel_path:
            paths.append(project / rel_path)
    ref_dir = project / "AD-creative/references"
    if ref_dir.exists():
        paths.extend(sorted(ref_dir.glob("*search_plan*.md")))
    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(path)
    return deduped


def review_search_quality(project: Path) -> tuple[str, list[str], Path]:
    _, artifacts = read_csv_rows(project / "AD-creative/orchestrator/artifact_index.csv")
    _, refs = read_csv_rows(project / "AD-creative/references/reference_cards.csv")
    plans = search_plan_files(project, artifacts)
    issues: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = [f"search_plans={len(plans)}", f"references={len(refs)}"]

    if not plans:
        warnings.append("未找到 search_plan / official_search_plan。")

    for plan in plans:
        rel_plan = safe_rel(project, plan)
        if not plan.exists():
            issues.append(f"搜索计划文件不存在: {rel_plan}")
            continue
        text = plan.read_text(encoding="utf-8", errors="ignore")
        lowered = text.lower()
        evidence.append(f"plan={rel_plan}")
        if "why search" not in lowered and "为什么" not in text and "why" not in lowered:
            warnings.append(f"{rel_plan} 缺少搜索原因。")
        if (
            "search scope" not in lowered
            and "suggested platforms" not in lowered
            and "搜索范围" not in text
            and "平台" not in text
        ):
            warnings.append(f"{rel_plan} 缺少搜索范围/平台。")
        if "expected output" not in lowered and "output" not in lowered and "产出" not in text:
            warnings.append(f"{rel_plan} 缺少预期产物。")
        if "user decision needed" in lowered or "needs_user_input" in lowered or "批准" in text:
            warnings.append(f"{rel_plan} 仍需用户批准或缩小范围。")
        if "do_not_copy" not in lowered and "do not copy" not in lowered and "禁止复制" not in text:
            warnings.append(f"{rel_plan} 未明确 do_not_copy 输出。")

    search_targets = [ref for ref in refs if ref.get("role", "").strip() == "search_target"]
    if search_targets:
        evidence.append(f"search_targets={len(search_targets)}")
    for ref in search_targets:
        ref_id = ref.get("reference_id", "")
        url = ref.get("url", "").strip()
        if url == "TBD" or not url:
            warnings.append(f"{ref_id} 仍是搜索目标，尚无真实 URL。")
        if not ref.get("why_relevant", "").strip():
            warnings.append(f"{ref_id} 缺少 why_relevant。")
        if not ref.get("borrow", "").strip():
            warnings.append(f"{ref_id} 缺少 borrow。")
        if not ref.get("do_not_copy", "").strip():
            warnings.append(f"{ref_id} 缺少 do_not_copy。")
        if ref.get("client_visible", "").strip().lower() == "true":
            issues.append(f"{ref_id} 搜索目标不能标记客户可见。")

    client_visible_refs = [
        ref for ref in refs if ref.get("client_visible", "").strip().lower() == "true"
    ]
    for ref in client_visible_refs:
        url = ref.get("url", "").strip()
        ref_id = ref.get("reference_id", "")
        if not url.startswith("https://"):
            issues.append(f"{ref_id} 客户可见参考不是真实 https URL。")
        if ref.get("source_owner", "").strip().lower() in {"research", "unknown", "ugc", ""}:
            issues.append(f"{ref_id} 客户可见参考来源归属不可信。")

    status = "PASS" if not issues and not warnings else "PARTIAL_PASS" if not issues else "BLOCKED"
    status = enforce_adversarial_gate_policy(
        project, "reference_research", status, warnings, evidence
    )
    report_path = project / "AD-creative/gates/GATE-AUTO-SEARCH-QUALITY-001_report.md"
    issue_text = "\n".join(f"- {issue}" for issue in issues) or "- 无"
    warning_text = "\n".join(f"- {warning}" for warning in warnings) or "- 无"
    evidence_text = "\n".join(f"- {item}" for item in evidence)
    write_text(
        report_path,
        f"""# Search Quality Gate

status: {status}
visibility: internal_only
checked_at: {now_iso()}

## Evidence

{evidence_text}

## Blocking Issues

{issue_text}

## Warnings

{warning_text}

## Rules

- 搜索计划必须说明 why / scope / platform / expected output / do_not_copy。
- `NEEDS_USER_INPUT` 或 `TBD` 只能内部推进，不能当成客户可见参考。
- role=search_target 的参考不能标记客户可见。
- 客户可见参考必须是真实 https URL 且来源归属可信。
""",
    )
    update_artifact(
        project,
        "ART-AUTO-SEARCH-QUALITY-GATE",
        "search_quality_gate_report",
        safe_rel(project, report_path),
        "reference_research",
        status="done" if status != "BLOCKED" else "blocked",
        visibility="internal_only",
        linked_references=";".join(ref.get("reference_id", "") for ref in refs if ref.get("reference_id")),
        gate_status=status,
    )
    append_gate(
        project,
        "GATE-AUTO-SEARCH-QUALITY-001",
        "reference_research",
        status,
        "90" if status == "PASS" else "65" if status == "PARTIAL_PASS" else "35",
        "ART-AUTO-SEARCH-QUALITY-GATE",
        ";".join(issues[:8]),
        ";".join(warnings[:8]) or "补齐搜索计划和真实参考后重跑 search-quality-gate。",
        "",
        "ready_for_reference_pack" if status != "BLOCKED" else "fix_search_quality",
        "ad_creative_operator",
    )
    append_event(
        project,
        {
            "event_id": "EVT-AUTO-SEARCH-QUALITY-GATE",
            "event_type": "search_quality_gate_run",
            "created_at": now_iso(),
            "status": status,
            "issues": issues[:12],
            "warnings": warnings[:12],
        },
    )
    return status, issues + warnings, report_path


def add_visual_asset(
    project: Path,
    file_path: Path,
    slot_id: str,
    requirement_id: str,
    reference_id: str,
    asset_type: str,
    visibility: str,
    qa_status: str,
    risk_level: str,
    prompt_or_edit_ref: str,
    notes: str,
    selected: bool,
) -> tuple[str, Path]:
    if not file_path.exists():
        raise FileNotFoundError(f"asset not found: {file_path}")
    target_dir = project / ("AD-creative/visual_assets/selected" if selected else "AD-creative/visual_assets/raw")
    target_dir.mkdir(parents=True, exist_ok=True)
    fields, assets = read_csv_rows(project / "AD-creative/visual_assets/asset_manifest.csv")
    if not fields:
        raise FileNotFoundError("asset_manifest.csv header not found")
    asset_id = next_id(assets, "asset_id", "IMG")
    suffix = file_path.suffix.lower() or ".bin"
    target = target_dir / f"{asset_id}{suffix}"
    shutil.copy2(file_path, target)
    image_note = ""
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        try:
            from PIL import Image

            with Image.open(target) as image:
                image_note = f"{image.width}x{image.height}"
        except Exception as exc:  # noqa: BLE001 - non-fatal QA evidence
            image_note = f"image_probe_failed={exc}"
    status = "selected" if selected else "registered"
    assets.append(
        {
            "asset_id": asset_id,
            "slot_id": slot_id,
            "requirement_id": requirement_id,
            "reference_id": reference_id,
            "path": safe_rel(project, target),
            "asset_type": asset_type,
            "stage": "visual_review",
            "version": "v001",
            "status": status,
            "visibility": visibility,
            "qa_status": qa_status,
            "risk_level": risk_level,
            "prompt_or_edit_ref": prompt_or_edit_ref,
            "notes": "; ".join(item for item in [notes, image_note] if item),
        }
    )
    write_csv_rows(project / "AD-creative/visual_assets/asset_manifest.csv", fields, assets)
    review_path = project / "AD-creative/visual_review/review_matrix.csv"
    review_fields, review_rows = read_csv_rows(review_path)
    if review_fields:
        review_rows.append(
            {
                "review_id": next_id(review_rows, "review_id", "VR"),
                "asset_id": asset_id,
                "slot_id": slot_id,
                "direction": "registered_asset",
                "check_type": "file_traceability",
                "result": qa_status,
                "score": "88" if qa_status.upper() == "PASS" else "60",
                "issue": "" if qa_status.upper() == "PASS" else "需要人工视觉筛选。",
                "action": "可用于内部排版；客户可见前再跑最终 Gate。",
                "reviewer": "ad_creative_operator",
                "created_at": now_iso(),
            }
        )
        write_csv_rows(review_path, review_fields, review_rows)
    update_artifact(
        project,
        f"ART-{asset_id}",
        "visual_asset",
        safe_rel(project, target),
        "visual_review",
        status=status,
        visibility=visibility,
        linked_requirements=requirement_id,
        linked_references="" if reference_id == "pending" else reference_id,
        linked_assets=asset_id,
        gate_status=qa_status,
    )
    append_gate(
        project,
        "GATE-AUTO-VISUAL-ASSET-001",
        "visual_review",
        "PASS" if qa_status.upper() == "PASS" else "PARTIAL_PASS",
        "88" if qa_status.upper() == "PASS" else "60",
        f"ART-{asset_id}",
        "" if qa_status.upper() == "PASS" else "图片尚需人工筛选。",
        "客户可见前确认 AI / 版权 / 品牌资产边界。",
        "",
        "ready_for_internal_ppt" if qa_status.upper() == "PASS" else "visual_review_needed",
        "ad_creative_operator",
    )
    append_event(
        project,
        {
            "event_id": f"EVT-{asset_id}",
            "event_type": "visual_asset_registered",
            "created_at": now_iso(),
            "asset_id": asset_id,
            "path": safe_rel(project, target),
            "qa_status": qa_status,
        },
    )
    return asset_id, target


def probe_image(path: Path) -> tuple[int, int, str]:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return image.width, image.height, image.format or path.suffix.lower().strip(".")
    except Exception as exc:  # noqa: BLE001 - gate report should carry the concrete probe failure
        return 0, 0, f"probe_failed={exc}"


def review_visual_quality(
    project: Path,
    *,
    min_long_edge: int = 720,
    min_short_edge: int = 480,
) -> tuple[str, list[str], Path]:
    _, assets = read_csv_rows(project / "AD-creative/visual_assets/asset_manifest.csv")
    _, references = read_csv_rows(project / "AD-creative/references/reference_cards.csv")
    reference_ids = unique_rows(references, "reference_id")
    issues: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = [
        f"assets={len(assets)}",
        f"min_long_edge={min_long_edge}",
        f"min_short_edge={min_short_edge}",
    ]

    if not assets:
        warnings.append("尚未登记视觉资产。")

    for asset in assets:
        asset_id = asset.get("asset_id", "").strip()
        status = asset.get("status", "").strip().lower()
        visibility = asset.get("visibility", "").strip().lower()
        qa_status = asset.get("qa_status", "").strip().upper()
        risk_level = asset.get("risk_level", "").strip().lower()
        asset_type = asset.get("asset_type", "").strip().lower()
        rel_path = asset.get("path", "").strip()
        prompt_ref = asset.get("prompt_or_edit_ref", "").strip()
        reference_id = asset.get("reference_id", "").strip()
        notes = asset.get("notes", "").strip()
        notes_lower = notes.lower()
        active = status in ACTIVE_ASSET_STATUSES and qa_status != "NOT_RUN"
        selected = status in SELECTED_ASSET_STATUSES
        client_visible = visibility in CLIENT_VISIBLE_VALUES

        if not asset_id:
            issues.append("asset_manifest 存在空 asset_id。")
            continue
        if not asset.get("slot_id", "").strip():
            issues.append(f"{asset_id} 缺少 slot_id。")
        if not asset.get("requirement_id", "").strip():
            warnings.append(f"{asset_id} 缺少 requirement_id。")
        if asset_type == "generated_image" and not prompt_ref:
            issues.append(f"{asset_id} 是生成图但缺少 prompt_or_edit_ref。")
        if prompt_ref and not (project / prompt_ref).exists() and not Path(prompt_ref).is_absolute():
            warnings.append(f"{asset_id} prompt_or_edit_ref 未在项目中找到: {prompt_ref}")
        if reference_id and reference_id != "pending" and reference_id not in reference_ids:
            issues.append(f"{asset_id} reference_id 未登记: {reference_id}")
        if selected and qa_status != "PASS":
            issues.append(f"{asset_id} 已选中但 QA 不是 PASS。")
        if selected and risk_level == "high":
            warnings.append(f"{asset_id} 已选中但 risk_level=high。")
        if client_visible:
            if qa_status != "PASS":
                issues.append(f"{asset_id} 客户可见但 QA 未 PASS。")
            if not selected:
                issues.append(f"{asset_id} 客户可见但未进入 selected/approved/done。")
            if asset_type == "generated_image" and "client_visibility_approved" not in notes_lower:
                issues.append(f"{asset_id} 客户可见生成图缺少 client_visibility_approved 记录。")
            if reference_id in {"", "pending"}:
                warnings.append(f"{asset_id} 客户可见但未绑定真实 reference_id。")
        if client_visible:
            risk_match = VISUAL_RISK_PATTERN.search(notes_lower)
            if risk_match:
                issues.append(f"{asset_id} 客户可见图片 notes 含风险词: {risk_match.group(0)}")

        if active:
            if not rel_path:
                issues.append(f"{asset_id} active asset 缺少 path。")
                continue
            path = project / rel_path
            if not path.exists():
                issues.append(f"{asset_id} 文件不存在: {rel_path}")
                continue
            if path.suffix.lower() not in GENERATED_IMAGE_SUFFIXES:
                warnings.append(f"{asset_id} 不是常见图片格式: {path.suffix}")
                continue
            width, height, image_format = probe_image(path)
            evidence.append(f"{asset_id}={width}x{height} {image_format}")
            if not width or not height:
                issues.append(f"{asset_id} 图片无法读取: {image_format}")
                continue
            if max(width, height) < min_long_edge or min(width, height) < min_short_edge:
                issues.append(f"{asset_id} 尺寸过低: {width}x{height}")

    status = "PASS" if not issues and not warnings else "PARTIAL_PASS" if not issues else "BLOCKED"
    status = enforce_adversarial_gate_policy(
        project, "visual_review", status, warnings, evidence
    )
    report_path = project / "AD-creative/gates/GATE-AUTO-VISUAL-QUALITY-001_report.md"
    issue_text = "\n".join(f"- {issue}" for issue in issues) or "- 无"
    warning_text = "\n".join(f"- {warning}" for warning in warnings) or "- 无"
    evidence_text = "\n".join(f"- {item}" for item in evidence)
    write_text(
        report_path,
        f"""# Visual Quality Gate

status: {status}
visibility: internal_only
checked_at: {now_iso()}

## Evidence

{evidence_text}

## Blocking Issues

{issue_text}

## Warnings

{warning_text}

## Rules

- active 图片必须存在且可读取。
- selected / approved / done 图片必须 QA PASS。
- 生成图必须有 prompt_or_edit_ref。
- 客户可见生成图必须记录 `client_visibility_approved`。
- 客户可见图片不能是 contact sheet、低质拼贴、placeholder-only、假 logo。
- 默认最低尺寸：长边 {min_long_edge}px，短边 {min_short_edge}px。
""",
    )
    update_artifact(
        project,
        "ART-AUTO-VISUAL-QUALITY-GATE",
        "visual_quality_gate_report",
        safe_rel(project, report_path),
        "visual_review",
        status="done" if status != "BLOCKED" else "blocked",
        visibility="internal_only",
        linked_assets=";".join(asset.get("asset_id", "") for asset in assets if asset.get("asset_id")),
        gate_status=status,
    )
    append_gate(
        project,
        "GATE-AUTO-VISUAL-QUALITY-001",
        "visual_review",
        status,
        "90" if status == "PASS" else "65" if status == "PARTIAL_PASS" else "35",
        "ART-AUTO-VISUAL-QUALITY-GATE",
        ";".join(issues[:8]),
        ";".join(warnings[:8]) or "修正视觉资产后重跑 visual-quality-gate。",
        "",
        "ready_for_internal_ppt" if status != "BLOCKED" else "fix_visual_assets",
        "ad_creative_operator",
    )
    append_event(
        project,
        {
            "event_id": "EVT-AUTO-VISUAL-QUALITY-GATE",
            "event_type": "visual_quality_gate_run",
            "created_at": now_iso(),
            "status": status,
            "issues": issues[:12],
            "warnings": warnings[:12],
        },
    )
    return status, issues + warnings, report_path


def review_film_quality(project: Path) -> tuple[str, list[str], Path]:
    counts = read_counts(project)
    _, requirements = read_csv_rows(project / "AD-creative/orchestrator/requirements.csv")
    _, references = read_csv_rows(project / "AD-creative/references/reference_cards.csv")
    _, assets = read_csv_rows(project / "AD-creative/visual_assets/asset_manifest.csv")
    _, artifacts = read_csv_rows(project / "AD-creative/orchestrator/artifact_index.csv")
    issues: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = [
        f"requirements={counts['requirements']}",
        f"references={counts['references']}",
        f"assets={counts['assets']}",
        f"artifacts={counts['artifacts']}",
    ]

    creative_path = project / "AD-creative/creative/creative_directions.md"
    proposal_path = project / "AD-creative/proposal_architecture/proposal_structure.md"
    treatment_path = project / "AD-creative/film/treatment_packet.md"
    shot_plan_path = project / "AD-creative/film/shot_list_storyboard_plan.md"
    constraints_path = project / "AD-creative/film/production_constraints.md"

    if not requirements:
        issues.append("缺少 requirements，影视/商业判断没有客户事实基线。")
    if not references:
        warnings.append("缺少 reference pack，影视调性和拍法证据不足。")
    if not assets:
        warnings.append("缺少 visual asset，关键画面和资产锁未验证。")
    for label, path in [
        ("creative_directions", creative_path),
        ("proposal_structure", proposal_path),
        ("treatment_packet", treatment_path),
        ("shot_list_storyboard_plan", shot_plan_path),
        ("production_constraints", constraints_path),
    ]:
        if path.exists():
            evidence.append(f"{label}={safe_rel(project, path)}")
        else:
            warnings.append(f"缺少 {safe_rel(project, path)}。")

    visual_gate = latest_gate(project, gate_id="GATE-AUTO-VISUAL-QUALITY-001")
    if not visual_gate:
        warnings.append("尚未运行 Visual Quality Gate。")
    elif visual_gate.get("status") == "BLOCKED":
        issues.append("Visual Quality Gate 为 BLOCKED，不能进入影视级客户审阅。")
    else:
        evidence.append(f"visual_quality_gate={visual_gate.get('status')}")

    client_visible_generated = [
        asset.get("asset_id", "")
        for asset in assets
        if asset.get("visibility", "").strip().lower() in CLIENT_VISIBLE_VALUES
        and asset.get("asset_type", "").strip().lower() == "generated_image"
        and "client_visibility_approved" not in asset.get("notes", "").lower()
    ]
    if client_visible_generated:
        issues.append("客户可见生成图缺少批准记录: " + ";".join(client_visible_generated))

    client_visible_artifacts = [
        artifact.get("artifact_id", "")
        for artifact in artifacts
        if artifact.get("visibility", "").strip().lower() in CLIENT_VISIBLE_VALUES
        and artifact.get("gate_status", "").strip().lower() not in PASS_GATE_VALUES
    ]
    if client_visible_artifacts:
        issues.append("客户可见产物 Gate 未 PASS: " + ";".join(client_visible_artifacts))

    commercial_requirements = [
        row for row in requirements
        if row.get("category", "").strip().lower() in {"delivery", "creative", "visual", "research"}
    ]
    if commercial_requirements:
        evidence.append(f"commercial_requirement_rows={len(commercial_requirements)}")
    else:
        warnings.append("未识别到 delivery/creative/visual/research 类商业需求。")

    status = "PASS" if not issues and not warnings else "PARTIAL_PASS" if not issues else "BLOCKED"
    status = enforce_adversarial_gate_policy(
        project, "film_quality", status, warnings, evidence
    )
    report_path = project / "AD-creative/gates/GATE-AUTO-FILM-QUALITY-001_report.md"
    issue_text = "\n".join(f"- {issue}" for issue in issues) or "- 无"
    warning_text = "\n".join(f"- {warning}" for warning in warnings) or "- 无"
    evidence_text = "\n".join(f"- {item}" for item in evidence)
    write_text(
        report_path,
        f"""# Film / Commercial Quality Gate

status: {status}
visibility: internal_only
checked_at: {now_iso()}

## Evidence

{evidence_text}

## Blocking Issues

{issue_text}

## Warnings

{warning_text}

## Review Dimensions

- cinematic_clarity: treatment / shot list / key-frame logic can explain the film idea.
- commercial_message: client value, product role, and campaign output are traceable to requirements.
- brand_fit: visual direction and references do not invent unsupported brand facts.
- product_truth: product, packaging, logo, and claims are not faked.
- production_feasibility: production constraints and known blockers are visible.
- client_risk: client-visible generated assets and artifacts remain gated.
""",
    )
    update_artifact(
        project,
        "ART-AUTO-FILM-QUALITY-GATE",
        "film_quality_gate_report",
        safe_rel(project, report_path),
        "film_quality",
        status="done" if status != "BLOCKED" else "blocked",
        visibility="internal_only",
        linked_assets=";".join(asset.get("asset_id", "") for asset in assets if asset.get("asset_id")),
        gate_status=status,
    )
    append_gate(
        project,
        "GATE-AUTO-FILM-QUALITY-001",
        "film_quality",
        status,
        "90" if status == "PASS" else "68" if status == "PARTIAL_PASS" else "35",
        "ART-AUTO-FILM-QUALITY-GATE",
        ";".join(issues[:8]),
        ";".join(warnings[:8]) or "补齐 treatment / shot list / production constraints 后复核。",
        "",
        "ready_for_client_pack_gate" if status != "BLOCKED" else "fix_film_quality",
        "ad_creative_operator",
    )
    append_event(
        project,
        {
            "event_id": "EVT-AUTO-FILM-QUALITY-GATE",
            "event_type": "film_quality_gate_run",
            "created_at": now_iso(),
            "status": status,
            "issues": issues[:12],
            "warnings": warnings[:12],
        },
    )
    return status, issues + warnings, report_path


def latest_generated_image(root: Path) -> Path:
    if not root.exists():
        raise FileNotFoundError(f"generated_images root not found: {root}")
    candidates = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in GENERATED_IMAGE_SUFFIXES
    ]
    if not candidates:
        raise FileNotFoundError(f"no generated image found under: {root}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def resolve_imagegen_source(raw_file: str) -> tuple[Path, Path]:
    root = codex_generated_images_root().resolve()
    source = Path(raw_file).expanduser().resolve() if raw_file else latest_generated_image(root)
    if source.suffix.lower() not in GENERATED_IMAGE_SUFFIXES:
        raise ValueError(f"unsupported generated image suffix: {source.suffix}")
    if not source.is_file():
        raise FileNotFoundError(f"generated image not found: {source}")
    try:
        source.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"source must be under {root}: {source}") from exc
    return source, root


def default_prompt_ref(project: Path) -> str:
    for rel_path in [
        "AD-creative/image_jobs/image_prompt_pack.json",
        "AD-creative/image_jobs/image_generation_policy.md",
        "AD-creative/image_jobs/image_job_spec_template.md",
    ]:
        if (project / rel_path).exists():
            return rel_path
    return ""


def md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def append_imagegen_import_log(
    project: Path,
    source_root: Path,
    source: Path,
    asset_id: str,
    target: Path,
    prompt_ref: str,
    qa_status: str,
    notes: str,
) -> Path:
    path = project / "AD-creative/image_jobs/imagegen_import_log.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    should_write_header = not path.exists()
    with path.open("a", encoding="utf-8") as handle:
        if should_write_header:
            handle.write(
                "# ImageGen Import Log\n\n"
                "visibility: internal_only\n\n"
                "| imported_at | asset_id | source | target | prompt_ref | qa_status | notes |\n"
                "| --- | --- | --- | --- | --- | --- | --- |\n"
            )
        handle.write(
            "| {imported_at} | {asset_id} | {source} | {target} | {prompt_ref} | {qa_status} | {notes} |\n".format(
                imported_at=now_iso(),
                asset_id=md_cell(asset_id),
                source=md_cell(safe_rel_to(source_root, source)),
                target=md_cell(safe_rel(project, target)),
                prompt_ref=md_cell(prompt_ref),
                qa_status=md_cell(qa_status),
                notes=md_cell(notes),
            )
        )

    status = "PASS" if qa_status.upper() == "PASS" else "PARTIAL_PASS"
    update_artifact(
        project,
        "ART-AUTO-IMAGEGEN-IMPORT",
        "imagegen_import_log",
        safe_rel(project, path),
        "visual_review",
        status="done",
        visibility="internal_only",
        linked_assets=asset_id,
        gate_status=status,
    )
    append_event(
        project,
        {
            "event_id": f"EVT-IMAGEGEN-IMPORT-{asset_id}",
            "event_type": "imagegen_asset_imported",
            "created_at": now_iso(),
            "asset_id": asset_id,
            "source": safe_rel_to(source_root, source),
            "target": safe_rel(project, target),
            "qa_status": qa_status,
        },
    )
    return path


def perform_intake(project: Path, source_ids: list[str], goal: str) -> dict[str, int]:
    source_path = project / "AD-creative/orchestrator/source_events.csv"
    _, source_rows = read_csv_rows(source_path)
    source_id_set = set(source_ids)
    target_sources = [
        row for row in source_rows if not source_id_set or row.get("source_event_id") in source_id_set
    ]
    materials: list[tuple[Path, str]] = []
    source_by_file: dict[Path, str] = {}
    for source in target_sources:
        raw_path = source.get("file_paths", "")
        path = Path(raw_path)
        if not path.is_absolute():
            path = project / raw_path
        for file_path in material_files(path):
            materials.append((file_path, read_material_text(file_path)))
            source_by_file[file_path] = source.get("source_event_id", "")

    requirement_path = project / "AD-creative/orchestrator/requirements.csv"
    req_fields, requirement_rows = read_csv_rows(requirement_path)
    existing_statements = unique_rows(requirement_rows, "statement")
    requirement_statements = extract_requirement_statements(materials)
    new_requirements: list[dict[str, str]] = []
    allocate_req_id = id_allocator(requirement_rows, "requirement_id", "REQ")
    for file_path, statement in requirement_statements:
        if statement in existing_statements:
            continue
        req_id = allocate_req_id()
        req_type, priority, affected_stage = classify_requirement(statement)
        row = {
            "requirement_id": req_id,
            "source_event_id": source_by_file.get(file_path, source_ids[0] if source_ids else ""),
            "owner": owner_for_statement(statement),
            "statement": statement,
            "requirement_type": req_type,
            "priority": priority,
            "status": "extracted",
            "confidence": "0.72",
            "scope": "project",
            "affected_stage": affected_stage,
            "linked_artifacts": "",
            "supersedes_requirement_id": "",
            "open_questions": "",
        }
        new_requirements.append(row)
        existing_statements.add(statement)
    if new_requirements:
        requirement_rows.extend(new_requirements)
        write_csv_rows(requirement_path, req_fields, requirement_rows)

    all_text = "\n".join(text for _, text in materials)
    gap_path = project / "AD-creative/orchestrator/gaps.csv"
    gap_fields, gap_rows = read_csv_rows(gap_path)
    existing_descriptions = unique_rows(gap_rows, "description")
    new_gaps: list[dict[str, str]] = []
    allocate_gap_id = id_allocator(gap_rows, "gap_id", "GAP")
    for template in gap_templates(requirement_rows, all_text):
        if template["description"] in existing_descriptions:
            continue
        gap_id = allocate_gap_id()
        new_gaps.append(
            {
                "gap_id": gap_id,
                "linked_requirement_id": template.get("linked_requirement_id", ""),
                "impact": template.get("impact", "medium"),
                "status": "open",
                "description": template["description"],
                "recommended_action": template["recommended_action"],
                "owner": "client" if template.get("question_for_client") else "operator",
                "question_for_user": "",
                "question_for_client": template.get("question_for_client", ""),
                "question_for_director": "",
            }
        )
        existing_descriptions.add(template["description"])
    if new_gaps:
        gap_rows.extend(new_gaps)
        write_csv_rows(gap_path, gap_fields, gap_rows)

    linked_req_ids = ";".join(row["requirement_id"] for row in new_requirements) or ";".join(
        row.get("requirement_id", "") for row in requirement_rows[:8]
    )
    linked_source_ids = ";".join(source_ids) if source_ids else ";".join(
        row.get("source_event_id", "") for row in target_sources
    )
    current_truth_path = project / "AD-creative/orchestrator/current_truth.md"
    confirmed = "\n".join(f"- {row['statement']}" for row in requirement_rows[:12]) or "- 暂无已抽取需求"
    open_questions = "\n".join(
        f"- {row.get('question_for_client') or row.get('description')}" for row in gap_rows[:8]
    ) or "- 暂无"
    write_text(
        current_truth_path,
        f"""# Current Truth

## Project
{project.name}

## Confirmed
{confirmed}

## Inferred
- 当前处于 intake；已从本地资料抽取第一轮需求和缺口。
- 客户可见稿前需要 Gate；AI 图默认 internal_only。

## Conflicted
- 暂无自动识别冲突。

## Deprecated
- 暂无。

## Open Questions
{open_questions}

## Current Stage
intake

## Next Action
按缺口向客户/内部负责人追问；三方议会 PASS 后可推进公开官方来源搜索计划。
""",
    )

    question_rows = "\n".join(
        f"| {row['gap_id']} | {row.get('question_for_client') or row['description']} | {row['recommended_action']} | {row['impact']} | 客户补充 / 先内部推进 |"
        for row in gap_rows[:8]
    )
    if not question_rows:
        question_rows = "| - | 暂无 | - | - | - |"
    write_text(
        project / "AD-creative/handoff/客户追问话术.md",
        f"""# 客户追问话术

## 建议询问
| ID | 问题 | 推荐动作 | 影响 | 可选动作 |
|---|---|---|---|---|
{question_rows}

## 可复制话术
我们已先把资料整理成需求和缺口。为避免误判，请补充品牌资产、产品高清图/包装规范、参考片边界、AI 图是否可用于客户审阅，以及本轮希望看到的方案精度。
""",
    )

    work_path = project / "AD-creative/orchestrator/work_items.csv"
    work_fields, work_rows = read_csv_rows(work_path)
    intake_work_id = "WORK-001"
    for row in work_rows:
        if row.get("stage") == "intake" and row.get("title") == "需求整理与缺口判断":
            intake_work_id = row.get("work_id", intake_work_id) or intake_work_id
            break

    artifact_path = project / "AD-creative/orchestrator/artifact_index.csv"
    now = now_iso()
    for artifact_id, artifact_type, rel_path, gate_status in [
        ("ART-AUTO-CURRENT-TRUTH", "intake_report", "AD-creative/orchestrator/current_truth.md", "PARTIAL_PASS"),
        ("ART-AUTO-CLIENT-QUESTIONS", "client_questions", "AD-creative/handoff/客户追问话术.md", "PARTIAL_PASS"),
    ]:
        update_or_append_csv_row(
            artifact_path,
            "artifact_id",
            {
                "artifact_id": artifact_id,
                "artifact_type": artifact_type,
                "path": rel_path,
                "stage": "intake",
                "version": "v001",
                "status": "done",
                "visibility": "internal_only",
                "source_event_ids": linked_source_ids,
                "linked_requirements": linked_req_ids,
                "linked_work_items": intake_work_id,
                "linked_references": "",
                "linked_assets": "",
                "gate_status": gate_status,
                "supersedes_artifact_id": "",
                "created_at": now,
                "updated_at": now,
            },
        )
    if work_rows:
        for row in work_rows:
            if row.get("stage") == "intake" and row.get("title") == "需求整理与缺口判断":
                row["status"] = "done"
                row["output_artifacts"] = "ART-AUTO-CURRENT-TRUTH;ART-AUTO-CLIENT-QUESTIONS"
                row["linked_requirements"] = linked_req_ids
                row["linked_source_events"] = linked_source_ids
                row["updated_at"] = now
                break
        write_csv_rows(work_path, work_fields, work_rows)

    gate_path = project / "AD-creative/orchestrator/gate_log.csv"
    update_or_append_csv_row(
        gate_path,
        "gate_id",
        {
            "gate_id": "GATE-AUTO-BRIEF-001",
            "stage": "intake",
            "status": "PARTIAL_PASS" if gap_rows else "PASS",
            "score": "72",
            "checked_artifacts": "ART-AUTO-CURRENT-TRUTH;ART-AUTO-CLIENT-QUESTIONS",
            "blocking_issues": ";".join(row["description"] for row in gap_rows[:5]),
            "revision_items": "补齐缺口后进入 research_plan。",
            "questions": ";".join(row.get("question_for_client", "") for row in gap_rows[:5]),
            "next_state": "research_plan",
            "created_at": now,
            "owner": "ad_creative_operator",
        },
    )

    append_event(
        project,
        {
            "event_id": f"EVT-INTAKE-{now}",
            "event_type": "intake_completed",
            "created_at": now,
            "actor": "ad_creative_operator",
            "summary": f"Extracted {len(new_requirements)} requirements and {len(new_gaps)} gaps from local materials.",
        },
    )
    return {"requirements": len(new_requirements), "gaps": len(new_gaps), "materials": len(materials)}


def render_handoff(project: Path, goal: str, source_ids: list[str]) -> None:
    counts = read_counts(project)
    _, work_items = read_csv_rows(project / "AD-creative/orchestrator/work_items.csv")
    _, gap_rows = read_csv_rows(project / "AD-creative/orchestrator/gaps.csv")
    _, requirement_rows = read_csv_rows(project / "AD-creative/orchestrator/requirements.csv")
    active_work = [
        row for row in work_items if row.get("status", "").lower() not in {"done", "closed"}
    ]
    latest_work = active_work[-5:]
    latest_source_ids = ";".join(source_ids) if source_ids else "无新增资料"

    board_rows = "\n".join(
        f"| {row.get('work_id', '')} | {row.get('status', '')} | {row.get('owner_agent', '')} | {row.get('title', '')} |"
        for row in latest_work
    )
    if not board_rows:
        board_rows = "| - | - | - | 暂无工作项 |"
    blocker_rows = "\n".join(
        f"| {row.get('description', '')} | {row.get('impact', '')} | {row.get('owner', '') or 'operator'} |"
        for row in gap_rows[:5]
    )
    if not blocker_rows:
        blocker_rows = "| 暂无强阻塞 | 可继续内部整理 | - |"
    question_rows = "\n".join(
        f"| {row.get('gap_id', '')} | {row.get('question_for_client') or row.get('description', '')} | {row.get('recommended_action', '')} | {row.get('impact', '')} | 客户补充 / 先内部推进 |"
        for row in gap_rows[:8]
    )
    if not question_rows:
        question_rows = "| - | 暂无 | - | - | - |"
    confirmed_rows = "\n".join(
        f"- {row.get('statement', '')}" for row in requirement_rows[:6]
    ) or "- 暂无已抽取需求"

    write_text(
        project / "AD-creative/handoff/项目看板.md",
        f"""# 项目看板

## 当前阶段
Intake / 准备整理

## 当前结论
项目结构已初始化。资料入口、需求/缺口、验证和操作台已可用。

## 已抽取需求
{confirmed_rows}

## 数量
| 项 | 数量 |
|---|---:|
| 资料事件 | {counts['source_events']} |
| 需求 | {counts['requirements']} |
| 缺口 | {counts['gaps']} |
| 工作项 | {counts['work_items']} |
| 参考链接 | {counts['references']} |
| 图片资产 | {counts['assets']} |
| 产物 | {counts['artifacts']} |
| Gate | {counts['gates']} |

## 正在进行
| Work | 状态 | Owner | 下一步 |
|---|---|---|---|
{board_rows}

## 阻塞
| 问题 | 影响 | 需要谁确认 |
|---|---|---|
{blocker_rows}

## 最近产物
| 产物 | 状态 | 是否客户可见 |
|---|---|---|
| AD-creative/handoff/操作台.html | ready | no |
| AD-creative/gates/THREE-COUNCIL-READINESS_report.md | ready after council | no |

## 下一步
按缺口追问客户或内部负责人；三方议会 PASS 后可推进公开官方来源搜索计划。
""",
    )

    write_text(
        project / "AD-creative/handoff/待你确认.md",
        f"""# 待你确认

当前无必须立即确认的事项。

| ID | 问题 | 推荐 | 不确认的影响 | 可选动作 |
|---|---|---|---|---|
{question_rows}
""",
    )

    write_text(
        project / "AD-creative/handoff/客户追问话术.md",
        f"""# 客户追问话术

## 建议询问
| ID | 问题 | 推荐动作 | 影响 | 可选动作 |
|---|---|---|---|---|
{question_rows}

## 可复制话术
我们已先把资料整理成需求和缺口。为避免误判，请补充品牌资产、产品高清图/包装规范、参考片边界、AI 图是否可用于客户审阅，以及本轮希望看到的方案精度。
""",
    )

    write_text(
        project / "AD-creative/handoff/下一步建议.md",
        f"""# 下一步建议

## 推荐动作
读取资料事件 `{latest_source_ids}`，生成 requirements / gaps / current_truth，并跑 Brief Gate。

## 理由
非开发者只需要看项目看板、待确认、客户追问和操作台；内部 CSV 继续作为可追溯事实源。

## 风险
未读取真实资料前，不能宣称创意方向、参考包或客户稿已经成立。

## 是否需要你确认
内部整理不需要确认；客户稿发送、付费/登录平台、全局 Skill 安装仍需要明确确认。
""",
    )

    write_text(
        project / "AD-creative/handoff/本轮交付说明.md",
        f"""# 本轮交付说明

## 本轮做了什么
初始化或补齐项目结构，登记资料，创建 intake 工作项，生成非开发者操作台；双击入口会继续生成可编辑 PPTX 草稿并检查文本层。

## 产物位置
| 产物 | 路径 |
|---|---|
| 操作台 | AD-creative/handoff/操作台.html |
| 项目看板 | AD-creative/handoff/项目看板.md |
| 待确认 | AD-creative/handoff/待你确认.md |
| 客户追问 | AD-creative/handoff/客户追问话术.md |

## 未完成事项
自动搜索结果质量、真实 image_gen 调用本身、最终客户稿内容审稿。

## 下一步建议
让 Codex 继续执行 ad-creative:next，先完成需求和缺口整理。
""",
    )


def cell(value: str | None) -> str:
    return html.escape(value or "")


def first_nonempty(*values: str | None, default: str = "-") -> str:
    for value in values:
        if value:
            return value
    return default


def project_stage(project: Path) -> str:
    path = project / "AD-creative/orchestrator/project.yml"
    if not path.exists():
        return "unknown"
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("stage:"):
            return stripped.split(":", 1)[1].strip() or "intake"
    return "intake"


def rows_to_table(rows: list[dict[str, str]], columns: list[tuple[str, str]], empty: str) -> str:
    if not rows:
        return f"<tr><td colspan=\"{len(columns)}\" class=\"empty\">{html.escape(empty)}</td></tr>"
    body = []
    for row in rows:
        cells = "".join(
            f'<td data-label="{cell(label)}">{cell(row.get(key))}</td>' for key, label in columns
        )
        body.append(f"<tr>{cells}</tr>")
    return "\n".join(body)


def html_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")


def parse_confirmation_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 5 or parts[0] in CONFIRMATION_HEADER_CELLS or set(parts[0]) == {"-"}:
            continue
        rows.append(
            {
                "id": parts[0],
                "question": parts[1],
                "recommendation": parts[2],
                "impact": parts[3],
                "actions": parts[4],
            }
        )
    return rows


def extract_markdown_section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.find(marker)
    if start == -1:
        return ""
    body = text[start + len(marker):]
    next_heading = body.find("\n## ")
    if next_heading != -1:
        body = body[:next_heading]
    return body.strip()


def first_section_line(text: str, heading: str) -> str:
    section = extract_markdown_section(text, heading)
    for line in section.splitlines():
        stripped = line.strip().strip("-").strip()
        if stripped and not stripped.startswith("|"):
            return stripped
    return ""


def parse_key_value_line(text: str, key: str) -> str:
    prefix = f"{key}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def goal_iteration_rows(project: Path) -> list[dict[str, str]]:
    goal_dir = project / GOAL_ITERATIONS_REL
    if not goal_dir.exists():
        return []
    rows: list[dict[str, str]] = []
    for path in sorted(goal_dir.glob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True):
        text = path.read_text(encoding="utf-8", errors="ignore")
        rows.append(
            {
                "goal_id": parse_key_value_line(text, "goal_id") or path.stem,
                "status": parse_key_value_line(text, "status") or "unknown",
                "title": parse_key_value_line(text, "goal_title") or path.stem,
                "owner": parse_key_value_line(text, "owner") or "Main Controller",
                "updated_at": parse_key_value_line(text, "updated_at"),
                "next": first_section_line(text, "Next Iteration Queue") or "按下一阶段 Gate 推进",
                "path": safe_rel(project, path),
            }
        )
    return rows


def latest_goal_row(project: Path) -> dict[str, str] | None:
    rows = goal_iteration_rows(project)
    return rows[0] if rows else None


def resolve_goal_row(project: Path, goal_id: str) -> dict[str, str] | None:
    rows = goal_iteration_rows(project)
    if not rows:
        return None
    if goal_id in {"", "latest"}:
        return rows[0]
    for row in rows:
        if row.get("goal_id") == goal_id:
            return row
    return None


def slug_text(value: str, default: str = "run") -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or default


def creative_production_root_candidates() -> list[Path]:
    candidates: list[Path] = []
    env_root = os.environ.get("ADCO_CREATIVE_PRODUCTION_ROOT", "").strip()
    if env_root:
        candidates.append(Path(env_root).expanduser())

    cache_root = Path.home() / ".codex/plugins/cache"
    for pattern in [
        "openai-curated-remote/creative-production/*",
        "openai-curated/creative-production/*",
        "creative-production/*",
    ]:
        if cache_root.exists():
            candidates.extend(sorted(cache_root.glob(pattern), reverse=True))

    source = source_root()
    if source:
        candidates.extend(
            [
                source / "plugins/creative-production",
                source / "creative-production",
            ]
        )
    return candidates


def is_creative_production_root(path: Path) -> bool:
    return all(
        (path / rel).exists()
        for rel in [
            "skills/ads-explorer/scripts/build_ads_explorer.py",
            "skills/shot-explorer/scripts/create_shot_explorer.py",
            "skills/moodboard-explorer/scripts/create_mood_board.py",
            "scripts/review_renderer.py",
        ]
    )


def resolve_creative_production_root() -> Path | None:
    for candidate in creative_production_root_candidates():
        root = candidate.expanduser().resolve()
        if is_creative_production_root(root):
            return root
    return None


def creative_production_script(root: Path, kind: str) -> Path:
    scripts = {
        "ads": root / "skills/ads-explorer/scripts/build_ads_explorer.py",
        "shots": root / "skills/shot-explorer/scripts/create_shot_explorer.py",
        "moodboard": root / "skills/moodboard-explorer/scripts/create_mood_board.py",
    }
    return scripts[kind]


def creative_doctor_report() -> tuple[str, list[str], list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = []
    root = resolve_creative_production_root()
    if not root:
        issues.append("Creative Production plugin root not found.")
        evidence.append("ADCO_CREATIVE_PRODUCTION_ROOT=" + os.environ.get("ADCO_CREATIVE_PRODUCTION_ROOT", ""))
        evidence.append("searched_candidates=" + str(len(creative_production_root_candidates())))
        return "BLOCKED", issues, warnings, evidence

    evidence.append(f"creative_production_root={root}")
    for kind in sorted(CREATIVE_PRODUCTION_KINDS):
        script = creative_production_script(root, kind)
        evidence.append(f"{kind}_script={script}")
        if not script.exists():
            issues.append(f"missing {kind} script: {script}")
    try:
        import PIL  # noqa: F401
    except Exception as exc:  # noqa: BLE001 - optional bridge should report exact reason
        warnings.append(f"Pillow import check failed: {exc}")
    return ("PASS" if not issues else "BLOCKED"), issues, warnings, evidence


def creative_output_dir(project: Path, kind: str, work_id: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return project / "AD-creative/creative_production/runs" / f"{kind}-{slug_text(work_id)}-{stamp}"


def brief_title(brief_file: Path, work_id: str) -> str:
    try:
        for line in brief_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip("# ").strip()
            if stripped:
                return stripped[:80]
    except FileNotFoundError:
        pass
    return work_id


def moodboard_spec_from_brief(brief_file: Path, work_id: str, output: Path) -> Path:
    text = brief_file.read_text(encoding="utf-8", errors="ignore")[:2400]
    title = brief_title(brief_file, work_id)
    cues = [
        ("audience-feel", "Audience feel", "single editorial photograph showing the target audience mood and occasion"),
        ("brand-world", "Brand world", "single cinematic brand-world reference image with setting, light, and material cues"),
        ("product-moment", "Product moment", "single commercial product-in-use visual reference image"),
        ("texture-light", "Texture and light", "single material and lighting study with premium production value"),
        ("story-beat", "Story beat", "single film-still style moment that can become a key frame"),
        ("campaign-kv", "Campaign key visual", "single clean advertising key visual reference without readable text"),
    ]
    items = []
    for index, (item_id, item_title, prompt_seed) in enumerate(cues, start=1):
        items.append(
            {
                "id": f"{item_id}-{index}",
                "title": item_title,
                "caption": f"{item_title} for {title}",
                "source": "ADCO brief",
                "tone": "commercial cinematic",
                "motif": item_title,
                "palette": "derived from brief",
                "prompt": (
                    f"{prompt_seed}. Preserve this business brief: {text}. "
                    "No logos, no readable copy, no collage, no contact sheet, no internal notes."
                ),
            }
        )
    spec = {
        "meta": {
            "title": f"{title} mood board",
            "summary": "ADCO review-only mood board generated from project brief.",
            "source": str(brief_file),
        },
        "signals": {
            "work_id": work_id,
            "brief_excerpt": text[:800],
            "visibility": "internal_only",
        },
        "items": items,
    }
    spec_path = output.parent / f"{output.name}-spec.json"
    write_text(spec_path, json.dumps(spec, ensure_ascii=False, indent=2))
    return spec_path


def register_agent_run(
    project: Path,
    *,
    work_id: str,
    role: str,
    status: str,
    input_files: str,
    output_files: str,
    gate_id: str = "",
    summary: str = "",
    next_action: str = "",
) -> str:
    path = project / "AD-creative/orchestrator/agent_runs.csv"
    fields, rows = read_csv_rows(path)
    if not fields:
        return ""
    run_id = next_id(rows, "run_id", "RUN")
    rows.append(
        {
            "run_id": run_id,
            "work_id": work_id,
            "agent_role": role,
            "status": status,
            "started_at": now_iso(),
            "completed_at": now_iso(),
            "input_files": input_files,
            "output_files": output_files,
            "gate_id": gate_id,
            "summary": summary,
            "next_action": next_action,
        }
    )
    write_csv_rows(path, fields, rows)
    return run_id


def work_id_exists(project: Path, work_id: str) -> bool:
    _, rows = read_csv_rows(project / "AD-creative/orchestrator/work_items.csv")
    return any(row.get("work_id") == work_id for row in rows)


def run_creative_production(
    project: Path,
    *,
    kind: str,
    work_id: str,
    brief_file: Path,
    base_asset: Path | None = None,
    generate: bool = False,
    force: bool = False,
) -> tuple[Path, list[str]]:
    root = resolve_creative_production_root()
    if not root:
        raise FileNotFoundError("Creative Production plugin root not found.")
    if kind not in CREATIVE_PRODUCTION_KINDS:
        raise ValueError(f"unknown creative production kind: {kind}")
    if not brief_file.exists():
        raise FileNotFoundError(f"brief file not found: {brief_file}")
    if not work_id_exists(project, work_id):
        raise ValueError(f"unknown work_id: {work_id}")

    out_dir = creative_output_dir(project, kind, work_id)
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    script = creative_production_script(root, kind)
    cmd: list[str]
    if kind == "ads":
        cmd = [
            sys.executable,
            str(script),
            "--ad-name",
            brief_title(brief_file, work_id),
            "--ad-brief-file",
            str(brief_file),
            "--out-dir",
            str(out_dir),
            "--force",
        ]
        if base_asset:
            cmd.extend(["--reference-image", str(base_asset)])
        cmd.append("--generate" if generate else "--review-only")
    elif kind == "shots":
        cmd = [
            sys.executable,
            str(script),
            "--output",
            str(out_dir),
            "--force",
            "--generate" if generate else "--review-only",
        ]
        if base_asset:
            cmd.extend(["--base-asset", str(base_asset)])
    else:
        spec_path = moodboard_spec_from_brief(brief_file, work_id, out_dir)
        cmd = [
            sys.executable,
            str(script),
            "--spec",
            str(spec_path),
            "--output",
            str(out_dir),
            "--force",
        ]

    if out_dir.exists() and force:
        shutil.rmtree(out_dir)
    completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
    log_path = out_dir.parent / f"{out_dir.name}-command.json"
    write_text(
        log_path,
        json.dumps(
            {
                "command": cmd,
                "returncode": completed.returncode,
                "stdout": completed.stdout[-4000:],
                "stderr": completed.stderr[-4000:],
                "generate": generate,
            },
            ensure_ascii=False,
            indent=2,
        ),
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Creative Production {kind} failed; see {log_path}")

    review = out_dir / ("mood-board.html" if kind == "moodboard" else "review-board.html")
    if not review.exists() and kind != "moodboard":
        review = out_dir
    update_artifact(
        project,
        f"ART-CP-{safe_artifact_suffix(out_dir.name)}",
        "creative_production_run",
        safe_rel(project, review),
        "visual_plan",
        status="done",
        visibility="internal_only",
        linked_work_items=work_id,
        gate_status="PARTIAL_PASS",
    )
    register_agent_run(
        project,
        work_id=work_id,
        role=f"creative_production_{kind}",
        status="done",
        input_files=safe_rel(project, brief_file),
        output_files=safe_rel(project, out_dir),
        summary=f"Creative Production {kind} {'generated' if generate else 'review-only'} run.",
        next_action="Import with adco import-creative-production before visual gate.",
    )
    append_event(
        project,
        {
            "event_id": f"EVT-CP-{safe_artifact_suffix(out_dir.name)}",
            "event_type": "creative_production_run",
            "created_at": now_iso(),
            "kind": kind,
            "work_id": work_id,
            "run_dir": safe_rel(project, out_dir),
            "generate": generate,
        },
    )
    render_dashboard(project)
    return out_dir, [safe_rel(project, log_path)]


def load_json_file(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def creative_manifest_paths(run_dir: Path, kind: str) -> dict[str, Path]:
    if kind == "shots":
        return {
            "manifest": run_dir / "data/prompts-manifest.json",
            "jobs": run_dir / "data/jobs.jsonl",
            "review": run_dir / "review-board.html",
            "widget": run_dir / "moodboard-widget-payload.json",
        }
    if kind == "moodboard":
        return {
            "manifest": run_dir / "data/stream.json",
            "jobs": run_dir / "data/stream-static.json",
            "review": run_dir / "mood-board.html",
            "widget": run_dir / "data/stream.json",
        }
    return {
        "manifest": run_dir / "prompts-manifest.json",
        "jobs": run_dir / "jobs.jsonl",
        "review": run_dir / "review-board.html",
        "widget": run_dir / "moodboard-widget-payload.json",
    }


def prompt_items_from_manifest(path: Path, kind: str) -> list[dict[str, object]]:
    if not path.exists():
        return []
    raw = load_json_file(path)
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        if isinstance(raw.get("items"), list):
            return [item for item in raw["items"] if isinstance(item, dict)]
        if isinstance(raw.get("routes"), list):
            return [item for item in raw["routes"] if isinstance(item, dict)]
    return []


def item_image_path(run_dir: Path, item: dict[str, object]) -> Path | None:
    for key in ("output", "src", "image", "imageUrl", "previewImageUrl", "sourceImageUrl", "path", "url"):
        value = str(item.get(key) or "").strip()
        if not value or value.startswith("data:") or value.startswith("http"):
            continue
        value = value.lstrip("/")
        path = run_dir / value
        if path.exists() and path.suffix.lower() in GENERATED_IMAGE_SUFFIXES:
            return path
    return None


def copy_creative_metadata(project: Path, run_dir: Path, kind: str, manifest_paths: dict[str, Path]) -> tuple[Path, list[str]]:
    target_dir = project / "AD-creative/image_jobs/creative_production" / slug_text(run_dir.name)
    target_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for label, source in manifest_paths.items():
        if source.exists() and source.is_file():
            target = target_dir / f"{label}{source.suffix or '.txt'}"
            shutil.copy2(source, target)
            copied.append(safe_rel(project, target))
    summary = {
        "kind": kind,
        "source_run_dir": str(run_dir.resolve()),
        "copied_files": copied,
        "imported_at": now_iso(),
        "visibility": "internal_only",
    }
    write_text(target_dir / "adco_import_summary.json", json.dumps(summary, ensure_ascii=False, indent=2))
    return target_dir, copied


def import_creative_production_run(
    project: Path,
    *,
    run_dir: Path,
    kind: str,
    slot_prefix: str,
    requirement_id: str = "",
    reference_id: str = "pending",
) -> tuple[list[str], Path]:
    if kind not in CREATIVE_PRODUCTION_KINDS:
        raise ValueError(f"unknown creative production kind: {kind}")
    if not run_dir.exists():
        raise FileNotFoundError(f"run dir not found: {run_dir}")

    manifest_paths = creative_manifest_paths(run_dir, kind)
    metadata_dir, copied = copy_creative_metadata(project, run_dir, kind, manifest_paths)
    manifest_rel = safe_rel(project, metadata_dir / "manifest.json") if (metadata_dir / "manifest.json").exists() else ""
    manifest = prompt_items_from_manifest(manifest_paths["manifest"], kind)
    imported_asset_ids: list[str] = []

    for index, item in enumerate(manifest, start=1):
        image_path = item_image_path(run_dir, item)
        if not image_path:
            continue
        slot_id = f"{slot_prefix}-{index:02d}"
        prompt_ref = manifest_rel or safe_rel(project, metadata_dir)
        label = str(item.get("title") or item.get("label") or item.get("id") or slot_id)
        asset_id, _ = add_visual_asset(
            project,
            image_path,
            slot_id,
            requirement_id,
            reference_id,
            "generated_image",
            "internal_only",
            "PARTIAL_PASS",
            "medium",
            prompt_ref,
            f"Imported from Creative Production {kind} run {run_dir.name}; route={label}; internal_only.",
            False,
        )
        imported_asset_ids.append(asset_id)

    checked_artifacts = []
    run_artifact_id = f"ART-CP-IMPORT-{safe_artifact_suffix(run_dir.name)}"
    review_path = manifest_paths.get("review")
    if review_path and review_path.exists():
        rel_review = safe_rel(project, review_path)
    else:
        rel_review = safe_rel(project, metadata_dir)
    update_artifact(
        project,
        run_artifact_id,
        "creative_production_import",
        rel_review,
        "visual_plan",
        status="done",
        visibility="internal_only",
        linked_assets=";".join(imported_asset_ids),
        gate_status="PARTIAL_PASS",
    )
    checked_artifacts.append(run_artifact_id)
    append_gate(
        project,
        f"GATE-CP-IMPORT-{safe_artifact_suffix(run_dir.name)}",
        "visual_plan",
        "PARTIAL_PASS",
        "70",
        ";".join(checked_artifacts),
        "",
        "Creative Production outputs are internal_only until visual-quality-gate and human review pass.",
        "",
        "run_visual_quality_gate",
        "ad_creative_operator",
    )
    append_event(
        project,
        {
            "event_id": f"EVT-CP-IMPORT-{safe_artifact_suffix(run_dir.name)}",
            "event_type": "creative_production_imported",
            "created_at": now_iso(),
            "kind": kind,
            "run_dir": str(run_dir.resolve()),
            "metadata_dir": safe_rel(project, metadata_dir),
            "imported_assets": imported_asset_ids,
        },
    )
    render_dashboard(project)
    return imported_asset_ids, metadata_dir


def latest_gate(project: Path, stage: str | None = None, gate_id: str | None = None) -> dict[str, str] | None:
    _, gates = read_csv_rows(project / "AD-creative/orchestrator/gate_log.csv")
    candidates = []
    for gate in gates:
        if gate_id and gate.get("gate_id") != gate_id:
            continue
        if stage and gate.get("stage") != stage:
            continue
        candidates.append(gate)
    if not candidates:
        return None
    return sorted(candidates, key=lambda row: row.get("created_at", ""), reverse=True)[0]


def has_gate(project: Path, gate_id: str) -> bool:
    return latest_gate(project, gate_id=gate_id) is not None


def derive_goal_phase(project: Path) -> str:
    counts = read_counts(project)
    if counts["source_events"] == 0 or counts["requirements"] == 0:
        return "P0"
    if counts["references"] == 0:
        return "P1"
    if counts["assets"] == 0 and not has_gate(project, "GATE-AUTO-VISUAL-QUALITY-001"):
        return "P2"
    if not has_gate(project, "GATE-AUTO-FILM-QUALITY-001"):
        return "P3" if counts["assets"] == 0 else "P4"
    if not has_gate(project, "GATE-AUTO-CLIENT-PACK-001"):
        return "P5"
    if not has_gate(project, "GATE-AUTO-HANDOFF-READINESS-001"):
        return "P6"
    return "P7"


def gate_status_for_stages(project: Path, stages: tuple[str, ...]) -> str:
    _, gates = read_csv_rows(project / "AD-creative/orchestrator/gate_log.csv")
    statuses = [
        gate.get("status", "")
        for gate in gates
        if gate.get("stage", "").strip() in stages and gate.get("status", "").strip()
    ]
    if not statuses:
        return "missing"
    if any(status == "BLOCKED" for status in statuses):
        return "blocked"
    if any(status == "PARTIAL_PASS" for status in statuses):
        return "partial"
    if any(status == "PASS" for status in statuses):
        return "pass"
    return statuses[-1].lower()


def goal_lane_states(project: Path) -> dict[str, str]:
    counts = read_counts(project)
    return {
        "brand_research": "active" if counts["requirements"] else "needs_material",
        "image_function": "active" if counts["assets"] else "planned",
        "gates": gate_status_for_stages(project, ("visual_review", "film_quality", "client_review", "final_delivery")),
        "delivery": "ready" if has_gate(project, "GATE-AUTO-HANDOFF-READINESS-001") else "internal_only",
    }


def goal_completion_readiness(project: Path, errors: list[str], confirmations: list[dict[str, str]]) -> dict[str, object]:
    _, gates = read_csv_rows(project / "AD-creative/orchestrator/gate_log.csv")
    blocking_gates = [gate.get("gate_id", "") for gate in gates if gate.get("status") == "BLOCKED"]
    required = [
        "GATE-AUTO-VISUAL-QUALITY-001",
        "GATE-AUTO-FILM-QUALITY-001",
        "GATE-AUTO-CLIENT-PACK-001",
        "GATE-AUTO-HANDOFF-READINESS-001",
    ]
    missing = [gate_id for gate_id in required if not has_gate(project, gate_id)]
    ready = not errors and not confirmations and not blocking_gates and not missing
    return {
        "status": "READY_INTERNAL_REVIEW" if ready else "NOT_READY",
        "missing_gates": missing,
        "blocking_gates": blocking_gates,
        "validation_errors": len(errors),
        "pending_confirmations": len(confirmations),
    }


def goal_stop_reason(payload: dict[str, object]) -> str:
    if payload["validation"] != "PASS":
        return "VALIDATION_CHECK"
    if payload["pending_confirmation_count"]:
        return "WAITING_FOR_CONFIRMATION"
    if payload["blocking_gap_count"]:
        return "BLOCKING_GAP"
    readiness = payload.get("completion_readiness", {})
    if isinstance(readiness, dict) and readiness.get("blocking_gates"):
        return "BLOCKED_GATE"
    if payload["counts"]["source_events"] == 0:
        return "NEEDS_MATERIAL"
    return ""


def item_title(row: dict[str, str], *keys: str, default: str = "-") -> str:
    for key in keys:
        value = row.get(key, "").strip()
        if value:
            return value
    return default


def render_dashboard(project: Path) -> Path:
    counts = read_counts(project)
    _, work_items = read_csv_rows(project / "AD-creative/orchestrator/work_items.csv")
    _, gaps = read_csv_rows(project / "AD-creative/orchestrator/gaps.csv")
    _, gates = read_csv_rows(project / "AD-creative/orchestrator/gate_log.csv")
    _, artifacts = read_csv_rows(project / "AD-creative/orchestrator/artifact_index.csv")
    _, source_events = read_csv_rows(project / "AD-creative/orchestrator/source_events.csv")
    _, references = read_csv_rows(project / "AD-creative/references/reference_cards.csv")
    _, visual_assets = read_csv_rows(project / "AD-creative/visual_assets/asset_manifest.csv")
    confirmations = parse_confirmation_rows(project / "AD-creative/handoff/待你确认.md")
    goals = goal_iteration_rows(project)
    creative_runs = [
        row
        for row in artifacts
        if row.get("artifact_type", "").strip() in {"creative_production_run", "creative_production_import"}
    ]

    stage = project_stage(project)
    phase = derive_goal_phase(project)
    lane_states = goal_lane_states(project)
    validation_errors, _ = validate(project)
    validation_status = "PASS" if not validation_errors else "CHECK"
    active_work = [row for row in work_items if row.get("status", "").lower() not in {"done", "closed"}]
    next_action = first_nonempty(active_work[0].get("title") if active_work else "", "读取资料并生成需求/缺口")
    payload = {
        "project": project.name,
        "stage": stage,
        "validation": validation_status,
        "updated": now_iso(),
        "counts": counts,
        "work": work_items,
        "gaps": gaps,
        "gates": gates,
        "artifacts": artifacts,
        "sources": source_events,
        "references": references,
        "visualAssets": visual_assets,
        "goals": goals,
        "creativeRuns": creative_runs,
        "goalPhase": {"id": phase, "name": GOAL_PHASE_NAMES.get(phase, phase)},
        "laneStates": lane_states,
        "completionReadiness": goal_completion_readiness(project, validation_errors, confirmations),
        "confirmations": confirmations,
        "validationErrors": validation_errors,
        "nextAction": next_action,
    }
    work_columns = [
        ("work_id", "工作"),
        ("status", "状态"),
        ("title", "标题"),
        ("owner_agent", "负责人"),
        ("gate_required", "关卡"),
        ("client_visibility", "可见性"),
    ]
    gap_columns = [
        ("gap_id", "缺口"),
        ("impact", "影响"),
        ("status", "状态"),
        ("recommended_action", "动作"),
    ]
    initial_row = active_work[0] if active_work else (work_items[0] if work_items else {})
    statuses = sorted({row.get("status", "") for row in work_items if row.get("status", "")})
    status_options = '<option value="all">全部状态</option>' + "".join(
        f'<option value="{cell(status)}">{cell(status)}</option>' for status in statuses
    )
    table_head = "<tr>" + "".join(f"<th>{cell(label)}</th>" for _, label in work_columns) + "</tr>"
    table_body = rows_to_table(work_items[:12], work_columns, "暂无工作项")
    gap_body = rows_to_table(gaps[:8], gap_columns, "暂无缺口")
    decision_html = (
        "\n".join(
            f"""<div class="decision"><strong>{cell(row['id'])} · {cell(row['question'])}</strong><div class="muted">{cell(row['recommendation'])}</div></div>"""
            for row in confirmations[:4]
        )
        or '<div class="decision"><strong>暂无待确认</strong><div class="muted">内部整理可继续。</div></div>'
    )
    selected_props = "\n".join(
        f'<div class="prop"><span>{cell(label)}</span><strong>{cell(value)}</strong></div>'
        for label, value in [
            ("ID", item_title(initial_row, "work_id", "artifact_id", "source_event_id", "gate_id")),
            ("状态", item_title(initial_row, "status", "gate_status", "trust_level")),
            ("阶段", item_title(initial_row, "stage", "affected_stage")),
            ("关卡", item_title(initial_row, "gate_required", "gate_status", "gate_id")),
            ("可见性", item_title(initial_row, "client_visibility", "visibility")),
            ("更新时间", item_title(initial_row, "updated_at", "created_at", default=payload["updated"])),
        ]
    )
    selected_objective = item_title(initial_row, "objective", "notes", "blocking_issues")

    html_doc = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>广告创意操作台</title>
<style>
:root {
  --bg: #f6f7f8;
  --ink: #202124;
  --muted: #6b7078;
  --soft: #8b9097;
  --line: #d8dde2;
  --panel: #ffffff;
  --panel-2: #f8fafb;
  --rail: #23262c;
  --rail-2: #30343b;
  --rail-muted: #aeb4bd;
  --blue: #285f89;
  --amber: #a96b18;
  --green: #237255;
  --red: #ad3b35;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif;
}
button, input, select { font: inherit; }
button { cursor: pointer; }
.app { min-height: 100vh; display: grid; grid-template-columns: 224px minmax(520px, 1fr) 382px; }
.sidebar { background: var(--rail); color: #f3f4f6; padding: 18px 14px; }
.brand { display: flex; align-items: center; gap: 10px; font-size: 13px; letter-spacing: .08em; text-transform: uppercase; color: #fff; margin-bottom: 22px; }
.mark { width: 18px; height: 18px; border: 1px solid rgba(255,255,255,.55); border-radius: 4px; display: grid; place-items: center; font-size: 10px; }
.nav { display: grid; gap: 4px; }
.nav button { width: 100%; display: flex; align-items: center; gap: 10px; border: 0; background: transparent; color: var(--rail-muted); padding: 8px 10px; border-radius: 6px; text-align: left; }
.nav button.active, .nav button:hover { color: #fff; background: rgba(255,255,255,.08); }
.nav .dot { width: 7px; height: 7px; border-radius: 999px; background: currentColor; opacity: .7; }
.main { min-width: 0; padding: 17px 22px 74px; }
.topbar { height: 42px; display: flex; align-items: center; justify-content: space-between; gap: 14px; border-bottom: 1px solid var(--line); margin-bottom: 14px; min-width: 0; }
.crumb { font-weight: 700; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tabs { display: flex; flex-shrink: 0; gap: 7px; color: var(--muted); font-size: 12px; }
.tabs button, .btn { border: 1px solid var(--line); border-radius: 6px; padding: 5px 8px; background: rgba(255,255,255,.65); color: var(--ink); }
.tabs button.active { color: #fff; background: var(--rail-2); border-color: var(--rail-2); }
	.summary { display: grid; grid-template-columns: repeat(6, minmax(98px, 1fr)); gap: 10px; margin-bottom: 14px; }
.metric { border: 1px solid var(--line); background: var(--panel); border-radius: 6px; padding: 9px 11px; min-width: 0; }
.metric small { display: block; color: var(--muted); font-size: 11px; }
.metric strong { display: block; font-size: 20px; line-height: 1.18; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.search { flex: 1; min-width: 160px; border: 1px solid var(--line); border-radius: 6px; background: #fff; padding: 7px 9px; }
.select { border: 1px solid var(--line); border-radius: 6px; background: #fff; padding: 7px 8px; color: var(--ink); max-width: 150px; }
.section { border: 1px solid var(--line); background: var(--panel); border-radius: 6px; overflow: hidden; margin-bottom: 13px; }
.section-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; border-bottom: 1px solid var(--line); padding: 9px 11px; }
.section h2 { margin: 0; font-size: 13px; }
.count { color: var(--muted); font-size: 12px; }
table { width: 100%; border-collapse: collapse; table-layout: fixed; }
th, td { border-bottom: 1px solid #ece9e2; padding: 8px 11px; text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
th { color: var(--muted); font-weight: 650; font-size: 11px; }
tr:last-child td { border-bottom: 0; }
tbody tr { outline: 0; }
tbody tr:hover, tbody tr.selected { background: #f3f7f8; }
.empty { color: var(--muted); padding: 18px 11px; }
.chip { display: inline-flex; align-items: center; min-height: 22px; padding: 2px 7px; border-radius: 999px; font-size: 11px; border: 1px solid var(--line); background: #fff; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pass { color: var(--green); border-color: rgba(35,114,85,.35); }
.warn { color: var(--amber); border-color: rgba(169,107,24,.35); }
.check { color: var(--red); border-color: rgba(173,59,53,.35); }
.muted { color: var(--muted); }
.inspector { border-left: 1px solid var(--line); background: var(--panel-2); padding: 17px 16px 74px; min-width: 0; }
.inspector h1 { font-size: 19px; line-height: 1.25; margin: 0 0 5px; overflow-wrap: anywhere; }
.sub { color: var(--muted); margin-bottom: 12px; }
.props { display: grid; gap: 8px; margin: 15px 0; }
.prop { display: flex; justify-content: space-between; gap: 12px; border-bottom: 1px solid var(--line); padding-bottom: 8px; }
.prop span:first-child { color: var(--muted); }
.prop strong { text-align: right; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.detail-box { border: 1px solid var(--line); border-radius: 6px; background: #fff; padding: 10px 11px; margin-top: 12px; }
.detail-box h3 { margin: 0 0 8px; font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .03em; }
.detail-box p { margin: 0; color: var(--ink); overflow-wrap: anywhere; }
.decision-list { display: grid; gap: 8px; }
.decision { border: 1px solid var(--line); border-radius: 6px; background: #fff; padding: 8px; }
.decision strong { display: block; margin-bottom: 3px; }
.rail { position: fixed; left: 224px; right: 0; bottom: 0; min-height: 50px; background: #fff; border-top: 1px solid var(--line); display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 18px; }
.rail strong { color: var(--blue); }
.rail-actions { display: flex; gap: 8px; flex-shrink: 0; }
	@media (max-width: 1060px) {
	  .app { grid-template-columns: 196px minmax(430px, 1fr); }
	  .inspector { display: none; }
	  .rail { left: 196px; }
	  .summary { grid-template-columns: repeat(3, minmax(0, 1fr)); }
	}
@media (max-width: 760px) {
  .app { grid-template-columns: 1fr; }
  .sidebar { display: none; }
  .main { padding: 12px 12px 86px; }
  .topbar { align-items: flex-start; height: auto; flex-direction: column; padding-bottom: 10px; }
  .tabs { flex-wrap: wrap; }
	  .summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
	  .toolbar { flex-wrap: wrap; }
	  .search, .select { flex: 1 1 100%; max-width: none; }
	  .section { overflow: visible; }
	  table { min-width: 0; }
	  thead { display: none; }
	  tbody, tr, td { display: block; width: 100%; }
	  tbody tr { padding: 8px 0; border-bottom: 1px solid #ece9e2; }
	  tbody tr:last-child { border-bottom: 0; }
	  td { border-bottom: 0; padding: 5px 11px; white-space: normal; display: grid; grid-template-columns: 86px minmax(0, 1fr); gap: 10px; align-items: start; }
	  td::before { content: attr(data-label); color: var(--muted); font-size: 11px; font-weight: 650; }
	  td.empty { display: block; }
	  td.empty::before { content: ""; display: none; }
	  .rail { position: static; left: auto; right: auto; bottom: auto; align-items: flex-start; flex-direction: column; }
	}
</style>
</head>
<body>
<script>const DATA = __PAYLOAD__;</script>
<div class="app">
  <aside class="sidebar">
    <div class="brand"><span class="mark">AD</span><span>广告创意操作台</span></div>
    <nav class="nav">
	      <button class="active" data-nav="work"><span class="dot"></span>工作台</button>
	      <button data-nav="sources"><span class="dot"></span>资料</button>
	      <button data-nav="references"><span class="dot"></span>参考</button>
	      <button data-nav="visualAssets"><span class="dot"></span>图片</button>
	      <button data-nav="creativeRuns"><span class="dot"></span>创意运行</button>
	      <button data-nav="goals"><span class="dot"></span>Goal</button>
	      <button data-nav="artifacts"><span class="dot"></span>产物</button>
	      <button data-nav="gates"><span class="dot"></span>关卡</button>
	      <button data-nav="confirmations"><span class="dot"></span>待确认</button>
    </nav>
  </aside>
  <main class="main">
    <div class="topbar">
      <div class="crumb">项目 / __PROJECT__</div>
      <div class="tabs">
	        <button class="active" data-view="work">工作</button>
	        <button data-view="sources">资料</button>
	        <button data-view="references">参考</button>
	        <button data-view="visualAssets">图片</button>
	        <button data-view="creativeRuns">创意运行</button>
	        <button data-view="goals">Goal</button>
	        <button data-view="artifacts">产物</button>
	        <button data-view="gates">关卡</button>
	        <button data-view="confirmations">待确认</button>
      </div>
    </div>
    <div class="summary">
	      <div class="metric"><small>阶段</small><strong>__STAGE__</strong></div>
	      <div class="metric"><small>校验</small><strong>__VALIDATION__</strong></div>
	      <div class="metric"><small>工作项</small><strong>__WORK_COUNT__</strong></div>
	      <div class="metric"><small>参考</small><strong>__REFERENCE_COUNT__</strong></div>
	      <div class="metric"><small>图片</small><strong>__ASSET_COUNT__</strong></div>
	      <div class="metric"><small>Goal阶段</small><strong>__GOAL_PHASE__</strong></div>
	      <div class="metric"><small>Goal</small><strong>__GOAL_COUNT__</strong></div>
	      <div class="metric"><small>产物</small><strong>__ARTIFACT_COUNT__</strong></div>
    </div>
    <section class="section">
      <div class="section-head">
        <h2 id="contentTitle">工作</h2>
        <span class="count" id="rowCount">__ROW_COUNT__</span>
      </div>
      <div class="toolbar">
	        <input id="searchInput" class="search" placeholder="搜索工作、资料、参考、图片、产物">
        <select id="statusFilter" class="select">__STATUS_OPTIONS__</select>
        <select id="riskFilter" class="select">
          <option value="all">全部</option>
          <option value="blocked">阻塞</option>
          <option value="client">客户可见</option>
          <option value="open">进行中</option>
        </select>
      </div>
      <table>
        <thead id="tableHead">__TABLE_HEAD__</thead>
        <tbody id="tableBody">__TABLE_BODY__</tbody>
      </table>
    </section>
    <section class="section">
      <div class="section-head"><h2>缺口</h2><span class="count" id="gapCount">__GAP_COUNT__</span></div>
      <table>
        <thead><tr><th>缺口</th><th>影响</th><th>状态</th><th>动作</th></tr></thead>
        <tbody id="gapBody">__GAP_BODY__</tbody>
      </table>
    </section>
  </main>
  <aside class="inspector">
    <h1 id="selectedTitle">__NEXT_ACTION__</h1>
    <div class="sub">当前选中项</div>
    <span class="chip __VALIDATION_CLASS__">校验 __VALIDATION__</span>
    <span class="chip warn">内部预览</span>
    <div class="props" id="selectedProps">__SELECTED_PROPS__</div>
    <div class="detail-box">
      <h3>目标 / 说明</h3>
      <p id="selectedObjective">__SELECTED_OBJECTIVE__</p>
    </div>
    <div class="detail-box">
      <h3>待确认</h3>
      <div class="decision-list" id="decisionList">__DECISIONS__</div>
    </div>
  </aside>
</div>
<div class="rail">
  <div><strong>需要你确认</strong> · 客户稿发送、付费/登录平台、上传资料、全局安装前需要明确确认</div>
  <div class="rail-actions"><button class="btn" data-view="confirmations">待确认</button><button class="btn" onclick="location.reload()">刷新</button></div>
</div>
<script>
const VIEWS = {
  work: {
    title: "工作",
    rows: DATA.work,
    columns: [
      ["work_id", "工作"], ["status", "状态"], ["title", "标题"], ["owner_agent", "负责人"], ["gate_required", "关卡"], ["client_visibility", "可见性"]
    ],
    id: "work_id",
    titleKey: "title",
    objectiveKey: "objective"
  },
	  sources: {
	    title: "资料",
    rows: DATA.sources,
    columns: [
      ["source_event_id", "ID"], ["declared_semantics", "语义"], ["source_type", "类型"], ["file_paths", "路径"], ["trust_level", "可信度"]
    ],
    id: "source_event_id",
	    titleKey: "raw_summary",
	    objectiveKey: "notes"
	  },
	  references: {
	    title: "参考",
	    rows: DATA.references,
	    columns: [
	      ["reference_id", "ID"], ["platform", "平台"], ["title", "标题"], ["role", "角色"], ["client_visible", "客户可见"]
	    ],
	    id: "reference_id",
	    titleKey: "title",
	    objectiveKey: "why_relevant"
	  },
	  visualAssets: {
	    title: "图片",
	    rows: DATA.visualAssets,
	    columns: [
	      ["asset_id", "图片"], ["slot_id", "槽位"], ["status", "状态"], ["visibility", "可见性"], ["qa_status", "QA"], ["risk_level", "风险"], ["prompt_or_edit_ref", "Trace"]
	    ],
	    id: "asset_id",
	    titleKey: "path",
	    objectiveKey: "notes"
	  },
	  creativeRuns: {
	    title: "创意运行",
	    rows: DATA.creativeRuns,
	    columns: [
	      ["artifact_id", "运行"], ["artifact_type", "类型"], ["status", "状态"], ["path", "路径"], ["gate_status", "关卡"]
	    ],
	    id: "artifact_id",
	    titleKey: "path",
	    objectiveKey: "stage"
	  },
	  goals: {
	    title: "Goal",
	    rows: DATA.goals,
	    columns: [
	      ["goal_id", "Goal"], ["status", "状态"], ["title", "标题"], ["owner", "负责人"], ["next", "下一步"]
	    ],
	    id: "goal_id",
	    titleKey: "title",
	    objectiveKey: "path"
	  },
	  artifacts: {
	    title: "产物",
	    rows: DATA.artifacts,
	    columns: [
	      ["artifact_id", "产物"], ["artifact_type", "类型"], ["status", "状态"], ["visibility", "可见性"], ["gate_status", "关卡"]
	    ],
    id: "artifact_id",
    titleKey: "path",
    objectiveKey: "stage"
  },
  gates: {
    title: "关卡",
    rows: DATA.gates,
    columns: [
      ["gate_id", "关卡"], ["stage", "阶段"], ["status", "状态"], ["score", "分数"], ["next_state", "下一步"]
    ],
    id: "gate_id",
    titleKey: "stage",
    objectiveKey: "blocking_issues"
  },
  confirmations: {
    title: "待确认",
    rows: DATA.confirmations,
    columns: [
      ["id", "ID"], ["question", "问题"], ["recommendation", "建议"], ["impact", "影响"], ["actions", "动作"]
    ],
    id: "id",
    titleKey: "question",
    objectiveKey: "recommendation"
  }
};
let currentView = "work";
let selectedKey = "";
const $ = (id) => document.getElementById(id);
function value(row, key) { return (row && row[key]) ? String(row[key]) : ""; }
function escapeHtml(text) {
  return String(text ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}
function statusClass(text) {
  const lower = String(text || "").toLowerCase();
  if (lower.includes("pass") || lower.includes("done") || lower.includes("resolved")) return "pass";
  if (lower.includes("block") || lower.includes("error") || lower.includes("reject")) return "check";
  if (lower.includes("partial") || lower.includes("pending") || lower.includes("wait") || lower.includes("draft")) return "warn";
  return "";
}
function searchable(row) { return Object.values(row).join(" ").toLowerCase(); }
function rowMatchesRisk(row, risk) {
  const text = searchable(row);
  if (risk === "all") return true;
  if (risk === "blocked") return text.includes("block") || text.includes("wait") || text.includes("needs_user");
  if (risk === "client") return text.includes("client_visible") || text.includes("客户");
  if (risk === "open") return !text.includes("done") && !text.includes("closed") && !text.includes("pass,");
  return true;
}
function rowStatus(row) {
  return value(row, "status") || value(row, "gate_status") || value(row, "trust_level") || value(row, "impact") || "";
}
function syncStatusOptions() {
  const view = VIEWS[currentView];
  const statuses = Array.from(new Set(view.rows.map(rowStatus).filter(Boolean))).sort();
  $("statusFilter").innerHTML = `<option value="all">全部状态</option>` + statuses.map((status) => `<option value="${escapeHtml(status)}">${escapeHtml(status)}</option>`).join("");
}
function filteredRows() {
  const view = VIEWS[currentView];
  const query = $("searchInput").value.trim().toLowerCase();
  const status = $("statusFilter").value;
  const risk = $("riskFilter").value;
  return view.rows.filter((row) => {
    const matchesQuery = !query || searchable(row).includes(query);
    const matchesStatus = status === "all" || rowStatus(row) === status;
    return matchesQuery && matchesStatus && rowMatchesRisk(row, risk);
  });
}
function renderTable() {
  const view = VIEWS[currentView];
  const rows = filteredRows();
  $("contentTitle").textContent = view.title;
  $("rowCount").textContent = `${rows.length} 条`;
  $("tableHead").innerHTML = `<tr>${view.columns.map(([, label]) => `<th>${escapeHtml(label)}</th>`).join("")}</tr>`;
  if (!rows.length) {
    $("tableBody").innerHTML = `<tr><td class="empty" colspan="${view.columns.length}">暂无记录</td></tr>`;
    renderInspector(null);
    return;
  }
  if (!selectedKey || !rows.some((row) => value(row, view.id) === selectedKey)) selectedKey = value(rows[0], view.id);
  $("tableBody").innerHTML = rows.map((row) => {
    const key = value(row, view.id);
    const selected = key === selectedKey ? ' class="selected"' : "";
    const cells = view.columns.map(([field]) => {
      const raw = value(row, field);
      const chip = field.includes("status") || field.includes("visibility") || field === "trust_level" || field === "impact";
      const content = chip && raw ? `<span class="chip ${statusClass(raw)}">${escapeHtml(raw)}</span>` : escapeHtml(raw || "-");
      const label = view.columns.find(([name]) => name === field)?.[1] || field;
      return `<td data-label="${escapeHtml(label)}" title="${escapeHtml(raw)}">${content}</td>`;
    }).join("");
    return `<tr data-key="${escapeHtml(key)}"${selected}>${cells}</tr>`;
  }).join("");
  document.querySelectorAll("#tableBody tr[data-key]").forEach((rowEl) => {
    rowEl.addEventListener("click", () => {
      selectedKey = rowEl.dataset.key;
      renderTable();
    });
  });
  renderInspector(rows.find((row) => value(row, view.id) === selectedKey) || rows[0]);
}
function renderGaps() {
  const rows = DATA.gaps.slice(0, 8);
  $("gapCount").textContent = `${DATA.gaps.length} 条`;
  $("gapBody").innerHTML = rows.length ? rows.map((row) => `
    <tr>
      <td data-label="缺口" title="${escapeHtml(value(row, "description"))}">${escapeHtml(value(row, "gap_id") || "-")}</td>
      <td data-label="影响"><span class="chip ${statusClass(value(row, "impact"))}">${escapeHtml(value(row, "impact") || "-")}</span></td>
      <td data-label="状态">${escapeHtml(value(row, "status") || "-")}</td>
      <td data-label="动作" title="${escapeHtml(value(row, "recommended_action"))}">${escapeHtml(value(row, "recommended_action") || "-")}</td>
    </tr>`).join("") : `<tr><td class="empty" colspan="4">暂无缺口</td></tr>`;
}
function renderInspector(row) {
  const view = VIEWS[currentView];
  if (!row) {
    $("selectedTitle").textContent = DATA.nextAction;
    $("selectedObjective").textContent = "-";
    $("selectedProps").innerHTML = "";
    return;
  }
  const title = value(row, view.titleKey) || value(row, view.id) || DATA.nextAction;
  $("selectedTitle").textContent = title;
  $("selectedObjective").textContent = value(row, view.objectiveKey) || value(row, "notes") || value(row, "blocking_issues") || "-";
  const props = [
    ["ID", value(row, view.id)],
    ["状态", rowStatus(row) || "-"],
    ["阶段", value(row, "stage") || value(row, "affected_stage") || "-"],
    ["关卡", value(row, "gate_required") || value(row, "gate_status") || value(row, "gate_id") || "-"],
    ["可见性", value(row, "client_visibility") || value(row, "visibility") || "-"],
    ["更新时间", value(row, "updated_at") || value(row, "created_at") || DATA.updated]
  ];
  $("selectedProps").innerHTML = props.map(([label, val]) => `<div class="prop"><span>${escapeHtml(label)}</span><strong title="${escapeHtml(val)}">${escapeHtml(val)}</strong></div>`).join("");
}
function renderDecisions() {
  const rows = DATA.confirmations;
  $("decisionList").innerHTML = rows.length ? rows.slice(0, 4).map((row) => `
    <div class="decision">
      <strong>${escapeHtml(value(row, "id"))} · ${escapeHtml(value(row, "question"))}</strong>
      <div class="muted">${escapeHtml(value(row, "recommendation"))}</div>
    </div>`).join("") : `<div class="decision"><strong>暂无待确认</strong><div class="muted">内部整理可继续。</div></div>`;
}
function setView(nextView) {
  currentView = nextView;
  selectedKey = "";
  document.querySelectorAll("[data-view]").forEach((button) => button.classList.toggle("active", button.dataset.view === nextView));
  document.querySelectorAll("[data-nav]").forEach((button) => button.classList.toggle("active", button.dataset.nav === nextView));
  syncStatusOptions();
  renderTable();
}
document.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
document.querySelectorAll("[data-nav]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.nav)));
$("searchInput").addEventListener("input", renderTable);
$("statusFilter").addEventListener("change", renderTable);
$("riskFilter").addEventListener("change", renderTable);
renderDecisions();
renderGaps();
setView("work");
</script>
</body>
</html>
"""
    replacements = {
        "__PAYLOAD__": html_json(payload),
        "__PROJECT__": cell(project.name),
        "__STAGE__": cell(stage),
	        "__VALIDATION__": validation_status,
	        "__WORK_COUNT__": str(counts["work_items"]),
	        "__REFERENCE_COUNT__": str(counts["references"]),
	        "__ASSET_COUNT__": str(counts["assets"]),
	        "__GOAL_PHASE__": cell(phase),
	        "__GOAL_COUNT__": str(len(goals)),
	        "__ARTIFACT_COUNT__": str(counts["artifacts"]),
        "__VALIDATION_CLASS__": "pass" if validation_status == "PASS" else "check",
        "__NEXT_ACTION__": cell(next_action),
        "__STATUS_OPTIONS__": status_options,
        "__ROW_COUNT__": f"{len(work_items)} 条",
        "__TABLE_HEAD__": table_head,
        "__TABLE_BODY__": table_body,
        "__GAP_COUNT__": f"{len(gaps)} 条",
        "__GAP_BODY__": gap_body,
        "__SELECTED_PROPS__": selected_props,
        "__SELECTED_OBJECTIVE__": cell(selected_objective),
        "__DECISIONS__": decision_html,
    }
    for placeholder, value in replacements.items():
        html_doc = html_doc.replace(placeholder, value)
    dashboard_path = project / DASHBOARD_REL
    write_text(dashboard_path, html_doc)
    return dashboard_path


def audit_dashboard(project: Path) -> list[str]:
    path = project / DASHBOARD_REL
    if not path.exists():
        return ["操作台 HTML 尚未生成。"]
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []
    required_markers = {
        "data-view=\"work\"": "缺少工作 Tab。",
        "data-view=\"sources\"": "缺少资料 Tab。",
        "data-view=\"references\"": "缺少参考 Tab。",
        "data-view=\"visualAssets\"": "缺少图片 Tab。",
        "data-view=\"creativeRuns\"": "缺少创意运行 Tab。",
        "data-view=\"goals\"": "缺少 Goal Tab。",
        "data-view=\"artifacts\"": "缺少产物 Tab。",
        "data-view=\"gates\"": "缺少关卡 Tab。",
        "data-view=\"confirmations\"": "缺少待确认 Tab。",
        "id=\"searchInput\"": "缺少搜索框。",
        "id=\"statusFilter\"": "缺少状态筛选。",
        "id=\"riskFilter\"": "缺少风险筛选。",
        "当前选中项": "缺少右侧检查器。",
        "<h3>待确认</h3>": "缺少待确认区。",
        "@media (max-width: 760px)": "缺少移动端降级。",
        "data-label=": "缺少移动端卡片式表格标签。",
        "const DATA =": "缺少嵌入数据。",
    }
    for marker, message in required_markers.items():
        if marker not in text:
            issues.append(message)
    unresolved = [
        marker
        for marker in [
            "__PAYLOAD__",
            "__PROJECT__",
            "__TABLE_BODY__",
            "__SELECTED_PROPS__",
            "__DECISIONS__",
        ]
        if marker in text
    ]
    if unresolved:
        issues.append(f"操作台存在未替换占位符：{', '.join(unresolved)}")
    if "<tbody id=\"tableBody\"></tbody>" in text:
        issues.append("首屏 Work 表格没有静态行。")
    if "广告创意操作台" not in text or "需要你确认" not in text:
        issues.append("非开发者关键入口文案缺失。")
    return issues


@dataclass
class CouncilResult:
    name: str
    status: str
    evidence: list[str]
    issues: list[str]


def council_status(results: list[CouncilResult]) -> str:
    if any(result.status == "BLOCKED" for result in results):
        return "BLOCKED"
    if any(result.status == "PARTIAL" for result in results):
        return "PARTIAL_PASS"
    return "PASS"


def run_council(project: Path) -> tuple[str, list[CouncilResult], Path]:
    errors, stats = validate(project)
    counts = read_counts(project)
    dashboard_path = project / DASHBOARD_REL
    board_path = project / "AD-creative/handoff/项目看板.md"
    confirm_path = project / "AD-creative/handoff/待你确认.md"
    _, artifacts = read_csv_rows(project / "AD-creative/orchestrator/artifact_index.csv")
    _, visual_assets = read_csv_rows(project / "AD-creative/visual_assets/asset_manifest.csv")

    strategy_issues = []
    if counts["source_events"] == 0:
        strategy_issues.append("未登记客户资料或项目输入。")
    if counts["work_items"] == 0:
        strategy_issues.append("没有可执行工作项。")
    strategy = CouncilResult(
        "Strategy Council",
        "PASS" if not strategy_issues else "PARTIAL",
        [
            f"source_events={counts['source_events']}",
            f"work_items={counts['work_items']}",
            "下一步聚焦需求/缺口/客户追问。",
        ],
        strategy_issues,
    )

    ops_issues = list(errors)
    for artifact in artifacts:
        visibility = artifact.get("visibility", "").lower()
        gate_status = artifact.get("gate_status", "").lower()
        is_client_visible = visibility in CLIENT_VISIBLE_VALUES
        has_pass_gate = gate_status in PASS_GATE_VALUES
        if is_client_visible and not has_pass_gate:
            ops_issues.append(
                f"client-visible artifact without pass gate: {artifact.get('artifact_id')}"
            )
    for asset in visual_assets:
        visibility = asset.get("visibility", "").lower()
        qa_status = asset.get("qa_status", "").upper()
        if visibility in CLIENT_VISIBLE_VALUES and qa_status != "PASS":
            ops_issues.append(f"client-visible asset without QA PASS: {asset.get('asset_id')}")
    operations = CouncilResult(
        "Operations Council",
        "PASS" if not ops_issues else "BLOCKED",
        [
            f"validation_errors={len(errors)}",
            f"artifacts={counts['artifacts']}",
            f"references={counts['references']}",
            f"assets={counts['assets']}",
            "客户可见产物必须有 Gate。",
            "客户可见图片必须 QA PASS。",
        ],
        ops_issues,
    )

    craft_issues = audit_dashboard(project)
    if not board_path.exists() or len(board_path.read_text(encoding="utf-8")) < 180:
        craft_issues.append("项目看板内容不足。")
    confirm_text = confirm_path.read_text(encoding="utf-8") if confirm_path.exists() else ""
    has_clear_empty_state = "当前无必须立即确认" in confirm_text
    has_decision_rows = bool(re.search(r"\|\s*(Q|DEC)-", confirm_text))
    if not confirm_path.exists() or not (has_clear_empty_state or has_decision_rows):
        craft_issues.append("待确认信息不够清晰。")
    craft = CouncilResult(
        "Craft Council",
        "PASS" if not craft_issues else "PARTIAL",
        [
            "操作台采用可搜索/筛选列表、右侧检查器、底部决策栏。",
            "操作台显示工作、资料、参考、图片、产物、关卡、待确认。",
            "操作台有静态首屏和浏览器交互增强。",
            "非开发者优先看 handoff，不直接编辑 CSV。",
        ],
        craft_issues,
    )

    results = [strategy, operations, craft]
    overall = council_status(results)
    report_path = project / COUNCIL_REPORT_REL
    report_sections = []
    for result in results:
        evidence = "\n".join(f"- {item}" for item in result.evidence)
        issues = "\n".join(f"- {item}" for item in result.issues) or "- 无"
        report_sections.append(
            f"""## {result.name}
Status: {result.status}

Evidence:
{evidence}

Issues:
{issues}
"""
        )

    write_text(
        report_path,
        f"""# Three Council Readiness Report

Generated: {now_iso()}
Overall: {overall}

{''.join(report_sections)}
## Self-Approval Boundary
Allowed after PASS:
- 初始化模板
- 登记资料
- 内部需求/缺口整理
- 公开官方来源搜索计划
- 内部视觉方向草图规划
- 只读操作台刷新
- 内部 Gate 初检

Still requires explicit confirmation:
- 发送客户稿
- 付费、登录、私密账号、KYC、钱包或凭据
- 上传客户资料到外部平台
- 全局安装 Skill
- 覆盖或删除旧版本
- 将 AI 图标记为客户可见
""",
    )

    update_or_append_csv_row(
        project / "AD-creative/orchestrator/gate_log.csv",
        "gate_id",
        {
            "gate_id": "GATE-THREE-COUNCIL-READINESS",
            "stage": "project_readiness",
            "status": overall,
            "score": "3/3" if overall == "PASS" else "",
            "checked_artifacts": "",
            "blocking_issues": ";".join(
                issue for result in results for issue in result.issues
            ),
            "revision_items": "",
            "questions": "",
            "next_state": "ready_for_non_developer_operation"
            if overall == "PASS"
            else "revise_readiness",
            "created_at": now_iso(),
            "owner": "three_council",
        },
    )
    return overall, results, report_path


def status_payload(project: Path) -> dict[str, object]:
    project = project.resolve()
    counts = read_counts(project)
    errors, _ = validate(project)
    dashboard = project / DASHBOARD_REL
    report = project / COUNCIL_REPORT_REL
    _, work_items = read_csv_rows(project / "AD-creative/orchestrator/work_items.csv")
    _, gaps = read_csv_rows(project / "AD-creative/orchestrator/gaps.csv")
    confirmations = parse_confirmation_rows(project / "AD-creative/handoff/待你确认.md")
    active_work = [
        row
        for row in work_items
        if row.get("status", "").strip().lower() not in {"done", "closed", "resolved"}
    ]
    open_gaps = [
        row
        for row in gaps
        if row.get("status", "").strip().lower() not in {"resolved", "closed", "done"}
    ]
    blocking_gaps = [
        row
        for row in open_gaps
        if row.get("impact", "").strip().lower() in {"blocking", "high_impact"}
    ]
    if errors:
        next_status = "VALIDATION_CHECK"
        next_action = "Fix validation errors before continuing."
    elif confirmations:
        next_status = "WAITING_FOR_CONFIRMATION"
        next_action = first_nonempty(confirmations[0].get("question"), default="Resolve pending confirmation.")
    elif active_work:
        next_status = "ACTIVE_WORK"
        next_action = first_nonempty(active_work[0].get("title"), active_work[0].get("objective"), default="Continue active work item.")
    elif blocking_gaps:
        next_status = "BLOCKING_GAP"
        next_action = first_nonempty(
            blocking_gaps[0].get("recommended_action"),
            blocking_gaps[0].get("description"),
            default="Resolve blocking gap.",
        )
    elif open_gaps:
        next_status = "OPEN_GAP"
        next_action = first_nonempty(
            open_gaps[0].get("recommended_action"),
            open_gaps[0].get("description"),
            default="Review open gap.",
        )
    elif counts["source_events"] == 0:
        next_status = "NEEDS_MATERIAL"
        next_action = "Run adco run <project> --material <brief_file_or_folder>."
    else:
        next_status = "READY_FOR_NEXT_GATE"
        next_action = "Run the next stage Gate or continue with ad-creative:next."
    goal = latest_goal_row(project)
    phase = derive_goal_phase(project)
    next_command = ""
    if next_status == "NEEDS_MATERIAL":
        next_command = f"adco run {project} --material <brief_file_or_folder>"
    elif next_status == "READY_FOR_NEXT_GATE":
        next_command = f"adco goal-run {project} --goal-id latest --max-steps 1"
    elif next_status == "ACTIVE_WORK":
        next_command = f"adco goal-run {project} --goal-id latest --max-steps 1"

    payload: dict[str, object] = {
        "project": str(project),
        "stage": project_stage(project),
        "phase": phase,
        "phase_name": GOAL_PHASE_NAMES.get(phase, phase),
        "goal_id": goal.get("goal_id") if goal else "",
        "goal": goal or {},
        "lane_states": goal_lane_states(project),
        "validation": "PASS" if not errors else "CHECK",
        "counts": counts,
        "active_work_count": len(active_work),
        "open_gap_count": len(open_gaps),
        "blocking_gap_count": len(blocking_gaps),
        "pending_confirmation_count": len(confirmations),
        "next_status": next_status,
        "next_action": next_action,
        "active_work": active_work[:5],
        "open_gaps": open_gaps[:5],
        "blocking_gaps": blocking_gaps[:5],
        "pending_confirmations": confirmations[:5],
        "dashboard": str(dashboard) if dashboard.exists() else None,
        "council_report": str(report) if report.exists() else None,
        "errors": errors,
        "next_command": next_command,
    }
    payload["completion_readiness"] = goal_completion_readiness(project, errors, confirmations)
    payload["stop_reason"] = goal_stop_reason(payload)
    return payload


def print_status(project: Path) -> None:
    payload = status_payload(project)
    counts = payload["counts"]
    print(f"PROJECT={payload['project']}")
    print(f"STAGE={payload['stage']}")
    print(f"PHASE={payload['phase']}")
    print(f"GOAL_ID={payload['goal_id']}")
    print(f"VALIDATION={payload['validation']}")
    print(f"SOURCE_EVENTS={counts['source_events']}")
    print(f"REQUIREMENTS={counts['requirements']}")
    print(f"GAPS={counts['gaps']}")
    print(f"WORK_ITEMS={counts['work_items']}")
    print(f"ACTIVE_WORK={payload['active_work_count']}")
    print(f"OPEN_GAPS={payload['open_gap_count']}")
    print(f"BLOCKING_GAPS={payload['blocking_gap_count']}")
    print(f"PENDING_CONFIRMATIONS={payload['pending_confirmation_count']}")
    print(f"REFERENCES={counts['references']}")
    print(f"ASSETS={counts['assets']}")
    print(f"ARTIFACTS={counts['artifacts']}")
    print(f"GATES={counts['gates']}")
    print(f"NEXT_STATUS={payload['next_status']}")
    print(f"NEXT_ACTION={payload['next_action']}")
    print(f"NEXT_COMMAND={payload['next_command']}")
    print(f"STOP_REASON={payload['stop_reason'] or 'NONE'}")
    print(f"DASHBOARD={payload['dashboard'] or 'MISSING'}")
    print(f"COUNCIL_REPORT={payload['council_report'] or 'MISSING'}")
    errors = payload["errors"]
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")


def all_source_event_ids(project: Path) -> list[str]:
    _, rows = read_csv_rows(project / "AD-creative/orchestrator/source_events.csv")
    return [row.get("source_event_id", "") for row in rows if row.get("source_event_id", "")]


def goal_run_step(project: Path, *, allow_generate: bool) -> tuple[str, str, str]:
    payload = status_payload(project)
    stop = goal_stop_reason(payload)
    if stop:
        return "stop", stop, str(payload.get("next_action", ""))

    counts = payload["counts"]
    if isinstance(counts, dict) and counts.get("source_events", 0) and counts.get("requirements", 0) == 0:
        source_ids = all_source_event_ids(project)
        perform_intake(project, source_ids, "goal-run 自动执行本地 intake。")
        render_handoff(project, "goal-run 自动执行本地 intake。", source_ids)
        render_dashboard(project)
        return "intake", "PASS", "Extracted requirements and gaps from registered materials."

    if not (project / DASHBOARD_REL).exists():
        dashboard = render_dashboard(project)
        return "dashboard", "PASS", safe_rel(project, dashboard)

    if not has_gate(project, "GATE-AUTO-VISUAL-QUALITY-001"):
        status, findings, report = review_visual_quality(project)
        render_dashboard(project)
        return "visual_quality_gate", status, f"{safe_rel(project, report)} findings={len(findings)}"

    if not has_gate(project, "GATE-AUTO-FILM-QUALITY-001"):
        status, findings, report = review_film_quality(project)
        render_dashboard(project)
        return "film_quality_gate", status, f"{safe_rel(project, report)} findings={len(findings)}"

    if not has_gate(project, "GATE-THREE-COUNCIL-READINESS"):
        status, _, report = run_council(project)
        render_dashboard(project)
        return "council", status, safe_rel(project, report)

    if not allow_generate:
        return "stop", "GENERATION_NOT_ALLOWED", "goal-run will not trigger Creative Production generation without --allow-generate."

    return "stop", "READY_FOR_HUMAN_REVIEW", "Deterministic internal actions are complete; choose search/generation/client-review next."


def run_goal(
    project: Path,
    *,
    goal_id: str,
    max_steps: int,
    allow_generate: bool,
) -> dict[str, object]:
    ensure_project(project)
    goal = resolve_goal_row(project, goal_id)
    if not goal:
        created_goal_id = default_goal_id()
        plan = render_goal_iteration_plan(
            project,
            goal_id=created_goal_id,
            title="Auto-created goal-run",
            objective="Run local deterministic ADCO goal steps until a safe stop condition.",
            owner="Main Controller",
        )
        goal = resolve_goal_row(project, created_goal_id) or {"goal_id": created_goal_id, "path": safe_rel(project, plan)}

    append_event(
        project,
        {
            "event_id": f"EVT-GOAL-RUN-{safe_artifact_suffix(goal.get('goal_id', 'GOAL'))}-{datetime.now().strftime('%H%M%S')}",
            "event_type": "goal_run_started",
            "created_at": now_iso(),
            "goal_id": goal.get("goal_id", ""),
            "max_steps": max_steps,
            "allow_generate": allow_generate,
        },
    )
    steps: list[dict[str, str]] = []
    stop_reason = ""
    for index in range(1, max(1, max_steps) + 1):
        action, status, detail = goal_run_step(project, allow_generate=allow_generate)
        steps.append(
            {
                "step": str(index),
                "action": action,
                "status": status,
                "detail": detail,
            }
        )
        append_event(
            project,
            {
                "event_id": f"EVT-GOAL-RUN-STEP-{index}-{datetime.now().strftime('%H%M%S')}",
                "event_type": "goal_run_step",
                "created_at": now_iso(),
                "goal_id": goal.get("goal_id", ""),
                "action": action,
                "status": status,
                "detail": detail,
            },
        )
        if action == "stop" or status == "BLOCKED":
            stop_reason = status
            break
    else:
        stop_reason = "MAX_STEPS_REACHED"

    dashboard = render_dashboard(project)
    payload = status_payload(project)
    if not stop_reason:
        stop_reason = str(payload.get("stop_reason") or "READY_FOR_NEXT_STEP")
    append_event(
        project,
        {
            "event_id": f"EVT-GOAL-RUN-STOP-{datetime.now().strftime('%H%M%S')}",
            "event_type": "goal_run_stopped",
            "created_at": now_iso(),
            "goal_id": goal.get("goal_id", ""),
            "stop_reason": stop_reason,
            "steps": steps,
            "dashboard": safe_rel(project, dashboard),
        },
    )
    return {
        "project": str(project),
        "goal_id": goal.get("goal_id", ""),
        "stop_reason": stop_reason,
        "steps": steps,
        "dashboard": str(dashboard),
        "status": payload,
    }


def inspect_pptx(path: Path) -> dict[str, int | bool | str]:
    if not path.exists():
        raise FileNotFoundError(f"pptx not found: {path}")
    slide_files: list[str] = []
    text_runs = 0
    image_refs = 0
    has_presentation = False
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        name_set = set(names)
        has_presentation = "ppt/presentation.xml" in name_set
        slide_files = sorted(
            name
            for name in names
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )
        media_files = [name for name in names if name.startswith("ppt/media/")]
        image_refs = len(media_files)
        for slide_name in slide_files:
            root = ET.fromstring(archive.read(slide_name))
            text_runs += sum(
                1
                for text_node in root.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}t")
                if text_node.text and text_node.text.strip()
            )
    editable = bool(has_presentation and slide_files and text_runs)
    return {
        "slides": len(slide_files),
        "editable_text_runs": text_runs,
        "embedded_media": image_refs,
        "has_presentation": has_presentation,
        "editable": editable,
    }


def write_pptx_check(project: Path, pptx_path: Path, stats: dict[str, int | bool | str]) -> Path:
    rel_pptx = safe_rel(project, pptx_path)
    status = "PASS" if stats["editable"] else "BLOCKED"
    check_path = project / "AD-creative/ppt/ppt_editability_check.md"
    write_text(
        check_path,
        f"""# PPT Editability Check

status: {status}
visibility: internal_only
checked_at: {now_iso()}
pptx: {rel_pptx}

## Result

| Check | Value |
| --- | --- |
| has_presentation_xml | {stats['has_presentation']} |
| slides | {stats['slides']} |
| editable_text_runs | {stats['editable_text_runs']} |
| embedded_media | {stats['embedded_media']} |
| editable | {stats['editable']} |

## Rules

- `editable=true` 只代表 PPTX 内存在可编辑文本层。
- 图片页若存在，必须在客户稿前说明用途、来源和可替换性。
- 客户可见前仍需 Delivery Gate。
""",
    )
    update_artifact(
        project,
        "ART-AUTO-PPTX",
        "pptx",
        rel_pptx,
        "ppt_gate",
        status="done" if stats["editable"] else "blocked",
        visibility="internal_only",
        gate_status=status,
    )
    update_artifact(
        project,
        "ART-AUTO-PPT-EDITABILITY",
        "ppt_editability_check",
        safe_rel(project, check_path),
        "ppt_gate",
        status="done",
        visibility="internal_only",
        gate_status=status,
    )
    append_gate(
        project,
        "GATE-AUTO-PPT-001",
        "ppt_gate",
        status,
        "90" if stats["editable"] else "35",
        "ART-AUTO-PPTX;ART-AUTO-PPT-EDITABILITY",
        "" if stats["editable"] else "PPTX 缺少可编辑文本层。",
        "客户可见前检查图片来源、页面备注和最终交付一致性。",
        "",
        "ready_for_internal_review" if stats["editable"] else "rebuild_pptx",
        "ad_creative_operator",
    )
    append_event(
        project,
        {
            "event_id": "EVT-AUTO-PPTX-CHECK",
            "event_type": "pptx_editability_checked",
            "created_at": now_iso(),
            "pptx": rel_pptx,
            "stats": stats,
        },
    )
    return check_path


RISKY_CLIENT_COPY_PATTERNS = [
    "internal_only",
    "internal note",
    "内部",
    "TODO",
    "TBD",
    "fake logo",
    "假 logo",
    "假logo",
    "placeholder-only",
    "simulated",
    "模拟",
    "do not send",
]
RISKY_CLIENT_COPY_PATTERNS_LOWER = tuple(pattern.lower() for pattern in RISKY_CLIENT_COPY_PATTERNS)
RISKY_CLIENT_COPY_PATTERN = re.compile(
    "|".join(
        re.escape(pattern)
        for pattern in sorted(RISKY_CLIENT_COPY_PATTERNS_LOWER, key=len, reverse=True)
    )
)


def candidate_client_files(project: Path, artifacts: list[dict[str, str]]) -> list[Path]:
    files: list[Path] = []
    for artifact in artifacts:
        visibility = artifact.get("visibility", "").lower()
        if visibility not in CLIENT_VISIBLE_VALUES:
            continue
        rel_path = artifact.get("path", "").strip()
        path = project / rel_path
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".csv"}:
            files.append(path)
    return sorted(files)


def artifact_path_by_id(project: Path, artifacts: list[dict[str, str]], artifact_id: str) -> Path | None:
    for artifact in artifacts:
        if artifact.get("artifact_id", "").strip() == artifact_id:
            rel_path = artifact.get("path", "").strip()
            return project / rel_path if rel_path else None
    return None


def current_pptx_path(project: Path, artifacts: list[dict[str, str]]) -> tuple[Path | None, bool]:
    current_truth = project / "AD-creative/orchestrator/current_truth.md"
    if not current_truth.exists():
        return None, False
    artifact_id = current_truth_value(
        current_truth.read_text(encoding="utf-8"), "current_pptx_artifact_id"
    )
    if not artifact_id:
        return None, False
    return artifact_path_by_id(project, artifacts, artifact_id), True


def review_client_pack(project: Path, pptx_path: Path | None = None) -> tuple[str, list[str], Path]:
    _, artifacts = read_csv_rows(project / "AD-creative/orchestrator/artifact_index.csv")
    _, version_map = read_csv_rows(project / "AD-creative/orchestrator/version_map.csv")
    _, feedback_rows = read_csv_rows(project / "AD-creative/feedback/feedback_map.csv")
    _, assets = read_csv_rows(project / "AD-creative/visual_assets/asset_manifest.csv")
    _, references = read_csv_rows(project / "AD-creative/references/reference_cards.csv")
    issues: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = []

    for artifact in artifacts:
        visibility = artifact.get("visibility", "").lower()
        gate_status = artifact.get("gate_status", "").lower()
        if visibility in CLIENT_VISIBLE_VALUES and gate_status not in PASS_GATE_VALUES:
            issues.append(f"客户可见产物未通过 Gate: {artifact.get('artifact_id')}")

    issues.extend(
        validate_client_delivery_readiness(
            project, artifacts, version_map, feedback_rows
        )
    )

    for asset in assets:
        visibility = asset.get("visibility", "").lower()
        qa_status = asset.get("qa_status", "").upper()
        status = asset.get("status", "").lower()
        asset_type = asset.get("asset_type", "").lower()
        notes = asset.get("notes", "").lower()
        reference_id = asset.get("reference_id", "").strip()
        if visibility in CLIENT_VISIBLE_VALUES:
            if qa_status != "PASS":
                issues.append(f"客户可见图片 QA 未 PASS: {asset.get('asset_id')}")
            if status not in CLIENT_REVIEW_ASSET_STATUSES:
                issues.append(f"客户可见图片未进入 selected/approved: {asset.get('asset_id')}")
            if asset_type == "generated_image" and "client_visibility_approved" not in notes:
                issues.append(f"客户可见生成图缺少批准记录: {asset.get('asset_id')}")
            if reference_id in {"", "pending"}:
                issues.append(f"客户可见图片未绑定真实参考: {asset.get('asset_id')}")

    for reference in references:
        if reference.get("client_visible", "").lower() == "true":
            url = reference.get("url", "")
            if not url.startswith("https://"):
                issues.append(f"客户可见参考不是 https: {reference.get('reference_id')}")
            if reference.get("do_not_copy", "").strip() == "":
                issues.append(f"客户可见参考缺少 do_not_copy: {reference.get('reference_id')}")

    exact_current_pptx, current_pptx_declared = current_pptx_path(project, artifacts)
    if current_pptx_declared and not exact_current_pptx:
        issues.append("current_pptx_artifact_id 未解析到带 path 的 PPTX artifact。")
    if pptx_path and exact_current_pptx and pptx_path.resolve() != exact_current_pptx.resolve():
        issues.append(
            f"PPTX 检查目标不是 current_pptx_artifact_id 指向的当前文件: {safe_rel(project, pptx_path)}"
        )
    default_pptx = project / "AD-creative/ppt/client_review_draft.pptx"
    check_target = (
        exact_current_pptx
        if current_pptx_declared
        else pptx_path or (default_pptx if default_pptx.exists() else None)
    )
    pptx_stats: dict[str, int | bool | str] | None = None
    if check_target:
        if not check_target.exists():
            issues.append(f"PPTX 文件不存在: {safe_rel(project, check_target)}")
            evidence.append(
                f"pptx={safe_rel(project, check_target)} missing=true exact_current={current_pptx_declared}"
            )
        else:
            pptx_stats = inspect_pptx(check_target)
            if not pptx_stats["editable"]:
                issues.append("PPTX 缺少可编辑文本层。")
            evidence.append(
                f"pptx={safe_rel(project, check_target)} slides={pptx_stats['slides']} editable_text_runs={pptx_stats['editable_text_runs']} exact_current={current_pptx_declared}"
            )
    else:
        issues.append("未找到可审稿 PPTX。")

    scanned_files = candidate_client_files(project, artifacts)
    risky_hits: list[str] = []
    for path in scanned_files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="ignore")
        lowered = text.lower()
        risky_patterns = {match.group(0) for match in RISKY_CLIENT_COPY_PATTERN.finditer(lowered)}
        risky_hits.extend(f"{safe_rel(project, path)}: {pattern}" for pattern in risky_patterns)
    if risky_hits:
        issues.extend(f"客户稿候选含风险词: {hit}" for hit in sorted(risky_hits)[:12])

    status = "PASS" if not issues else "BLOCKED"
    status = enforce_adversarial_gate_policy(
        project, "final_delivery", status, warnings, evidence
    )
    report_path = project / "AD-creative/gates/GATE-AUTO-CLIENT-PACK-001_report.md"
    evidence.extend(
        [
            f"client_candidate_files={len(scanned_files)}",
            f"artifacts={len(artifacts)}",
            f"assets={len(assets)}",
            f"references={len(references)}",
        ]
    )
    issue_text = "\n".join(f"- {issue}" for issue in issues) or "- 无"
    warning_text = "\n".join(f"- {warning}" for warning in warnings) or "- 无"
    evidence_text = "\n".join(f"- {item}" for item in evidence)
    write_text(
        report_path,
        f"""# Client Pack Gate

status: {status}
checked_at: {now_iso()}
visibility: internal_only

## Evidence

{evidence_text}

## Issues

{issue_text}

## Warnings

{warning_text}

## Rules

- 客户可见产物必须 Gate PASS。
- 客户可见图片必须 QA PASS 且进入 selected/approved。
- 客户可见参考必须是 https，并保留 do_not_copy。
- PPTX 必须存在可编辑文本层。
- 客户稿候选不能含内部注释、模拟标记、TODO/TBD、假 logo、placeholder-only。
- 当前交付包必须具备 current version、PPTX、PDF、preview、text extract、PPT editability 和 feedback closure 证据。
""",
    )
    update_artifact(
        project,
        "ART-AUTO-CLIENT-PACK-GATE",
        "client_pack_gate_report",
        safe_rel(project, report_path),
        "final_delivery",
        status="done" if status != "BLOCKED" else "blocked",
        visibility="internal_only",
        gate_status=status,
    )
    append_gate(
        project,
        "GATE-AUTO-CLIENT-PACK-001",
        "final_delivery",
        status,
        "92" if status == "PASS" else "65" if status == "PARTIAL_PASS" else "40",
        "ART-AUTO-CLIENT-PACK-GATE",
        ";".join(issues[:8]),
        ";".join(warnings[:8]) or "修正客户稿风险后重跑 client-pack-gate。",
        "",
        "ready_for_manual_send_confirmation" if status == "PASS" else "revise_client_pack",
        "ad_creative_operator",
    )
    append_event(
        project,
        {
            "event_id": "EVT-AUTO-CLIENT-PACK-GATE",
            "event_type": "client_pack_gate_run",
            "created_at": now_iso(),
            "status": status,
            "issues": issues[:12],
            "warnings": warnings[:12],
        },
    )
    return status, issues + warnings, report_path


def latest_gate_status(project: Path, gate_id: str) -> str:
    _, gates = read_csv_rows(project / "AD-creative/orchestrator/gate_log.csv")
    for row in reversed(gates):
        if row.get("gate_id") == gate_id:
            return row.get("status", "").strip().upper()
    return ""


def normalize_stage(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def markdown_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_markdown_separator(cells: list[str]) -> bool:
    return bool(cells) and all(set(cell.replace(" ", "")) <= {"-", ":"} for cell in cells)


def text_value_after_colon(line: str) -> str:
    if ":" not in line:
        return ""
    return line.split(":", 1)[1].strip()


def adversarial_report_paths(project: Path) -> list[Path]:
    candidates: list[Path] = []
    gate_dir = project / "AD-creative/gates"
    if gate_dir.exists():
        candidates.extend(
            path
            for path in gate_dir.glob("*.md")
            if "template" not in path.name.lower()
        )
    goal_dir = project / GOAL_ITERATIONS_REL
    if goal_dir.exists():
        candidates.extend(goal_dir.glob("*.md"))
    return sorted(candidates)


def has_adversarial_row_for_stage(text: str, stage: str) -> bool:
    target_stage = normalize_stage(stage)
    report_stage = ""
    for line in text.splitlines():
        if line.lower().startswith("stage:"):
            report_stage = normalize_stage(text_value_after_colon(line))
            break
    if report_stage and report_stage != target_stage:
        return False

    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = markdown_cells(line)
        if is_markdown_separator(cells):
            continue
        joined = " ".join(cells).lower()
        if "objection" in joined or "反对意见" in joined:
            continue

        if len(cells) >= 9:
            objection = cells[2]
            rebuttal = cells[6]
            revision = cells[7]
            gate_status = cells[8]
            if objection and rebuttal and revision and gate_status:
                return True
        elif len(cells) >= 5:
            row_stage = normalize_stage(cells[0])
            if row_stage and row_stage not in {target_stage, "all", "global"}:
                continue
            objection = cells[1]
            rebuttal = cells[2]
            revision = cells[3]
            gate_status = cells[4]
            if objection and rebuttal and revision and gate_status:
                return True
    return False


def adversarial_council_evidence(project: Path, stage: str) -> tuple[bool, list[str]]:
    evidence: list[str] = []
    for path in adversarial_report_paths(project):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if has_adversarial_row_for_stage(text, stage):
            evidence.append(safe_rel(project, path))
    return bool(evidence), evidence


def enforce_adversarial_gate_policy(
    project: Path,
    stage: str,
    status: str,
    warnings: list[str],
    evidence: list[str],
) -> str:
    has_record, records = adversarial_council_evidence(project, stage)
    evidence.append(
        "adversarial_council="
        + (";".join(records) if has_record else "missing")
    )
    if status == "PASS" and not has_record:
        warnings.append("缺少有效反驳性议会记录，Gate 最高只能 PARTIAL_PASS。")
        return "PARTIAL_PASS"
    return status


def default_goal_id() -> str:
    return datetime.now().strftime("GOAL-%Y%m%d-%H%M%S")


def safe_artifact_suffix(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()
    return cleaned[:48] or "GOAL"


@dataclass(frozen=True)
class ThreadRoleSpec:
    role_id: str
    label: str
    professional_identity: str
    purpose: str
    default_environment: str
    default_write_scope: str
    read_first: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    required_output: tuple[str, ...]
    stop_condition: str
    validation_proof: str


THREADOPS_ROLE_ORDER = (
    "brand_client",
    "copy_creative",
    "film_director",
    "art_design",
    "producer_risk",
    "qa_review",
)
THREADOPS_DEFAULT_ROLES = ("brand_client", "copy_creative", "qa_review")
THREADOPS_REGISTRY_FIELDS = [
    "thread_id",
    "title",
    "role",
    "lane_id",
    "work_id",
    "lifecycle_state",
    "pinned",
    "archived",
    "created_at",
    "updated_at",
    "cleanup_action",
    "notes",
    "goal_id",
    "mode",
    "environment",
    "workspace_path",
    "write_scope",
    "professional_identity",
    "receipt_path",
    "receipt_status",
    "reconciliation_status",
    "assigned_at",
    "returned_at",
    "reconciled_at",
    "archived_at",
    "cleanup_reason",
    "last_seen_at",
    "duplicate_of",
]
THREADOPS_AGENT_RUN_FIELDS = [
    "run_id",
    "work_id",
    "agent_role",
    "status",
    "started_at",
    "completed_at",
    "input_files",
    "output_files",
    "gate_id",
    "summary",
    "next_action",
    "thread_id",
    "lane_id",
    "receipt_path",
    "proof_status",
    "reconciliation_status",
]
THREADOPS_ROLE_SPECS = {
    "brand_client": ThreadRoleSpec(
        "BRAND_CLIENT",
        "BrandClient",
        "Brand strategist and client-demand interpreter.",
        "Check client intent, misunderstanding risk, brand fit, and missing decisions.",
        "read_only",
        "receipt only",
        (
            "AD-creative/orchestrator/current_truth.md",
            "AD-creative/orchestrator/requirements.csv",
            "AD-creative/orchestrator/gaps.csv",
            "AD-creative/handoff/待你确认.md",
        ),
        (
            "Inspect project truth, requirements, gaps, and handoff files.",
            "Propose questions, blockers, and client-risk guardrails.",
        ),
        (
            "Do not edit current_truth, version_map, artifact_index, gate_log, final exports, or client-visible files.",
            "Do not approve client send or mark AI assets client-visible.",
        ),
        (
            "client intent summary",
            "misunderstanding risks",
            "blocking questions",
            "recommended next action",
        ),
        "All client-intent risks and missing decisions are listed with evidence.",
        "Receipt references exact project files and rows inspected.",
    ),
    "copy_creative": ThreadRoleSpec(
        "COPY_CREATIVE",
        "CopyCreative",
        "Advertising copy lead for concepts, campaign lines, and tone.",
        "Review concept clarity, message hierarchy, headlines, and proposal language.",
        "isolated_workspace",
        "AD-creative/workspaces/{work_id}/{lane_id}/copy_drafts.md; AD-creative/agents/receipts/{work_id}/{lane_id}_receipt.md",
        (
            "AD-creative/creative/creative_directions.md",
            "AD-creative/copywriting/message_line_candidates.md",
            "AD-creative/client_review/client_review_outline.md",
            "AD-creative/client_review/slide_spec.md",
        ),
        (
            "Inspect copy and proposal structure.",
            "Draft rewrites only in the lane workspace and receipt path declared by write_scope.",
        ),
        (
            "Do not rewrite client-visible files directly unless the lane plan grants an exact write path.",
            "Do not remove story, brand mapping, timing, or key dialogue to simplify layout.",
        ),
        (
            "copy diagnosis",
            "candidate wording",
            "message hierarchy risks",
            "revision checklist",
        ),
        "Copy risks and proposed replacements are concrete enough for the master thread to merge.",
        "Receipt includes old/new wording or target section references.",
    ),
    "film_director": ThreadRoleSpec(
        "FILM_DIRECTOR",
        "FilmDirector",
        "Commercial film director focused on story logic and scene rhythm.",
        "Review treatment, story beats, timing, scene transitions, and dialogue labels.",
        "isolated_workspace",
        "AD-creative/workspaces/{work_id}/{lane_id}/film_notes.md; AD-creative/agents/receipts/{work_id}/{lane_id}_receipt.md",
        (
            "AD-creative/film/treatment_packet.md",
            "AD-creative/film/shot_list_storyboard_plan.md",
            "AD-creative/film/production_constraints.md",
            "AD-creative/client_review/slide_spec.md",
        ),
        (
            "Inspect film/story files and slide spec.",
            "Draft story, timing, and shot-level fixes only in the lane workspace and receipt path declared by write_scope.",
        ),
        (
            "Do not export PPT/PDF.",
            "Do not invent unavailable production facts or talent approvals.",
        ),
        (
            "story logic review",
            "timing and rhythm notes",
            "shot/scene risks",
            "fix recommendations",
        ),
        "Story and scene issues are listed with file/section evidence.",
        "Receipt identifies affected scenes, slides, or treatment sections.",
    ),
    "art_design": ThreadRoleSpec(
        "ART_DESIGN",
        "ArtDesign",
        "Art director for visual system, layout, typography, and image quality.",
        "Review visual direction, asset slots, layout risks, and client-visible image safety.",
        "isolated_workspace",
        "AD-creative/workspaces/{work_id}/{lane_id}/art_direction_notes.md; AD-creative/agents/receipts/{work_id}/{lane_id}_receipt.md",
        (
            "AD-creative/ppt/ppt_visual_system.md",
            "AD-creative/visual_assets/asset_manifest.csv",
            "AD-creative/visual_assets/visual_asset_slots.csv",
            "AD-creative/visual_review/visual_qa_checklist.md",
        ),
        (
            "Inspect visual system, asset manifest, asset slots, and QA checklist.",
            "Draft visual risks and exact gate/checklist additions only in the lane workspace and receipt path declared by write_scope.",
        ),
        (
            "Do not mark generated assets client-visible.",
            "Do not replace source images or final exports.",
        ),
        (
            "visual system diagnosis",
            "asset safety risks",
            "layout QA issues",
            "gate recommendations",
        ),
        "Visual risks are tied to asset ids, slots, or checklist items.",
        "Receipt names asset/slot ids and required gate checks.",
    ),
    "producer_risk": ThreadRoleSpec(
        "PRODUCER_RISK",
        "ProducerRisk",
        "Producer and risk controller for feasibility, scope, legal, and platform constraints.",
        "Review feasibility, budget/scope exposure, rights risk, platform risk, and stop points.",
        "read_only",
        "receipt only",
        (
            "AD-creative/orchestrator/decisions.csv",
            "AD-creative/orchestrator/resolutions.csv",
            "AD-creative/film/production_constraints.md",
            "AD-creative/handoff/待你确认.md",
        ),
        (
            "Inspect decisions, resolutions, constraints, and pending confirmations.",
            "Return production risks, stop points, and owner assignments.",
        ),
        (
            "Do not approve paid, login, upload, send, identity, KYC, wallet, or private-account actions.",
            "Do not downgrade blockers without evidence.",
        ),
        (
            "feasibility risk list",
            "stop conditions",
            "owner/action matrix",
            "scope guardrails",
        ),
        "Every high-risk action has an owner, stop condition, and evidence path.",
        "Receipt lists blocker severity and affected delivery stage.",
    ),
    "qa_review": ThreadRoleSpec(
        "QA_REVIEW",
        "QAReview",
        "Independent adversarial reviewer and evidence checker.",
        "Cold-review the proposed handoff, validation evidence, thread cleanup, and missing tests.",
        "read_only",
        "receipt only",
        (
            "AD-creative/orchestrator/thread_lane_plan.md",
            "AD-creative/orchestrator/thread_registry.csv",
            "AD-creative/orchestrator/artifact_index.csv",
            "AD-creative/orchestrator/gate_log.csv",
        ),
        (
            "Inspect changed control-plane files and validation output.",
            "Return severity-ranked findings and final readiness gate.",
        ),
        (
            "Do not edit files.",
            "Do not mark final readiness without validation and cleanup proof.",
        ),
        (
            "severity-ranked findings",
            "missing validation",
            "thread cleanup issues",
            "approve/block recommendation",
        ),
        "Review is complete when blocker, risk, and validation gaps are enumerated.",
        "Receipt includes validation command/output references and cleanup status.",
    ),
}
THREADOPS_ROLE_ALIASES = {
    "brand": "brand_client",
    "brand_client": "brand_client",
    "client": "brand_client",
    "copy": "copy_creative",
    "copy_creative": "copy_creative",
    "creative": "copy_creative",
    "film": "film_director",
    "film_director": "film_director",
    "director": "film_director",
    "art": "art_design",
    "art_design": "art_design",
    "design": "art_design",
    "visual": "art_design",
    "producer": "producer_risk",
    "producer_risk": "producer_risk",
    "risk": "producer_risk",
    "qa": "qa_review",
    "qa_review": "qa_review",
    "review": "qa_review",
}

READ_ONLY_THREADOPS_ROLES = {"brand_client", "producer_risk"}
THREADOPS_DEFAULT_LOOP_MODE = "sequential"
THREADOPS_LOOP_MODES = ("sequential", "rfc_dag", "continuous_pr", "infinite")
THREADOPS_OBSERVATION_CONTRACT = (
    "status success|warning|error; summary one-line result; artifacts file paths or ids; "
    "next_actions actionable follow-ups; evidence_refs exact files, rows, or commands"
)
THREADOPS_ERROR_RECOVERY_CONTRACT = (
    "include root_cause_hint, safe_retry_instruction, and explicit_stop_condition; "
    "freeze after repeated same root cause or thread confusion"
)
THREADOPS_CONTEXT_BUDGET = (
    "role brief, lane plan, and declared read_first files only; load extra context only with a reason"
)
THREADOPS_ITERATION_BUDGET = (
    "max 3 internal passes per worker; no unbounded retries; main/control may lower the budget"
)
THREADOPS_REPLAY_TRIGGER = (
    "validation_result FAIL, missing required receipt field, stale evidence, out-of-scope edit, "
    "or reopened user/client feedback"
)
THREADOPS_FREEZE_TRIGGER = (
    "thread confusion, wrong-thread behavior, heat/cost spike, worker budget exceeded, "
    "same root cause twice, or cleanup request"
)
THREADOPS_PROMPT_ONLY_FORBIDDEN = (
    "prompt-only output is invalid for production workers; execution_worker must produce declared files "
    "or return BLOCKED with evidence"
)
THREADOPS_HELPER_DEFAULT_MODE = "none"
THREADOPS_HELPER_MODE = "stateless_secondary_helper"
THREADOPS_ALLOWED_HELPER_KINDS = (
    "image_generation",
    "ocr",
    "layout_lint",
    "asset_resize",
    "reference_extraction",
)
THREADOPS_HELPER_POLICY = (
    "optional bounded stateless helper/subagent-style local invocation inside a real Codex Thread worker; "
    "helper is stateless and cannot replace the worker/reviewer layer"
)
THREADOPS_HELPER_WRITE_BOUNDARY = (
    "helper has no thread_id, no thread_registry row, and no write_scope; "
    "any kept artifact must be written or imported by the L1 worker inside declared write_scope"
)
THREADOPS_HELPER_EVIDENCE_REQUIRED = (
    "when helper_mode is stateless_secondary_helper, receipt must include helper_invocations, "
    "helper_input_refs, helper_output_refs, helper_artifacts, helper_validation_result, "
    "helper_adopted_by_worker, helper_failure_reason if any, and worker_synthesis"
)
THREADOPS_HELPER_FAILURE_POLICY = (
    "helper failure cannot bypass worker validation; worker records failure reason, "
    "continues without helper evidence only when safe, or returns BLOCKED/PARTIAL"
)


def threadops_action_space(mode: str, write_scope: str) -> str:
    if mode == "execution_worker":
        return (
            "read declared inputs; write only declared workspace and receipt paths; "
            f"respect write_scope [{write_scope}]; no master truth, final export, send, upload, login, or paid action"
        )
    return (
        "read declared inputs; write receipt only; propose changes and blockers; "
        "do not edit artifacts, master truth, final exports, or client-visible files"
    )


def threadops_harness_contract(
    *,
    mode: str,
    write_scope: str,
    validation_proof: str,
    stop_condition: str,
) -> dict[str, str]:
    return {
        "action_space": threadops_action_space(mode, write_scope),
        "observation_contract": THREADOPS_OBSERVATION_CONTRACT,
        "error_recovery_contract": THREADOPS_ERROR_RECOVERY_CONTRACT,
        "context_budget": THREADOPS_CONTEXT_BUDGET,
        "iteration_budget": THREADOPS_ITERATION_BUDGET,
        "eval_gate": validation_proof,
        "adoption_decision": "pending_main_control_adoption",
        "rejection_reason": "required_if_adoption_decision_is_reject_or_partial",
        "loop_state": "planned",
        "replay_trigger": THREADOPS_REPLAY_TRIGGER,
        "freeze_trigger": THREADOPS_FREEZE_TRIGGER,
        "stop_condition": stop_condition,
    }


def format_threadops_contract(contract: dict[str, str]) -> str:
    return "\n".join(f"{key}: {value}" for key, value in contract.items())


def threadops_helper_contract() -> dict[str, str]:
    return {
        "helper_mode": THREADOPS_HELPER_DEFAULT_MODE,
        "helper_policy": THREADOPS_HELPER_POLICY,
        "allowed_helper_kinds": ",".join(THREADOPS_ALLOWED_HELPER_KINDS),
        "helper_write_boundary": THREADOPS_HELPER_WRITE_BOUNDARY,
        "helper_evidence_required": THREADOPS_HELPER_EVIDENCE_REQUIRED,
        "helper_failure_policy": THREADOPS_HELPER_FAILURE_POLICY,
        "helper_invocations": "none",
        "helper_input_refs": "none",
        "helper_output_refs": "none",
        "helper_artifacts": "none",
        "helper_validation_result": "not_applicable",
        "helper_adopted_by_worker": "no",
        "helper_failure_reason": "none",
        "worker_synthesis": "worker must synthesize and adopt/reject helper output before returning receipt",
    }


def format_threadops_helper_contract(contract: dict[str, str] | None = None) -> str:
    return format_threadops_contract(contract or threadops_helper_contract())


def threadops_loop_mode_contract() -> str:
    return """loop_mode: sequential
allowed_loop_modes: sequential,rfc_dag,continuous_pr,infinite
sequential: default; finish one bounded lane step before the next handoff
rfc_dag: use only when an RFC-style dependency graph is written in the lane plan
continuous_pr: use only for controlled PR/check cycles with explicit validation commands
infinite: bounded internal exploration only; must declare iteration_budget, freeze_trigger, replay_trigger, and stop_condition
safe_stop: stop before client-visible send, paid/private/upload actions, destructive edits, global install, validation failure, or missing receipt proof
replay_trigger: validation_result FAIL, missing receipt schema, stale evidence, out-of-scope edit, or reopened feedback
freeze_trigger: thread confusion, wrong thread, heat/cost spike, budget exceeded, repeated same root cause, or cleanup request
stop_condition: receipt reconciled, eval_gate passed or blocker recorded, adoption_decision recorded, and cleanup action planned"""


def threadops_lane_mode(role: str, spec: ThreadRoleSpec) -> str:
    if spec.default_environment in {"isolated_workspace", "worktree"}:
        return "execution_worker"
    if role == "brand_client":
        return "research"
    if role == "qa_review":
        return "cold_review"
    if role in READ_ONLY_THREADOPS_ROLES:
        return "read_only_review"
    return "read_only_review"


def threadops_workspace_path(work_id: str, lane_id: str, spec: ThreadRoleSpec) -> str:
    if spec.default_environment == "isolated_workspace":
        return f"AD-creative/workspaces/{work_id}/{lane_id}"
    if spec.default_environment == "worktree":
        return "declared_git_worktree_required"
    return "not_applicable_for_read_only"


def resolve_threadops_write_scope(work_id: str, lane_id: str, spec: ThreadRoleSpec) -> str:
    return spec.default_write_scope.format(work_id=work_id, lane_id=lane_id)


def markdown_table_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("|", "/")).strip()


def parse_threadops_roles(raw_roles: str) -> list[str]:
    raw_values = [item.strip().lower() for item in raw_roles.split(",") if item.strip()]
    if not raw_values:
        raw_values = list(THREADOPS_DEFAULT_ROLES)
    roles: list[str] = []
    for raw in raw_values:
        role = THREADOPS_ROLE_ALIASES.get(raw)
        if not role:
            choices = ", ".join(THREADOPS_ROLE_ORDER)
            raise ValueError(f"unknown ThreadOps role: {raw}; choices: {choices}")
        if role not in roles:
            roles.append(role)
    return roles


def current_version_id(project: Path) -> str:
    path = project / "AD-creative/orchestrator/current_truth.md"
    if not path.exists():
        return ""
    return current_truth_value(path.read_text(encoding="utf-8"), "current_version_id")


def default_threadops_work_id(goal_id: str) -> str:
    return f"WORK-{safe_artifact_suffix(goal_id)}-THREADS"


def default_task_signature_id(goal_id: str) -> str:
    return f"TS-{safe_artifact_suffix(goal_id)}"


def threadops_role_brief_content(
    *,
    spec: ThreadRoleSpec,
    goal_id: str,
    work_id: str,
    title: str,
    objective: str,
    task_signature: dict[str, str],
    mode: str,
    write_scope: str,
) -> str:
    contract = threadops_harness_contract(
        mode=mode,
        write_scope=write_scope,
        validation_proof=spec.validation_proof,
        stop_condition=spec.stop_condition,
    )
    helper_contract = threadops_helper_contract()
    project_facts = "\n".join(
        f"- {key}: {value or 'TBD'}" for key, value in task_signature.items()
    )
    read_first = "\n".join(f"- `{item}`" for item in spec.read_first)
    allowed = "\n".join(f"- {item}" for item in spec.allowed_actions)
    forbidden = "\n".join(f"- {item}" for item in spec.forbidden_actions)
    output = "\n".join(f"- {item}" for item in spec.required_output)
    return f"""# {spec.role_id} Role Brief

goal_id: {goal_id}
work_id: {work_id}
goal_title: {title}
role_id: {spec.role_id}
role_label: {spec.label}
mode: {mode}
environment: {spec.default_environment}
write_scope: {write_scope}
loop_mode: {THREADOPS_DEFAULT_LOOP_MODE}

## Professional Identity

{spec.professional_identity}

## Role Objective

{spec.purpose}

Goal objective: {objective}

## Project Facts To Honor

{project_facts}

## Read First

{read_first}

## Allowed Actions

{allowed}

## Forbidden Actions

{forbidden}

## Output Contract

{output}

## Harness Contract

```text
{format_threadops_contract(contract)}
```

## Loop Mode Contract

```text
{threadops_loop_mode_contract()}
```

## Stateless Secondary Helper Contract

```text
{format_threadops_helper_contract(helper_contract)}
```

## Acceptance Evidence

- Stop condition: {spec.stop_condition}
- Validation proof: {spec.validation_proof}
- Main/control thread is the only merge owner.
- Final PPT/PDF export is not allowed from this lane.
- Helpers are not Codex Threads, substitute workers, registry rows, or write scopes.
"""


def threadops_worker_prompt_content(
    *,
    project: Path,
    spec: ThreadRoleSpec,
    goal_id: str,
    work_id: str,
    lane_id: str,
    title: str,
    objective: str,
    task_signature_id: str,
    task_signature: dict[str, str],
    role_brief_path: Path,
    receipt_path: Path,
    extra_read_first: list[str],
    mode: str,
    workspace_path: str,
    write_scope: str,
) -> str:
    contract = threadops_harness_contract(
        mode=mode,
        write_scope=write_scope,
        validation_proof=spec.validation_proof,
        stop_condition=spec.stop_condition,
    )
    helper_contract = threadops_helper_contract()
    read_first = list(dict.fromkeys([*spec.read_first, *extra_read_first]))
    read_first_text = "\n".join(f"- {item}" for item in read_first)
    allowed = "\n".join(f"- {item}" for item in spec.allowed_actions)
    forbidden = "\n".join(f"- {item}" for item in spec.forbidden_actions)
    output = "\n".join(f"- {item}" for item in spec.required_output)
    task_signature_text = "\n".join(
        f"- {key}: {value or 'TBD'}" for key, value in task_signature.items()
    )
    execution_receipt = (
        "- write_scope\n"
        "- files_changed (required; prompt-only output is invalid)\n"
        "- validation_result\n"
        "- dirty_state_impact\n"
        "- manifest_index_updates\n"
        "- QA/gate status\n"
        "- adoption/rejection recommendation\n"
        "- recurrence_guard\n"
        "- cleanup_actions"
        if mode == "execution_worker"
        else "- files_inspected\n- proposed_changes\n- no_files_changed_confirmation\n- adoption/rejection recommendation"
    )
    return f"""Repo: {project}
Mode: {mode}
Loop mode: {THREADOPS_DEFAULT_LOOP_MODE}
Task signature: {task_signature_id}
Agent role md: {safe_rel(project, role_brief_path)}
Agency selection id: none
Agency role brief: {safe_rel(project, role_brief_path)}
Agency source agents: none
Source staff count: 0
Goal: {title}
Goal id: {goal_id}
Goal objective: {objective}
Work item: {work_id}
Lane id: {lane_id}

Task signature details:
{task_signature_text}

Harness contract:
{format_threadops_contract(contract)}

Loop mode contract:
{threadops_loop_mode_contract()}

Codex Thread contract:
- Main/control must create or reuse a real Codex Thread for this prompt and replace the planned thread id in thread_registry.csv.
- Codex Threads are not subagents and must not be simulated by role-play inside the control thread.
- Writable work requires an execution_worker lane with isolated_workspace or worktree write_scope.
- If real Codex Thread tooling or isolated writable scope is unavailable for writable work, stop with TOOL_BLOCKED instead of falling back.

Stateless secondary helper invocation contract:
{format_threadops_helper_contract(helper_contract)}
- A helper invocation may be backed by a stateless helper/subagent-style call, but it is not a Codex Thread, not a substitute worker/reviewer, has no thread_id, has no thread_registry.csv row, and has no write_scope.
- Helper output must be recorded in this L1 worker receipt, adopted or rejected by the worker, then exposed to main/control through the worker receipt.
- Do not call real image generation, OCR, or other helpers unless the lane task explicitly needs a bounded local subtask; this repo defines the contract only.

Read first:
{read_first_text}

Environment: {spec.default_environment}
Workspace path: {workspace_path}
Allowed actions:
{allowed}

Forbidden actions:
{forbidden}
- Do not edit files unless the lane plan grants an exact write path.
- Do not update current_truth, version_map, artifact_index, gate_log, or final exports.
- Do not send, upload, purchase, log in, or use private accounts.

Write scope: {write_scope}
Receipt path: {safe_rel(project, receipt_path)}
Stop condition: {spec.stop_condition}
Merge owner: main/control thread
Final export allowed: no
Completion proof: {spec.validation_proof}

Return format:
- summary
- write_scope: {write_scope}
{execution_receipt}
- evidence refs
- QA/gate status
- open questions
- adoption_decision: ADOPT, PARTIAL_ADOPT, REJECT, or BLOCKED recommendation
- rejection_reason: required when recommendation is not ADOPT
- loop_state
- replay_trigger
- freeze_trigger
- helper_mode
- helper_invocations
- helper_input_refs
- helper_output_refs
- helper_artifacts
- helper_validation_result
- helper_adopted_by_worker
- helper_failure_reason
- worker_synthesis
- workflow issue and recurrence guard, if found

Required output:
{output}
"""


def threadops_receipt_template_content(
    *,
    spec: ThreadRoleSpec,
    goal_id: str,
    work_id: str,
    lane_id: str,
    mode: str,
    workspace_path: str,
    write_scope: str,
) -> str:
    contract = threadops_harness_contract(
        mode=mode,
        write_scope=write_scope,
        validation_proof=spec.validation_proof,
        stop_condition=spec.stop_condition,
    )
    helper_contract = threadops_helper_contract()
    files_changed_rule = (
        "files_changed: required_non_empty_for_adopt; if no file changed, set status BLOCKED and explain the blocker"
        if mode == "execution_worker"
        else "files_changed: forbidden_for_read_only; confirm no files changed"
    )
    return f"""# {lane_id} Receipt

status: pending
goal_id: {goal_id}
work_id: {work_id}
role_id: {spec.role_id}
mode: {mode}
environment: {spec.default_environment}
workspace_path: {workspace_path}
write_scope: {write_scope}
thread_id: TBD
harness_id: HARN-{safe_artifact_suffix(work_id)}-{lane_id}
loop_mode: {THREADOPS_DEFAULT_LOOP_MODE}
prompt_only_output: invalid
production_receipt_rule: {THREADOPS_PROMPT_ONLY_FORBIDDEN}
helper_mode: {helper_contract["helper_mode"]}
helper_policy: {helper_contract["helper_policy"]}
allowed_helper_kinds: {helper_contract["allowed_helper_kinds"]}
helper_write_boundary: {helper_contract["helper_write_boundary"]}
helper_evidence_required: {helper_contract["helper_evidence_required"]}
helper_failure_policy: {helper_contract["helper_failure_policy"]}

## Harness Contract

```text
{format_threadops_contract(contract)}
```

## Loop Mode Contract

```text
{threadops_loop_mode_contract()}
```

## Stateless Secondary Helper Contract

```text
{format_threadops_helper_contract(helper_contract)}
```

## Helper Invocation Evidence

helper_mode: {THREADOPS_HELPER_DEFAULT_MODE}
helper_invocations: none
helper_input_refs: none
helper_output_refs: none
helper_artifacts: none
helper_validation_result: not_applicable
helper_adopted_by_worker: no
helper_failure_reason: none
worker_synthesis: none

## Observation

status: pending
summary: pending
artifacts: pending
next_actions: pending
evidence_refs: pending

## Files Changed

{files_changed_rule}

pending

## Validation Result

pending

## Dirty-State Impact

pending

## Manifest / Index Updates

pending

## QA / Gate Status

pending

## Open Questions

pending

## Recurrence Guard

pending

## Adoption / Rejection Recommendation

adoption_decision: pending
rejection_reason: pending_if_not_adopted
files_merged: pending_main_control_decision

## Cleanup Actions

pending

## Evidence

pending
"""


def render_thread_cleanup_note(
    project: Path,
    *,
    goal_id: str,
    work_id: str,
    roles: list[str],
    max_active: int,
) -> Path:
    output = project / f"AD-creative/orchestrator/thread_cleanup_{work_id}.md"
    role_lines = "\n".join(f"- {THREADOPS_ROLE_SPECS[role].role_id}: planned" for role in roles)
    write_text(
        output,
        f"""# Thread Cleanup Plan

goal_id: {goal_id}
work_id: {work_id}
status: planned
created_at: {now_iso()}

## Active Budget

- max_active_worker_reviewer: {max_active}
- main/control thread remains integration owner.
- worker/reviewer threads are archived after their receipts are reconciled.

## Planned Lanes

{role_lines}

## Audit Steps

1. Run `list_threads` with query `ADCO`.
2. Keep the main/control thread active.
3. Keep only lanes whose lifecycle is `created`, `assigned`, `running`, or `returned`.
4. Archive duplicate, stale, superseded, off-scope, or reconciled employee threads.
5. Record real thread ids and archive decisions in `AD-creative/orchestrator/thread_registry.csv`.
6. Before final status, confirm no consumed worker remains active.
""",
    )
    return output


def render_thread_execution_plan(
    project: Path,
    *,
    goal_id: str,
    title: str,
    objective: str,
    roles: list[str],
    work_id: str = "",
    task_signature_id: str = "",
    brand: str = "",
    product: str = "",
    talent_or_ip: str = "",
    platform_or_channel: str = "",
    deliverable: str = "",
    stage: str = "threadops",
    primary_risks: str = "",
    evidence_needed: str = "",
    master_thread_id: str = "",
    current_version: str = "",
    max_active: int = 3,
    extra_read_first: list[str] | None = None,
    force: bool = False,
) -> dict[str, object]:
    if not roles:
        raise ValueError("at least one ThreadOps role is required")
    if max_active < 1 or max_active > 3:
        raise ValueError("max_active_worker_reviewer must be between 1 and 3")
    if len(roles) > 5:
        raise ValueError("broad council over 5 roles requires explicit user approval")

    ensure_project(project)
    work_id = work_id or default_threadops_work_id(goal_id)
    task_signature_id = task_signature_id or default_task_signature_id(goal_id)
    current_version = current_version or current_version_id(project)
    extra_read_first = extra_read_first or []
    now = now_iso()
    task_signature = {
        "brand": brand,
        "product": product,
        "talent_or_ip": talent_or_ip,
        "platform_or_channel": platform_or_channel,
        "deliverable": deliverable,
        "stage": stage,
        "primary_risks": primary_risks,
        "evidence_needed": evidence_needed,
    }
    plan_path = project / "AD-creative/orchestrator/thread_lane_plan.md"
    if plan_path.exists() and not force:
        raise FileExistsError(f"thread lane plan already exists: {plan_path}; pass --force to replace it")
    ensure_csv_fields(project / "AD-creative/orchestrator/thread_registry.csv", THREADOPS_REGISTRY_FIELDS)
    ensure_csv_fields(project / "AD-creative/orchestrator/agent_runs.csv", THREADOPS_AGENT_RUN_FIELDS)

    role_dir = project / "AD-creative/agents/role_briefs"
    prompt_dir = project / f"AD-creative/agents/thread_prompts/{work_id}"
    receipt_dir = project / f"AD-creative/agents/receipts/{work_id}"
    role_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    receipt_dir.mkdir(parents=True, exist_ok=True)

    lane_rows: list[dict[str, str]] = []
    registry_rows: list[dict[str, str]] = []
    prompt_paths: list[Path] = []
    role_brief_paths: list[Path] = []
    receipt_paths: list[Path] = []

    for index, role in enumerate(roles, 1):
        spec = THREADOPS_ROLE_SPECS[role]
        lane_id = f"LANE-{index:02d}-{spec.role_id}"
        mode = threadops_lane_mode(role, spec)
        workspace_path = threadops_workspace_path(work_id, lane_id, spec)
        write_scope = resolve_threadops_write_scope(work_id, lane_id, spec)
        harness_contract = threadops_harness_contract(
            mode=mode,
            write_scope=write_scope,
            validation_proof=spec.validation_proof,
            stop_condition=spec.stop_condition,
        )
        helper_contract = threadops_helper_contract()
        run_id = f"RUN-{safe_artifact_suffix(work_id)}-{index:02d}"
        thread_title = f"ADCO 员工｜{spec.label}｜{title[:24] or work_id}"
        role_brief_path = role_dir / f"{spec.role_id}_{work_id}.md"
        prompt_path = prompt_dir / f"{lane_id}_prompt.md"
        receipt_path = receipt_dir / f"{lane_id}_receipt.md"
        role_brief_paths.append(role_brief_path)
        prompt_paths.append(prompt_path)
        receipt_paths.append(receipt_path)

        write_text(
            role_brief_path,
            threadops_role_brief_content(
                spec=spec,
                goal_id=goal_id,
                work_id=work_id,
                title=title,
                objective=objective,
                task_signature=task_signature,
                mode=mode,
                write_scope=write_scope,
            ),
        )
        write_text(
            prompt_path,
            threadops_worker_prompt_content(
                project=project,
                spec=spec,
                goal_id=goal_id,
                work_id=work_id,
                lane_id=lane_id,
                title=title,
                objective=objective,
                task_signature_id=task_signature_id,
                task_signature=task_signature,
                role_brief_path=role_brief_path,
                receipt_path=receipt_path,
                extra_read_first=extra_read_first,
                mode=mode,
                workspace_path=workspace_path,
                write_scope=write_scope,
            ),
        )
        write_text(
            receipt_path,
            threadops_receipt_template_content(
                spec=spec,
                goal_id=goal_id,
                work_id=work_id,
                lane_id=lane_id,
                mode=mode,
                workspace_path=workspace_path,
                write_scope=write_scope,
            ),
        )

        lane_rows.append(
            {
                "lane_id": lane_id,
                "thread_id": f"planned:{lane_id}",
                "thread_title": thread_title,
                "thread_role": spec.role_id,
                "professional_identity": spec.professional_identity,
                "agent_role_md": safe_rel(project, role_brief_path),
                "agency_selection_id": "none",
                "agency_role_brief": safe_rel(project, role_brief_path),
                "agency_source_agents": "none",
                "source_staff_count": "0",
                "work_id": work_id,
                "purpose": spec.purpose,
                "spawn_mode": "create_or_reuse_codex_thread",
                "mode": mode,
                "environment": spec.default_environment,
                "workspace_path": workspace_path,
                "read_first": ";".join([*spec.read_first, *extra_read_first]),
                "write_scope": write_scope,
                "receipt_path": safe_rel(project, receipt_path),
                "receipt_status": "missing",
                "reconciliation_status": "pending",
                "action_space": harness_contract["action_space"],
                "observation_contract": harness_contract["observation_contract"],
                "error_recovery_contract": harness_contract["error_recovery_contract"],
                "context_budget": harness_contract["context_budget"],
                "iteration_budget": harness_contract["iteration_budget"],
                "eval_gate": harness_contract["eval_gate"],
                "adoption_decision": harness_contract["adoption_decision"],
                "rejection_reason": harness_contract["rejection_reason"],
                "loop_state": harness_contract["loop_state"],
                "replay_trigger": harness_contract["replay_trigger"],
                "freeze_trigger": harness_contract["freeze_trigger"],
                "helper_mode": helper_contract["helper_mode"],
                "helper_policy": helper_contract["helper_policy"],
                "allowed_helper_kinds": helper_contract["allowed_helper_kinds"],
                "helper_write_boundary": helper_contract["helper_write_boundary"],
                "helper_evidence_required": helper_contract["helper_evidence_required"],
                "helper_failure_policy": helper_contract["helper_failure_policy"],
                "helper_invocations": helper_contract["helper_invocations"],
                "helper_input_refs": helper_contract["helper_input_refs"],
                "helper_output_refs": helper_contract["helper_output_refs"],
                "helper_artifacts": helper_contract["helper_artifacts"],
                "helper_validation_result": helper_contract["helper_validation_result"],
                "helper_adopted_by_worker": helper_contract["helper_adopted_by_worker"],
                "helper_failure_reason": helper_contract["helper_failure_reason"],
                "worker_synthesis": helper_contract["worker_synthesis"],
                "stop_condition": spec.stop_condition,
                "validation_proof": spec.validation_proof,
                "required_output": ";".join(spec.required_output),
                "merge_owner": "main/control thread",
                "final_export_allowed": "no",
                "lifecycle_status": "planned",
                "cleanup_note": "archive after receipt is reconciled",
                "run_id": run_id,
            }
        )
        registry_rows.append(
            {
                "thread_id": f"planned:{lane_id}",
                "title": thread_title,
                "role": spec.role_id,
                "lane_id": lane_id,
                "work_id": work_id,
                "lifecycle_state": "planned",
                "pinned": "false",
                "archived": "false",
                "created_at": now,
                "updated_at": now,
                "cleanup_action": "create_or_reuse_thread_then_archive_after_reconcile",
                "notes": f"prompt={safe_rel(project, prompt_path)}",
                "goal_id": goal_id,
                "mode": mode,
                "environment": spec.default_environment,
                "workspace_path": workspace_path,
                "write_scope": write_scope,
                "professional_identity": spec.professional_identity,
                "receipt_path": safe_rel(project, receipt_path),
                "receipt_status": "missing",
                "reconciliation_status": "pending",
                "assigned_at": "",
                "returned_at": "",
                "reconciled_at": "",
                "archived_at": "",
                "cleanup_reason": "",
                "last_seen_at": now,
                "duplicate_of": "",
            }
        )
        update_or_append_csv_row(
            project / "AD-creative/orchestrator/agent_runs.csv",
            "run_id",
            {
                "run_id": run_id,
                "work_id": work_id,
                "agent_role": spec.role_id,
                "status": "planned",
                "started_at": "",
                "completed_at": "",
                "input_files": ";".join([safe_rel(project, role_brief_path), safe_rel(project, prompt_path)]),
                "output_files": safe_rel(project, receipt_path),
                "gate_id": "",
                "summary": f"Planned Codex Thread lane for {spec.role_id}.",
                "next_action": "create_or_reuse_codex_thread",
                "thread_id": f"planned:{lane_id}",
                "lane_id": lane_id,
                "receipt_path": safe_rel(project, receipt_path),
                "proof_status": "pending",
                "reconciliation_status": "pending",
            },
        )

    for row in registry_rows:
        update_or_append_csv_row(
            project / "AD-creative/orchestrator/thread_registry.csv",
            "thread_id",
            row,
        )

    cleanup_path = render_thread_cleanup_note(
        project,
        goal_id=goal_id,
        work_id=work_id,
        roles=roles,
        max_active=max_active,
    )

    lane_header = [
        "lane_id",
        "thread_id",
        "thread_title",
        "thread_role",
        "professional_identity",
        "agent_role_md",
        "agency_selection_id",
        "agency_role_brief",
        "agency_source_agents",
        "source_staff_count",
        "work_id",
        "purpose",
        "spawn_mode",
        "mode",
        "environment",
        "workspace_path",
        "read_first",
        "write_scope",
        "receipt_path",
        "receipt_status",
        "reconciliation_status",
        "stop_condition",
        "validation_proof",
        "required_output",
        "merge_owner",
        "final_export_allowed",
        "lifecycle_status",
        "cleanup_note",
    ]
    lane_table = [
        "| " + " | ".join(lane_header) + " |",
        "| " + " | ".join("---" for _ in lane_header) + " |",
    ]
    for row in lane_rows:
        lane_table.append(
            "| " + " | ".join(markdown_table_cell(row.get(column, "")) for column in lane_header) + " |"
        )

    harness_header = [
        "lane_id",
        "action_space",
        "observation_contract",
        "error_recovery_contract",
        "context_budget",
        "iteration_budget",
        "eval_gate",
        "adoption_decision",
        "rejection_reason",
        "loop_state",
        "replay_trigger",
        "freeze_trigger",
        "stop_condition",
    ]
    harness_table = [
        "| " + " | ".join(harness_header) + " |",
        "| " + " | ".join("---" for _ in harness_header) + " |",
    ]
    for row in lane_rows:
        harness_table.append(
            "| " + " | ".join(markdown_table_cell(row.get(column, "")) for column in harness_header) + " |"
        )

    helper_header = [
        "lane_id",
        "helper_mode",
        "helper_policy",
        "allowed_helper_kinds",
        "helper_write_boundary",
        "helper_evidence_required",
        "helper_failure_policy",
        "helper_invocations",
        "helper_input_refs",
        "helper_output_refs",
        "helper_artifacts",
        "helper_validation_result",
        "helper_adopted_by_worker",
        "helper_failure_reason",
        "worker_synthesis",
    ]
    helper_table = [
        "| " + " | ".join(helper_header) + " |",
        "| " + " | ".join("---" for _ in helper_header) + " |",
    ]
    for row in lane_rows:
        helper_table.append(
            "| " + " | ".join(markdown_table_cell(row.get(column, "")) for column in helper_header) + " |"
        )

    registry_header = [
        "thread_id",
        "title",
        "role",
        "mode",
        "lane_id",
        "lifecycle_state",
        "receipt_status",
        "reconciliation_status",
        "pinned",
        "cleanup_action",
        "notes",
    ]
    registry_table = [
        "| " + " | ".join(registry_header) + " |",
        "| " + " | ".join("---" for _ in registry_header) + " |",
    ]
    for row in registry_rows:
        registry_table.append(
            "| " + " | ".join(markdown_table_cell(row.get(column, "")) for column in registry_header) + " |"
        )

    task_signature_block = "\n".join(f"{key}: {value or 'TBD'}" for key, value in task_signature.items())
    prompt_list = "\n".join(f"- `{safe_rel(project, path)}`" for path in prompt_paths)
    role_brief_list = "\n".join(f"- `{safe_rel(project, path)}`" for path in role_brief_paths)
    receipt_list = "\n".join(f"- `{safe_rel(project, path)}`" for path in receipt_paths)
    write_text(
        plan_path,
        f"""# Thread Lane Plan

goal_id: {goal_id}
run_id: {work_id}
created_at: {now}
master_thread_id: {master_thread_id or 'TBD'}
project_kind: ppt_material_project
task_signature_id: {task_signature_id}
current_version_id: {current_version or 'TBD'}
loop_mode: {THREADOPS_DEFAULT_LOOP_MODE}

## Goal

```text
user_outcome: {title}
success_standard: {objective}
blocked_if: thread budget exceeds {max_active}, worker edits undeclared files, validation fails, or cleanup proof is missing
```

## Task Signature

```text
{task_signature_block}
```

## Thread Budget

```text
max_active_worker_reviewer: {max_active}
broad_council_requires_user_approval_over: 5
main_thread_only_for: integration,current_truth,version_map,artifact_index,gate_log,final_export,final_status
freeze_trigger: user reports thread confusion / high heat / wrong thread / cleanup request
lane_modes: execution_worker requires exact write_scope; research/read_only_review/cold_review are read-only receipt lanes
```

## Loop Mode Contract

```text
{threadops_loop_mode_contract()}
```

## Harness Field Contract

```text
action_space: what the lane may read, write, call, and never do
observation_contract: required receipt observation shape with status, summary, artifacts, next_actions, and evidence_refs
error_recovery_contract: root cause hint, safe retry instruction, and explicit stop condition for failures
context_budget: maximum context allowed before the lane must ask main/control to add more files
iteration_budget: bounded internal pass count before stop, replay, or freeze
eval_gate: validation or gate evidence required before adoption
adoption_decision: ADOPT, PARTIAL_ADOPT, REJECT, or BLOCKED recorded by main/control
rejection_reason: required when adoption_decision is not ADOPT
loop_state: planned, running, blocked, replay_requested, frozen, returned, reconciled, or archived
replay_trigger: condition that forces a replay with tighter acceptance criteria
freeze_trigger: condition that stops new workers until cleanup/audit is complete
stop_condition: lane-specific completion boundary
```

## Stateless Secondary Helper Contract

```text
helper_mode: default none; set to stateless_secondary_helper only when a real worker invokes a bounded local helper
helper_policy: optional stateless helper inside an L1 Codex Thread worker; never a Codex Thread or substitute worker
allowed_helper_kinds: image_generation,ocr,layout_lint,asset_resize,reference_extraction
helper_write_boundary: helper has no thread_id, no thread_registry.csv row, and no write_scope; worker owns any kept artifacts
helper_evidence_required: helper_invocations, helper_input_refs, helper_output_refs, helper_artifacts, helper_validation_result, helper_adopted_by_worker, helper_failure_reason, worker_synthesis
helper_failure_policy: helper failure is recorded by the worker and cannot bypass worker validation or main/control adoption
worker_synthesis: L1 worker adopts/rejects helper output before returning receipt; main/control adopts through the worker receipt
```

## Invocation

1. Run `list_threads` with query `ADCO` and reuse/archive stale project worker threads before spawning.
2. Create at most {max_active} active worker/reviewer Codex Threads at one time.
3. Send each worker exactly one prompt from `AD-creative/agents/thread_prompts/{work_id}/`.
4. Require each worker to return a receipt matching `AD-creative/agents/receipts/{work_id}/`.
5. Main/control thread reads every receipt, merges only accepted changes, runs validation/gates, then archives reconciled workers.

## Role Briefs

{role_brief_list}

## Worker Prompts

{prompt_list}

## Receipts

{receipt_list}

## Lane Harness Matrix

{chr(10).join(harness_table)}

## Lane Helper Matrix

{chr(10).join(helper_table)}

## Lane Map

{chr(10).join(lane_table)}

## Thread Registry

{chr(10).join(registry_table)}

## Master Thread Rules

```text
Owns current_truth, work_items, agent_runs, gate_log, artifact_index, and final answer.
Reads every worker result before accepting it.
Does not copy worker output blindly.
Runs or records the relevant validation/gate before advancing state.
Lists existing ADCO threads before creating a new employee thread.
Archives duplicate, stale, superseded, or reconciled employee threads.
Uses execution_worker for scoped production/editing work; uses read_only only for explorer, reviewer, research, or cold-review lanes.
Execution worker lanes must declare exact write_scope, files_changed, validation_result, dirty_state_impact, and cleanup_actions in the receipt.
Production worker receipts cannot be prompt-only; execution_worker lanes must produce declared files or return BLOCKED with evidence.
Records adoption_decision and rejection_reason before merging or discarding worker output.
Allows stateless secondary helper invocations only inside real worker threads; helpers are not Codex Threads and have no thread_id, registry row, write_scope, or adoption authority.
Requires helper output to be synthesized and adopted/rejected by the worker, then adopted/rejected by main/control through the worker receipt.
Uses replay_trigger for failed eval gates and freeze_trigger for thread confusion, repeated root cause, or budget breach.
Does not allow more than {max_active} active workers in this plan.
Exports final PPT/PDF only from the main control thread.
```

## Reconciliation Log

| lane_id | adoption_decision | rejection_reason | files_merged | gate_id | notes |
|---|---|---|---|---|---|

## Cleanup Log

| checked_at | active_threads_kept | threads_archived | duplicate_titles_fixed | notes |
|---|---|---|---|---|
| {now} | main/control only until worker creation | TBD | TBD | cleanup plan: `{safe_rel(project, cleanup_path)}` |
""",
    )

    artifact_plan_id = f"ART-{safe_artifact_suffix(work_id)}-LANE-PLAN"
    artifact_prompt_id = f"ART-{safe_artifact_suffix(work_id)}-PROMPTS"
    artifact_cleanup_id = f"ART-{safe_artifact_suffix(work_id)}-CLEANUP"
    update_artifact(
        project,
        artifact_plan_id,
        "thread_lane_plan",
        safe_rel(project, plan_path),
        "threadops",
        status="done",
        visibility="internal_only",
        gate_status="PASS",
    )
    update_artifact(
        project,
        artifact_prompt_id,
        "thread_prompt_pack",
        safe_rel(project, prompt_dir),
        "threadops",
        status="done",
        visibility="internal_only",
        gate_status="PASS",
    )
    update_artifact(
        project,
        artifact_cleanup_id,
        "thread_cleanup_plan",
        safe_rel(project, cleanup_path),
        "threadops",
        status="planned",
        visibility="internal_only",
        gate_status="PARTIAL_PASS",
    )
    update_or_append_csv_row(
        project / "AD-creative/orchestrator/work_items.csv",
        "work_id",
        {
            "work_id": work_id,
            "stage": "threadops",
            "title": title,
            "objective": objective,
            "owner_agent": "Main Controller",
            "status": "planned",
            "priority": "high",
            "input_refs": "",
            "output_artifacts": ";".join([artifact_plan_id, artifact_prompt_id, artifact_cleanup_id]),
            "linked_requirements": "",
            "linked_source_events": "",
            "linked_references": "",
            "linked_assets": "",
            "linked_slides": "",
            "blocked_by": "",
            "gate_required": "ThreadOps cleanup audit",
            "client_visibility": "internal_only",
            "created_at": now,
            "updated_at": now,
            "supersedes_work_id": "",
        },
    )
    append_event(
        project,
        {
            "event_id": f"EVT-{work_id}",
            "event_type": "thread_execution_plan_created",
            "created_at": now,
            "goal_id": goal_id,
            "work_id": work_id,
            "roles": [THREADOPS_ROLE_SPECS[role].role_id for role in roles],
            "thread_lane_plan": safe_rel(project, plan_path),
            "prompt_dir": safe_rel(project, prompt_dir),
            "cleanup_plan": safe_rel(project, cleanup_path),
        },
    )
    return {
        "goal_id": goal_id,
        "work_id": work_id,
        "task_signature_id": task_signature_id,
        "thread_lane_plan": plan_path,
        "prompt_dir": prompt_dir,
        "role_briefs": role_brief_paths,
        "prompts": prompt_paths,
        "receipts": receipt_paths,
        "cleanup_plan": cleanup_path,
        "roles": [THREADOPS_ROLE_SPECS[role].role_id for role in roles],
    }


def render_goal_iteration_plan(
    project: Path,
    *,
    goal_id: str,
    title: str,
    objective: str,
    owner: str,
    force: bool = False,
) -> Path:
    template = project / GOAL_PLAN_TEMPLATE_REL
    if not template.exists():
        template = TEMPLATE_ROOT / GOAL_PLAN_TEMPLATE_REL
    if not template.exists():
        raise FileNotFoundError(f"goal iteration template not found: {GOAL_PLAN_TEMPLATE_REL}")

    output_dir = project / GOAL_ITERATIONS_REL
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{goal_id}.md"
    if output.exists() and not force:
        raise FileExistsError(f"goal plan already exists: {output}")

    now = now_iso()
    write_text(
        output,
        f"""# Goal Iteration Plan

goal_id: {goal_id}
goal_title: {title}
status: active
owner: {owner}
created_at: {now}
updated_at: {now}
loop_mode: {THREADOPS_DEFAULT_LOOP_MODE}

## Objective

{objective}

## Scope

- 使用双泳道：品牌深度研究 / 图片功能。
- 阶段完成后直接推进下一步低风险内部任务。
- 每个 Gate 前必须有反驳性议会记录。

## Loop Mode Contract

```text
{threadops_loop_mode_contract()}
```

## Non Scope

- 不自动发送客户稿。
- 不自动上传客户资料到外部平台。
- 不自动将 AI 图标记为客户可见。
- 不自动安装全局 Skill。

## Source Of Truth

- current_truth: `AD-creative/orchestrator/current_truth.md`
- requirements: `AD-creative/orchestrator/requirements.csv`
- gaps: `AD-creative/orchestrator/gaps.csv`
- work_items: `AD-creative/orchestrator/work_items.csv`
- gate_log: `AD-creative/orchestrator/gate_log.csv`
- handoff_board: `AD-creative/handoff/项目看板.md`
- pending_decisions: `AD-creative/handoff/待你确认.md`

## Execution Batches

| batch_id | objective | owner | inputs | outputs | gate | status | exit_condition |
|---|---|---|---|---|---|---|---|
| B1 | 建立本轮 goal 执行记录 | Main Controller | goal objective | goal iteration plan | Adversarial Council | done | plan written |
| B2 | 按双泳道推进下一阶段 | Main Controller | current_truth / work_items | updated artifacts | stage gate | queued | stage gate not BLOCKED |
| B3 | 验证并写入下一轮队列 | Operations Council | gate_log / artifacts | verification evidence | validation | queued | VALIDATION=PASS |

## Dual Lane Mapping

| phase | brand_research_lane | image_function_lane | dependency | exit_condition | next_phase |
|---|---|---|---|---|---|
| P0 | 需求、事实、缺口 | 图片/素材状态 | source_events | Brief Gate 非 BLOCKED | P1 |
| P1 | 搜索计划、stop condition | 图片路线、asset lock 条件 | P0 gaps | Research Plan Gate 非 BLOCKED | P2 |
| P2 | reference pack、visual DNA | asset slots、manifest skeleton | P1 plan | Reference/Slot Gate 非 BLOCKED | P3 |
| P3 | 创意方向、proposal structure | image job spec、prompt pack | P2 evidence | Creative/Image Job Gate 非 BLOCKED | P4 |
| P4 | 内部原型 | internal_only 图片探索 | P3 contract | Visual QA 非 BLOCKED | P5 |
| P5 | 客户审阅包 | visual review、client flags | P4 assets | Client Pack Gate 非 BLOCKED | P6 |
| P6 | final delivery | approved assets / PPT slots | P5 pack | Final Gate 非 BLOCKED，发送前人工确认 | P7 |
| P7 | 反馈合并 | asset/job supersede | feedback | next_version_plan | next goal |

## Adversarial Council

| stage | objection | rebuttal_path | revision_decision | gate_status |
|---|---|---|---|---|
| global | 自动连续执行可能跳过客户可见风险 | 检查授权策略、Gate 日志、待确认文件 | 只自动推进低风险内部动作；客户稿发送、AI 图客户可见、外部上传仍停 | PASS |

## Pause / Continue / Rollback Rules

continue_when: Gate 非 BLOCKED，且无客户可见/付费/上传/覆盖/安装风险。
pause_when: 客户/导演冲突、AI 图客户可见、客户稿发送、外部上传、全局安装、覆盖旧版本。
rollback_path: 回到产生断链的最近阶段，更新 affected artifacts 和 gate report。
resume_when: 阻塞项关闭，Gate report 和 decisions/resolutions 已更新。

## Verification

| check | method | threshold | result | evidence |
|---|---|---|---|---|
| goal plan exists | file check | exists | pending | `{safe_rel(project, output)}` |
| project validation | validate_project.py | VALIDATION=PASS | pending | run after execution |

## Execution Log

| time | action | artifact | result | next |
|---|---|---|---|---|
| {now} | created goal iteration plan | `{safe_rel(project, output)}` | done | run next batch |

## Next Iteration Queue

| priority | task | owner | trigger | exit_condition |
|---|---|---|---|---|
| P1 | 执行下一阶段 work item | Main Controller | current gate non-blocked | next gate report written |
| P1 | 补充阶段反驳性议会 | QA / Review Council | before each Gate | objection chain recorded |
""",
    )
    artifact_id = f"ART-{safe_artifact_suffix(goal_id)}"
    update_artifact(
        project,
        artifact_id,
        "goal_iteration_plan",
        safe_rel(project, output),
        "goal_planning",
        status="done",
        visibility="internal_only",
        gate_status="PASS",
    )
    append_event(
        project,
        {
            "event_id": f"EVT-{goal_id}",
            "event_type": "goal_iteration_plan_created",
            "created_at": now,
            "goal_id": goal_id,
            "path": safe_rel(project, output),
        },
    )
    return output


def write_manual_review_checklist(project: Path) -> Path:
    path = project / "AD-creative/delivery/manual_review_checklist.md"
    write_text(
        path,
        f"""# Manual Review Checklist

status: ready_for_human_review
visibility: internal_only
created_at: {now_iso()}

## Search Sampling

- [ ] 随机打开 3 条客户可见候选参考，确认链接可访问。
- [ ] 确认每条客户可见参考不是 UGC 冒充官方来源。
- [ ] 确认 `do_not_copy` 限制已进入客户稿备注。

## Visual Taste

- [ ] 打开 `AD-creative/handoff/操作台.html` 的图片区，确认没有低质拼贴、contact sheet、假 logo。
- [ ] 对 selected 图片做审美判断：构图、光线、产品真实感、品牌气质、文字/标志风险。
- [ ] 客户可见生成图必须有 `client_visibility_approved` 记录。

## Client Pack

- [ ] 打开 `AD-creative/ppt/client_review_draft.pptx`，确认页面文本可编辑。
- [ ] 逐页读客户稿，确认没有内部注释、模拟标记、TODO/TBD、假案例。
- [ ] 最终发送前由负责人确认发送对象、附件、版本号。

## Rule

本清单是人工审阅入口，不替代 `client-pack-gate`、`visual-quality-gate`、`search-quality-gate`。
""",
    )
    update_artifact(
        project,
        "ART-AUTO-MANUAL-REVIEW-CHECKLIST",
        "manual_review_checklist",
        safe_rel(project, path),
        "final_delivery",
        status="done",
        visibility="internal_only",
        gate_status="PASS",
    )
    return path


def review_handoff_readiness(project: Path) -> tuple[str, list[str], list[str], Path]:
    blockers: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = []

    errors, stats = validate(project)
    evidence.append(f"validation_errors={len(errors)}")
    if errors:
        blockers.extend(errors[:12])

    _, artifacts = read_csv_rows(project / "AD-creative/orchestrator/artifact_index.csv")
    _, version_map = read_csv_rows(project / "AD-creative/orchestrator/version_map.csv")
    _, feedback_rows = read_csv_rows(project / "AD-creative/feedback/feedback_map.csv")
    delivery_errors = validate_client_delivery_readiness(
        project, artifacts, version_map, feedback_rows
    )
    evidence.append(f"client_delivery_readiness_errors={len(delivery_errors)}")
    if delivery_errors:
        blockers.extend(delivery_errors[:12])

    dashboard = render_dashboard(project)
    dashboard_issues = audit_dashboard(project)
    evidence.append(f"dashboard={safe_rel(project, dashboard)}")
    if dashboard_issues:
        blockers.extend(dashboard_issues)

    checklist = write_manual_review_checklist(project)
    evidence.append(f"manual_review_checklist={safe_rel(project, checklist)}")

    required_gates = {
        "GATE-THREE-COUNCIL-READINESS": {"PASS"},
        "GATE-AUTO-CLIENT-PACK-001": {"PASS"},
        "GATE-AUTO-VISUAL-QUALITY-001": {"PASS"},
        "GATE-AUTO-SEARCH-QUALITY-001": {"PASS", "PARTIAL_PASS"},
        "GATE-AUTO-REFERENCE-PACK-001": {"PASS", "PARTIAL_PASS"},
    }
    for gate_id, allowed in required_gates.items():
        status = latest_gate_status(project, gate_id)
        evidence.append(f"{gate_id}={status or 'MISSING'}")
        if not status:
            warnings.append(f"{gate_id} 尚未运行。")
        elif status not in allowed:
            blockers.append(f"{gate_id} status={status}")

    pptx, _ = current_pptx_path(project, artifacts)
    pptx = pptx or project / "AD-creative/ppt/client_review_draft.pptx"
    if pptx.exists():
        pptx_stats = inspect_pptx(pptx)
        evidence.append(
            f"pptx={safe_rel(project, pptx)} slides={pptx_stats['slides']} editable_text_runs={pptx_stats['editable_text_runs']}"
        )
        if not pptx_stats["editable"]:
            blockers.append("PPTX 缺少可编辑文本层。")
    else:
        blockers.append("缺少 client_review_draft.pptx。")

    launcher = REPO_ROOT / "启动广告创意项目.command"
    if launcher.exists() and os.access(launcher, os.X_OK):
        evidence.append(f"launcher={launcher} executable=true")
    else:
        blockers.append("双击启动脚本不存在或不可执行。")

    skill = check_global_skill()
    evidence.append(f"skill_install_match={skill['match']}")
    evidence.append(f"skill_target={skill['target']}")
    if not skill["match"]:
        blockers.append("全局 Skill 未安装或与项目草稿不一致。")

    status = "PASS" if not blockers else "BLOCKED"
    status = enforce_adversarial_gate_policy(
        project, "final_delivery", status, warnings, evidence
    )
    report_path = project / "AD-creative/gates/GATE-AUTO-HANDOFF-READINESS-001_report.md"
    evidence_text = "\n".join(f"- {item}" for item in evidence)
    blocker_text = "\n".join(f"- {item}" for item in blockers) or "- 无"
    warning_text = "\n".join(f"- {item}" for item in warnings) or "- 无"
    write_text(
        report_path,
        f"""# Non-Developer Handoff Readiness Gate

status: {status}
visibility: internal_only
checked_at: {now_iso()}

## Evidence

{evidence_text}

## Blockers

{blocker_text}

## Warnings

{warning_text}

## Scope

此 Gate 证明项目可交给非开发广告创意者继续内部操作。
它不代表已经发送客户稿，也不替代真实客户最终人工审稿。
""",
    )
    update_artifact(
        project,
        "ART-AUTO-HANDOFF-READINESS-GATE",
        "handoff_readiness_gate_report",
        safe_rel(project, report_path),
        "final_delivery",
        status="done" if status != "BLOCKED" else "blocked",
        visibility="internal_only",
        gate_status=status,
    )
    append_gate(
        project,
        "GATE-AUTO-HANDOFF-READINESS-001",
        "final_delivery",
        status,
        "95" if status == "PASS" else "65" if status == "PARTIAL_PASS" else "40",
        "ART-AUTO-HANDOFF-READINESS-GATE;ART-AUTO-MANUAL-REVIEW-CHECKLIST",
        ";".join(blockers[:8]),
        ";".join(warnings[:8]) or "保持 gate 定期重跑。",
        "",
        "ready_for_non_developer_handoff" if status == "PASS" else "fix_handoff_blockers",
        "ad_creative_operator",
    )
    append_event(
        project,
        {
            "event_id": "EVT-AUTO-HANDOFF-READINESS-GATE",
            "event_type": "handoff_readiness_gate_run",
            "created_at": now_iso(),
            "status": status,
            "blockers": blockers[:12],
            "warnings": warnings[:12],
        },
    )
    for key, value in stats.items():
        evidence.append(f"{key}={value}")
    return status, blockers, warnings, report_path


def export_editable_pptx(project: Path, output: Path | None = None) -> Path:
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
    except Exception as exc:  # noqa: BLE001 - actionable dependency error
        raise RuntimeError(f"python-pptx unavailable: {exc}") from exc

    _, requirements = read_csv_rows(project / "AD-creative/orchestrator/requirements.csv")
    _, gaps = read_csv_rows(project / "AD-creative/orchestrator/gaps.csv")
    _, refs = read_csv_rows(project / "AD-creative/references/reference_cards.csv")
    output = output or (project / "AD-creative/ppt/client_review_draft.pptx")
    output.parent.mkdir(parents=True, exist_ok=True)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    def add_title(slide, title: str, subtitle: str = "") -> None:
        title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.55), Inches(11.8), Inches(0.7))
        frame = title_box.text_frame
        frame.clear()
        paragraph = frame.paragraphs[0]
        paragraph.text = title
        paragraph.font.size = Pt(26)
        paragraph.font.bold = True
        if subtitle:
            sub_box = slide.shapes.add_textbox(Inches(0.62), Inches(1.18), Inches(11.5), Inches(0.35))
            sub_frame = sub_box.text_frame
            sub_frame.text = subtitle
            sub_frame.paragraphs[0].font.size = Pt(11)

    def add_bullets(slide, items: list[str], left: float, top: float, width: float, height: float) -> None:
        box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        frame = box.text_frame
        frame.word_wrap = True
        frame.clear()
        for index, item in enumerate(items):
            paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            paragraph.text = item
            paragraph.level = 0
            paragraph.font.size = Pt(15)

    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)
    add_title(slide, f"{project.name} 第一轮广告创意整理", "自动生成 editable PPTX 草稿；客户可见前仍需人工审稿和 Delivery Gate。")
    add_bullets(
        slide,
        [
            "当前用途：内部结构审阅",
            "事实源：AD-creative/orchestrator/",
            "边界：未自动发送客户稿，未声明最终视觉",
        ],
        0.8,
        2.0,
        10.8,
        2.8,
    )

    slide = prs.slides.add_slide(blank)
    add_title(slide, "已抽取需求", f"{len(requirements)} 条")
    add_bullets(
        slide,
        [row.get("statement", "") for row in requirements[:8]] or ["暂无已抽取需求"],
        0.8,
        1.55,
        11.4,
        5.2,
    )

    slide = prs.slides.add_slide(blank)
    add_title(slide, "缺口与追问", f"{len(gaps)} 条")
    add_bullets(
        slide,
        [
            f"{row.get('impact', '')}: {row.get('description', '')}"
            for row in gaps[:8]
        ]
        or ["暂无缺口"],
        0.8,
        1.55,
        11.4,
        5.2,
    )

    slide = prs.slides.add_slide(blank)
    add_title(slide, "参考与资产状态", "只列已登记事实，不把模拟参考当真实来源。")
    add_bullets(
        slide,
        [
            f"{row.get('reference_id', '')}: {row.get('title', '')} ({row.get('platform', '')})"
            for row in refs[:6]
        ]
        or ["暂无真实参考链接"],
        0.8,
        1.55,
        11.4,
        5.2,
    )

    slide = prs.slides.add_slide(blank)
    add_title(slide, "下一步确认", "以下动作需要明确确认后才能进入客户可见稿。")
    add_bullets(
        slide,
        [
            "客户稿发送",
            "付费/登录平台或上传客户资料",
            "将 AI 图标记为客户可见",
            "最终 PPTX 交付",
        ],
        0.8,
        1.55,
        11.4,
        5.2,
    )

    prs.save(output)
    stats = inspect_pptx(output)
    write_pptx_check(project, output, stats)
    return output


def command_goal_plan(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    goal_id = args.goal_id or default_goal_id()
    title = args.title or goal_id
    objective = args.objective or "按双泳道 goal 模式推进下一轮低风险内部工作。"
    plan = render_goal_iteration_plan(
        project,
        goal_id=goal_id,
        title=title,
        objective=objective,
        owner=args.owner,
        force=args.force,
    )
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    print(f"GOAL_ID={goal_id}")
    print(f"GOAL_PLAN={plan}")
    print(f"DASHBOARD={dashboard}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def command_thread_plan(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    goal_id = args.goal_id or default_goal_id()
    try:
        roles = parse_threadops_roles(args.roles)
        payload = render_thread_execution_plan(
            project,
            goal_id=goal_id,
            title=args.title or goal_id,
            objective=args.objective or "Use Codex Threads as controlled execution lanes for this delivery goal.",
            roles=roles,
            work_id=args.work_id,
            task_signature_id=args.task_signature_id,
            brand=args.brand,
            product=args.product,
            talent_or_ip=args.talent_or_ip,
            platform_or_channel=args.platform_or_channel,
            deliverable=args.deliverable,
            stage=args.stage,
            primary_risks=args.primary_risks,
            evidence_needed=args.evidence_needed,
            master_thread_id=args.master_thread_id,
            current_version=args.current_version_id,
            max_active=args.max_active,
            extra_read_first=args.read_first,
            force=args.force,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should surface actionable plan failure
        print("THREAD_PLAN=CHECK")
        print(f"ERROR={exc}")
        return 1
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    if args.json:
        output = {
            "thread_plan": "PASS" if not errors else "CHECK",
            "project": str(project),
            "goal_id": payload["goal_id"],
            "work_id": payload["work_id"],
            "task_signature_id": payload["task_signature_id"],
            "thread_lane_plan": str(payload["thread_lane_plan"]),
            "prompt_dir": str(payload["prompt_dir"]),
            "cleanup_plan": str(payload["cleanup_plan"]),
            "roles": payload["roles"],
            "dashboard": str(dashboard),
            "validation": "PASS" if not errors else "CHECK",
            "stats": stats,
            "errors": errors,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if not errors else 1
    print(f"THREAD_PLAN={'PASS' if not errors else 'CHECK'}")
    print(f"PROJECT={project}")
    print(f"GOAL_ID={payload['goal_id']}")
    print(f"WORK_ID={payload['work_id']}")
    print(f"TASK_SIGNATURE_ID={payload['task_signature_id']}")
    print(f"THREAD_LANE_PLAN={payload['thread_lane_plan']}")
    print(f"PROMPT_DIR={payload['prompt_dir']}")
    print(f"CLEANUP_PLAN={payload['cleanup_plan']}")
    print("ROLES=" + ";".join(payload["roles"]))
    print(f"DASHBOARD={dashboard}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def command_goal_run(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    result = run_goal(
        project,
        goal_id=args.goal_id,
        max_steps=args.max_steps,
        allow_generate=args.allow_generate,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"PROJECT={result['project']}")
        print(f"GOAL_ID={result['goal_id']}")
        print(f"STOP_REASON={result['stop_reason']}")
        print(f"DASHBOARD={result['dashboard']}")
        for step in result["steps"]:
            print(f"STEP={step['step']} ACTION={step['action']} STATUS={step['status']} DETAIL={step['detail']}")
    return 1 if result["stop_reason"] in {"VALIDATION_CHECK", "BLOCKED_GATE"} else 0


def command_creative_doctor(args: argparse.Namespace) -> int:
    status, issues, warnings, evidence = creative_doctor_report()
    if args.json:
        print(
            json.dumps(
                {
                    "status": status,
                    "issues": issues,
                    "warnings": warnings,
                    "evidence": evidence,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"CREATIVE_PRODUCTION={status}")
        for item in evidence:
            print(f"EVIDENCE={item}")
        if warnings:
            print("WARNINGS:")
            for warning in warnings:
                print(f"- {warning}")
        if issues:
            print("ISSUES:")
            for issue in issues:
                print(f"- {issue}")
    return 0 if status == "PASS" else 1


def command_creative_run(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    if args.generate and args.review_only:
        print("CREATIVE_RUN=CHECK")
        print("ERROR=Choose either --review-only or --generate, not both.")
        return 1
    base_asset = Path(args.base_asset).expanduser().resolve() if args.base_asset else None
    try:
        run_dir, logs = run_creative_production(
            project,
            kind=args.kind,
            work_id=args.work_id,
            brief_file=Path(args.brief_file).expanduser().resolve(),
            base_asset=base_asset,
            generate=args.generate,
            force=args.force,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should surface bridge failure
        print("CREATIVE_RUN=BLOCKED")
        print(f"ERROR={exc}")
        return 1
    errors, stats = validate(project)
    print("CREATIVE_RUN=PASS")
    print(f"KIND={args.kind}")
    print(f"RUN_DIR={run_dir}")
    for log in logs:
        print(f"LOG={log}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def command_import_creative_production(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    try:
        asset_ids, metadata_dir = import_creative_production_run(
            project,
            run_dir=Path(args.run_dir).expanduser().resolve(),
            kind=args.kind,
            slot_prefix=args.slot_prefix,
            requirement_id=args.requirement_id,
            reference_id=args.reference_id,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should surface import failure
        print("CREATIVE_PRODUCTION_IMPORT=BLOCKED")
        print(f"ERROR={exc}")
        return 1
    errors, stats = validate(project)
    print("CREATIVE_PRODUCTION_IMPORT=PASS")
    print(f"KIND={args.kind}")
    print(f"METADATA_DIR={metadata_dir}")
    print(f"IMPORTED_ASSETS={len(asset_ids)}")
    if asset_ids:
        print("ASSET_IDS=" + ";".join(asset_ids))
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def command_creative_proposal(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    payload = render_creative_proposal(project, work_id=args.work_id)
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    payload.update(
        {
            "creative_proposal": "PASS" if not errors else "CHECK",
            "dashboard": str(dashboard),
            "validation": "PASS" if not errors else "CHECK",
            "stats": stats,
            "errors": errors,
        }
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if not errors else 1
    print(f"CREATIVE_PROPOSAL={'PASS' if not errors else 'CHECK'}")
    print(f"PROJECT={project}")
    if args.work_id:
        print(f"WORK_ID={args.work_id}")
    print("ARTIFACT_IDS=" + ";".join(payload["artifact_ids"]))
    for path in payload["paths"]:
        print(f"ARTIFACT_PATH={path}")
    print(f"DASHBOARD={dashboard}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def command_init(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser().resolve()
    template = Path(args.template).expanduser().resolve() if args.template else TEMPLATE_ROOT
    if not template.exists():
        print("INIT=CHECK")
        print(f"ERROR=template not found: {template}")
        return 1
    project.mkdir(parents=True, exist_ok=True)
    created, skipped = copy_template(template, project)
    agents_status = agents_policy_status(project)
    errors, stats = validate(project)
    print(f"PROJECT={project}")
    print(f"TEMPLATE={template}")
    print(f"CREATED_FILES={created}")
    print(f"SKIPPED_EXISTING_FILES={skipped}")
    print(f"AGENTS_MD={agents_status}")
    print(f"INIT={'PASS' if not errors else 'CHECK'}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def command_run(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    created, skipped = ensure_project(project)
    agents_status = agents_policy_status(project)
    materials = [Path(item).expanduser().resolve() for item in args.material]
    source_ids = register_materials(project, materials, args.goal) if materials else []
    if source_ids or args.goal:
        ensure_intake_work(project, source_ids, args.goal)
    intake_stats = perform_intake(project, source_ids, args.goal) if source_ids else {
        "requirements": 0,
        "gaps": 0,
        "materials": 0,
    }
    render_handoff(project, args.goal, source_ids)
    dashboard = render_dashboard(project)
    overall, _, report = run_council(project)
    dashboard = render_dashboard(project)
    errors, stats = validate(project)

    print(f"PROJECT={project}")
    print(f"CREATED_FILES={created}")
    print(f"SKIPPED_EXISTING_FILES={skipped}")
    print(f"AGENTS_MD={agents_status}")
    print(f"REGISTERED_SOURCES={len(source_ids)}")
    print(f"INTAKE_MATERIALS={intake_stats['materials']}")
    print(f"INTAKE_REQUIREMENTS={intake_stats['requirements']}")
    print(f"INTAKE_GAPS={intake_stats['gaps']}")
    print(f"DASHBOARD={dashboard}")
    print(f"COUNCIL={overall}")
    print(f"COUNCIL_REPORT={report}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def command_sample(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    created, skipped = ensure_project(project)
    agents_status = agents_policy_status(project)
    material, material_action = write_sample_brief(project, force=args.force_material)
    source_ids = existing_source_ids_for_material(project, material)
    registered_sources = 0
    if not source_ids:
        source_ids = register_materials(project, [material], SAMPLE_GOAL)
        registered_sources = len(source_ids)
    ensure_intake_work(project, source_ids, SAMPLE_GOAL)
    intake_stats = perform_intake(project, source_ids, SAMPLE_GOAL)
    render_handoff(project, SAMPLE_GOAL, source_ids)
    goal_id = args.goal_id or default_goal_id()
    goal_plan = render_goal_iteration_plan(
        project,
        goal_id=goal_id,
        title=args.title,
        objective=SAMPLE_GOAL,
        owner="Main Controller",
        force=args.force_goal,
    )
    dashboard = render_dashboard(project)
    overall, _, report = run_council(project)
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    print(f"SAMPLE={'PASS' if not errors else 'CHECK'}")
    print(f"PROJECT={project}")
    print(f"CREATED_FILES={created}")
    print(f"SKIPPED_EXISTING_FILES={skipped}")
    print(f"AGENTS_MD={agents_status}")
    print(f"SAMPLE_MATERIAL={material}")
    print(f"SAMPLE_MATERIAL_ACTION={material_action}")
    print(f"REGISTERED_SOURCES={registered_sources}")
    print(f"SOURCE_IDS={';'.join(source_ids)}")
    print(f"INTAKE_MATERIALS={intake_stats['materials']}")
    print(f"INTAKE_REQUIREMENTS={intake_stats['requirements']}")
    print(f"INTAKE_GAPS={intake_stats['gaps']}")
    print(f"GOAL_PLAN={goal_plan}")
    print(f"DASHBOARD={dashboard}")
    print(f"COUNCIL={overall}")
    print(f"COUNCIL_REPORT={report}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def command_demo(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser().resolve() if args.project else DEFAULT_DEMO_PROJECT
    created, skipped = ensure_project(project)
    agents_status = agents_policy_status(project)
    material, material_action = write_sample_brief(project, force=args.force_material)
    source_ids = existing_source_ids_for_material(project, material)
    registered_sources = 0
    if not source_ids:
        source_ids = register_materials(project, [material], SAMPLE_GOAL)
        registered_sources = len(source_ids)
    ensure_intake_work(project, source_ids, SAMPLE_GOAL)
    intake_stats = perform_intake(project, source_ids, SAMPLE_GOAL)
    render_handoff(project, SAMPLE_GOAL, source_ids)
    goal_id = args.goal_id or default_goal_id()
    goal_plan = render_goal_iteration_plan(
        project,
        goal_id=goal_id,
        title=args.title,
        objective=SAMPLE_GOAL,
        owner="Main Controller",
        force=args.force_goal,
    )
    dashboard = render_dashboard(project)
    overall, _, report = run_council(project)
    dashboard = render_dashboard(project)
    open_status = "SKIPPED"
    if not args.no_open:
        open_status = "PASS" if webbrowser.open(dashboard.as_uri()) else "CHECK"
    errors, stats = validate(project)
    print(f"DEMO={'PASS' if not errors and open_status != 'CHECK' else 'CHECK'}")
    print(f"PROJECT={project}")
    print(f"CREATED_FILES={created}")
    print(f"SKIPPED_EXISTING_FILES={skipped}")
    print(f"AGENTS_MD={agents_status}")
    print(f"SAMPLE_MATERIAL={material}")
    print(f"SAMPLE_MATERIAL_ACTION={material_action}")
    print(f"REGISTERED_SOURCES={registered_sources}")
    print(f"SOURCE_IDS={';'.join(source_ids)}")
    print(f"INTAKE_MATERIALS={intake_stats['materials']}")
    print(f"INTAKE_REQUIREMENTS={intake_stats['requirements']}")
    print(f"INTAKE_GAPS={intake_stats['gaps']}")
    print(f"GOAL_PLAN={goal_plan}")
    print(f"DASHBOARD={dashboard}")
    print(f"DASHBOARD_OPEN={open_status}")
    print(f"COUNCIL={overall}")
    print(f"COUNCIL_REPORT={report}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors or open_status == "CHECK":
        if errors:
            print("ERRORS:")
            for error in errors:
                print(f"- {error}")
        return 1
    return 0


def command_quickstart(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser().resolve() if args.project else DEFAULT_DEMO_PROJECT
    created, skipped = ensure_project(project)
    agents_status = agents_policy_status(project)
    material, material_action = write_sample_brief(project, force=args.force_material)
    source_ids = existing_source_ids_for_material(project, material)
    registered_sources = 0
    if not source_ids:
        source_ids = register_materials(project, [material], SAMPLE_GOAL)
        registered_sources = len(source_ids)
    ensure_intake_work(project, source_ids, SAMPLE_GOAL)
    intake_stats = perform_intake(project, source_ids, SAMPLE_GOAL)
    render_handoff(project, SAMPLE_GOAL, source_ids)
    goal_id = args.goal_id or default_goal_id()
    goal_plan = render_goal_iteration_plan(
        project,
        goal_id=goal_id,
        title=args.title,
        objective=SAMPLE_GOAL,
        owner="Main Controller",
        force=args.force_goal,
    )
    dashboard = render_dashboard(project)
    overall, _, report = run_council(project)
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    open_status = "SKIPPED"
    if not args.no_open:
        open_status = "PASS" if webbrowser.open(dashboard.as_uri()) else "CHECK"
    quickstart_status = "PASS" if not errors and open_status != "CHECK" else "CHECK"
    payload = {
        "quickstart": quickstart_status,
        "project": str(project),
        "created_files": created,
        "skipped_existing_files": skipped,
        "agents_md": agents_status,
        "sample_material": str(material),
        "sample_material_action": material_action,
        "registered_sources": registered_sources,
        "source_ids": source_ids,
        "intake_materials": intake_stats["materials"],
        "intake_requirements": intake_stats["requirements"],
        "intake_gaps": intake_stats["gaps"],
        "goal_plan": str(goal_plan),
        "dashboard": str(dashboard),
        "dashboard_open": open_status,
        "council": overall,
        "council_report": str(report),
        "next_command": f"adco next {project}",
        "status_command": f"adco status {project}",
        "validate_command": f"adco validate {project}",
        "real_project_command": "adco run <project_dir> --material <material_file_or_folder>",
        "stats": stats,
        "validation": "PASS" if not errors else "CHECK",
        "errors": errors,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if quickstart_status == "PASS" else 1
    print(f"QUICKSTART={quickstart_status}")
    print(f"PROJECT={project}")
    print(f"CREATED_FILES={created}")
    print(f"SKIPPED_EXISTING_FILES={skipped}")
    print(f"AGENTS_MD={agents_status}")
    print(f"SAMPLE_MATERIAL={material}")
    print(f"SAMPLE_MATERIAL_ACTION={material_action}")
    print(f"REGISTERED_SOURCES={registered_sources}")
    print(f"SOURCE_IDS={';'.join(source_ids)}")
    print(f"INTAKE_MATERIALS={intake_stats['materials']}")
    print(f"INTAKE_REQUIREMENTS={intake_stats['requirements']}")
    print(f"INTAKE_GAPS={intake_stats['gaps']}")
    print(f"GOAL_PLAN={goal_plan}")
    print(f"DASHBOARD={dashboard}")
    print(f"DASHBOARD_OPEN={open_status}")
    print(f"COUNCIL={overall}")
    print(f"COUNCIL_REPORT={report}")
    print(f"NEXT_COMMAND=adco next {project}")
    print(f"STATUS_COMMAND=adco status {project}")
    print(f"VALIDATE_COMMAND=adco validate {project}")
    print("REAL_PROJECT_COMMAND=adco run <project_dir> --material <material_file_or_folder>")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors or open_status == "CHECK":
        if errors:
            print("ERRORS:")
            for error in errors:
                print(f"- {error}")
        return 1
    return 0


def command_render_dashboard(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    dashboard = render_dashboard(project)
    print(f"DASHBOARD={dashboard}")
    return 0


def command_open_dashboard(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    open_status = "SKIPPED"
    if not args.no_open:
        open_status = "PASS" if webbrowser.open(dashboard.as_uri()) else "CHECK"
    print(f"DASHBOARD={dashboard}")
    print(f"DASHBOARD_OPEN={open_status}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors or open_status == "CHECK":
        if errors:
            print("ERRORS:")
            for error in errors:
                print(f"- {error}")
        return 1
    return 0


def command_intake(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    source_ids = args.source_id or []
    ensure_intake_work(project, source_ids, args.goal)
    stats = perform_intake(project, source_ids, args.goal)
    render_handoff(project, args.goal, source_ids)
    dashboard = render_dashboard(project)
    errors, validate_stats = validate(project)
    print(f"PROJECT={project}")
    print(f"INTAKE_MATERIALS={stats['materials']}")
    print(f"INTAKE_REQUIREMENTS={stats['requirements']}")
    print(f"INTAKE_GAPS={stats['gaps']}")
    print(f"DASHBOARD={dashboard}")
    for key, value in validate_stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def command_profile_analyze(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    source_ids = args.source_id or []
    work_id = ensure_profile_work(project, source_ids, args.goal)
    try:
        stats = analyze_profiles(
            project,
            source_ids=source_ids,
            work_id=work_id,
            goal=args.goal,
            brand=args.brand,
            company=args.company,
            client=args.client,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should surface actionable analysis failure
        print("PROFILE_ANALYSIS=CHECK")
        print(f"ERROR={exc}")
        return 1
    dashboard = render_dashboard(project)
    errors, validate_stats = validate(project)
    if args.json:
        output = {
            "profile_analysis": "PASS" if not errors else "CHECK",
            "project": str(project),
            "work_id": work_id,
            "profile_current_truth": str(stats["profile_current_truth"]),
            "handoff": str(stats["handoff"]),
            "stats": {key: value for key, value in stats.items() if isinstance(value, (int, str))},
            "dashboard": str(dashboard),
            "validation": "PASS" if not errors else "CHECK",
            "validate_stats": validate_stats,
            "errors": errors,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    print(f"PROJECT={project}")
    print(f"WORK_ID={work_id}")
    print(f"PROFILE_MATERIALS={stats['materials']}")
    print(f"PROFILE_SUBJECTS={stats['subjects']}")
    print(f"PROFILE_VOICES={stats['voices']}")
    print(f"PROFILE_INSIGHTS={stats['insights']}")
    print(f"PROFILE_CONFLICTS={stats['conflicts']}")
    print(f"PROFILE_DEDUPED={stats['deduped']}")
    print(f"PROFILE_CURRENT_TRUTH={stats['profile_current_truth']}")
    print(f"HANDOFF={stats['handoff']}")
    print(f"DASHBOARD={dashboard}")
    for key, value in validate_stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def command_hygiene(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    report = workspace_hygiene_report(project)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "PASS" or not args.strict else 1
    print(f"WORKSPACE_HYGIENE={report['status']}")
    print(f"PROJECT={report['project']}")
    print(f"GIT_ROOT={report['git_root'] or 'none'}")
    print(f"TRACKED_CHANGES={len(report['tracked_changes'])}")
    print(f"UNTRACKED_FILES={len(report['untracked_files'])}")
    print(f"POLLUTION_PATHS={len(report['pollution_paths'])}")
    print(f"ACTIVE_THREADS={len(report['active_threads'])}")
    if report["issues"]:
        print("ISSUES:")
        for issue in report["issues"]:
            print(f"- {issue}")
    if report["tracked_changes"]:
        print("TRACKED:")
        for line in report["tracked_changes"][:30]:
            print(f"- {line}")
    if report["untracked_files"]:
        print("UNTRACKED:")
        for line in report["untracked_files"][:30]:
            print(f"- {line}")
    if report["pollution_paths"]:
        print("POLLUTION:")
        for path in report["pollution_paths"][:30]:
            print(f"- {path}")
    print("PLAN:")
    for item in report["plan"]:
        print(f"- {item}")
    return 0 if report["status"] == "PASS" or not args.strict else 1


def command_council(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    if args.render_dashboard:
        render_dashboard(project)
    overall, results, report = run_council(project)
    print(f"COUNCIL={overall}")
    print(f"REPORT={report}")
    for result in results:
        print(f"{result.name.upper().replace(' ', '_')}={result.status}")
    return 0 if overall == "PASS" else 1


def command_status(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    if args.json:
        print(json.dumps(status_payload(project), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_status(project)
    return 0


def command_next(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    if args.render_dashboard:
        ensure_project(project)
        render_dashboard(project)
    payload = status_payload(project)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"PROJECT={payload['project']}")
        print(f"NEXT_STATUS={payload['next_status']}")
        print(f"NEXT_ACTION={payload['next_action']}")
        print(f"VALIDATION={payload['validation']}")
        print(f"ACTIVE_WORK={payload['active_work_count']}")
        print(f"OPEN_GAPS={payload['open_gap_count']}")
        print(f"BLOCKING_GAPS={payload['blocking_gap_count']}")
        print(f"PENDING_CONFIRMATIONS={payload['pending_confirmation_count']}")
        print(f"DASHBOARD={payload['dashboard'] or 'MISSING'}")
        if payload["next_status"] == "NEEDS_MATERIAL":
            print(f"SUGGESTED_COMMAND=adco run {payload['project']} --material <brief_file_or_folder>")
        elif payload["next_status"] == "READY_FOR_NEXT_GATE":
            print(f"SUGGESTED_COMMAND=adco goal-plan {payload['project']} --title <title> --objective <objective>")
    return 1 if payload["next_status"] == "VALIDATION_CHECK" else 0


def command_validate(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    errors, stats = validate(project)
    status = "PASS" if not errors else "CHECK"
    if args.json:
        print(
            json.dumps(
                {
                    "project": str(project),
                    "validation": status,
                    "stats": stats,
                    "errors": errors,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        for key, value in stats.items():
            print(f"{key.upper()}={value}")
        print(f"VALIDATION={status}")
    if errors:
        if not args.json:
            print("ERRORS:")
            for error in errors:
                print(f"- {error}")
        return 1
    return 0


def command_check(args: argparse.Namespace) -> int:
    import run_checks

    return run_checks.main()


def command_doctor(args: argparse.Namespace) -> int:
    status, issues, warnings, evidence = doctor_report()
    if args.json:
        print(
            json.dumps(
                {
                    "status": status,
                    "issues": issues,
                    "warnings": warnings,
                    "evidence": evidence,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"ADCO_DOCTOR={status}")
        print(f"ISSUES={len(issues)}")
        print(f"WARNINGS={len(warnings)}")
        for item in evidence:
            print(f"EVIDENCE={item}")
        if warnings:
            print("DOCTOR_WARNINGS:")
            for warning in warnings:
                print(f"- {warning}")
        if issues:
            print("DOCTOR_ISSUES:")
            for issue in issues:
                print(f"- {issue}")
    return 0 if not issues else 1


def command_release_status(args: argparse.Namespace) -> int:
    payload = release_status_payload()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"RELEASE_STATUS={payload['release_status']}")
        print(f"DOCTOR={payload['doctor_status']}")
        print(f"REMOTE={payload['remote_status']}")
        print(f"MODE={payload['mode']}")
        print(f"GIT_REMOTE={payload['git_remote']}")
        print(f"VERIFY_COMMAND={payload['verify_command']}")
        print(f"NEXT_ACTION={payload['next_action']}")
        warnings = payload["warnings"]
        issues = payload["issues"]
        print(f"WARNINGS={len(warnings)}")
        print(f"ISSUES={len(issues)}")
        if warnings:
            print("RELEASE_WARNINGS:")
            for warning in warnings:
                print(f"- {warning}")
        if issues:
            print("RELEASE_ISSUES:")
            for issue in issues:
                print(f"- {issue}")
    if args.strict and payload["release_status"] != "READY_FOR_REMOTE_CHECKS":
        return 1
    return 1 if payload["release_status"] == "CHECK" else 0


def command_docs(args: argparse.Namespace) -> int:
    payload = docs_payload()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"DOCS_MODE={payload['mode']}")
        print(f"SOURCE_ROOT={payload['source_root'] or 'NOT_AVAILABLE'}")
        print(f"TEMPLATE_ROOT={payload['template_root']}")
        print(f"SKILL_DRAFT={payload['skill_draft']}")
        docs = payload["docs"]
        if docs:
            print("DOCS:")
            for item in docs:
                exists = "PASS" if item["exists"] else "MISSING"
                print(f"- {item['label']}={item['path']} [{exists}]")
        else:
            print("DOCS=INSTALLED_PACKAGE_COMMAND_HELP_ONLY")
        print("QUICKSTART:")
        for command in payload["quickstart"]:
            print(f"- {command}")
    missing = [item for item in payload["docs"] if not item["exists"]]
    return 1 if missing else 0


def command_support_bundle(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    if not project.exists():
        if args.json:
            print(json.dumps({
                "support_bundle": "CHECK",
                "project": str(project),
                "report": None,
                "validation": "CHECK",
                "stats": {},
                "errors": [f"project not found: {project}"],
            }, ensure_ascii=False, indent=2, sort_keys=True))
            return 1
        print("SUPPORT_BUNDLE=CHECK")
        print(f"ERROR=project not found: {project}")
        return 1
    report = render_support_bundle(project)
    errors, stats = validate(project)
    payload = {
        "support_bundle": "PASS" if not errors else "CHECK",
        "project": str(project),
        "report": str(report),
        "validation": "PASS" if not errors else "CHECK",
        "stats": stats,
        "errors": errors,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if not errors else 1
    print(f"SUPPORT_BUNDLE={'PASS' if not errors else 'CHECK'}")
    print(f"REPORT={report}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def command_audit_dashboard(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    if args.render:
        ensure_project(project)
        render_dashboard(project)
    issues = audit_dashboard(project)
    payload = {
        "dashboard_audit": "PASS" if not issues else "CHECK",
        "project": str(project),
        "dashboard": str(project / DASHBOARD_REL),
        "rendered": bool(args.render),
        "issues": issues,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if not issues else 1
    print(f"DASHBOARD_AUDIT={'PASS' if not issues else 'CHECK'}")
    print(f"DASHBOARD={project / DASHBOARD_REL}")
    if issues:
        print("ISSUES:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    return 0


def command_add_reference(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    ref_id, action = add_reference(
        project,
        args.url,
        args.title or args.url,
        args.role,
        args.reference_type,
        source_owner=args.source_owner,
        why_relevant=args.why_relevant,
        borrow=args.borrow,
        do_not_copy=args.do_not_copy,
        client_visible=str(args.client_visible).lower(),
        live_check=not args.no_live_check,
    )
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    print(f"REFERENCE_ID={ref_id}")
    print(f"REFERENCE_ACTION={action}")
    print(f"DASHBOARD={dashboard}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def command_reference_pack_gate(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    status, items, report = review_reference_pack(project, live_check=args.live_check)
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    print(f"REFERENCE_PACK_GATE={status}")
    print(f"REPORT={report}")
    print(f"FINDINGS={len(items)}")
    print(f"DASHBOARD={dashboard}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors or status == "BLOCKED":
        if items:
            print("GATE_ISSUES:")
            for item in items:
                print(f"- {item}")
        if errors:
            print("ERRORS:")
            for error in errors:
                print(f"- {error}")
        return 1
    return 0


def command_search_quality_gate(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    status, items, report = review_search_quality(project)
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    print(f"SEARCH_QUALITY_GATE={status}")
    print(f"REPORT={report}")
    print(f"FINDINGS={len(items)}")
    print(f"DASHBOARD={dashboard}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors or status == "BLOCKED":
        if items:
            print("GATE_ISSUES:")
            for item in items:
                print(f"- {item}")
        if errors:
            print("ERRORS:")
            for error in errors:
                print(f"- {error}")
        return 1
    return 0


def command_creative_quality_gate(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    status, items, report = review_creative_quality(project)
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    print(f"CREATIVE_QUALITY_GATE={status}")
    print(f"REPORT={report}")
    print(f"FINDINGS={len(items)}")
    print(f"DASHBOARD={dashboard}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors or status == "BLOCKED":
        if items:
            print("GATE_ISSUES:")
            for item in items:
                print(f"- {item}")
        if errors:
            print("ERRORS:")
            for error in errors:
                print(f"- {error}")
        return 1
    return 0


def command_add_asset(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    asset_id, target = add_visual_asset(
        project,
        Path(args.file).expanduser().resolve(),
        args.slot_id,
        args.requirement_id,
        args.reference_id,
        args.asset_type,
        args.visibility,
        args.qa_status,
        args.risk_level,
        args.prompt_or_edit_ref,
        args.notes,
        args.selected,
    )
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    print(f"ASSET_ID={asset_id}")
    print(f"ASSET_PATH={target}")
    print(f"DASHBOARD={dashboard}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def command_import_imagegen(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    source, source_root = resolve_imagegen_source(args.file)
    requirement_id = args.requirement_id or first_existing_id(
        project, "AD-creative/orchestrator/requirements.csv", "requirement_id"
    )
    prompt_ref = args.prompt_or_edit_ref or default_prompt_ref(project)
    asset_id, target = add_visual_asset(
        project,
        source,
        args.slot_id,
        requirement_id,
        args.reference_id,
        "generated_image",
        args.visibility,
        args.qa_status,
        args.risk_level,
        prompt_ref,
        args.notes,
        args.selected,
    )
    log_path = append_imagegen_import_log(
        project,
        source_root,
        source,
        asset_id,
        target,
        prompt_ref,
        args.qa_status,
        args.notes,
    )
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    print(f"IMAGEGEN_SOURCE_ROOT={source_root}")
    print(f"IMAGEGEN_SOURCE={source}")
    print(f"ASSET_ID={asset_id}")
    print(f"ASSET_PATH={target}")
    print(f"IMAGEGEN_IMPORT_LOG={log_path}")
    print(f"DASHBOARD={dashboard}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def command_visual_quality_gate(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    status, items, report = review_visual_quality(
        project,
        min_long_edge=args.min_long_edge,
        min_short_edge=args.min_short_edge,
    )
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    print(f"VISUAL_QUALITY_GATE={status}")
    print(f"REPORT={report}")
    print(f"FINDINGS={len(items)}")
    print(f"DASHBOARD={dashboard}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors or status == "BLOCKED":
        if items:
            print("GATE_ISSUES:")
            for item in items:
                print(f"- {item}")
        if errors:
            print("ERRORS:")
            for error in errors:
                print(f"- {error}")
        return 1
    return 0


def command_film_quality_gate(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    status, items, report = review_film_quality(project)
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    print(f"FILM_QUALITY_GATE={status}")
    print(f"REPORT={report}")
    print(f"FINDINGS={len(items)}")
    print(f"DASHBOARD={dashboard}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors or status == "BLOCKED":
        if items:
            print("GATE_ISSUES:")
            for item in items:
                print(f"- {item}")
        if errors:
            print("ERRORS:")
            for error in errors:
                print(f"- {error}")
        return 1
    return 0


def command_export_pptx(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    output = Path(args.output).expanduser().resolve() if args.output else None
    pptx_path = export_editable_pptx(project, output)
    stats = inspect_pptx(pptx_path)
    dashboard = render_dashboard(project)
    errors, validate_stats = validate(project)
    print(f"PPTX={pptx_path}")
    print(f"PPTX_SLIDES={stats['slides']}")
    print(f"PPTX_EDITABLE_TEXT_RUNS={stats['editable_text_runs']}")
    print(f"PPTX_EDITABLE={'PASS' if stats['editable'] else 'CHECK'}")
    print(f"DASHBOARD={dashboard}")
    for key, value in validate_stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors or not stats["editable"]:
        if errors:
            print("ERRORS:")
            for error in errors:
                print(f"- {error}")
        return 1
    return 0


def command_check_pptx(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    pptx_path = Path(args.file).expanduser().resolve()
    stats = inspect_pptx(pptx_path)
    check_path = write_pptx_check(project, pptx_path, stats)
    dashboard = render_dashboard(project)
    errors, validate_stats = validate(project)
    print(f"PPTX={pptx_path}")
    print(f"PPTX_CHECK={check_path}")
    print(f"PPTX_SLIDES={stats['slides']}")
    print(f"PPTX_EDITABLE_TEXT_RUNS={stats['editable_text_runs']}")
    print(f"PPTX_EDITABLE={'PASS' if stats['editable'] else 'CHECK'}")
    print(f"DASHBOARD={dashboard}")
    for key, value in validate_stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors or not stats["editable"]:
        if errors:
            print("ERRORS:")
            for error in errors:
                print(f"- {error}")
        return 1
    return 0


def command_client_pack_gate(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    pptx_path = Path(args.pptx).expanduser().resolve() if args.pptx else None
    status, issues, report = review_client_pack(project, pptx_path)
    dashboard = render_dashboard(project)
    errors, validate_stats = validate(project)
    print(f"CLIENT_PACK_GATE={status}")
    print(f"REPORT={report}")
    print(f"ISSUES={len(issues)}")
    print(f"DASHBOARD={dashboard}")
    for key, value in validate_stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors or status != "PASS":
        if issues:
            print("GATE_ISSUES:")
            for issue in issues:
                print(f"- {issue}")
        if errors:
            print("ERRORS:")
            for error in errors:
                print(f"- {error}")
        return 1
    return 0


def command_install_skill(args: argparse.Namespace) -> int:
    target = Path(args.target).expanduser().resolve() if args.target else DEFAULT_SKILL_INSTALL_DIR
    result = install_global_skill(target)
    print(f"SKILL_INSTALL={'PASS' if result['match'] else 'CHECK'}")
    print(f"SOURCE={result['source']}")
    print(f"TARGET={result['target']}")
    print(f"SOURCE_SHA256={result['source_hash']}")
    print(f"TARGET_SHA256={result['target_hash']}")
    return 0 if result["match"] else 1


def command_handoff_readiness_gate(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    status, blockers, warnings, report = review_handoff_readiness(project)
    dashboard = render_dashboard(project)
    errors, stats = validate(project)
    print(f"HANDOFF_READINESS_GATE={status}")
    print(f"REPORT={report}")
    print(f"BLOCKERS={len(blockers)}")
    print(f"WARNINGS={len(warnings)}")
    print(f"DASHBOARD={dashboard}")
    for key, value in stats.items():
        print(f"{key.upper()}={value}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    if errors or status != "PASS":
        if blockers:
            print("GATE_BLOCKERS:")
            for blocker in blockers:
                print(f"- {blocker}")
        if warnings:
            print("GATE_WARNINGS:")
            for warning in warnings:
                print(f"- {warning}")
        if errors:
            print("ERRORS:")
            for error in errors:
                print(f"- {error}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Operate an Ad Creative Orchestrator project without editing CSVs by hand."
    )
    parser.add_argument("--version", action="version", version=f"adco {package_version()}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a project from packaged templates.")
    init_parser.add_argument("project", help="Project directory.")
    init_parser.add_argument("--template", default="", help="Template directory. Defaults to packaged templates.")
    init_parser.set_defaults(func=command_init)

    goal_parser = subparsers.add_parser("goal-plan", help="Create a reusable goal iteration execution plan.")
    goal_parser.add_argument("project", help="Project directory.")
    goal_parser.add_argument("--goal-id", default="", help="Stable goal id. Defaults to timestamp.")
    goal_parser.add_argument("--title", default="", help="Human-readable goal title.")
    goal_parser.add_argument("--objective", default="", help="Goal objective.")
    goal_parser.add_argument("--owner", default="Main Controller", help="Goal owner.")
    goal_parser.add_argument("--force", action="store_true", help="Overwrite an existing goal plan with the same id.")
    goal_parser.set_defaults(func=command_goal_plan)

    thread_plan_parser = subparsers.add_parser(
        "thread-plan",
        help="Create a Codex ThreadOps lane plan, role briefs, worker prompts, and registry rows.",
    )
    thread_plan_parser.add_argument("project", help="Project directory.")
    thread_plan_parser.add_argument("--goal-id", default="", help="Stable goal id. Defaults to timestamp.")
    thread_plan_parser.add_argument("--work-id", default="", help="Stable work id. Defaults from goal id.")
    thread_plan_parser.add_argument("--task-signature-id", default="", help="Stable task signature id. Defaults from goal id.")
    thread_plan_parser.add_argument("--title", default="", help="Human-readable goal title.")
    thread_plan_parser.add_argument("--objective", default="", help="Goal objective.")
    thread_plan_parser.add_argument(
        "--roles",
        default=",".join(THREADOPS_DEFAULT_ROLES),
        help="Comma-separated roles. Choices: brand_client, copy_creative, film_director, art_design, producer_risk, qa_review.",
    )
    thread_plan_parser.add_argument("--brand", default="")
    thread_plan_parser.add_argument("--product", default="")
    thread_plan_parser.add_argument("--talent-or-ip", default="")
    thread_plan_parser.add_argument("--platform-or-channel", default="")
    thread_plan_parser.add_argument("--deliverable", default="")
    thread_plan_parser.add_argument("--stage", default="threadops")
    thread_plan_parser.add_argument("--primary-risks", default="")
    thread_plan_parser.add_argument("--evidence-needed", default="")
    thread_plan_parser.add_argument("--master-thread-id", default="")
    thread_plan_parser.add_argument("--current-version-id", default="")
    thread_plan_parser.add_argument("--max-active", type=int, default=3)
    thread_plan_parser.add_argument("--read-first", action="append", default=[], help="Extra read-first file for every lane. Repeatable.")
    thread_plan_parser.add_argument("--force", action="store_true", help="Replace an existing thread_lane_plan.md for this project.")
    thread_plan_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    thread_plan_parser.set_defaults(func=command_thread_plan)

    goal_run_parser = subparsers.add_parser("goal-run", help="Run deterministic local goal steps until a safe stop condition.")
    goal_run_parser.add_argument("project", help="Project directory.")
    goal_run_parser.add_argument("--goal-id", default="latest", help="Goal id or latest.")
    goal_run_parser.add_argument("--max-steps", type=int, default=3, help="Maximum deterministic steps to execute.")
    goal_run_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    goal_run_parser.add_argument("--allow-generate", action="store_true", help="Allow generation-capable goal steps. Defaults to off.")
    goal_run_parser.set_defaults(func=command_goal_run)

    creative_doctor_parser = subparsers.add_parser("creative-doctor", help="Diagnose optional Creative Production bridge availability.")
    creative_doctor_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    creative_doctor_parser.set_defaults(func=command_creative_doctor)

    creative_run_parser = subparsers.add_parser("creative-run", help="Create a Creative Production review-only or generation run.")
    creative_run_parser.add_argument("project", help="Project directory.")
    creative_run_parser.add_argument("--kind", choices=sorted(CREATIVE_PRODUCTION_KINDS), required=True)
    creative_run_parser.add_argument("--work-id", required=True)
    creative_run_parser.add_argument("--brief-file", required=True)
    creative_run_parser.add_argument("--base-asset", default="", help="Optional source image for shots or ads.")
    creative_run_parser.add_argument("--review-only", action="store_true", help="Write manifests/review surface without generation. This is the default.")
    creative_run_parser.add_argument("--generate", action="store_true", help="Run Creative Production generation. Outputs remain internal_only.")
    creative_run_parser.add_argument("--force", action="store_true", help="Replace output directory if needed.")
    creative_run_parser.set_defaults(func=command_creative_run)

    creative_import_parser = subparsers.add_parser("import-creative-production", help="Import Creative Production run metadata and images into ADCO manifests.")
    creative_import_parser.add_argument("project", help="Project directory.")
    creative_import_parser.add_argument("--run-dir", required=True)
    creative_import_parser.add_argument("--kind", choices=sorted(CREATIVE_PRODUCTION_KINDS), required=True)
    creative_import_parser.add_argument("--slot-prefix", default="CP")
    creative_import_parser.add_argument("--requirement-id", default="")
    creative_import_parser.add_argument("--reference-id", default="pending")
    creative_import_parser.set_defaults(func=command_import_creative_production)

    proposal_parser = subparsers.add_parser(
        "creative-proposal",
        help="Create traceable internal creative proposal draft artifacts.",
    )
    proposal_parser.add_argument("project", help="Project directory.")
    proposal_parser.add_argument("--work-id", default="", help="Optional work item id to link artifacts.")
    proposal_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    proposal_parser.set_defaults(func=command_creative_proposal)

    run_parser = subparsers.add_parser("run", help="Initialize, register materials, render dashboard, run council.")
    run_parser.add_argument("project", help="Project directory.")
    run_parser.add_argument("--material", action="append", default=[], help="Client material file or folder. Repeatable.")
    run_parser.add_argument("--goal", default="先完成需求整理、缺口判断、客户追问、下一步建议。")
    run_parser.set_defaults(func=command_run)

    sample_parser = subparsers.add_parser("sample", help="Create a runnable bundled sample project.")
    sample_parser.add_argument("project", help="Project directory.")
    sample_parser.add_argument("--title", default="Bundled sample dual-lane run", help="Sample goal title.")
    sample_parser.add_argument("--goal-id", default="", help="Stable sample goal id. Defaults to timestamp.")
    sample_parser.add_argument("--force-material", action="store_true", help="Overwrite the bundled sample brief.")
    sample_parser.add_argument("--force-goal", action="store_true", help="Overwrite an existing sample goal plan with the same id.")
    sample_parser.set_defaults(func=command_sample)

    demo_parser = subparsers.add_parser("demo", help="Create a sample project and open the dashboard.")
    demo_parser.add_argument("project", nargs="?", help="Project directory. Defaults to the system temp adco-demo folder.")
    demo_parser.add_argument("--title", default="Bundled sample dual-lane run", help="Sample goal title.")
    demo_parser.add_argument("--goal-id", default="", help="Stable sample goal id. Defaults to timestamp.")
    demo_parser.add_argument("--force-material", action="store_true", help="Overwrite the bundled sample brief.")
    demo_parser.add_argument("--force-goal", action="store_true", help="Overwrite an existing sample goal plan with the same id.")
    demo_parser.add_argument("--no-open", action="store_true", help="Render and validate without opening a browser.")
    demo_parser.set_defaults(func=command_demo)

    quickstart_parser = subparsers.add_parser(
        "quickstart",
        help="Create a demo project, validate it, open the dashboard, and print first next steps.",
    )
    quickstart_parser.add_argument("project", nargs="?", help="Project directory. Defaults to the system temp adco-demo folder.")
    quickstart_parser.add_argument("--title", default="Bundled sample dual-lane run", help="Sample goal title.")
    quickstart_parser.add_argument("--goal-id", default="", help="Stable sample goal id. Defaults to timestamp.")
    quickstart_parser.add_argument("--force-material", action="store_true", help="Overwrite the bundled sample brief.")
    quickstart_parser.add_argument("--force-goal", action="store_true", help="Overwrite an existing sample goal plan with the same id.")
    quickstart_parser.add_argument("--no-open", action="store_true", help="Render and validate without opening a browser.")
    quickstart_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    quickstart_parser.set_defaults(func=command_quickstart)

    status_parser = subparsers.add_parser("status", help="Print current project status.")
    status_parser.add_argument("project", help="Project directory.")
    status_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    status_parser.set_defaults(func=command_status)

    next_parser = subparsers.add_parser("next", help="Print the next safe action for a project.")
    next_parser.add_argument("project", help="Project directory.")
    next_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    next_parser.add_argument("--render-dashboard", action="store_true", help="Render dashboard before deciding.")
    next_parser.set_defaults(func=command_next)

    validate_parser = subparsers.add_parser("validate", help="Validate a project directory.")
    validate_parser.add_argument("project", help="Project directory.")
    validate_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    validate_parser.set_defaults(func=command_validate)

    check_parser = subparsers.add_parser("check", help="Run the full verification suite.")
    check_parser.set_defaults(func=command_check)

    doctor_parser = subparsers.add_parser("doctor", help="Diagnose installation, templates, optional dependencies, and release blockers.")
    doctor_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    doctor_parser.set_defaults(func=command_doctor)

    release_parser = subparsers.add_parser("release-status", help="Summarize local release readiness and remote blockers.")
    release_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    release_parser.add_argument("--strict", action="store_true", help="Return non-zero unless ready for remote checks.")
    release_parser.set_defaults(func=command_release_status)

    docs_parser = subparsers.add_parser("docs", help="Print local documentation paths and quickstart commands.")
    docs_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    docs_parser.set_defaults(func=command_docs)

    support_parser = subparsers.add_parser("support-bundle", help="Write a sanitized support bundle for bug reports.")
    support_parser.add_argument("project", help="Project directory.")
    support_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    support_parser.set_defaults(func=command_support_bundle)

    dashboard_parser = subparsers.add_parser("render-dashboard", help="Render static operation dashboard.")
    dashboard_parser.add_argument("project", help="Project directory.")
    dashboard_parser.set_defaults(func=command_render_dashboard)

    open_dashboard_parser = subparsers.add_parser("open-dashboard", help="Render and open the operation dashboard.")
    open_dashboard_parser.add_argument("project", help="Project directory.")
    open_dashboard_parser.add_argument("--no-open", action="store_true", help="Render and validate without opening a browser.")
    open_dashboard_parser.set_defaults(func=command_open_dashboard)

    intake_parser = subparsers.add_parser("intake", help="Extract first-pass requirements and gaps from registered materials.")
    intake_parser.add_argument("project", help="Project directory.")
    intake_parser.add_argument("--source-id", action="append", default=[], help="Registered source_event_id to process. Repeatable.")
    intake_parser.add_argument("--goal", default="先完成需求整理、缺口判断、客户追问、下一步建议。")
    intake_parser.set_defaults(func=command_intake)

    profile_parser = subparsers.add_parser(
        "profile-analyze",
        help="Analyze meeting/client materials into participant, brand, company, decision, and conflict profiles.",
    )
    profile_parser.add_argument("project", help="Project directory.")
    profile_parser.add_argument("--source-id", action="append", default=[], help="Registered source_event_id to process. Repeatable.")
    profile_parser.add_argument("--goal", default="分析会议资料中的人物画像、品牌画像、需求权重、决策权和分歧融合路径。")
    profile_parser.add_argument("--brand", default="", help="Brand name to use for brand profile.")
    profile_parser.add_argument("--company", default="", help="Company or client organization name.")
    profile_parser.add_argument("--client", default="", help="Client group name if the company/brand is unclear.")
    profile_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    profile_parser.set_defaults(func=command_profile_analyze)

    hygiene_parser = subparsers.add_parser(
        "hygiene",
        help="Audit workspace cleanliness without deleting files.",
    )
    hygiene_parser.add_argument("project", help="Project or repo directory.")
    hygiene_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    hygiene_parser.add_argument("--strict", action="store_true", help="Return non-zero when hygiene status is CHECK.")
    hygiene_parser.set_defaults(func=command_hygiene)

    audit_parser = subparsers.add_parser("audit-dashboard", help="Audit dashboard usability markers.")
    audit_parser.add_argument("project", help="Project directory.")
    audit_parser.add_argument("--render", action="store_true", help="Render dashboard before auditing.")
    audit_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    audit_parser.set_defaults(func=command_audit_dashboard)

    council_parser = subparsers.add_parser("council", help="Run three-council readiness audit.")
    council_parser.add_argument("project", help="Project directory.")
    council_parser.add_argument("--render-dashboard", action="store_true", help="Render dashboard before the audit.")
    council_parser.set_defaults(func=command_council)

    ref_parser = subparsers.add_parser("add-reference", help="Register a live https reference link.")
    ref_parser.add_argument("project", help="Project directory.")
    ref_parser.add_argument("--url", required=True, help="HTTPS reference URL.")
    ref_parser.add_argument("--title", default="", help="Human-readable title.")
    ref_parser.add_argument("--role", default="direction_reference", help="Reference role in the project.")
    ref_parser.add_argument("--reference-type", default="official_or_public_reference")
    ref_parser.add_argument("--source-owner", default="official_or_public")
    ref_parser.add_argument("--why-relevant", default="")
    ref_parser.add_argument("--borrow", default="")
    ref_parser.add_argument("--do-not-copy", default="")
    ref_parser.add_argument("--client-visible", action="store_true")
    ref_parser.add_argument("--no-live-check", action="store_true", help="Skip HTTP check for offline validation.")
    ref_parser.set_defaults(func=command_add_reference)

    ref_gate_parser = subparsers.add_parser("reference-pack-gate", help="Audit reference pack quality before client use.")
    ref_gate_parser.add_argument("project", help="Project directory.")
    ref_gate_parser.add_argument("--live-check", action="store_true", help="Run live HTTPS checks for registered URLs.")
    ref_gate_parser.set_defaults(func=command_reference_pack_gate)

    search_gate_parser = subparsers.add_parser("search-quality-gate", help="Audit search plans and search-target references.")
    search_gate_parser.add_argument("project", help="Project directory.")
    search_gate_parser.set_defaults(func=command_search_quality_gate)

    creative_quality_parser = subparsers.add_parser(
        "creative-quality-gate",
        help="Audit creative/proposal artifacts for traceable quality and client-facing safety.",
    )
    creative_quality_parser.add_argument("project", help="Project directory.")
    creative_quality_parser.set_defaults(func=command_creative_quality_gate)

    asset_parser = subparsers.add_parser("add-asset", help="Register a real/generated visual asset file.")
    asset_parser.add_argument("project", help="Project directory.")
    asset_parser.add_argument("--file", required=True, help="Image file to copy into AD-creative/visual_assets.")
    asset_parser.add_argument("--slot-id", default="AUTO-SLOT")
    asset_parser.add_argument("--requirement-id", default="")
    asset_parser.add_argument("--reference-id", default="")
    asset_parser.add_argument("--asset-type", default="generated_image")
    asset_parser.add_argument("--visibility", default="internal_only")
    asset_parser.add_argument("--qa-status", default="PASS")
    asset_parser.add_argument("--risk-level", default="medium")
    asset_parser.add_argument("--prompt-or-edit-ref", default="")
    asset_parser.add_argument("--notes", default="")
    asset_parser.add_argument("--selected", action="store_true")
    asset_parser.set_defaults(func=command_add_asset)

    imagegen_parser = subparsers.add_parser(
        "import-imagegen",
        help="Import a built-in image_gen output from CODEX_HOME/generated_images.",
    )
    imagegen_parser.add_argument("project", help="Project directory.")
    imagegen_parser.add_argument(
        "--file",
        default="",
        help="Generated image under CODEX_HOME/generated_images. Uses the latest generated image when omitted.",
    )
    imagegen_parser.add_argument("--slot-id", default="AUTO-IMAGEGEN")
    imagegen_parser.add_argument("--requirement-id", default="")
    imagegen_parser.add_argument("--reference-id", default="pending")
    imagegen_parser.add_argument("--visibility", default="internal_only")
    imagegen_parser.add_argument("--qa-status", default="PARTIAL_PASS")
    imagegen_parser.add_argument("--risk-level", default="medium")
    imagegen_parser.add_argument("--prompt-or-edit-ref", default="")
    imagegen_parser.add_argument(
        "--notes",
        default="Imported from built-in image_gen output; internal review only.",
    )
    imagegen_parser.add_argument("--selected", action="store_true")
    imagegen_parser.set_defaults(func=command_import_imagegen)

    visual_quality_parser = subparsers.add_parser(
        "visual-quality-gate",
        help="Audit visual assets for file quality, traceability, and client-visible safety.",
    )
    visual_quality_parser.add_argument("project", help="Project directory.")
    visual_quality_parser.add_argument("--min-long-edge", type=int, default=720)
    visual_quality_parser.add_argument("--min-short-edge", type=int, default=480)
    visual_quality_parser.set_defaults(func=command_visual_quality_gate)

    film_quality_parser = subparsers.add_parser(
        "film-quality-gate",
        help="Audit cinematic/commercial quality before client-review packaging.",
    )
    film_quality_parser.add_argument("project", help="Project directory.")
    film_quality_parser.set_defaults(func=command_film_quality_gate)

    export_pptx_parser = subparsers.add_parser("export-pptx", help="Create an editable internal PPTX draft and check it.")
    export_pptx_parser.add_argument("project", help="Project directory.")
    export_pptx_parser.add_argument("--output", default="", help="Optional PPTX output path.")
    export_pptx_parser.set_defaults(func=command_export_pptx)

    check_pptx_parser = subparsers.add_parser("check-pptx", help="Check an actual PPTX for editable text layers.")
    check_pptx_parser.add_argument("project", help="Project directory.")
    check_pptx_parser.add_argument("--file", required=True, help="PPTX file to inspect.")
    check_pptx_parser.set_defaults(func=command_check_pptx)

    client_gate_parser = subparsers.add_parser("client-pack-gate", help="Audit client-review candidates before any send.")
    client_gate_parser.add_argument("project", help="Project directory.")
    client_gate_parser.add_argument("--pptx", default="", help="Optional PPTX file to inspect.")
    client_gate_parser.set_defaults(func=command_client_pack_gate)

    handoff_gate_parser = subparsers.add_parser(
        "handoff-readiness-gate",
        help="Audit whether the project can be handed to a non-developer operator.",
    )
    handoff_gate_parser.add_argument("project", help="Project directory.")
    handoff_gate_parser.set_defaults(func=command_handoff_readiness_gate)

    install_skill_parser = subparsers.add_parser("install-skill", help="Install the project skill into ~/.codex/skills.")
    install_skill_parser.add_argument("--target", default="", help="Optional skill install directory.")
    install_skill_parser.set_defaults(func=command_install_skill)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
