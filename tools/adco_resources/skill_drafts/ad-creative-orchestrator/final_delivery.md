# FinalDelivery Reference

Read this file only for `05_最终交付_FinalDelivery` inventory, locking, or
reconciliation.

Files in FinalDelivery are protected user data. Inventory and hash-register them;
never overwrite, move, delete, copy, symlink, alias, or silently replace them.

Use:

```text
adco final-delivery-lock <project>
adco final-delivery-reconcile <project> --old-path <path> --new-path <path> \
  --kind <rename|supersession> --confirmed-by <human> \
  --confirmed-at <timezone-aware-iso> \
  --evidence-ref <project-relative-structured-confirmation.json> \
  [--version-id <id>]
```

An existing baseline path/hash/size is immutable. A missing or changed baseline
remains fail-closed. A same-hash rename and a different-hash supersession both
require structured, source-registered, host-readback confirmation; a worker note,
filename, alias, or self-declared identity is not authority.

Gate reports, checklists, previews, text extracts, manifests, and locks are
metadata, not automatic `user_final` deliverables. `dedupe-audit` and
`cleanup-plan` are review-only and never delete.
