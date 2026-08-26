# Security policy

- Реальні ключі зберігаються лише в локальному `~/.continue/config.yaml` з правами `600`.
- У репозиторій дозволені лише `configs/*.yaml.example`.
- Fixture не може містити PII, production-документи, токени, `.env`, дампи або сирі логи.
- Candidate bundle не містить oracle, results чи responses інших моделей.
- За знайдений секрет відкликайте ключ у провайдера; видалення лише з HEAD недостатнє.
