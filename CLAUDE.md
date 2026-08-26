# superbench

- CX33-native проєкт у `/home/benkigeek/projects-new/superbench`.
- Реальні API keys живуть лише в ignored `configs/*.yaml` або
  `/home/benkigeek/.continue/config.yaml` (mode 600).
- Candidate запускається лише проти `.superbench/workspace/current`; не
  розширювати MCP root на весь репозиторій, бо там є oracle/results.
- Кожну відповідь перевіряють три нові різні reviewer sessions.
- Retry максимум 3; `infra_error` не зараховується як помилка моделі.
- Перед commit: `./scripts/ci.sh`.
- Після зміни даних: `python3 -m superbench render --output site`.
- Nginx static, systemd/backend/database не потрібні.
