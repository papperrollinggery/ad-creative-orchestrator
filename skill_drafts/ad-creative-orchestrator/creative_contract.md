# Creative Contract Reference

Read this file only for creative direction work or a durable candidate exchange.

## Use direct reasoning by default

For an internal brief, concept, script, storyboard, or ordinary revision, reason
directly from the inspected material and return the useful creative work. Do not
create a candidate contract, version, Gate, or Specialist handoff merely because
the task is creative. Match the number of directions to the request; do not force
a preset option count after the useful distinctions are already covered.

An explicit internal second judgment may use a read-only Critic on the Content
Surface. Return that judgment directly; do not create a Delivery Surface, Thread,
Gate, candidate contract, version ledger, or persistent Critic receipt for that
reason alone. Use a durable independent Critic only when a consequential review
must bind an exact candidate/client-visible version, or when the user explicitly
requests isolated/parallel execution. Critic review is not mandatory for every
brainstorm.

ADCO's deterministic strings are evidence and structural checks, not a complete
creative engine. The active model or an explicitly chosen creative Specialist
owns creative reasoning; ADCO owns any durable evidence, provenance, and version
contract that the task actually needs.

Before returning direct creative work, silently verify the draft itself against
every explicit hard constraint: runtime, cast, allowed locations (including
sub-locations), required product exposure, and prohibited claims. Location names
are exact and physically literal: a living room does not authorize kitchen/fridge
retrieval; an exterior entrance does not authorize interior fridges, shelves, or
checkout. Relabeling the scene does not cure the mismatch. Evidence refs
prove provenance, not compliance. Repair violations before answering. When the
user names multiple channels, specify the execution difference that matters on
each channel. When showing alternatives, vary the causal creative mechanism and
run a brand-replacement test against adjacent substitutes, not only unrelated
categories. The named brand/product truth must cause the mechanism to work rather
than appear as a label. If supplied facts support only category ownership, say so
and identify the replacement risk rather than inventing exclusivity. Use no
comparative production claim such as lowest, easiest, or safest unless a
visible comparison cites a differentiating location, shot, permission, prop,
performance, or post-production burden against every alternative; otherwise omit
the ranking.

Treat a ban on fabricated facts or data literally in the creative itself. Do not
invent exact meeting times, calendar entries, clock displays, prices, cities,
metrics, testimonials, or product attributes merely as story texture. Production
timecodes, total runtime, and cast count may use numbers because they describe the
proposed artifact, not the advertised world. Also remove close euphemisms for a
prohibited outcome: a ban on sobering or health claims includes unsupported
`clear-headed`, `sober`, `low-burden`, or equivalent benefit language even when
the exact banned noun is absent.

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

When a parsed hard requirement is real but not yet authoritative, confirm only
that row instead of opening a broader workflow:

```text
adco creative-requirement-confirm <project> --requirement-id <id> --confirmation-ref <user_confirmation:id|client_confirmation:id> [--evidence-ref <chunk>] [--json]
adco creative-brief <project>
```

When one candidate check is explicitly `REVIEW_REQUIRED` because no safe
deterministic checker exists, resolve that exact candidate/constraint pair:

```text
adco creative-constraint-resolve <project> --file <candidate.json> --direction-id <id> --constraint-id <id> --confirmation-ref <user_confirmation:id|client_confirmation:id> --decision <approved|rejected> --note <reason> [--json]
```

Do not use either command for ordinary internal drafting. They exist only to
close a real durable-import blocker without creating Council, Thread, Gate, or
Delivery work.

The referenced `source_events.csv` row is an authority record, not a name:

- requirement confirmation: `source_type=user_confirmation|client_confirmation`,
  matching `source_owner` and `<authority>_confirmed` trust,
  `declared_semantics=creative_requirement_confirmation`, exactly one
  `affects_requirements=<requirement_id>`, no `affects_artifacts`, and one
  project-local evidence file;
- constraint resolution: the same identity rules, semantics
  `creative_constraint_approval|creative_constraint_rejection`, the exact
  requirement id, and semicolon-separated exact artifact bindings for
  `candidate_payload_sha256`, `brief_snapshot_sha256`, `direction_id`, and
  `constraint_id`.

The event row and evidence file are hash-bound in the receipt. A later edit or
target change invalidates the authority.

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

The manifest binds the exact bytes of every brief member, while the snapshot
self-hash is recomputed and compared with current evidence/facts/requirements/
gaps at import and review time. A corrupt, hand-edited, or stale member fails
closed instead of falling back to a generic direction count.

The contract extracts machine-readable hard constraints when the source is
explicit: maximum runtime, maximum cast, location allowlist, required or
prohibited physical product exposure, and prohibited claims. A durable import
enforces only a requirement whose workflow receipt binds the exact row to a
registered source/evidence and a typed user/client confirmation event with exact
owner, trust, semantics, evidence hash, and target binding. A display name is
never authority.
Editing status/owner text alone never grants authority. Parser-created
`candidate` rows remain `REVIEW_REQUIRED`; parser confidence never upgrades them
silently. The generation request requires supported constraints to appear in
checkable direction fields. Any explicit hard clause without a deterministic
checker remains `REVIEW_REQUIRED` until a typed user/client resolution bound to
the exact candidate payload, direction, constraint, and snapshot approves or
rejects it.

## Imported candidate contract

The imported JSON binds the exact `brief_snapshot_sha256` and contains the
explicitly requested number of directions, or the smallest sufficient set when
no count was requested (one to six). Add an independent Critic before import
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
mechanisms, failed hard constraints, and unresolved hard-constraint review items
before writing any candidate/current/receipt/rendered artifact. Weak or generic
brand ownership is flagged as a brand-replacement risk. A valid import then
creates a versioned candidate, current candidate, import receipt, readable
directions, and option matrix; all remain `internal_only`. The receipt's
`candidate_sha256` hashes the exact persisted version bytes; the separately named
`candidate_payload_sha256` is only the normalized semantic payload hash. Files
are atomically replaced; the receipt is written before `current_candidate.json`,
which is the final pointer switch. Review rejects any exact-byte mismatch across
the current candidate, version, receipt, brief manifest, directions, or matrix.

`creative-review` reports evidence refs as `PROVENANCE_ONLY` and separates that
from brief adherence. For the
supported hard constraints above, it semantically checks the candidate text and
fails closed when a required value is missing, outside an allowlist, or cannot
be confirmed. It also lints mechanism difference, ownership, visual clarity,
shootability, and production risk. On the Content Surface it returns the lint
result without a persistent receipt; Delivery writes a bound receipt. It does
not replace the independent creative Critic, client judgment, or effectiveness
evidence. `creative-quality-gate` remains a downstream legacy proposal safety
Gate and must not be presented as Sol or Critic judgment.
