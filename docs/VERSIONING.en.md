# Versioning and reproducible history

[Українська](VERSIONING.md) · **English**

The harness version is defined in `pyproject.toml` and `superbench.__version__`.
Each case has its own version in `incident.json`. Increase the case version
and update the changelog when its prompt, fixture or oracle changes.

Since 0.3.0, each new `record` stores a benchmark snapshot, file hashes,
case fingerprint, case/harness versions and a source commit, or null if Git
is unavailable. The snapshot and hashes define the exact evaluated inputs:
a commit alone may not describe uncommitted local changes. Adjudication uses
the pinned oracle instead of the current catalog and rejects changed snapshots.
The run ID includes the case fingerprint, so the same answer on a different
case revision creates a separate run.

`registration.json` preserves initial registration. `response.json` and
`adjudication.json` are current projections. Every adjudication also creates
an immutable numbered revision in `adjudications/`. The append-only ledger
keeps earlier outcomes; the leaderboard counts the latest adjudication for
each response once. Pending panels do not imply successful reliability.

Legacy results are not automatically migrated or assigned invented versions.
A reassessment without a snapshot is explicitly marked `legacy-unpinned` and
uses the current available case. Verify its original criteria before treating
that reassessment as historically comparable. Existing legacy adjudication
JSON is archived before its current projection is replaced.

Snapshots containing oracles are evaluator-only. Candidates receive only
`prepare` bundles. Control experiments remain separate from coding-agent
results. Private provider reports are not published automatically. Use one
writer per run or pair; concurrent writes to the same output are not supported.
