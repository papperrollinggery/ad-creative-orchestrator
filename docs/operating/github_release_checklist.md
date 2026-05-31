# GitHub Release Checklist

Status: local release gate ready

## Current Blocker

```text
git remote -v: empty
```

Remote push and GitHub Actions verification cannot run until a GitHub repository remote is configured.

## Local Release Gate

Run from repository root:

```bash
make release-check
git status --short
python3 tools/ad_creative_operator.py sample /tmp/adco-release-sample
python3 tools/ad_creative_operator.py audit-dashboard examples/moncler_protocol_dry_run --render
python3 tools/ad_creative_operator.py audit-dashboard examples/simulated_qingling_outdoor_launch --render
```

Pass threshold:

```text
git status --short only contains intended release changes
RUN_CHECKS=PASS
INSTALL_SMOKE=PASS
RELEASE_CHECK=PASS
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
GitHub Actions / check: PASS
README images render
Issue templates visible
PR template visible
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
release_status=LOCAL_READY
remote_status=BLOCKED_UNTIL_REMOTE_ADDED
next_action=add GitHub remote, push main, wait for GitHub Actions check
```
