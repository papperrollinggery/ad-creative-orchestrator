# Content-first forward-test receipt

Date: 2026-07-19

Candidate scope: repository source candidate only. The installed global Skill was
not changed. Headless tests copied the candidate into a disposable project under
the unique alias `adco-content-first-candidate`; the only mechanical change was
the Skill name/invocation token, so an explicit invocation could not resolve to
the older global installation.

## Candidate binding

| File | SHA-256 | Lines |
|---|---|---:|
| `SKILL.md` | `112d65fed6489c586810016bfc72bc4c5c52d88ac83ff5a439a491602173cb4d` | 110 |
| `creative_contract.md` | `269a3c014461ee7ad0bd3051ef90a3f6ccd5d581c3f1bd816a677b08a64b18a5` | 76 |
| `operator_cli_and_gates.md` | `129742ed25db8dd29fa533f1a0993fcf0a0dd017ba41f47a87cd91702f091f35` | 194 |
| `ppt_and_client_pack.md` | `8309d27f97051844459afbedfb93feaa5a03d3d41706acf9ee7f4d756bf514fc` | 32 |

## Durable answer evidence

The real headless final messages were preserved as normalized UTF-8 JSON, not
rewritten as expected-output prose. Normalization changed only whitespace and
key order; tests load the files as JSON and assert the content/delivery
contracts.

| Headless result | Raw output SHA-256 | Repository fixture | Fixture SHA-256 |
|---|---|---|---|
| Internal creative answer | `f1be012d64db6b0709d5ca6a33245acfd94554b0b8134387f4f05e2609f9ce9b` | `tools/fixtures/content_first_forward/answer.example.json` | `c9ade47121563c99045b151915af6b4d42c46a7a156711d45bfb5cef8598f726` |
| Client-send boundary answer | `e79d0f4e183a0fa70a9da0b0d16cb6b6a951a15ed4a2a4b26b4a68a73e065fbd` | `tools/fixtures/content_first_forward/delivery_answer.example.json` | `913c1b97a52e72ee2396461e8c9cafa07b78969af53e878cab7699d55f6a48e5` |

## Results

### Runtime and CLI

- Default `adco init`: 9 files, Content Surface, host root `AGENTS.md`
  preserved.
- First `adco run`: 11 project files, a machine-readable content answer, 0
  Dashboard/Council/full-validation runs, and no Gate, Thread, artifact, version,
  or six-folder index files.
- Explicit `goal-plan` promoted the same project to Delivery Surface without
  overwriting existing content. Re-running `init` did not downgrade it.
- Delivery `run`, `sample`, and legacy-project repair retained linked intake
  work, artifacts, Gate entries, and audit events.
- The macOS launcher produced a content answer and its explicitly requested
  Dashboard, while creating no artifact registry or client outline.

### Headless internal creative task

Fixture: `tools/fixtures/content_first_forward/brief.md`

- First tool action inspected the brief; the only Skill reference read was
  `creative_contract.md`.
- The schema-valid answer gave the strategy “早高峰里不必牺牲拿铁满足感的
  轻松减法” and three mechanism-distinct directions: “早高峰删减键”、
  “3g 的一站” and “一瓶到工位”.
- It treated the missing spokesperson and final price as non-blocking, returned
  no blocking unknown, and proposed a concrete storyboard next action.
- Dashboard, Council, Thread, Git, and delivery-ledger operations were all 0.
- It created no project control plane or delivery artifact.

Result: `HEADLESS_CONTENT_ANSWER=PASS`

### Headless client-send boundary

Fixture: `tools/fixtures/content_first_forward/delivery_request.md`

- First tool action inspected the request. After tightening reference routing,
  the rerun read only the 32-line `ppt_and_client_pack.md`, not the 194-line
  general CLI/Gate reference.
- The schema-valid answer selected `surface=delivery`, returned
  `decision=BLOCKED_BEFORE_SEND`, and kept `external_action_taken=false`.
- It named the missing outline confirmation, asset authorization, exact-current
  PPT/derivatives, independent review, separate send authority, and external
  credentials, while listing internal content work that could continue.
- It ran no ADCO/Git command, created no `AD-creative/` tree, and did not upload,
  send, publish, or fabricate evidence.

Result: `DELIVERY_FORWARD_RERUN=PASS`

## Cold-review closure

The accepted review path was single-level and read-only. An attempted external
reviewer was stopped and excluded when it recursively created five additional
review worktrees instead of returning findings; the clean temporary worktrees
and branches were removed before verification.

Three independent review passes produced actionable findings:

1. The first pass found lost Delivery creative-brief bindings, non-blocking gaps
   presented as blockers, current requirements hidden by older rows, and missing
   Delivery repair. All four received regressions and were fixed.
2. The second pass found unsafe legacy surface inference, lost Delivery `run`
   bookkeeping, and low-impact confirmations blocking Content status. All three
   received regressions and were fixed.
3. The final one-level pass found three P1s: early Delivery writes on dry-run or
   invalid preflight, `adco-init --full` not upgrading an existing Content
   declaration, and a Content declaration bypassing Delivery validation when
   Delivery-only ledgers existed. CLI-entry regressions now cover each case.

The same reviewer re-read the fixes and marked all three final P1s `CLOSED` with
`No blocking findings`. No reviewer was allowed to edit the worktree.

## Interpretation and limits

The two forward tests cover the intended contrast: ordinary internal creative
work gets a substantive answer without control-plane theatre, while an actual
client-send request activates only the safeguards needed for that boundary.

The local Codex installation emitted a pre-existing warning that its total
installed Skill descriptions exceed the global context budget. Explicit alias
invocation still loaded and followed this candidate. That machine-wide inventory
warning is outside this repository and is not evidence that this Skill was
globally installed.

These are synthetic, privacy-safe fixtures. They prove candidate behavior,
schema compliance, routing, and side-effect boundaries; they do not prove the
quality of every future campaign, third-party provider output, or a future global
installation. Global installation remains a separate user-authorized action.
