# Durable Creative Contract

Read this file only for cross-model/provider exchange, imported candidates, or a
versioned review that must bind an exact brief snapshot. Direct creative work is
in [creative_work.md](creative_work.md). ADCO's deterministic checks protect
evidence and structure; the current model or an explicitly chosen Specialist does
the creative reasoning.

## Durable candidate exchange

Use this flow only for cross-model/provider exchange, imported candidates, or a
versioned review that must bind to an exact brief snapshot:

```text
adco creative-brief <project> [--work-id <id>] [--json]
-> creative model or Specialist generates mechanism-distinct candidates
-> Critic is added when the decision boundary requires independent judgment
-> retain the requested number of viable candidates
adco creative-import <project> --file <candidate.json> [--json]
adco creative-review <project> [--json]
```

When the local operator intentionally chooses to enforce a parsed hard
requirement, record and bind only that row instead of opening a broader workflow:

```text
adco creative-assertion-record <project> --semantics creative_requirement_confirmation --requirement-id <id> --note <reason> [--json]
adco creative-requirement-confirm <project> --requirement-id <id> --confirmation-ref <local_operator_assertion:id> [--evidence-ref <chunk>] [--json]
adco creative-brief <project>
```

When one candidate check is explicitly `REVIEW_REQUIRED` because no safe
deterministic checker exists, resolve that exact candidate/constraint pair:

```text
adco creative-assertion-record <project> --semantics <creative_constraint_approval|creative_constraint_rejection> --requirement-id <id> --artifact-binding <candidate_payload_sha256:...> --artifact-binding <brief_snapshot_sha256:...> --artifact-binding <direction_id:...> --artifact-binding <constraint_id:...> --note <reason> [--json]
adco creative-constraint-resolve <project> --file <candidate.json> --direction-id <id> --constraint-id <id> --confirmation-ref <local_operator_assertion:id> --decision <approved|rejected> --note <reason> [--json]
adco creative-assertion-status <project> [--assertion-ref <local_operator_assertion:id>] [--json]
adco creative-assertion-revoke <project> --assertion-ref <local_operator_assertion:id> --reason <reason> [--json]
```

Do not use either command for ordinary internal drafting. They exist only to
close a real durable-import blocker without creating Council, Thread, Gate, or
Delivery work.

The referenced row is deliberately a **local workflow assertion**, not identity,
consent, client approval, or send authority:

- requirement assertion: `source_type=local_operator_assertion`,
  `source_owner=local_operator`, `trust_level=local_asserted`,
  `declared_semantics=creative_requirement_confirmation`, exactly one
  `affects_requirements=<requirement_id>`, no `affects_artifacts`, and one
  generated project-local assertion record;
- constraint resolution: the same local-only boundary, semantics
  `creative_constraint_approval|creative_constraint_rejection`, the exact
  requirement id, and semicolon-separated exact artifact bindings for
  `candidate_payload_sha256`, `brief_snapshot_sha256`, `direction_id`, and
  `constraint_id`.

The event row and evidence file are hash-bound in the receipt. A later edit,
target change, or revocation invalidates its use. Every status/readback repeats
`identity_assurance=NONE`; project files cannot prove who the human was.

`adco creative-proposal` is a deprecated compatibility alias for
`creative-brief`. It emits a deprecation notice and does not generate directions.

`creative-brief` writes only:

```text
AD-creative/creative/brief_snapshot.json
AD-creative/creative/creative_brief_manifest.json
AD-creative/creative/creative_brief_contract.json
AD-creative/creative/creative_candidate.schema.json
AD-creative/creative/creative_generation_request.json
AD-creative/creative/creative_open_evidence_gaps.json
```

It binds current facts, requirements, evidence chunk ids, and open evidence gaps.
It does not write `creative_directions.md`, an option matrix, slogans, a client
outline, or a PPT.

The generation request inherits the active host model or the user's explicit
selection. Read the source text at `evidence_input.path`, verified against its
exact byte hash and the allowed refs in `brief_snapshot_path`; the snapshot's
ids and metadata alone do not contain the source meaning. This keeps one evidence
owner rather than duplicating the material into each request. A changed upstream
input makes an existing brief stale and scoped validation reports `CHECK` until
the brief is rebuilt when needed. It never rewrites the old creative output.

