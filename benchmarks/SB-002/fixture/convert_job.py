import asyncio


async def convert_today() -> None:
    await asyncio.sleep(0)
    print("done")


if __name__ == "__main__":
    asyncio.run(convert_today())
```
**Крок 2: Запуск скрипту.**
TOOL_NAME: run_terminal_command
BEGIN_ARG: command
python scripts/convert_job.py
END_ARG
