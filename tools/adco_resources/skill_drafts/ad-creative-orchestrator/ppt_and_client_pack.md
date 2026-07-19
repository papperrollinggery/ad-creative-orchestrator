# PPT and Client Pack Reference

Read this file only for client-outline confirmation, PPT export, exact-current
derivatives, Client Pack binding, independent review, or send readiness.

## Required order

```text
client-readable exact outline
-> explicit human/client confirmation bound to its digest
-> client-outline-gate PASS
-> new immutable PPTX version
-> exact-current PDF/preview/text/editability evidence
-> language/layout/asset-authorization checks
-> fresh Client Pack input manifest and digest
-> independent manual review on that digest
-> separate send authorization on the same digest
-> client-send-readiness-gate (never sends)
```

Do not enter this route from default `adco run`. `creative-brief` and
`creative-import` also do not create PPT or Client Pack artifacts.

`export-pptx` refuses overwrite and registers exact version/hash/size. Derive
every PDF, preview, and text extract from the same current PPTX and record the
derivation. A changed outline, PPTX, derivative, asset, authorization, or package
input invalidates stale evidence.

`client-pack-gate` means ready for independent review only. A generated checklist
is `NOT_RUN` until completed independently and bound to the current version,
PPTX hash, and package digest. `client-send-readiness-gate` checks the independent
receipt and separate authorization; it never uploads, emails, publishes, or sends.
