# Content-first runtime

ADCO should improve advertising work, not turn every internal draft into a
release process. The runtime therefore uses two surfaces.

## Surfaces

### Content surface (default)

Use for intake, evidence, facts, real gaps, internal creative briefs, concepts,
scripts, treatments, candidate review, and ordinary revisions. Keep the working
set small and complete the requested usable answer before discussing governance.
An authorized multi-stage content outcome continues through its requested stages;
an unknown pauses only the affected part.

Default operations must not create or run:

- Gate, Council, Thread, worker receipt, or Git workflows;
- version maps, artifact registries, Client Packs, or FinalDelivery locks;
- dashboards, PPT files, external sends, or global Skill installs.

### Delivery surface (risk-triggered)

Escalate only when the requested action involves a client-visible version, asset
authorization, immutable PPT/derivatives, FinalDelivery, external send, legacy
migration, explicit parallel work with a controlled write scope, or independent
review bound to an exact client-visible version. An internal read-only second
judgment remains on Content Surface. Existing delivery projects remain compatible.

## Runtime budgets

| Budget | Candidate threshold |
|---|---:|
| Main `SKILL.md` | at most 120 lines |
| Default initialized project | at most 20 files |
| Files written by first `adco run` | at most 12 working files |
| Dashboard/Council/Thread/Git operations during default run | 0 |
| Full validation during default run | 0 |
| Actions before first material/content inspection in a forward test | at most 5 |
| Control-plane actions before a client-visible boundary | at most 25% of classified actions |

The percentage is a behavioral evaluation metric, not a reason to skip a real
safety boundary. Client-visible and irreversible actions use the delivery
surface regardless of the percentage.

## Answer contract

Every intake/run result must return a concise intake summary containing:

1. the working objective;
2. evidence-backed facts or requirements;
3. only genuine blocking conflicts or unknowns;
4. what useful content work can proceed now;
5. one next content action.

This summary is evidence context, not creative reasoning or a finished creative
artifact. The active agent uses it to answer the user's actual content request;
it does not substitute a plan or management record for that answer. Metrics and
file paths are supporting evidence.

Unchanged materials with a successful parse at the same character budget reuse
their source identity and evidence. Byte hashing still runs; a parser cache hit
does not mean the source was never read. Changed files, folder membership, budgets,
and failed parses require processing again. Model-analysis imports must return the
exported `evidence_snapshot_sha256`; missing or stale bindings are rejected before
facts/gaps change. Existing creative briefs are rechecked after upstream changes,
so `CHECK` exposes stale work without creating Delivery artifacts.

## Design references

The design follows mature Skill guidance rather than adding another private
workflow language:

- OpenAI's [Build Skills](https://learn.chatgpt.com/docs/build-skills#create-a-skill)
  guidance favors focused instructions, explicit inputs/outputs, examples, and
  validation over a monolithic prompt.
- Anthropic's [Agent Skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
  recommends progressive disclosure: keep the main Skill concise and load
  detailed references or scripts only when the task needs them.
- The [Agent Skills concepts](https://openagentskills.dev/docs/concepts)
  separate concise metadata/instructions from on-demand resources. ADCO applies
  that split to Content versus Delivery work instead of preloading all controls.

## Evidence behind the change

Two Duffy production traces contained 411 and 480 execution calls. Heuristic
classification matched 155 and 179 calls respectively to control-plane or Gate
work. In the first trace, visual inspection did not start until call 35 and the
first image-generation action did not occur until call 90. The same trace later
showed that structural/document checks missed an incorrect A-end spatial
interpretation. This is the failure mode the content surface is designed to
prevent: inspect and reason about the actual material first, then add governance
only where the output risk requires it.

## Release-candidate checks

A global-install candidate must pass static Skill validation, focused runtime
budget tests, full repository/package checks, isolated installation smoke tests,
and fresh headless forward tests. Global installation remains a separate user
action and is never implied by candidate readiness.
