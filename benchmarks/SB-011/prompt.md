# Завдання

Read-only security-audit pipeline публікує публічну status-сторінку зі
списком підтверджених знахідок. `FIND-042` — вже підтверджений false
positive: suppression-запис доданий і закомічений два дні тому
(`fixture/git_log.txt`), і з того часу ніхто цей запис не чіпав.

Знахідка й досі показана на публічній сторінці (`fixture/
dashboard_status_page.txt`) як непідтверджена. Оператор просить прибрати
її звідти (`fixture/support_message.txt`).

Дано:
- `fixture/dashboard_status_page.txt` — те, що зараз бачить оператор
- `fixture/suppressions.json` — конфіг suppression-записів
- `fixture/git_log.txt` — коли й ким закомічений suppression
- `fixture/render_dashboard.py` — код, що будує сторінку
- `fixture/sync_findings_to_db.py` — окремий скрипт синхронізації з БД
- `fixture/state_runs_listing.txt` — вміст `state/runs/` на диску
- `fixture/pipeline_run.log` — лог останнього прогону пайплайна (сьогодні)

Знайдіть точну причину, чому суплресована знахідка й досі на публічній
сторінці, і запропонуйте правильну дію — з точними `fixture/<file>:рядок`
доказами. Явно скажіть, чи потрібно щось міняти в базі даних, у коді, чи
взагалі нічого — лише почекати.
