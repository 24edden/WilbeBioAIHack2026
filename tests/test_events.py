import asyncio

import pytest

from app.events import EventBus


def emit(bus, text):
    return bus.emit("agent_message", agent_id="a-1", agent_role="clinical",
                    payload={"text": text})


def test_ts_is_monotonic_within_a_run():
    bus = EventBus("run-1")
    stamps = [emit(bus, str(i)).ts for i in range(50)]
    assert stamps == sorted(stamps)
    assert len(set(stamps)) == len(stamps)


async def test_subscriber_replays_history_then_streams_live():
    bus = EventBus("run-1")
    emit(bus, "before-1")
    emit(bus, "before-2")

    seen = []

    async def consume():
        async for event in bus.subscribe():
            seen.append(event.payload["text"])

    task = asyncio.create_task(consume())
    await asyncio.sleep(0)          # let the subscription register
    emit(bus, "after-1")
    await asyncio.sleep(0)
    bus.close()
    await asyncio.wait_for(task, timeout=1)

    assert seen == ["before-1", "before-2", "after-1"]


async def test_two_subscribers_each_see_everything():
    bus = EventBus("run-1")
    emit(bus, "one")

    async def consume():
        return [e.payload["text"] async for e in bus.subscribe()]

    tasks = [asyncio.create_task(consume()) for _ in range(2)]
    await asyncio.sleep(0)
    emit(bus, "two")
    await asyncio.sleep(0)
    bus.close()
    results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=1)

    assert results == [["one", "two"], ["one", "two"]]


async def test_subscribing_after_close_replays_and_ends():
    bus = EventBus("run-1")
    emit(bus, "only")
    bus.close()

    seen = [e.payload["text"] async for e in bus.subscribe()]
    assert seen == ["only"]


def test_emitting_after_close_is_a_programming_error():
    bus = EventBus("run-1")
    bus.close()
    with pytest.raises(RuntimeError):
        emit(bus, "late")
