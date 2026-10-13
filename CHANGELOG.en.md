# Changelog

[Українська](CHANGELOG.md) · **English**

## 0.3.1 — 2026-10-13

- Added a full English static website and a UA / EN language switch.
- Added English repository documentation and translated catalog presentation.
- Both website languages use the same local assets; benchmark inputs and criteria remain unchanged.

## 0.3.0 — 2026-10-13

- Added oracle-free control pairs with evaluator-only keys and randomized labels.
- Added control-record/control-summary, separating transport completion from usable reviews and preserving unknown outcomes/costs.
- New runs pin case snapshots, hashes and versions; adjudication uses pinned oracles and rejects changed snapshots.
- Reassessment retains numbered revisions; leaderboard counting no longer duplicates the same response after each adjudication.
- Historical results remain unchanged; external control experiments do not replace official agent-panel evaluation.

## Earlier: 0.2.0

Deterministic correctness/evidence/adversarial reduction and an append-only
result ledger. Git preserves history before this changelog; release dates
have not been assigned retroactively.
