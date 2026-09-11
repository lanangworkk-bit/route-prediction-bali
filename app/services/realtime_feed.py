import asyncio
import logging

logger = logging.getLogger(__name__)


class RealtimeFeed:
    """Tiny in-process pub/sub used to push live events over SSE.

    Producers call publish() (sync-safe); connected streams consume via
    subscribe(). Queues are bounded so slow subscribers never block.
    """

    def __init__(self, maxsize: int = 50):
        self._subscribers: set[asyncio.Queue] = set()
        self._maxsize = maxsize

    async def subscribe(self):
        queue: asyncio.Queue = asyncio.Queue(maxsize=self._maxsize)
        self._subscribers.add(queue)
        try:
            while True:
                try:
                    yield await queue.get()
                except asyncio.CancelledError:
                    break
        finally:
            self._subscribers.discard(queue)

    def publish(self, data: dict):
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(data)
            except asyncio.QueueFull:
                # Drop newest for slow consumers to avoid memory pressure.
                continue
            except RuntimeError:
                continue


incident_feed = RealtimeFeed()
traffic_feed = RealtimeFeed()
