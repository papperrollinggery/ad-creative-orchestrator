# ADCO Repository Self-Maintenance Mode

These rules apply whenever the current Git root is the
`ad-creative-orchestrator` source repository.

- Changes to ADCO source, templates, schemas, tests, documentation, installers,
  or the ADCO skill draft are repository maintenance, not ADCO project work.
- Use the ordinary Python and Git development workflow for repository
  maintenance. Inspect the worktree first, make scoped edits, and verify with
  focused tests followed by the repository checks.
- Do not invoke an installed `ad-creative-orchestrator` skill while maintaining
  this repository, and do not run `adco run` against the repository root.
- Do not create a real `AD-creative/` control plane in this repository.
- Do not delegate repository maintenance to DIRcreative or another creative
  specialist.
- ADCO CLI, Council, Specialist Exchange, PPT, and Gate commands may run only
  inside disposable test fixtures or temporary sample projects for verification.
- ADCO Gates do not decide whether repository maintenance is complete. Completion
  is determined by source review, tests, package parity, installation smoke tests,
  and an explicit accounting of remaining work.
