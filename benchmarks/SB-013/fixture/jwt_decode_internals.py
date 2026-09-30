"""Витяг з внутрішньої реалізації decode() бібліотеки для роботи з JWT (версія,
встановлена в проєкті на момент інциденту). Показує лише порядок операцій, не
повний код бібліотеки.
"""

def decode_complete(jwt_token, key, algorithms, options=None):
    # Крок 1: розібрати токен на header/payload/signature і json.loads() header.
    # Це відбувається ЗАВЖДИ, незалежно від того, чи передано правильний ключ,
    # чи буде підпис верифіковано взагалі.
    unverified = _load(jwt_token)  # -> {"header": {...}, "payload": ..., "signature": ...}

    # Крок 2: лише ТЕПЕР, після успішного парсингу заголовка, перевіряється підпис.
    if options is None or options.get("verify_signature", True):
        _verify_signature(unverified, key, algorithms)

    return unverified


def _load(jwt_token):
    header_segment, payload_segment, signature_segment = jwt_token.split(".")
    header_json = _urlsafe_b64decode(header_segment)
    # json.loads() на РЯДКУ, що прийшов від клієнта, без керування максимальною
    # глибиною вкладеності. CPython-парсер JSON рекурсивний: кожен вкладений "{"
    # чи "[" — ще один кадр стека. Досить глибоко вкладеного значення, щоб
    # вичерпати стек до досягнення будь-якого ліміту довжини рядка чи розміру.
    header = json.loads(header_json)  # може підняти RecursionError, не ValueError
    ...
