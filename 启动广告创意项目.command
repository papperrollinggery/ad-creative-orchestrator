#!/bin/zsh
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || true)}"
DEFAULT_GOAL="先完成需求整理、缺口判断、客户追问、下一步建议。"

fail_dialog() {
  local message="$1"
  if [[ -z "${AD_CREATIVE_NO_DIALOG:-}" ]]; then
    /usr/bin/osascript - "$message" <<'APPLESCRIPT' >/dev/null 2>&1 || true
on run argv
  display alert "广告创意项目启动失败" message (item 1 of argv) as warning
end run
APPLESCRIPT
  fi
  print -r -- "$message"
}

choose_project() {
  if [[ -n "${AD_CREATIVE_PROJECT:-}" ]]; then
    print -r -- "$AD_CREATIVE_PROJECT"
    return 0
  fi
  /usr/bin/osascript <<'APPLESCRIPT'
try
  set pickedFolder to choose folder with prompt "选择或新建广告项目文件夹。可以在弹窗里点 New Folder。"
  return POSIX path of pickedFolder
on error number -128
  return "__CANCELLED__"
end try
APPLESCRIPT
}

choose_material() {
  if [[ -n "${AD_CREATIVE_MATERIAL:-}" ]]; then
    print -r -- "$AD_CREATIVE_MATERIAL"
    return 0
  fi
  /usr/bin/osascript <<'APPLESCRIPT'
try
  set modeChoice to choose from list {"资料文件夹", "单个资料文件", "跳过资料选择"} with prompt "选择客户 brief、会议记录、反馈、参考链接等资料。" default items {"资料文件夹"}
  if modeChoice is false then return "__CANCELLED__"
  set modeText to item 1 of modeChoice
  if modeText is "跳过资料选择" then return ""
  if modeText is "资料文件夹" then
    set pickedFolder to choose folder with prompt "选择客户资料文件夹"
    return POSIX path of pickedFolder
  end if
  set pickedFile to choose file with prompt "选择客户资料文件"
  return POSIX path of pickedFile
on error number -128
  return "__CANCELLED__"
end try
APPLESCRIPT
}

ask_goal() {
  if [[ -n "${AD_CREATIVE_GOAL:-}" ]]; then
    print -r -- "$AD_CREATIVE_GOAL"
    return 0
  fi
  /usr/bin/osascript <<'APPLESCRIPT'
try
  set answerText to text returned of (display dialog "本轮要 Codex 先完成什么？" default answer "先完成需求整理、缺口判断、客户追问、下一步建议。" buttons {"取消", "开始"} default button "开始" cancel button "取消")
  return answerText
on error number -128
  return "__CANCELLED__"
end try
APPLESCRIPT
}

if [[ -z "$PYTHON_BIN" ]]; then
  fail_dialog "找不到 python3。请先安装 Python 3。"
  exit 1
fi

PROJECT_PATH="$(choose_project)"
if [[ "$PROJECT_PATH" == "__CANCELLED__" || -z "$PROJECT_PATH" ]]; then
  print -r -- "已取消。"
  exit 0
fi

MATERIAL_PATH="$(choose_material)"
if [[ "$MATERIAL_PATH" == "__CANCELLED__" ]]; then
  print -r -- "已取消。"
  exit 0
fi

GOAL_TEXT="$(ask_goal)"
if [[ "$GOAL_TEXT" == "__CANCELLED__" ]]; then
  print -r -- "已取消。"
  exit 0
fi
if [[ -z "$GOAL_TEXT" ]]; then
  GOAL_TEXT="$DEFAULT_GOAL"
fi

mkdir -p "$PROJECT_PATH"
LOG_PATH="$PROJECT_PATH/ad-creative-run-$(date +%Y%m%d-%H%M%S).log"

print -r -- "PROJECT=$PROJECT_PATH"
print -r -- "MATERIAL=$MATERIAL_PATH"
print -r -- "GOAL=$GOAL_TEXT"
print -r -- "LOG=$LOG_PATH"
print -r -- ""

if [[ -n "$MATERIAL_PATH" ]]; then
  "$PYTHON_BIN" "$SCRIPT_DIR/tools/ad_creative_operator.py" run "$PROJECT_PATH" --material "$MATERIAL_PATH" --goal "$GOAL_TEXT" 2>&1 | tee "$LOG_PATH"
  STATUS=${pipestatus[1]}
else
  "$PYTHON_BIN" "$SCRIPT_DIR/tools/ad_creative_operator.py" run "$PROJECT_PATH" --goal "$GOAL_TEXT" 2>&1 | tee "$LOG_PATH"
  STATUS=${pipestatus[1]}
fi

DASHBOARD_PATH="$PROJECT_PATH/AD-creative/handoff/操作台.html"

if [[ "$STATUS" -ne 0 ]]; then
  fail_dialog "运行未通过。日志：$LOG_PATH"
  exit "$STATUS"
fi

print -r -- ""
print -r -- "正在生成可编辑 PPTX 草稿..."
"$PYTHON_BIN" "$SCRIPT_DIR/tools/ad_creative_operator.py" export-pptx "$PROJECT_PATH" 2>&1 | tee -a "$LOG_PATH"
PPT_STATUS=${pipestatus[1]}
if [[ "$PPT_STATUS" -ne 0 ]]; then
  fail_dialog "PPTX 草稿生成或可编辑性检查未通过。日志：$LOG_PATH"
  exit "$PPT_STATUS"
fi

print -r -- ""
print -r -- "正在运行客户稿风险 Gate..."
"$PYTHON_BIN" "$SCRIPT_DIR/tools/ad_creative_operator.py" client-pack-gate "$PROJECT_PATH" 2>&1 | tee -a "$LOG_PATH"
CLIENT_GATE_STATUS=${pipestatus[1]}
if [[ "$CLIENT_GATE_STATUS" -ne 0 ]]; then
  fail_dialog "客户稿风险 Gate 未通过。日志：$LOG_PATH"
  exit "$CLIENT_GATE_STATUS"
fi

if [[ -z "${AD_CREATIVE_NO_OPEN:-}" && -f "$DASHBOARD_PATH" ]]; then
  open "$DASHBOARD_PATH"
fi

if [[ -z "${AD_CREATIVE_NO_DIALOG:-}" ]]; then
  /usr/bin/osascript -e "display notification \"操作台已生成\" with title \"广告创意项目\"" >/dev/null 2>&1 || true
fi

print -r -- ""
print -r -- "DONE"
print -r -- "DASHBOARD=$DASHBOARD_PATH"
