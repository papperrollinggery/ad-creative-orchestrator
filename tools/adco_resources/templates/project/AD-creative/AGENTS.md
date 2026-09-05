# ADCO project files

Apply these rules only inside this `AD-creative/` directory. ADCO activation is
decided once per task and occurs only when the user explicitly invokes
`$ad-creative-orchestrator` for this initialized project. Delivery-boundary
wording in a user-owned root `AGENTS.md` means post-activation escalation, not a
second implicit trigger. ADCO never creates or overwrites the root `AGENTS.md`.

- Put advertising reasoning and the requested artifact before process reporting.
- Default to the content surface: inspect materials, record evidence-backed
  facts and real gaps as needed, then produce the useful internal answer. Complete
  an authorized multi-stage artifact; an unknown pauses only the part it blocks.
- A one-off concept, script, treatment, storyboard, or revision is answered in
  chat. Initialize or update durable project records only when the user asks for
  project management, continuing work, or traceable state.
- For direct creative work, connect audience resistance to evidence-backed product
  causality and a visible mechanism. Preserve the adopted direction, voice, and
  latest explicit change during revision; do one focused repair, not score-chasing.
- Do not create Gate, Council, Thread, Git, version, PPT, Client Pack, or
  FinalDelivery work unless the requested risk boundary needs it.
- Escalate to delivery governance for client-visible versions, asset
  authorization, PPT/derivatives, FinalDelivery, external send, legacy
  migration, explicit parallel work with a controlled write scope, or independent
  review bound to an exact client-visible version. An internal read-only second
  judgment remains Content Surface work.
- Never present structural validation as creative quality or client approval.
- Treat FinalDelivery as protected user data. Only inventory/hash-lock it. Never
  overwrite, edit, move, copy, delete, symlink, or alias it. Reconcile an
  externally performed rename/supersession through the lock contract.
- Keep evidence/source status, claim wording confirmation, client/legal
  approval, and asset authorization independent. A fact, manifest approval, or
  Gate PASS never grants another axis. Client-visible asset use requires one
  non-revoked `approved` authorization bound to exact asset hash and scope.
- Review the exact client outline first; only the human/client confirmer may run
  `adco confirm-client-outline`. Then run `adco client-outline-gate`. Any outline
  content change makes the receipt stale; agents and automation never self-confirm.
- Before `adco export-pptx`, require project-wide validation PASS. On historical
  CHECK, report `TOOL_BLOCKED` and keep targeted WIP separate; never repair old
  FinalDelivery or legacy debt merely to make a new export run.
- Register source material at its existing path; do not copy a source/reference
  library into project folders, meeting packs, concepts, or version archives.
- After new materials are used, offer one read-only organization review when
  loose root files or exact duplicates exist. Never move or delete without an
  explicitly reviewed plan; FinalDelivery is always protected.
- Keep ordinary QA, preview, contact-sheet, and visualization output as one
  replace-current staging artifact. Preserve another copy only for a real
  immutable delivery milestone.
- `adco.specialist-exchange` is a protocol id, not a command. Use
  `adco specialist-handoff` and `adco specialist-adopt` for the CLI workflow.
- `adco thread-reconcile --receipt-path` must point to the dispatch-bound real
  worker receipt. The `thread_cleanup_<work_id>.md` file is a host projection
  created by `thread-plan` and refreshed only after reconciliation; it is never
  a worker receipt or authority. Record adoption/rejection before cleanup/archive.
- Never send, publish, upload, purchase, install globally, or delete without the
  required explicit authority.

Use project files as durable evidence, but keep the record proportional to the
current action. `current_truth.md` is a replace-current summary: authoritative
state lives in its owning CSV/JSON/receipt, user/date sections stay untouched,
and chat memory never substitutes for a durable governed-state update.
