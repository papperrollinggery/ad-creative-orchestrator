# Creative Contract Reference

Read this file only for creative briefing, candidate generation/import, and
Critic review.

## Ownership

```text
ADCO = evidence, contract, import, provenance, versions, and gates
GPT-5.6 Sol or an explicitly selected professional Specialist = creative reasoning
independent Critic = creative judgment and brand-replacement challenge
DIRcreative = film craft provider after a valid Specialist Exchange handoff
```

ADCO's deterministic strings are not a complete creative engine.

## Commands and flow

```text
adco creative-brief <project> [--work-id <id>] [--json]
-> Sol/professional Specialist generates 4-6 mechanism-distinct candidates
-> independent Critic rejects weak, duplicate, or replaceable ideas
-> retain 2-3 candidates
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

## Candidate contract

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
