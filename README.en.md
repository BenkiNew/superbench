# SUPERBENCH

[Українська](README.md) · **English**

[![validate](https://github.com/BenkiNew/superbench/actions/workflows/ci.yml/badge.svg)](https://github.com/BenkiNew/superbench/actions/workflows/ci.yml)

A reproducible benchmark for AI coding agents, built from real anonymized
incidents. Small fixtures capture actual failure mechanisms and require
verifiable evidence instead of plausible explanations alone.

**[English website and leaderboard](https://benkinew.github.io/superbench/en/)** ·
[Ukrainian website](https://benkinew.github.io/superbench/)

## Independent evaluation

Every provider, model, agent and tool is subject to the same
[independent testing and publication policy](TESTING_POLICY.en.md).
SUPERBENCH publishes its own methods, measurements and conclusions under its
own name. Free access or credits do not grant a provider editorial control.
Publication rights for joint non-public evaluations require explicit agreement.

## What is public

The public repository contains the benchmark harness, anonymized fixtures,
criteria, deterministic reducer and generated static website. GitHub Pages
publishes only `site/`; it has no access to private servers, databases,
documents, logs or credentials. The website has static UA and EN pages and
uses shared local assets, with no CDN or remote fonts.

A candidate runs in an isolated bundle in the user's Codex or Claude session.
Its answer is passed to the local CLI as a file. GitHub Actions does not run
third-party coding agents or require provider API keys.

## Current capabilities

- 14 formalized anonymized incidents;
- oracle-free candidate bundles;
- heuristic pre-scoring with anti-pattern checks;
- three independent reviewer roles: correctness, evidence and adversarial;
- a deterministic reducer with replayable criterion traces;
- append-only result events and a generated leaderboard;
- blinded control pairs and explicit partial/unavailable panel states;
- pinned case snapshots and immutable adjudication revisions;
- CI checks for syntax, case validity, tests, deterministic rendering and secrets.

## Quick start

Run the CLI from a source checkout with Python 3.11 or later:

```bash
python3 -m superbench validate
python3 -m superbench list
python3 -m superbench prepare SB-001 --output .superbench/workspace/current

# Give PROMPT.md and fixture/ to a separate candidate session.
# Save its final answer as answer.md, then evaluate it locally.
python3 -m superbench score SB-001 answer.md
python3 -m superbench record SB-001 answer.md \
  --model "Model Name" --provider provider --attempt 1
```

The heuristic score is not an independent verdict. Three separate reviewer
sessions are required for official adjudication:

1. Correctness labels every atomic criterion.
2. Evidence checks candidate file:line references against the fixture.
3. Adversarial challenges affect scoring only with reproduced counterexamples.

The reducer assigns met=1, partial=0.5 and other states=0. Invalid required
evidence removes the criterion's points. A contradicted core criterion or a
reproduced counterexample to a core criterion causes a hard fail. Confirmed
requires a score of at least 80 and all core criteria met; partial covers
50–79 or missing core criteria; rejected covers scores below 50 or a hard fail.

## Control experiments and history

A control pair contains a correct answer and an answer with a known injected
defect. Review quality is separate from request completion: `Completed`
without a substantive response is not a usable reviewer. Control results
never automatically enter the coding-agent leaderboard.

[Control workflow](docs/CONTROL_EXPERIMENTS.en.md) ·
[Versioning and history](docs/VERSIONING.en.md) ·
[Changelog](CHANGELOG.en.md)

New runs pin case inputs and criteria. Reassessment creates a new immutable
revision; the event ledger retains previous results. The leaderboard counts
the latest adjudication of a response once. Unknown costs remain unknown.

```bash
python3 -m superbench render --output site
./scripts/ci.sh
```

## Layout

```text
benchmarks/SB-NNN/   incident manifest, prompt, fixture and oracle
agents/              reviewer role contracts
superbench/          standard-library CLI, scoring, experiments and renderer
results/            event ledger and per-response reviews
site/               generated Ukrainian and English static pages
scripts/            validation and runner helpers
tests/              regression tests
```

See [contribution guidelines](CONTRIBUTING.en.md) and the
[security policy](SECURITY.en.md). Original prompts, fixtures and oracles are
not translated by the website: the tested inputs remain unchanged.

## Repair evidence — experimental

Version 0.4 adds proof-record: separate supported / refuted / unverified outcomes within explicit scope. Case, response, proposal, recipe and environment hashes bind each immutable assessment. Existing diagnosis scores and verdicts remain unchanged; model code is never executed and manual review remains required. [Format and CLI](docs/fix-proofs.md).