The manifest binds the exact bytes of every brief member. Snapshot inputs are
read once through POSIX anchored, no-follow descriptors; the snapshot binds the
actual evidence record and text hashes plus the captured facts, requirements,
gaps, relevant source events, confirmations, and revocations. Its self-hash is
recomputed and compared at import and review time. A corrupt, hand-edited,
raced, or stale member fails closed instead of falling back to a generic count.

The contract extracts machine-readable hard constraints when the source is
explicit: maximum runtime, maximum cast, location allowlist, required or
prohibited physical product exposure, and prohibited claims. A durable import
enforces only a requirement whose workflow receipt binds the exact row to a
registered source/evidence and an active local-operator assertion with exact
semantics, evidence hash, and target binding. This is enforceable only inside
the local workflow and has no identity assurance. Editing status/owner text
alone never creates a valid assertion. Parser-created
`candidate` rows remain `REVIEW_REQUIRED`; parser confidence never upgrades them
silently. The generation request requires supported constraints to appear in
checkable direction fields. Any explicit hard clause without a deterministic
checker remains `REVIEW_REQUIRED` until a local workflow resolution bound to
the exact candidate payload, direction, constraint, and snapshot approves or
rejects it.

## Imported candidate contract

The imported JSON binds the exact `brief_snapshot_sha256` and contains the
explicitly requested number of directions, or the smallest sufficient set when
no count was requested (one to six). The six-direction limit is a durable import
limit, not a cap on direct exploration. A larger explicit request must be fulfilled
directly before a selected set is bound for import; never silently reduce its count.
Add an independent Critic before import
only when the decision boundary requires it. Every direction has non-empty:

```text
direction_id, name, human_tension, brand_truth, audience_truth,
single_minded_proposition, creative_mechanism, key_visual, story_or_behavior,
product_role, channel_execution, why_brand_can_own_it, production_risk,
evidence_refs
```

It also declares `runtime_seconds`, `cast_count`, `locations`,
`product_exposure.physical_product_visible`, a product-exposure description,
and the claims the direction actually makes. These structured values are the
primary deterministic contract; prose is cross-checked for contradictions.

Every evidence ref must name an existing evidence chunk. That proves provenance,
not semantic support for every claim. `creative-import` rejects unbound refs,
stale snapshots, missing/extra fields, duplicate ids/names, duplicate normalized
mechanisms, prohibited claims in any persisted narrative or product-description
field, failed hard constraints, and unresolved hard-constraint review items
before writing any candidate/current/receipt/rendered artifact. Weak or generic
brand ownership is flagged as a brand-replacement risk. A valid import prepares
one immutable generation directory containing the exact candidate, import
receipt, readable directions, option matrix, and generation manifest; all remain
`internal_only`. The receipt's
`candidate_sha256` hashes the exact persisted version bytes; the separately named
`candidate_payload_sha256` is only the normalized semantic payload hash. Only
`AD-creative/creative/current_generation.json` is atomically switched after the
entire generation verifies. Human-readable current views resolve through that
pointer, so an interrupted switch leaves every old current artifact coherent;
an unreferenced prepared generation is never current. Review rejects any
exact-byte mismatch across the pointer, generation manifest, candidate, receipt,
brief manifest, directions, or matrix.

`creative-review` reports evidence refs as `PROVENANCE_ONLY` and separates that
from brief adherence. For the
supported hard constraints above, it semantically checks the candidate text and
fails closed when a required value is missing, outside an allowlist, or cannot
be confirmed. It also lints mechanism difference, ownership, visual clarity,
shootability, and production risk. On the Content Surface it returns the lint
result without a persistent receipt; Delivery writes a bound receipt. It does
not replace the independent creative Critic, client judgment, or effectiveness
evidence. `creative-quality-gate` remains a downstream legacy proposal safety
Gate and must not be presented as model reasoning or independent Critic judgment.
