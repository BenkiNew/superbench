# superbench

- Публічний репозиторій містить лише анонімізовані fixtures, benchmark-логіку
  і статичний GitHub Pages; приватний vhost лишається Tailscale-only.
- Не додавати provider API keys або workflow, який запускає сторонній coding
  agent. Candidate запускається окремою сесією Codex або Claude.
- Candidate запускається лише проти `.superbench/workspace/current`; не
  розширювати MCP root на весь репозиторій, бо там є oracle/results.
- Кожну відповідь перевіряють три нові різні reviewer sessions.
- Перед commit: `./scripts/ci.sh`.
- Після зміни даних: `python3 -m superbench render --output site`.
- Nginx static, systemd/backend/database не потрібні.
