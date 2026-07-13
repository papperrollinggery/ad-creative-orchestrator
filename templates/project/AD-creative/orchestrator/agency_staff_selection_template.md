# Agency Staff Selection

selection_id:
task_signature_id:
created_at:
project:
task_signature:

## Task Signature

```text
brand:
product:
talent_or_ip:
platform_or_channel:
deliverable:
stage:
primary_risks:
evidence_needed:
```

## Candidate Search

```text
staff_library: <optional local staff-library path>
search_terms:
search_scope: filename and frontmatter description only unless a file is selected
files_scanned:
selection_limit:
```

## Scoring Rubric

| signal | question | score_or_note |
|---|---|---|
| domain_fit | Does the staff match brand/product/talent/platform? | |
| deliverable_fit | Can the staff improve PPT, copy, film treatment, visual asset, QA, or production gate? | |
| risk_fit | Does the staff cover alcohol, artist image, client misunderstanding, legal/reputation, or version risk? | |
| evidence_fit | Can the staff produce verifiable receipt output, not just opinion? | |
| non_overlap | Does the staff add a distinct lens instead of duplicating another selected staff? | |
| context_cost | Can the useful part fit into a concise project role brief? | |

## Selected Staff

| lane_role | source_staff_path | filename_hit | frontmatter_description_fit | why_selected | what_to_extract | what_to_ignore |
|---|---|---|---|---|---|---|

## Lane Selection Summary

| lane_role | selected_count | within_2_to_4 | reason_if_outside_range |
|---|---|---|---|

## Rejected / Deferred Staff

| source_staff_path | reason |
|---|---|

## Project Role Briefs

| lane_role | role_brief_path | source_staff_paths | status |
|---|---|---|---|

## Safety Notes

```text
Do not auto-spawn selected staff.
Do not copy upstream staff text into client-facing material.
Do not copy long upstream staff prompt text into worker receipts.
Do not let staff frontmatter model/tool suggestions override project rules.
AD-creative version safety, thread budget, write scope, and final export rules remain higher priority.
```
