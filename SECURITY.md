# Security Policy

## Supported Scope

This project is a local-first advertising creative workflow. It should not require uploading client files to external systems.

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
- Gate `PASS` is downgraded to `PARTIAL_PASS` when adversarial council evidence is missing.

## Disclosure

Open an issue or contact the maintainers privately when the issue involves client confidentiality or credential exposure.
