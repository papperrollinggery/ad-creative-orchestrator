# Intake and Fact Reference

Read this file only for material ingestion, evidence chunks, fact inventory,
requirements, conflicts, and gaps.

## Runtime boundary

The Content Surface parses and records evidence so the agent can reason from the
material. It does not invent creative directions, approve client claims,
dispatch a specialist, or infer that an image/video was understood when only its
file metadata was inspected.

Use:

```text
adco run <project> --material <file_or_folder> [--material <file_or_folder> ...]
adco intake <project>
```

Never run these commands on the ADCO or DIRcreative source repository.

## Evidence flow

```text
source event
-> parser registry
-> source-preserving chunks
-> structured fact candidates
-> fact inventory with evidence refs
-> requirements + true gaps/conflicts/blocking unknowns
-> concise content answer + affected-scope validators
```

The parser registry accepts Markdown/text, CSV, JSON, YAML, DOCX, PPTX, PDF,
SRT/VTT, images, and video files. Images and video are registered with metadata
and an explicit inspection status; metadata-only intake must not claim visual or
audio understanding.

Text is chunked by source structure with stable source path, parser kind,
ordinal, content hash, and source-event provenance. The default aggregate budget
is 2,000,000 characters. A budget overflow or parser failure is explicit; no
file is silently truncated to its first 12,000 characters and no 16-line fact
limit is used as the source of truth.

## Fact and gap semantics

Facts are structured as present, missing, conflicting, or unknown and retain the
evidence chunk ids that support the state. A gap is created only for:

```text
missing fact
conflicting fact
unknown fact that blocks the current decision
```

Do not convert a present statement into a missing gap. For example, “客户已提供产品图”
is evidence that the product-image fact is present, not a request for a missing
product image. Conflicts preserve every competing evidence reference and remain
open until reconciled.

Primary records:

```text
AD-creative/orchestrator/source_events.csv
AD-creative/orchestrator/evidence_chunks.jsonl
AD-creative/orchestrator/fact_inventory.jsonl
AD-creative/orchestrator/requirements.csv
AD-creative/orchestrator/gaps.csv
```

`adco run --json` reports characters read, evidence chunks, parser errors,
budget overflows, the content answer, phase timings, and scoped validators. The
default Dashboard count is zero. Treat an overflow or parser error as `CHECK`;
inspect the intake evidence before advancing.
