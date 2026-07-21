---
name: ad-creative-orchestrator
description: "Use only when the user explicitly invokes $ad-creative-orchestrator for an initialized or about-to-be-initialized advertising project. Put material understanding and advertising reasoning first; add version, asset, PPT, approval, and delivery governance only when the requested risk boundary needs it. Do not use for ADCO or DIRcreative source repository maintenance, testing, ordinary advertising questions, ordinary code tasks, or work without ADCO project context."
---

# Ad Creative Orchestrator

## Outcome

Help the user make better advertising work from real project material. Lead with
the useful content answer; use files and governance only to preserve evidence or
protect a real delivery boundary.

This Skill is opt-in: activate only after explicit `$ad-creative-orchestrator`
invocation, never during ADCO source repository or DIRcreative source repository
maintenance or testing.

## Default: Content Surface

Use the Content Surface for intake, research, internal strategy, creative
briefs, concepts, scripts, storyboards, visual analysis, and ordinary revision.

1. Inspect the requested material before designing workflow. For images, video,
   decks, or documents, inspect the actual content; metadata is not understanding.
2. Identify the objective, audience, proposition, evidence, constraints, and
   contradictions that matter to the requested artifact.
3. Separate confirmed facts, supported inference, and unknowns. Ask only about a
   genuine blocker; continue all work that the blocker does not prevent.
4. Do the advertising reasoning or artifact work. The CLI may preserve evidence,
   but its records are never a substitute for judgment.
5. Return a decision-readable answer: conclusion/artifact first, evidence and
   real blockers second, next content action last.

Before returning a creative artifact, silently map every explicit hard constraint
to the draft and repair violations: locations/sub-locations, cast, duration,
claims, product exposure, and any ban on invented facts or data. Treat the last
one literally: do not invent numeric schedules, timestamps, prices, places,
metrics, testimonials, or product facts as story devices. Only supplied facts and
clearly labeled production timecodes/runtime/cast may use numbers. Avoid close
synonyms of prohibited outcomes (for example, sober/clear-headed/low-burden for a
sobering or health ban), not only the exact banned words. Treat each allowed
location as physically exact: a living room does not authorize kitchen/fridge
retrieval; a store entrance does not authorize interior fridges, shelves, or
checkout. Scene labels cannot cure a mismatch. Make alternatives differ in causal
mechanism, and revise any idea an adjacent substitute can replace unchanged. For
named channels, change the hook, pacing, participation, or proof behavior, not
merely crop or caption. State replacement risk when evidence cannot support
exclusive ownership. Make no lowest/easiest/safest production claim without a
visible comparison against every alternative. Do not expose a checklist or create
records unless needed.

For a new project, use:

```text
adco run <project> --material <path> --goal "<requested outcome>"
```

The default run creates a small workspace, evidence/fact records, and an intake
summary labeled as intake, not creative output. It runs no Dashboard, Council,
Thread, Git workflow, PPT, Client Pack, FinalDelivery lock, or full validation. Do not add those
manually merely to make the process look complete.

Keep durable state proportional to the task. Chat is the primary human decision
surface; project records preserve evidence but never outrank the creative outcome.

## Escalate only at a Delivery Boundary

Use the Delivery Surface only when the current action involves at least one of:

- a client-visible immutable version or derivative;
- asset authorization for client-visible use;
- PPT export, Client Pack, FinalDelivery, or send-readiness evidence;
- external upload/send/publish;
- legacy control-plane migration;
- explicit isolated/parallel execution with a controlled write scope;
- independent review bound to an exact client-visible version or delivery decision.

An internal second opinion remains on the Content Surface. It does not by itself
justify Delivery files, a Thread, a Gate, or a version ledger.

Delivery-risk CLI commands materialize the full surface on demand. Once
escalated, preserve existing client-visible files and exact-current evidence.
`VALIDATION=PASS` proves structure and traceability only; it never proves
creative quality, client approval, or permission to send.

Never send, publish, upload, purchase, delete, overwrite the only client-visible
copy, or install globally without the required explicit authority.

## Read One Relevant Reference

Do not preload the reference set. Read only the file needed for the current
boundary:

- Material parsing, facts, and real gaps: [intake_and_facts.md](intake_and_facts.md)
- Explicit CLI invocation, command syntax, status, or phase diagnosis only:
  [operator_cli_and_gates.md](operator_cli_and_gates.md)
- Creative brief/candidate/Critic contract: [creative_contract.md](creative_contract.md)
- Specialist handoff and adoption: [specialist_exchange_and_craft.md](specialist_exchange_and_craft.md)
- Client outline, PPT, exact-current derivatives, Client Pack, external upload,
  or send evidence: [ppt_and_client_pack.md](ppt_and_client_pack.md)
- FinalDelivery integrity: [final_delivery.md](final_delivery.md)
- Legacy migration and lifecycle: [migration_and_lifecycle.md](migration_and_lifecycle.md)
- Real Codex Threads: [thread_operations.md](thread_operations.md)
- Optional chat visualization: [chat_interaction_and_visualization.md](chat_interaction_and_visualization.md)

Provider names or words such as video, script, storyboard, commercial, or
prompt never trigger delegation by themselves. Use a Specialist only when its
expertise is needed and the handoff scope is explicit. ADCO retains project
truth and adoption responsibility.

## Finish the Requested Work

On the Content Surface, completion means the requested internal answer or
artifact is usable, evidence-aware, and honest about material unknowns. It does
not require a Gate ledger.

On the Delivery Surface, read the relevant delivery reference and verify the
exact target, version/hash bindings, authorization, unresolved feedback, and
fresh validation required by that boundary. A passed Gate is evidence for one
decision, not a reason to stop thinking about the work itself.
