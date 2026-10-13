# Контрольні пари та неповні панелі

**Українська** · [English](CONTROL_EXPERIMENTS.en.md)

Контрольний експеримент перевіряє, чи reviewer виявляє внесений дефект та чи
відхиляє правильну відповідь. Це окремий тип результату, який не змінює
офіційну триагентну adjudication або лідерборд coding agents.

## Підготовка

```bash
python3 -m superbench control-prepare SB-004 \
  --correct correct.md --incorrect incorrect.md \
  --defect-id premature-resolution --output .superbench/control-004-v1
```

Відповіді мають відрізнятися; правильність контрольної відповіді та дефект
визначає й перевіряє організатор. CLI випадково розподіляє їх між sample-a та
sample-b. Порядок сам по собі не забезпечує сліпе оцінювання: використовуйте
окремі свіжі reviewer-сесії, контролюйте їхній контекст та shared memory.

Передавайте лише окрему папку `samples/sample-a` або `samples/sample-b`.
`evaluation.json` та `benchmark/` лишаються у організатора: там є ключ
очікувань, версія case, hashes і snapshot із oracle. Не передавайте корінь
пари, ключ чи oracle reviewer-у. Bundle містить лише PROMPT, fixture,
ANSWER та відкриті metadata. Не запускати більше audits автоматично.

## Облік рецензій

Після фактичного review та локальної перевірки findings створіть JSON:

```json
{
  "schema_version": 1,
  "cost_usd": null,
  "voices": [
    {
      "id": "reviewer-1",
      "transport_status": "completed",
      "review": {
        "verdict": "rejected",
        "findings": [
          {
            "defect_id": "premature-resolution",
            "decision": "confirmed",
            "evidence": "latest_scan.json:3-5: incomplete, coverage 0/12; no relevant negative evidence"
          }
        ]
      }
    },
    {
      "id": "reviewer-2",
      "transport_status": "completed",
      "error": "Model unavailable; no substantive review"
    },
    {
      "id": "reviewer-3",
      "transport_status": "failed",
      "error": "Timeout"
    }
  ]
}
```

```bash
python3 -m superbench control-record .superbench/control-004-v1 sample-a report.json
python3 -m superbench control-summary .superbench/control-004-v1
```

`voices` має містити **всіх запрошених** reviewer-ів, включно зі збоями;
Додайте `requested_voice_ids` з повним списком запрошених. За його наявності
CLI відхиляє пропущені, зайві або дубльовані ID. Старі звіти без цього списку
не перевіряються на пропуски; сам список потрібно звірити з початковим запитом.
`transport_status=completed` сам по собі не дає придатної рецензії.
`review` додають тільки для змістовного результату; `verdict` accepted,
rejected або unclear — локальна нормалізація відповіді reviewer-а, не
автоматичний аналіз довільного тексту. Findings потребують локальної
`decision` confirmed/unsupported та evidence. Відхилення відповіді потребує
щонайменше одного підтвердженого finding. Minor побажання не слід
нормалізувати як rejected без невиконаної вимоги.

Повнота панелі: complete, partial або unavailable за кількістю придатних
рецензій. Жодного придатного voice — результат невідомий, а не «чисто».
`target_detected` рахує підтверджений внесений defect_id для помилкового
контролю. `control_rejected` фіксує відхилення правильного контролю для
подальшого розбору можливого false positive; це не доказ безпомилковості
самого контрольного ключа. Відсутність findings не є глобальною гарантією.

Невідома вартість — null, а не 0. Для зіставлення часу зберігайте окремо
час сервісу та wall time всієї сесії; їх не можна підміняти. Додаткові
поля звіту з provenance, версіями, run ids і times зберігаються як надані.
Не додавайте секрети, приватну інфраструктуру або персональні дані.

## Історія

Кожний `control-record` створює новий immutable JSON у `reviews/` і дописує
`events.jsonl`. Summary читає останній запис для кожного sample; усі попередні
лишаються доступними. Зміна pinned input блокує запис — створіть нову пару
нової версії. Підсумок не приховує requested/usable voices та не потрапляє
в `results/results.jsonl` офіційного лідерборду.
