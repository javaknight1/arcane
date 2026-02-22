"""In-memory pub/sub event bus for SSE streaming.

Each generation job can have multiple SSE subscribers (browser tabs).
Events are published by WebStorageAdapter and consumed by the SSE endpoint.
"""

import asyncio

_subscribers: dict[str, list[asyncio.Queue]] = {}


def subscribe(job_id: str) -> asyncio.Queue:
    """Create and register a new subscriber queue for a job."""
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers.setdefault(job_id, []).append(queue)
    return queue


def unsubscribe(job_id: str, queue: asyncio.Queue) -> None:
    """Remove a subscriber queue. Cleans up empty entries."""
    queues = _subscribers.get(job_id)
    if queues is None:
        return
    try:
        queues.remove(queue)
    except ValueError:
        pass
    if not queues:
        _subscribers.pop(job_id, None)


def publish(job_id: str, event: dict) -> None:
    """Publish an event to all subscribers for a job (non-blocking)."""
    queues = _subscribers.get(job_id)
    if not queues:
        return
    for queue in queues:
        queue.put_nowait(event)


def cleanup(job_id: str) -> None:
    """Remove all subscribers for a job (called on completion)."""
    _subscribers.pop(job_id, None)
