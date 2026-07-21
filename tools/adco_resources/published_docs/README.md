# Ad Creative Orchestrator

[![check](https://github.com/papperrollinggery/ad-creative-orchestrator/actions/workflows/check.yml/badge.svg)](https://github.com/papperrollinggery/ad-creative-orchestrator/actions/workflows/check.yml)
[![release](https://img.shields.io/github/v/release/papperrollinggery/ad-creative-orchestrator?display_name=tag)](https://github.com/papperrollinggery/ad-creative-orchestrator/releases/latest)
[![python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://github.com/papperrollinggery/ad-creative-orchestrator/blob/main/pyproject.toml)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Turn real project material into usable advertising thinking, then add traceability only when the work reaches a delivery boundary.

Ad Creative Orchestrator (ADCO) is a content-first Codex Skill and local CLI for advertising projects. Its default workspace is deliberately small: understand the material, preserve evidence, expose real gaps, and produce the requested internal answer. Version, asset, PPT, approval, and delivery controls appear only when the requested action needs them.

中文简介：ADCO 默认先读懂真实资料并完成广告内容工作；只有进入客户可见版本、PPT、资产授权或发送准备时，才按需展开完整交付治理。

> **Alpha:** use version control or backups and keep a human reviewer in the loop for real client work.

<p>
  <img src="docs/assets/dashboard-desktop.png" alt="ADCO project dashboard on desktop" width="760">
</p>
<p>
  <img src="docs/assets/dashboard-mobile.png" alt="ADCO project dashboard on mobile" width="260">
</p>

## Why ADCO

Creative projects rarely fail because a team cannot make another slide. They fail because the latest brief, approved copy, image rights, deck version, and client feedback drift apart.

ADCO gives each project two proportional operating surfaces:

- **Content Surface:** material evidence, facts, requirements, real gaps, and the useful answer stay readable without a release workflow.
- **Delivery Surface:** client-visible versions, assets, PPTX, packages, approvals, and send evidence become traceable only when needed.
- **Versioned deliverables:** PPTX files and client packages are immutable and bound to exact-current inputs.
- **Review gates:** copy, references, assets, layout, editability, and send readiness are checked separately.
- **Human handoffs:** a browser dashboard and bilingual folders show non-developers what is current and what happens next.
- **Safe automation:** external uploads, paid actions, destructive overwrites, global installs, and client sends require explicit approval.

## Quickstart

ADCO requires Python 3.10 or newer. Install the current release with [`pipx`](https://pipx.pypa.io/):

```bash
pipx install --force https://github.com/papperrollinggery/ad-creative-orchestrator/releases/download/v0.3.2/ad_creative_orchestrator-0.3.2-py3-none-any.whl
adco --version
adco doctor
```

Create and inspect a safe demo:

```bash
adco quickstart /tmp/adco-demo --no-open
adco open-dashboard /tmp/adco-demo
adco status /tmp/adco-demo
adco next /tmp/adco-demo
```

Expected first-run checks:

```text
QUICKSTART=PASS
VALIDATION=PASS
```

The dashboard is generated at:

```text
/tmp/adco-demo/AD-creative/handoff/操作台.html
```

For source installation, upgrades, Skill installation, and uninstall instructions, see the [installation guide](docs/operating/install.md).

## Start a Real Project

```bash
adco init <project_dir>
adco run <project_dir> --material <brief_or_material_folder>
# Optional when a local status view is useful:
adco open-dashboard <project_dir>
```

`adco run` parses source material into evidence chunks, updates the fact inventory, requirements, true gaps/conflicts, writes a concise content answer, and runs only affected-scope validators. By default it renders no dashboard and runs no Council, Thread, Git workflow, Specialist Exchange, PPT, Client Pack, or full delivery validation. Add `--dashboard` only when that view is useful.

Supported intake includes Markdown/text, CSV, JSON, YAML, DOCX, PPTX, PDF, SRT/VTT, images, and video. Long text is processed under an explicit aggregate character budget instead of silently truncating each file; media that was only registered by metadata is never presented as understood.

Every new Content Surface starts with only the core project files:

```text
project/
└── AD-creative/
    ├── AGENTS.md         # scoped, opt-in project rules
    ├── handoff/          # content summary and genuine questions
    └── orchestrator/     # source events, truth, requirements, gaps
```

Delivery-risk commands expand this workspace on demand with the six human folders and the version, artifact, Gate, asset, feedback, Thread, and FinalDelivery records required by that action. `adco init --full` explicitly starts with the Delivery Surface.

ADCO writes its policy to `AD-creative/AGENTS.md`; an existing project-root `AGENTS.md` is never overwritten and no manual merge is required. The scoped policy applies only after explicit `$ad-creative-orchestrator` invocation inside that initialized project.

## How the Delivery Surface Stays Safe

```text
Briefs and feedback
        ↓
Requirements and gaps
        ↓
Client-readable outline ── human hash-bound confirmation
        ↓
References, creative work, and specialist handoffs
        ↓
Immutable PPTX version ── language, asset, layout, and editability checks
        ↓
Exact-current client package ── independent review + send authorization
        ↓
Send-readiness result (ADCO never sends)
```

The project lifecycle keeps truth, outline approval, creative work, presentation export, package binding, independent review, and feedback as separate states. Passing one state never silently approves the next.

Important boundaries:

- `VALIDATION=PASS` proves structural integrity and traceability—not creative quality, client approval, asset rights, or permission to send.
- `client-pack-gate` means a package is ready for independent review—not ready to send.
- `client-send-readiness-gate` checks that independent review and explicit authorization match the same current package. It never sends files.
- AI-generated images remain internal until visual QA and hash-bound authorization are recorded.
- Files manually placed in `05_最终交付_FinalDelivery/` are protected from automatic move, overwrite, and deletion.
- Invalid private source state blocks support/client-package export; ZIP-based candidates are privacy-scanned with bounded streaming.

Read the [authorization policy](docs/operating/authorization_policy.md) for the complete stop conditions.

## Core Commands

| Command | Purpose |
|---|---|
| `adco quickstart [project_dir]` | Create, validate, and open a safe first-run demo. |
| `adco run <project_dir> --material <path>` | Register real materials and produce the first project state. |
| `adco creative-brief <project_dir>` | Freeze current evidence into a creative contract; generates no directions. |
| `adco creative-import <project_dir> --file <candidate.json>` | Import 2-3 selected, evidence-bound, mechanism-distinct candidates. |
| `adco creative-review <project_dir>` | Run deterministic candidate lint; add independent creative review when the decision boundary requires it. |
| `adco profile-analyze <project_dir>` | Analyze meeting/client profiles on the Content Surface; Dashboard is opt-in. |
| `adco status <project_dir>` | Show blockers, pending confirmations, and current validation. |
| `adco next <project_dir>` | Print the next safe action. |
| `adco open-dashboard <project_dir>` | Open the non-developer project dashboard. |
| `adco validate <project_dir>` | Validate structure and traceability. |
| `adco support-bundle <project_dir>` | Create a local diagnostic bundle; review it before sharing. |
| `adco docs` | Locate the packaged README, changelog, and operating guides. |
| `adco check` | Run the repository's deterministic checks. |

Run `adco --help` or `adco <command> --help` for the complete CLI reference. The [operating manual](docs/operating/operating_manual.md) explains the full workflow and gate commands.

## What ADCO Owns—and What It Does Not

ADCO owns project truth, evidence and creative contracts, candidate provenance, artifact versions, review evidence, specialist adoption, presentation/client-package binding, FinalDelivery protection, and send-readiness checks. GPT-5.6 Sol or an explicitly selected professional Specialist supplies creative reasoning. DIRcreative is a film-craft provider used only through a negotiated, bounded Specialist Exchange.

ADCO is **not** a SaaS, image generator, video generator, deterministic three-direction creative engine, autonomous creative approver, or delivery bot. `creative-brief` generates a contract, not ideas. The active model or a professional Specialist produces the number of directions the task needs. An explicit internal second judgment may use a read-only Critic on the Content Surface; it does not trigger Delivery or write a persistent governance receipt. A consequential selection or exact client-visible boundary may instead use a durable Critic bound to that candidate/version. `creative-import` accepts 2-3 selected directions and rejects stale or unbound evidence and duplicate mechanisms while flagging weak brand ownership. Image and film work can come from specialist tools through a versioned exchange contract; ADCO remains the owner of adoption, provenance, and client-facing readiness.

## Documentation

| Start here | Use it for |
|---|---|
| [Non-developer quickstart](docs/operating/non_developer_quickstart.md) | Starting a project without learning the full CLI. |
| [First real project runbook](docs/operating/first_real_project_runbook.md) | Running a live project from intake through handoff. |
| [Operating manual](docs/operating/operating_manual.md) | Commands, gates, and lifecycle details. |
| [Adoption patterns](docs/operating/adoption_patterns.md) | Adding ADCO to an existing workflow. |
| [Real-project acceptance criteria](docs/operating/real_project_acceptance_criteria.md) | Deciding whether a project is genuinely ready. |
| [Specialist exchange v1/v2](docs/operating/specialist_exchange_v1.md) | Negotiating and integrating external image, film, or craft specialists. |
| [Runtime refactor performance receipt](docs/operating/runtime_refactor_performance.md) | Reproducing the measured before/after intake and `run` behavior. |
| [Security policy](SECURITY.md) | Reporting vulnerabilities without exposing client data. |
| [Changelog](CHANGELOG.md) | User-visible changes by release. |
| [Roadmap](ROADMAP.md) | Planned product work. |

`docs/operating/` is the current operator contract. `docs/design/` records design rationale, while `docs/reviews/` contains historical evidence and may include old paths or commands.

## Development

```bash
git clone https://github.com/papperrollinggery/ad-creative-orchestrator.git
cd ad-creative-orchestrator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
make check
```

Release candidates must also pass:

```bash
make release-check
```

The public CI runs the release checks on Python 3.10 and 3.12. See the [release checklist](docs/operating/github_release_checklist.md) before publishing a new version.

## Current Release

The current public release is [`v0.3.2`](https://github.com/papperrollinggery/ad-creative-orchestrator/releases/tag/v0.3.2). Use the Release tag target to identify the source commit and the published wheel as the installation artifact.

Compared with earlier releases, `v0.3.2` makes current materials easier to find, protects final-delivery files from silent replacement, strengthens specialist and review evidence, and packages the operator guides available through `adco docs`. See the [changelog](CHANGELOG.md) for technical details.

## Contributing and Security

Bug reports and focused pull requests are welcome. Use the [issue templates](https://github.com/papperrollinggery/ad-creative-orchestrator/issues/new/choose) and describe the smallest reproducible project state without attaching confidential client materials.

Report vulnerabilities through [GitHub private vulnerability reporting](https://github.com/papperrollinggery/ad-creative-orchestrator/security/advisories/new). See [SECURITY.md](SECURITY.md) for scope and disclosure guidance.

## License

[MIT](LICENSE)
