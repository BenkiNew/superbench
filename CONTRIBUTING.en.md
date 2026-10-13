# Contributing benchmark cases

[Українська](CONTRIBUTING.md) · **English**

1. Create `benchmarks/SB-NNN/incident.json`, `prompt.md`, `fixture/` and `oracle.json`.
2. Fixtures must be anonymized, self-contained and free of credentials or production data.
3. Prompts must require verifiable file:line evidence.
4. Oracles must break answers into atomic criteria and identify core criteria.
5. Run `python3 -m superbench validate` and `./scripts/ci.sh`.

Once published, an oracle remains useful as a regression test, but the case is
no longer a contamination-free evaluation of a foundation model.

Each candidate answer requires three fresh, distinct reviewer sessions:
correctness, evidence and adversarial. Reviewers must not see the candidate
model name, cost, prior score or other reviewers' conclusions. The CLI rejects
reuse of the same `agent_name` for multiple roles on the same answer.

For prompt, fixture or oracle changes, increase the case version and update
the changelog. Do not edit published ledger events or historical snapshots.
See [versioning](docs/VERSIONING.en.md) and
[control experiments](docs/CONTROL_EXPERIMENTS.en.md).

For catalog presentation, provide English text in superbench/localization.py
when the source title or summary is Ukrainian. Translate presentation only;
do not replace benchmark inputs to localize the website.
