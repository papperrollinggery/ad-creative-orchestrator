# Demo Script

Status: public demo ready

## Goal

Show a new user the core loop without real client material:

```text
init project -> register material -> render dashboard -> goal plan -> verify
```

## Commands

From the repository root:

```bash
python3 -m pip install -e .
adco sample /tmp/adco-sample
adco status /tmp/adco-sample
adco-check
```

Manual equivalent:

```bash
adco-init /tmp/adco-demo
adco run /tmp/adco-demo --material examples/simulated_qingling_outdoor_launch/00_项目资料_ProjectMaterials/01_客户资料_ClientMaterials/brief_v1.md
adco goal-plan /tmp/adco-demo --title "Dual-lane demo" --objective "Run brand research and image workflow through gated goal mode."
adco status /tmp/adco-demo
adco-check
```

Expected verification:

```text
VALIDATION=PASS
DASHBOARD=.../AD-creative/handoff/操作台.html
SAMPLE=PASS
RUN_CHECKS=PASS
```

## Screenshots

Desktop:

```text
docs/assets/dashboard-desktop.png
```

Mobile:

```text
docs/assets/dashboard-mobile.png
```

## Demo Boundaries

- Uses bundled examples only.
- Does not upload client material.
- Does not send client-facing deliverables.
- Does not install the global skill.
- Does not claim remote GitHub Actions until a remote repository exists.
