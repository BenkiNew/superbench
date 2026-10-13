# Як додати benchmark case

**Українська** · [English](CONTRIBUTING.en.md)

1. Створіть `benchmarks/SB-NNN/incident.json`, `prompt.md`, `fixture/` та `oracle.json`.
2. Fixture має бути анонімізованим, самодостатнім і без секретів чи production-даних.
3. Prompt повинен вимагати перевірні file:line докази.
4. Oracle розбиває відповідь на атомарні критерії; core-критерії позначаються явно.
5. Запустіть `python3 -m superbench validate` і `./scripts/ci.sh`.

Після публікації oracle case лишається regression test, але не contamination-free оцінкою foundation model.

## Agent-panel

Кожну candidate response перевіряють три нові, різні сесії: correctness,
evidence та adversarial. Reviewer не бачить назву candidate model, ціну,
prior score або висновки інших reviewer-ів. Повторне використання одного
`agent_name` для тієї самої відповіді блокується CLI.

## Версії та повторні перевірки

Для змін prompt/fixture/oracle підвищуйте version у incident.json і записуйте
зміст у CHANGELOG. Не редагуйте опубліковані ledger events чи snapshots старих
прогонів. [Правила історії](docs/VERSIONING.md) і
[контрольні експерименти](docs/CONTROL_EXPERIMENTS.md) описують новий workflow.

Для українських title/summary додавайте англійський текст каталогу в
`superbench/localization.py`. Локалізуйте presentation, не вихідні матеріали
тестового кейсу.
