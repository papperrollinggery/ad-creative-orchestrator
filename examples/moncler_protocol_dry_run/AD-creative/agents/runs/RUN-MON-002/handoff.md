# Agent Handoff Packet

run_id: RUN-MON-002
work_id: W-MON-002
agent_role: Research Agent
status: needs_input

## Task Objective

Prepare official Moncler reference research after user approves scope.

## Input Files

```text
AD-creative/orchestrator/current_truth.md
AD-creative/orchestrator/requirements.csv
AD-creative/orchestrator/gaps.csv
AD-creative/references/official_search_plan.md
```

## Required Outputs

```text
AD-creative/references/reference_cards.csv
AD-creative/references/reference_shortlist.md
AD-creative/references/brand_visual_dna.md
AD-creative/references/do_not_copy.md
```

## Allowed Actions

```text
Search only approved official or clearly attributable sources.
Summarize visual DNA.
Flag uncertain sources.
Recommend what can inform visual direction.
```

## Forbidden Actions

```text
Do not cite unverified uploads as official.
Do not download or reuse copyrighted images as client assets.
Do not generate images.
Do not create client-facing slides.
Do not mark any reference client_visible without gate.
```

## Linked Requirements

```text
R-MON-002
R-MON-003
```

## Gate To Pass

```text
Research Gate
```

## Handoff Back Format

```text
summary
verified sources
uncertain sources
reference cards produced
open questions
recommended next action
```
