# GitHub Release Checklist

Status: public remote ready

## Current Remote State

```text
repo: https://github.com/papperrollinggery/ad-creative-orchestrator
git remote -v: origin https://github.com/papperrollinggery/ad-creative-orchestrator.git
adco release-status: RELEASE_STATUS=READY_FOR_REMOTE_CHECKS
GitHub Actions / check: PASS on Python 3.10 and 3.12
public clone trial: git clone + pip install . + adco quickstart/open-dashboard/validate PASS
```

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
adco quickstart /tmp/adco-release-quickstart --no-open
adco quickstart /tmp/adco-release-quickstart-json --no-open --json
adco demo /tmp/adco-release-demo --no-open
adco sample /tmp/adco-release-sample
adco support-bundle /tmp/adco-release-sample
adco support-bundle /tmp/adco-release-sample --json
adco open-dashboard /tmp/adco-release-sample --no-open
adco audit-dashboard /tmp/adco-release-sample --render --json
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
RELEASE_STATUS=READY_FOR_REMOTE_CHECKS
DOCS_MODE=source
DEMO=PASS
QUICKSTART=PASS
quickstart_json=PASS
NEXT_STATUS=WAITING_FOR_CONFIRMATION
SUPPORT_BUNDLE=PASS
support_bundle_json=PASS
DASHBOARD_OPEN=SKIPPED
dashboard_audit_json=PASS
VALIDATION=PASS
SAMPLE=PASS
DASHBOARD_AUDIT=PASS
```

## Remote Verification Gate

Remote is configured:

```bash
git remote -v
git push
```

Remote pass threshold:

```text
GitHub Actions / check: PASS on Python 3.10 and 3.12
GitHub Actions command: make release-check
Actions use actions/checkout@v6 and actions/setup-python@v6
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
release_status=READY_FOR_REMOTE_CHECKS
doctor=PASS
remote_status=PASS
next_action=run first external-user trial and turn friction into focused improvements
```
