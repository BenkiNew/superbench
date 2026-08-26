import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("repro")
ALREADY_DONE = {"item_2", "item_5", "item_6"}


async def process_item(name: str) -> dict[str, str]:
    if name in ALREADY_DONE:
        return {"status": "skipped", "name": name}
    await asyncio.sleep(0.01)
    return {"status": "done", "name": name}


async def consumer(queue: asyncio.Queue[str | None]) -> None:
    while True:
        name = await queue.get()
        if name is None:
            queue.task_done()
            return
        logger.info("Обробляємо: %s", name)
        result = await process_item(name)
        if result["status"] == "done":
            logger.info("Готово: %s", name)
        elif result["status"] == "skipped":
            logger.debug("Пропущено: %s", name)
        queue.task_done()


async def main() -> None:
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    for number in range(8):
        queue.put_nowait(f"item_{number}")
    queue.put_nowait(None)
    await consumer(queue)


if __name__ == "__main__":
    asyncio.run(main())
