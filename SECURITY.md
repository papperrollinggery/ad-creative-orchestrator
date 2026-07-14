# Security Policy

## Supported Scope

This project is a local-first advertising creative workflow. Core project state stays on disk; provider-facing generation and external uploads require explicit approval.

## Reportable Issues

Report issues that could cause:

- client materials to be uploaded externally without explicit approval
- private credentials, cookies, account data, or API keys to be stored in project artifacts
- AI-generated images to be marked client-visible without approval evidence
- unverified references to be presented as official evidence
- generated or fake logos, packaging text, or case studies to enter client-facing material

## Safe Defaults

- AI images default to `internal_only`.
- Search targets default to internal planning until real source evidence exists.
- Client sends, paid actions, login actions, external uploads, and global skill installation require explicit confirmation.
- Content/reference/search/visual/client-package Gates downgrade or block when exact-target independent evidence is missing; outline, authorization, FinalDelivery, and send-readiness checks remain fail-closed on their own evidence rules.
- FinalDelivery baselines are immutable and cannot be renamed, superseded, moved, or overwritten without structured hash-bound confirmation.
- Worker or specialist receipts cannot grant themselves client, version, PPT, FinalDelivery, send, or control-plane authority.

## Disclosure

For vulnerabilities or anything involving client confidentiality or credential exposure, use [GitHub private vulnerability reporting](https://github.com/papperrollinggery/ad-creative-orchestrator/security/advisories/new). Do not open a public issue.

Use a public issue only for non-sensitive bugs that do not expose client data, credentials, private paths, or exploit details.
