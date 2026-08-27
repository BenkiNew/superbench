"""Health-check + self-heal guard for a messaging-instance API.

Запускається таймером (systemd/cron) — кожен запуск це окремий процес,
тому єдина пам'ять між запусками — persisted state.json.
"""
import json
import subprocess
from pathlib import Path

STATE_PATH = Path("state.json")
DOWN_STREAK_THRESHOLD = 3
ALERT_AFTER_ACTIONS = 5


def _load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"down_streak": 0, "action_count": 0}


def _save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state))


def fetch_status() -> str:
    """Опитує instance API. Повертає connectionStatus: 'open'|'close'|'unreachable'."""
    return query_instance_api()


def restart_instance() -> None:
    subprocess.run(["systemctl", "restart", "wa-instance.service"], check=True)


def check_ready() -> None:
    """Одразу після рестарту опитує API ще раз; кидає RuntimeError, якщо
    контейнер ще не встиг підняти HTTP-сервер (типовий cold start ~10-15с)."""
    if query_instance_api() == "unreachable":
        raise RuntimeError("instance API not ready yet")


def send_alert(text: str) -> None:
    ...  # шле в Telegram; неважливо для цього інциденту


def run_once() -> None:
    state = _load_state()
    status = fetch_status()

    if status == "open":
        state["down_streak"] = 0
        state["action_count"] = 0
        _save_state(state)
        return

    state["down_streak"] += 1
    if state["down_streak"] < DOWN_STREAK_THRESHOLD:
        _save_state(state)
        return

    restart_instance()
    check_ready()

    state["action_count"] += 1
    state["down_streak"] = 0
    _save_state(state)

    if state["action_count"] >= ALERT_AFTER_ACTIONS:
        send_alert(f"instance досі close після {ALERT_AFTER_ACTIONS} спроб рестарту")
