# Версійність та історична відтворюваність

**Українська** · [English](VERSIONING.en.md)

Версія harness задається в pyproject.toml та superbench.__version__.
Версія кожного кейсу — в incident.json. Змінюючи prompt, fixture або oracle,
оновлюйте версію кейсу й CHANGELOG; не підміняйте умови старого результату.

З 0.3.0 новий `record` зберігає snapshot benchmark разом із oracle у папці
прогону та hashes його файлів, case version, case fingerprint, harness
version і source commit (або null, якщо Git недоступний). Hashes і snapshot
є точними умовами оцінювання: commit може не описувати локальні незакомічені
зміни. При adjudication snapshot перевіряється і використовується замість
поточних критеріїв. Зміна snapshot відхиляється. Run ID включає fingerprint,
тому однакова відповідь на нову версію кейсу не перезаписує старий прогін.

`registration.json` фіксує первинну реєстрацію. `response.json` і
`adjudication.json` — поточні проєкції, які оновлюються. Кожне оцінювання
зберігається окремо в `adjudications/000001.json`, `000002.json` тощо;
події append-only ledger зберігають попередні оцінки. Лідерборд враховує
останню оцінку response_id один раз; pending не означає успіх чи reliability.

Старі результати не мігруються автоматично й не отримують вигаданих версій.
Якщо legacy-прогін не має snapshot, нова adjudication явно позначає
provenance legacy-unpinned; вона використовує доступний поточний case.
Перш ніж використати таку переоцінку як історично порівнювану, окремо
перевірте початкові критерії. Перед оновленням legacy adjudication її
наявний JSON також зберігається в історії.

Snapshots з oracle призначені для evaluator-а; candidate отримує лише
`prepare` bundle. Контрольні експерименти зберігаються окремо від coding-agent
results. Не переносіть приватні provider reports у публічний каталог
автоматично. CLI розрахований на одного writer-а на один каталог результатів;
паралельний запис у той самий run/pair не підтримується.
