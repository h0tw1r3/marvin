import asyncio
from collections.abc import Awaitable, Iterable

from marvin.config import settings
from marvin.libs.logger import get_logger

logger = get_logger("GATHER")


async def bounded_gather[T](coroutines: Iterable[Awaitable[T]]) -> tuple[T, ...]:
    sem = asyncio.Semaphore(settings.core.concurrency)

    async def wrap(coro: Awaitable[T]) -> T:
        async with sem:
            try:
                return await coro
            except Exception as error:
                logger.warning(f"Task failed: {type(error).__name__}: {error}")
                return error

    results = await asyncio.gather(*(wrap(coroutine) for coroutine in coroutines), return_exceptions=True)
    return tuple(results)
