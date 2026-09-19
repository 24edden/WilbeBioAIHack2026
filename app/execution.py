"""Small async execution primitives with bounded task allocation and cleanup."""

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")
DEFAULT_VARIANT_CONCURRENCY = 8


def initial_metrics() -> dict[str, int | float]:
    return {"wall_ms": 0, "planning_ms": 0, "specialists_ms": 0, "synthesis_ms": 0,
            "variant_requests": 0, "variant_unique_requests": 0,
            "variant_cache_hits": 0, "variant_peak_concurrency": 0}


async def bounded_map(items: Sequence[T], call: Callable[[T], Awaitable[R]], limit: int) -> list[R]:
    """Preserve input order while allocating at most `limit` worker tasks."""
    if type(limit) is not int or not 1 <= limit <= 16:
        raise ValueError("worker concurrency must be an integer between 1 and 16")
    if not items:
        return []
    pending = iter(enumerate(items))
    results = [None] * len(items)

    async def worker():
        for index, item in pending:
            results[index] = await call(item)

    workers = [asyncio.create_task(worker()) for _ in range(min(limit, len(items)))]
    try:
        await asyncio.gather(*workers)
    finally:
        for task in workers:
            if not task.done():
                task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
    return results
