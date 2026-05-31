# First Run Transcript

Status: generated from local commands

This transcript is produced by:

```bash
python3 tools/render_demo_transcript.py
```

```console
$ adco demo /tmp/adco-first-run --goal-id GOAL-DEMO-FIRST-RUN --no-open
DEMO=PASS
PROJECT=/tmp/adco-first-run
CREATED_FILES=69
SKIPPED_EXISTING_FILES=0
SAMPLE_MATERIAL=/tmp/adco-first-run/00_项目资料_ProjectMaterials/01_客户资料_ClientMaterials/sample_brief.md
SAMPLE_MATERIAL_ACTION=created
REGISTERED_SOURCES=1
SOURCE_IDS=SRC-001
INTAKE_MATERIALS=1
INTAKE_REQUIREMENTS=9
INTAKE_GAPS=5
GOAL_PLAN=/tmp/adco-first-run/AD-creative/orchestrator/goal_iterations/GOAL-DEMO-FIRST-RUN.md
DASHBOARD=/tmp/adco-first-run/AD-creative/handoff/操作台.html
DASHBOARD_OPEN=SKIPPED
COUNCIL=PASS
COUNCIL_REPORT=/tmp/adco-first-run/AD-creative/gates/THREE-COUNCIL-READINESS_report.md
SOURCE_EVENTS=1
REQUIREMENTS=9
WORK_ITEMS=1
AGENT_RUNS=0
ARTIFACTS=3
GATES=2
VERSIONS=0
REFERENCES=0
ASSETS=0
ERRORS=0
VALIDATION=PASS
```

```console
$ adco status /tmp/adco-first-run
PROJECT=/tmp/adco-first-run
STAGE=intake
VALIDATION=PASS
SOURCE_EVENTS=1
REQUIREMENTS=9
GAPS=5
WORK_ITEMS=1
ACTIVE_WORK=0
OPEN_GAPS=5
BLOCKING_GAPS=4
PENDING_CONFIRMATIONS=5
REFERENCES=0
ASSETS=0
ARTIFACTS=3
GATES=2
NEXT_ACTION=请提供品牌 logo、字体、包装或产品露出规范。
DASHBOARD=/tmp/adco-first-run/AD-creative/handoff/操作台.html
COUNCIL_REPORT=/tmp/adco-first-run/AD-creative/gates/THREE-COUNCIL-READINESS_report.md
```

```console
$ adco validate /tmp/adco-first-run
SOURCE_EVENTS=1
REQUIREMENTS=9
WORK_ITEMS=1
AGENT_RUNS=0
ARTIFACTS=3
GATES=2
VERSIONS=0
REFERENCES=0
ASSETS=0
ERRORS=0
VALIDATION=PASS
```

```console
$ adco open-dashboard /tmp/adco-first-run --no-open
DASHBOARD=/tmp/adco-first-run/AD-creative/handoff/操作台.html
DASHBOARD_OPEN=SKIPPED
SOURCE_EVENTS=1
REQUIREMENTS=9
WORK_ITEMS=1
AGENT_RUNS=0
ARTIFACTS=3
GATES=2
VERSIONS=0
REFERENCES=0
ASSETS=0
ERRORS=0
VALIDATION=PASS
```

```console
$ adco support-bundle /tmp/adco-first-run
SUPPORT_BUNDLE=PASS
REPORT=/tmp/adco-first-run/AD-creative/handoff/support_bundle.md
SOURCE_EVENTS=1
REQUIREMENTS=9
WORK_ITEMS=1
AGENT_RUNS=0
ARTIFACTS=3
GATES=2
VERSIONS=0
REFERENCES=0
ASSETS=0
ERRORS=0
VALIDATION=PASS
```

```console
$ adco audit-dashboard /tmp/adco-first-run --render
DASHBOARD_AUDIT=PASS
DASHBOARD=/tmp/adco-first-run/AD-creative/handoff/操作台.html
```

## Expected Files

```text
/tmp/adco-first-run/AD-creative/handoff/操作台.html
/tmp/adco-first-run/AD-creative/orchestrator/current_truth.md
/tmp/adco-first-run/AD-creative/orchestrator/requirements.csv
/tmp/adco-first-run/AD-creative/orchestrator/gaps.csv
/tmp/adco-first-run/AD-creative/orchestrator/goal_iterations/GOAL-DEMO-FIRST-RUN.md
```
