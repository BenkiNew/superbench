# SUPERBENCH

[![validate](https://github.com/BenkiNew/superbench/actions/workflows/ci.yml/badge.svg)](https://github.com/BenkiNew/superbench/actions/workflows/ci.yml)
[![leaderboard](https://img.shields.io/badge/leaderboard-live-brightgreen)](https://benkinew.github.io/superbench/)

Відтворюваний benchmark AI coding agents на реальних анонімізованих
інцидентах. Замість абстрактних задач — мінімальні fixtures із багів, які
справді траплялися в робочих проєктах.

**[→ Публічний лідерборд](https://benkinew.github.io/superbench/)**

## Модель публікації

Публічний GitHub містить тільки код benchmark, анонімізовані fixtures,
критерії, алгоритм reducer і згенерований статичний leaderboard. GitHub Pages
публікує лише каталог `site/` і не має доступу до серверів, баз даних,
DATABANK, внутрішніх журналів або ключів.

Приватне серверне дзеркало доступне лише через Tailscale і не є
публічним тестовим середовищем. Candidate запускається користувачем у Codex
або Claude проти ізольованого bundle; відповідь передається локальному CLI
як звичайний файл. Репозиторій не запускає стороннього coding agent у GitHub
Actions і не приймає provider API keys.

## Що вже є

- 11 формалізованих анонімізованих інцидентів;
- oracle-free bundle для candidate agent;
- евристичний pre-score з anti-patterns;
- три нові незалежні reviewer-агенти на кожну відповідь;
- deterministic reducer із replayable criterion trace;
- append-only `results/results.jsonl` і статичний leaderboard;
- CI: syntax, schema, unit tests, deterministic render і gitleaks.

## Швидкий старт

```bash
python3 -m superbench validate
python3 -m superbench list

python3 -m superbench prepare SB-001 \
  --output .superbench/workspace/current --force

# Передайте PROMPT.md і fixture з цього bundle окремій сесії Codex або Claude,
# збережіть її остаточну відповідь у answer.md, потім перевірте результат.
python3 -m superbench score SB-001 answer.md

python3 -m superbench record SB-001 answer.md \
  --model "Model Name" --provider provider --attempt 1
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
tests/               regression tests
```

Додавання cases описано в [CONTRIBUTING.md](CONTRIBUTING.md), правила
секретів — у [SECURITY.md](SECURITY.md).
