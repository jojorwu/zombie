import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(slots=True)
class GameEvent:
    """Base class for all decoupled engine simulation events."""
    timestamp: float = field(default_factory=time.time)


@dataclass(slots=True)
class NoiseEmittedEvent(GameEvent):
    x: float = 0.0
    y: float = 0.0
    z: int = 0
    volume: float = 10.0
    source_type: str = "generic"


@dataclass(slots=True)
class DamageDealtEvent(GameEvent):
    target: object = None
    attacker: object = None
    damage: float = 0.0
    body_part: object = None


@dataclass(slots=True)
class InfectionProgressEvent(GameEvent):
    entity: object = None
    progress: float = 0.0


@dataclass(slots=True)
class ItemCollectedEvent(GameEvent):
    collector: object = None
    item: object = None


class EventBus:
    """Thread-safe, high-throughput event bus for decoupled Event-Driven Engine Architecture."""
    def __init__(self):
        self._lock = threading.Lock()
        self._subscribers: dict[type[GameEvent], list[Callable]] = {}
        self._queue: list[GameEvent] = []

    def subscribe(self, event_type: type[GameEvent], handler: Callable[[GameEvent], None]):
        """Registers an event handler callback for a specific GameEvent type."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)

    def publish(self, event: GameEvent):
        """Enqueues an event to be dispatched on the next batch processing cycle."""
        with self._lock:
            self._queue.append(event)

    def process_events(self):
        """Flushes queued events and executes subscribed handlers in batch without lock contention."""
        with self._lock:
            if not self._queue:
                return
            events_to_process = self._queue
            self._queue = []
            subscribers_snapshot = {k: list(v) for k, v in self._subscribers.items()}

        for event in events_to_process:
            event_type = type(event)
            handlers = subscribers_snapshot.get(event_type)
            if not handlers:
                continue

            for handler in handlers:
                try:
                    handler(event)
                except Exception:
                    logging.getLogger(__name__).exception(
                        "Error handling event %s", event_type.__name__)

    def clear(self):
        """Resets all queues and subscribers for clean memory teardown."""
        with self._lock:
            self._queue.clear()
            self._subscribers.clear()
