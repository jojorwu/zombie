import threading
from typing import Callable, Dict, List, Type
from dataclasses import dataclass, field
import time


@dataclass
class GameEvent:
    """Base class for all decoupled engine simulation events."""
    timestamp: float = field(default_factory=time.time)


@dataclass
class NoiseEmittedEvent(GameEvent):
    x: float = 0.0
    y: float = 0.0
    z: int = 0
    volume: float = 10.0
    source_type: str = "generic"


@dataclass
class DamageDealtEvent(GameEvent):
    target: object = None
    attacker: object = None
    damage: float = 0.0
    body_part: object = None


@dataclass
class InfectionProgressEvent(GameEvent):
    entity: object = None
    progress: float = 0.0


@dataclass
class ItemCollectedEvent(GameEvent):
    collector: object = None
    item: object = None


class EventBus:
    """Thread-safe event bus for decoupled Event-Driven Engine Architecture."""
    def __init__(self):
        self._lock = threading.Lock()
        self._subscribers: Dict[Type[GameEvent], List[Callable]] = {}
        self._queue: List[GameEvent] = []

    def subscribe(self, event_type: Type[GameEvent], handler: Callable[[GameEvent], None]):
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
        """Flushes queued events and executes subscribed handlers in batch."""
        with self._lock:
            events_to_process = list(self._queue)
            self._queue.clear()

        for event in events_to_process:
            event_type = type(event)
            with self._lock:
                handlers = list(self._subscribers.get(event_type, []))

            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    import logging
                    logging.error(f"Error handling event {event_type.__name__}: {e}")
