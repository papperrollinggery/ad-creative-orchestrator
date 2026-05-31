# GitHub Release Checklist

Status: local release gate ready

## Current Blocker

```text
git remote -v: empty
adco release-status: RELEASE_STATUS=BLOCKED_REMOTE_MISSING
```

Remote push and GitHub Actions verification cannot run until a GitHub repository remote is configured.

## Local Release Gate

Run from repository root:

```bash
make release-check
make dist-check
adco --version
adco doctor
adco doctor --json
adco release-status
adco release-status --json
adco docs
adco docs --json
git status --short
adco init /tmp/adco-release-init
adco demo /tmp/adco-release-demo --no-open
adco sample /tmp/adco-release-sample
adco support-bundle /tmp/adco-release-sample
adco open-dashboard /tmp/adco-release-sample --no-open
adco status /tmp/adco-release-sample --json
adco next /tmp/adco-release-sample
adco next /tmp/adco-release-sample --json
adco validate /tmp/adco-release-sample
adco validate /tmp/adco-release-sample --json
adco audit-dashboard examples/moncler_protocol_dry_run --render
adco audit-dashboard examples/simulated_qingling_outdoor_launch --render
```

Pass threshold:

```text
git status --short only contains intended release changes
RUN_CHECKS=PASS
INSTALL_SMOKE=PASS
PACKAGE_SMOKE=PASS
RELEASE_CHECK=PASS
DIST_CHECK=PASS
adco 0.1.0
ADCO_DOCTOR=PASS
RELEASE_STATUS=BLOCKED_REMOTE_MISSING
DOCS_MODE=source
DEMO=PASS
NEXT_STATUS=WAITING_FOR_CONFIRMATION
SUPPORT_BUNDLE=PASS
DASHBOARD_OPEN=SKIPPED
VALIDATION=PASS
SAMPLE=PASS
DASHBOARD_AUDIT=PASS
```

## Remote Setup Gate

Required manual setup:

```bash
git remote add origin <github_repo_url>
git push -u origin main
```

After push:

```text
GitHub Actions / check: PASS on Python 3.10 and 3.12
GitHub Actions command: make release-check
README images render
Issue templates visible
PR template visible
Bug template requires version, doctor, and reproduction evidence
License detected as MIT
```

## Public Safety Gate

Before public release, verify:

- No confidential client materials are committed.
- No AI image is marked client-visible without approval evidence.
- No fake logo, fake packaging text, or unverified reference is presented as official evidence.
- Demo screenshots use bundled example state only.
- README does not claim remote CI until GitHub Actions has run on GitHub.

## Release Decision

```text
release_status=BLOCKED_REMOTE_MISSING
doctor=PASS
remote_status=CHECK
next_action=add GitHub remote, push main, wait for GitHub Actions check
```
