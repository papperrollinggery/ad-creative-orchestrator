# Creative Contract Reference

Read this file only for creative direction work or a durable candidate exchange.

## Use direct reasoning by default

For an internal brief, concept, script, storyboard, or ordinary revision, reason
directly from the inspected material and return the useful creative work. Do not
create a candidate contract, version, Gate, or Specialist handoff merely because
the task is creative. Match the number of directions to the request; do not force
4-6 options when three strong, mechanism-distinct directions are enough.

Use an independent Critic when the selection is consequential, the user asks for
a second judgment, or a client-visible boundary needs it. It is not a mandatory
step for every brainstorm.

ADCO's deterministic strings are evidence and structural checks, not a complete
creative engine. The active model or an explicitly chosen creative Specialist
owns creative reasoning; ADCO owns any durable evidence, provenance, and version
contract that the task actually needs.

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

`adco creative-proposal` is a deprecated compatibility alias for
`creative-brief`. It emits a deprecation notice and does not generate directions.

`creative-brief` writes only:

```text
AD-creative/creative/brief_snapshot.json
AD-creative/creative/creative_brief_contract.json
AD-creative/creative/creative_candidate.schema.json
AD-creative/creative/creative_generation_request.json
AD-creative/creative/creative_open_evidence_gaps.json
```

It binds current facts, requirements, evidence chunk ids, and open evidence gaps.
It does not write `creative_directions.md`, an option matrix, slogans, a client
outline, or a PPT.

## Imported candidate contract

The imported JSON binds the exact `brief_snapshot_sha256` and contains 2-3
post-Critic directions. Every direction has non-empty:

```text
direction_id, name, human_tension, brand_truth, audience_truth,
single_minded_proposition, creative_mechanism, key_visual, story_or_behavior,
product_role, channel_execution, why_brand_can_own_it, production_risk,
evidence_refs
```

Every evidence ref must name an existing evidence chunk. `creative-import`
rejects unbound refs, stale snapshots, missing/extra fields, duplicate ids/names,
and duplicate normalized mechanisms. Weak or generic brand ownership is flagged
as a brand-replacement risk. A valid import creates a versioned candidate,
current candidate, import receipt, readable directions, and option matrix; all
remain `internal_only`.

`creative-review` is deterministic structural/language lint for brief adherence,
mechanism difference, ownership, visual clarity, shootability, and production
risk. It does not replace the independent creative Critic, client judgment, or
effectiveness evidence. `creative-quality-gate` remains a downstream legacy
proposal safety Gate and must not be presented as Sol or Critic judgment.
