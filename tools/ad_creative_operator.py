#!/usr/bin/env python3
"""Non-developer operation surface for Ad Creative Orchestrator projects."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable
import xml.etree.ElementTree as ET

from init_project import copy_template
from runtime_paths import repo_or_module_root, skill_draft_dir, template_root
from validate_project import validate


REPO_ROOT = repo_or_module_root()
TEMPLATE_ROOT = template_root()
SKILL_DRAFT_DIR = skill_draft_dir()
DEFAULT_SKILL_INSTALL_DIR = Path.home() / ".codex/skills/ad-creative-orchestrator"
DASHBOARD_REL = Path("AD-creative/handoff/操作台.html")
COUNCIL_REPORT_REL = Path("AD-creative/gates/THREE-COUNCIL-READINESS_report.md")
GOAL_PLAN_TEMPLATE_REL = Path("AD-creative/orchestrator/goal_iteration_plan_template.md")
GOAL_ITERATIONS_REL = Path("AD-creative/orchestrator/goal_iterations")
SAMPLE_MATERIAL_REL = Path("00_项目资料_ProjectMaterials/01_客户资料_ClientMaterials/sample_brief.md")
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

    stage = project_stage(project)
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
	      ["asset_id", "图片"], ["slot_id", "槽位"], ["status", "状态"], ["visibility", "可见性"], ["qa_status", "QA"]
	    ],
	    id: "asset_id",
	    titleKey: "path",
	    objectiveKey: "notes"
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


def print_status(project: Path) -> None:
    counts = read_counts(project)
    errors, _ = validate(project)
    dashboard = project / DASHBOARD_REL
    report = project / COUNCIL_REPORT_REL
    print(f"PROJECT={project.resolve()}")
    print(f"STAGE={project_stage(project)}")
    print(f"VALIDATION={'PASS' if not errors else 'CHECK'}")
    print(f"SOURCE_EVENTS={counts['source_events']}")
    print(f"WORK_ITEMS={counts['work_items']}")
    print(f"REFERENCES={counts['references']}")
    print(f"ASSETS={counts['assets']}")
    print(f"ARTIFACTS={counts['artifacts']}")
    print(f"GATES={counts['gates']}")
    print(f"DASHBOARD={dashboard if dashboard.exists() else 'MISSING'}")
    print(f"COUNCIL_REPORT={report if report.exists() else 'MISSING'}")
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"- {error}")


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


def review_client_pack(project: Path, pptx_path: Path | None = None) -> tuple[str, list[str], Path]:
    _, artifacts = read_csv_rows(project / "AD-creative/orchestrator/artifact_index.csv")
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

    default_pptx = project / "AD-creative/ppt/client_review_draft.pptx"
    check_target = pptx_path or (default_pptx if default_pptx.exists() else None)
    pptx_stats: dict[str, int | bool | str] | None = None
    if check_target:
        pptx_stats = inspect_pptx(check_target)
        if not pptx_stats["editable"]:
            issues.append("PPTX 缺少可编辑文本层。")
        evidence.append(
            f"pptx={safe_rel(project, check_target)} slides={pptx_stats['slides']} editable_text_runs={pptx_stats['editable_text_runs']}"
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

## Objective

{objective}

## Scope

- 使用双泳道：品牌深度研究 / 图片功能。
- 阶段完成后直接推进下一步低风险内部任务。
- 每个 Gate 前必须有反驳性议会记录。

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

    pptx = project / "AD-creative/ppt/client_review_draft.pptx"
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


def command_run(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    created, skipped = ensure_project(project)
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


def command_render_dashboard(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    ensure_project(project)
    dashboard = render_dashboard(project)
    print(f"DASHBOARD={dashboard}")
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
    print_status(Path(args.project).resolve())
    return 0


def command_audit_dashboard(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    if args.render:
        ensure_project(project)
        render_dashboard(project)
    issues = audit_dashboard(project)
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
    subparsers = parser.add_subparsers(dest="command", required=True)

    goal_parser = subparsers.add_parser("goal-plan", help="Create a reusable goal iteration execution plan.")
    goal_parser.add_argument("project", help="Project directory.")
    goal_parser.add_argument("--goal-id", default="", help="Stable goal id. Defaults to timestamp.")
    goal_parser.add_argument("--title", default="", help="Human-readable goal title.")
    goal_parser.add_argument("--objective", default="", help="Goal objective.")
    goal_parser.add_argument("--owner", default="Main Controller", help="Goal owner.")
    goal_parser.add_argument("--force", action="store_true", help="Overwrite an existing goal plan with the same id.")
    goal_parser.set_defaults(func=command_goal_plan)

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

    status_parser = subparsers.add_parser("status", help="Print current project status.")
    status_parser.add_argument("project", help="Project directory.")
    status_parser.set_defaults(func=command_status)

    dashboard_parser = subparsers.add_parser("render-dashboard", help="Render static operation dashboard.")
    dashboard_parser.add_argument("project", help="Project directory.")
    dashboard_parser.set_defaults(func=command_render_dashboard)

    intake_parser = subparsers.add_parser("intake", help="Extract first-pass requirements and gaps from registered materials.")
    intake_parser.add_argument("project", help="Project directory.")
    intake_parser.add_argument("--source-id", action="append", default=[], help="Registered source_event_id to process. Repeatable.")
    intake_parser.add_argument("--goal", default="先完成需求整理、缺口判断、客户追问、下一步建议。")
    intake_parser.set_defaults(func=command_intake)

    audit_parser = subparsers.add_parser("audit-dashboard", help="Audit dashboard usability markers.")
    audit_parser.add_argument("project", help="Project directory.")
    audit_parser.add_argument("--render", action="store_true", help="Render dashboard before auditing.")
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
