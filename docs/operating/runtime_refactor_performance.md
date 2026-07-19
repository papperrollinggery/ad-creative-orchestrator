# Runtime Refactor Performance Receipt

Status: measured locally on 2026-07-19 with Python 3.14.5

## Comparison

Baseline: `46c548a` (`docs: streamline public repository onboarding`)

Refactored runtime: `7732d77` (`test: add activation ingestion creative and latency regressions`)

Each side ran five fresh temporary projects with the same two materials:

```text
pasted-text.txt: 15,466 characters
intake_and_facts.md: includes “客户已提供产品图”
```

Timing covers `command_run` from entry to return; the table reports the median of
five runs. Counters on the baseline were measured by wrapping the real runtime
functions, not inferred from documentation. Current counters came from
`adco run --json`.

| Metric | Baseline | Refactored | Result |
|---|---:|---:|---|
| `adco run` median | 57 ms | 38 ms | 33% lower |
| Dashboard renders | 2 | 1 | target met |
| Full validation calls | 4 | 0 | scoped validation only |
| Council calls | 1 | 0 | target met |
| Material characters read | 14,478 | 19,180 | no silent 12,000-character truncation |
| Evidence chunks | 0 | 7 | source-preserving chunks written |
| False “missing product image” gaps | 1 | 0 | semantic inversion removed |
| Files present after fresh run | 105 | 105 | no file-count expansion |
| Template files reported created | 95 | 95 | unchanged |

The refactored run executed only:

```text
validate_source_events
validate_evidence_chunks
validate_fact_inventory
validate_requirements_gaps
```

It reported Specialist handoffs, PPT auto-generation, Client Pack runs, and full
validation runs as zero.

## Positive headless workflow receipt

A separate fresh project ingested this material:

```text
客户已提供产品图，包含正面、侧面和包装细节，文件可用于本轮内部方案。
```

Observed result:

```text
RUN=PASS
characters_read=44
evidence_chunks=1
fact_key=asset.product_images
fact_state=present
gaps=0
dashboard_render_count=1
council_run_count=0
full_validation_run_count=0
```

The same project then ran `creative-brief`, imported a two-direction candidate
bound to the exact brief snapshot/evidence chunk, ran `creative-review`, and
finished with explicit full project validation:

```text
creative-brief=PASS; directions_generated=0
creative-import=PASS; directions=2; creative_quality=NOT_EVALUATED
creative-review=PARTIAL_PASS; independent_critic_required=true
adco validate=PASS; errors=0
```

This receipt proves the headless control path and deterministic contracts. It does
not claim that the fixture's creative content passed an independent human Critic.
