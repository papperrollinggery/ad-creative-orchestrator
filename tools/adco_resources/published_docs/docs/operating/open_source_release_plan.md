# Open Source Release Plan

Status: public release baseline at `v0.3.2`; subsequent changes require a new versioned Release.

## Current Public Baseline

```text
release: v0.3.2
commit: use the immutable tag target recorded by the GitHub Release
GitHub Release: https://github.com/papperrollinggery/ad-creative-orchestrator/releases/tag/v0.3.2
GitHub Actions: check PASS on Python 3.10 and 3.12
```

ADCO is a local-first, Codex-first control plane for advertising creative projects. It owns project truth, requirements and gaps, versioned artifacts, Human Workspace indexes, Gate evidence, specialist adoption, PPT/client-package binding, FinalDelivery protection, and client-send readiness. It does not directly generate video or images, approve creative quality, or send files to clients.

## Release Contract

| Area | Required state |
|---|---|
| Source truth | README, CHANGELOG, operating docs, CLI help, Skill references, templates, and package metadata describe the same current behavior. |
| Installed docs | `adco docs` exposes packaged README, changelog, install guide, adoption patterns, release plan, and first-run transcript; no empty installed-docs fallback. |
| Skill parity | Source Skill, packaged Skill, global installed Skill, and public wheel Skill match by managed-file SHA-256. |
| Current workflow | P0-P8 remains split across truth, outline, hash confirmation, specialist work, immutable PPT, exact-current checks, fresh Client Pack, independent review/send readiness, and feedback. |
| Lifecycle safety | Human Workspace v2 is current-first; schema-v2 migration, legacy quarantine, tombstones, and FinalDelivery reconciliation remain fail-closed. |
| Thread safety | Thread dispatch proof is immutable per work/lane/attempt, worker writes are scope-bound, and host reconciliation remains authoritative. |
| Specialist boundary | DIRcreative and other providers return bounded recommendations/receipts; ADCO alone owns adoption, version, PPT, FinalDelivery, and send readiness. |
| Validation | `make release-check`, distribution inspection, editable-install smoke, package-install smoke, and GitHub Actions pass. |
| User-facing limits | `VALIDATION=PASS` is structural/traceability evidence only; no client or creative approval is implied. |

## Release Sequence

1. Update code, templates, Skill references, README, changelog, install guide, and release-facing descriptions together.
2. Synchronize packaged templates, packaged Skill tree, and published-doc resources.
3. Run `python3 tools/check_packaged_assets.py`, `python3 tools/check_docs_commands.py`, and `make release-check`.
4. Build the wheel and verify package metadata plus installed `adco docs` paths.
5. Run an independent cold review against the exact release candidate.
6. Obtain explicit approval before commit/push, GitHub Release creation, global Skill installation, or CLI reinstall.
7. After publishing, reinstall from the public wheel URL and verify source/package/global/public-wheel hashes.

## Next Product Work

1. Run external-user trials on real but non-confidential projects.
2. Turn onboarding and dashboard friction into focused changes.
3. Keep release documentation and packaged descriptions inside the parity gate so they cannot silently lag the runtime again.

## Stop Conditions

- Do not upload real client materials.
- Do not make AI images client-visible without exact authorization evidence.
- Do not claim a release before the GitHub Release, assets, and Actions read back successfully.
- Do not publish, reinstall globally, or mutate external systems without explicit approval.
