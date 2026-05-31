## What Changed

## Why

## Verification

- [ ] `python3 tools/run_checks.py`
- [ ] `make release-check`
- [ ] `adco --version`
- [ ] `adco doctor`
- [ ] `adco demo <sample_project> --no-open`
- [ ] `adco support-bundle <sample_project>`
- [ ] `adco support-bundle <sample_project> --json`
- [ ] `adco open-dashboard <sample_project> --no-open`
- [ ] `adco audit-dashboard <sample_project> --render --json`
- [ ] `adco validate <sample_project>`
- [ ] `adco check`

## Safety

- [ ] No real client confidential material added.
- [ ] No AI image is marked client-visible without approval evidence.
- [ ] No unverified reference is presented as official evidence.
- [ ] Client-send, external upload, paid/login, and global skill install boundaries remain intact.
