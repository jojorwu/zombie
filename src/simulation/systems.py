from typing import List
from src.simulation.event_bus import EventBus, NoiseEmittedEvent, InfectionProgressEvent, DamageDealtEvent


class AcousticSystem:
    """ECS Acoustic System processing published noise propagation events."""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.active_noises: List[dict] = []
        self.event_bus.subscribe(NoiseEmittedEvent, self.handle_noise)

    def _handle_noise(self, event: NoiseEmittedEvent):
        self.active_noises.append({
            "x": event.x, "y": event.y, "z": event.z,
            "volume": event.volume, "type": event.source_type
        })

    def handle_noise(self, event: NoiseEmittedEvent):
        self._handle_noise(event)


class InfectionSystem:
    """ECS Infection System processing zombie bite infection progression."""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe(InfectionProgressEvent, self.handle_infection)

    def handle_infection(self, event: InfectionProgressEvent):
        if event.entity and hasattr(event.entity, "infection_progress"):
            event.entity.infection_progress = min(100.0, event.entity.infection_progress + event.progress)


class ParticleSystem:
    """ECS Particle System handling environmental window shatter and dust particles."""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.particles: List[dict] = []

    def spawn_shatter_particles(self, x: float, y: float, z: int):
        self.particles.append({"x": x, "y": y, "z": z, "type": "glass_shatter", "lifetime": 10})
