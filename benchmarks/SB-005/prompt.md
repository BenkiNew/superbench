# Завдання

Сканер позначив SQL f-strings у `fixture/repro_sql.py`. Розробник відповідає,
що назви колонок проходять allowlist до виклику builder-а.

Оцініть реальний ризик кожної інтерполяції окремо: `sort`, `direction`,
`filter_column`, `filter_values`. Не змішуйте identifier binding із value
parameters. Запропонуйте локально безпечний API, який не покладається на
непоказаний caller, і наведіть точні file:line докази.
