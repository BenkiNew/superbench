# SUPERBENCH

[![validate](https://github.com/BenkiNew/superbench/actions/workflows/ci.yml/badge.svg)](https://github.com/BenkiNew/superbench/actions/workflows/ci.yml)
[![leaderboard](https://img.shields.io/badge/leaderboard-live-brightgreen)](https://benkinew.github.io/superbench/)

Відтворюваний benchmark AI coding agents на реальних анонімізованих
інцидентах. Замість абстрактних задач — мінімальні fixtures із багів, які
справді траплялися в робочих проєктах.

**[→ Публічний лідерборд](https://benkinew.github.io/superbench/)**

## Спробуй за 2 хвилини (без локального сетапу)

1. Форкніть репозиторій.
2. Settings → Secrets and variables → Actions → додайте секрет
   `GROQ_API_KEY` (або `CEREBRAS_API_KEY`/`GEMINI_API_KEY`/`GEMMA_API_KEY`/
   `GLM_API_KEY`/`MISTRAL_API_KEY` — залежно від провайдера).
3. Actions → **try-it-yourself** → Run workflow, оберіть інцидент і
   провайдера.
4. За ~1-2 хв у Summary запуску — heuristic-скор вашої моделі на реальному
   багу, без жодного локального встановлення.

Сподобалось — відкрийте PR з вашим `results/`-записом, щоб потрапити у
спільний лідерборд.

## Що вже є

- 7 формалізованих інцидентів: asyncio silent skip, AI transcript у Python,
  inactive Git hook, stale security finding, SQL data-flow, OSV provenance,
  silent-success sandboxed scanner;
- oracle-free bundle для candidate agent;
- евристичний pre-score з anti-patterns;
- три нові незалежні reviewer-агенти на кожну відповідь;
- deterministic reducer із replayable criterion trace;
- до 3 retry для provider/timeout помилок;
- append-only `results/results.jsonl` і статичний leaderboard;
- CI: syntax, schema, unit tests, deterministic render і gitleaks.

## Швидкий старт

```bash
python3 -m superbench validate
python3 -m superbench list

python3 -m superbench prepare SB-001 \
  --output .superbench/workspace/current --force

python3 -m superbench score SB-001 answer.md

python3 -m superbench record SB-001 answer.md \
  --model "Model Name" --provider provider --attempt 1
```

Bounded runner для Continue CLI:

```bash
python3 scripts/run_agent.py SB-001 \
  --model "Groq GPT-OSS 120B" --provider groq \
  --config configs/groq.yaml --attempts 3
```

## Чому три агенти — не majority vote

1. `correctness` розмічає кожен atomic criterion;
2. `evidence` звіряє candidate file:line із pinned fixture;
3. `adversarial` може заперечити твердження лише відтвореним тестом.

Reducer рахує `met=1`, `partial=0.5`, решту `0`; invalid evidence обнуляє
відповідний criterion. Contradicted core criterion або відтворений
контрприклад для core дає hard fail. Пороги: confirmed `>=80` і всі core met,
partial `50–79`, rejected `<50` або hard fail.

## Міні-база

`results/results.jsonl` — append-only event ledger. Кожна спроба містить
incident, model/provider, attempt `1..3`, latency, verdict і UTC date.
Adjudication дописується окремою подією, тому історія не переписується.

```bash
python3 -m superbench render --output site
```

## Структура

```text
benchmarks/SB-NNN/   manifest + prompt + fixture + oracle
agents/              fixed reviewer role contracts
superbench/          stdlib-only CLI, scoring, reducer, renderer
results/             JSONL ledger + per-response reviews
site/                generated static portal
scripts/             bounded runner and CI
configs/             local ignored configs + safe examples
tests/               regression tests
```

Додавання cases описано в [CONTRIBUTING.md](CONTRIBUTING.md), правила
секретів — у [SECURITY.md](SECURITY.md).
