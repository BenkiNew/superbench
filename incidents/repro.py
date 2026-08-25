"""
superbench — incident 001, мінімальна відтворювана версія.

Спрощена, анонімізована модель реального бага з приватного проєкту:
черга + консюмер + функція обробки, яка іноді повертає статус "skipped"
(вже оброблено раніше), і саме ця гілка логується на рівні DEBUG під
логером, налаштованим на INFO. Запустіть і подивіться на вивід — досвід
має бути ІДЕНТИЧНИМ до опису симптому в incident.md: для частини елементів
з черги немає взагалі жодного видимого рядка після "Обробляємо: X".

Запуск:
    python3 repro.py
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("repro")

# Симулює "вже було оброблено раніше з тим самим хешем" для частини елементів
_ALREADY_DONE = {"item_2", "item_5", "item_6"}


async def process_item(name: str) -> dict:
    if name in _ALREADY_DONE:
        return {"status": "skipped", "name": name}
    await asyncio.sleep(0.05)  # симулює реальну роботу (embeddings тощо)
    return {"status": "done", "name": name}


async def consumer(queue: "asyncio.Queue[str | None]") -> None:
    while True:
        name = await queue.get()
        if name is None:
            queue.task_done()
            break

        logger.info(f"Обробляємо: {name}")
        result = await process_item(name)

        if result["status"] == "done":
            logger.info(f"✅ {name}")
        elif result["status"] == "skipped":
            # ось вона, пастка: рядок формується, але DEBUG < INFO
            logger.debug(f"Пропущено (вже оброблено): {name}")
        else:
            logger.warning(f"⚠ Невідомий статус для {name}: {result['status']}")

        queue.task_done()


async def main() -> None:
    queue: "asyncio.Queue[str | None]" = asyncio.Queue()
    for i in range(8):
        queue.put_nowait(f"item_{i}")
    queue.put_nowait(None)
    await consumer(queue)


if __name__ == "__main__":
    asyncio.run(main())
