"""Presentation translations; benchmark inputs and oracles stay unchanged."""
LABELS = {
    'uk': {
        'hero1': 'Бенчмарк, якому', 'hero2': 'є що доводити.',
        'lead': 'Реальні анонімізовані інциденти, ізольовані fixtures та три незалежні reviewer-агенти для кожної відповіді.',
        'incidents': 'інцидентів', 'catalog': 'Каталог інцидентів',
        'catalog_note': 'Не toy-задачі — мінімальні відтворення реальних відмов',
        'leaderboard': 'Лідерборд', 'board_note': 'Якість окремо від стабільності провайдера',
        'model': 'Модель', 'quality': 'Якість', 'reliability': 'Надійність',
        'recent': 'Останні відповіді', 'empty_board': 'Результати ще накопичуються.',
        'empty_runs': 'Нові agent-panel результати ще не записані',
        'principle': 'Один агент не судить іншого одноосібно.',
        'principle_text': 'Correctness розмічає атомарні факти. Evidence звіряє file:line. Adversarial впливає лише відтвореним контрприкладом. Reducer лишає replayable trace.',
        'language': 'Мова сайту',
    },
    'en': {
        'hero1': 'A benchmark with', 'hero2': 'evidence to show.',
        'lead': 'Real anonymized incidents, isolated fixtures, and three independent reviewer agents for each answer.',
        'incidents': 'incidents', 'catalog': 'Incident catalog',
        'catalog_note': 'Minimal reproductions of real failures',
        'leaderboard': 'Leaderboard', 'board_note': 'Quality separate from provider reliability',
        'model': 'Model', 'quality': 'Quality', 'reliability': 'Reliability',
        'recent': 'Recent answers', 'empty_board': 'Results are still being collected.',
        'empty_runs': 'No new agent-panel results recorded yet',
        'principle': 'No single agent judges another alone.',
        'principle_text': 'Correctness labels atomic criteria. Evidence checks file:line references. Adversarial challenges count only with reproduced counterexamples. The reducer keeps a replayable trace.',
        'language': 'Site language',
    },
}

CASE_EN = {
    'SB-001': ('Silent skips in a background asyncio consumer', 'Explain missing final logs without inventing a deadlock or a missing await.'),
    'SB-002': ('An AI transcript appended to a Python file', 'Find the exact cause of PartialParsing and propose a prevention gate.'),
    'SB-003': ('A valid pre-commit guard in an inactive directory', 'Explain why a syntax guard exists in the repository but Git never runs it.'),
    'SB-004': ('A portal shows an old confirmed finding after an incomplete scan', 'Distinguish a stale verified fallback from the current source state.'),
    'SB-005': ('A SQL identifier allowlist hides other injection paths', 'Separate a safe identifier from unvalidated direction and values.'),
    'SB-006': ('OSV associates a package and version absent from the repository', 'Distinguish a code vulnerability from a systematic artifact-association bug.'),
    'SB-008': ('A guard restarts every cycle but never recovers or escalates', 'A restart without waiting for readiness causes an uncaught exception before state is saved. The down_streak counter never advances and no alert is raised.'),
}


def case_text(incident, field: str, locale: str) -> str:
    if locale == 'en' and incident.id in CASE_EN:
        return CASE_EN[incident.id][0 if field == 'title' else 1]
    return incident.data[field]
