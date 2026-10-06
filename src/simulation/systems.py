from typing import List
from src.simulation.event_bus import EventBus, NoiseEmittedEvent, InfectionProgressEvent, DamageDealtEvent

try:
    from rust_vulkan_render import RustAcousticSystem
    RUST_ACOUSTIC_AVAILABLE = True
except ImportError:
    RUST_ACOUSTIC_AVAILABLE = False


class AcousticSystem:
    """ECS Acoustic System processing published noise propagation events."""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.active_noises: List[dict] = []
        self.rust_acoustics = RustAcousticSystem() if RUST_ACOUSTIC_AVAILABLE else None
        self.event_bus.subscribe(NoiseEmittedEvent, self.handle_noise)

    def _handle_noise(self, event: NoiseEmittedEvent):
        self.active_noises.append({
            "x": event.x, "y": event.y, "z": event.z,
            "volume": event.volume, "type": event.source_type
        })

    def handle_noise(self, event: NoiseEmittedEvent):
        self._handle_noise(event)

    def calculate_noise_at(self, src_x: float, src_y: float, src_z: int, vol: float, target_x: float, target_y: float, target_z: int) -> float:
        if self.rust_acoustics:
            return RustAcousticSystem.propagate_noise_decibels(src_x, src_y, src_z, vol, target_x, target_y, target_z)
        import math
        dist = math.hypot(target_x - src_x, target_y - src_y) + abs(src_z - target_z) * 2.0
        return max(0.0, vol - dist)


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
