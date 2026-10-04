import threading
import copy
from dataclasses import dataclass, field
from typing import List, Tuple, Dict


@dataclass
class EntityStateSnapshot:
    """Read-only snapshot of an entity state for render thread interpolation."""
    entity_id: int
    x: float
    y: float
    z: int
    facing_angle: float = 0.0
    entity_type: str = "survivor"
    is_alive: bool = True
    health: float = 100.0


@dataclass
class WorldStateSnapshot:
    """Decoupled double-buffered world state snapshot."""
    tick: int = 0
    timestamp: float = 0.0
    survivors: List[EntityStateSnapshot] = field(default_factory=list)
    zombies: List[EntityStateSnapshot] = field(default_factory=list)
    vehicles: List[EntityStateSnapshot] = field(default_factory=list)
    items: List[EntityStateSnapshot] = field(default_factory=list)


class DoubleBufferedStateExchanger:
    """Thread-safe double-buffered state exchanger between logic tick thread and rendering thread."""
    def __init__(self):
        self._lock = threading.Lock()
        self._back_buffer = WorldStateSnapshot()
        self._front_buffer = WorldStateSnapshot()
        self._updated = False

    def capture_snapshot(self, world, survivors, zombies, vehicles, items):
        """Logic Thread: Creates a state snapshot into the back buffer and swaps buffers."""
        surv_snapshots = [
            EntityStateSnapshot(
                entity_id=id(s), x=s.x, y=s.y, z=s.z,
                facing_angle=getattr(s, 'facing_angle', 0.0),
                entity_type="survivor", is_alive=s.is_alive, health=s.health
            ) for s in survivors
        ]

        zomb_snapshots = [
            EntityStateSnapshot(
                entity_id=id(z), x=z.x, y=z.y, z=z.z,
                facing_angle=getattr(z, 'facing_angle', 0.0),
                entity_type="zombie", is_alive=z.is_alive, health=getattr(z, 'health', 100.0)
            ) for z in zombies if z.is_alive
        ]

        veh_snapshots = [
            EntityStateSnapshot(
                entity_id=id(v), x=v.x, y=v.y, z=v.z,
                facing_angle=getattr(v, 'facing_angle', 0.0),
                entity_type="vehicle", is_alive=True, health=100.0
            ) for v in vehicles
        ]

        item_snapshots = [
            EntityStateSnapshot(
                entity_id=id(i), x=i.x, y=i.y, z=i.z,
                facing_angle=0.0, entity_type="item",
                is_alive=not getattr(i, 'collected', False), health=100.0
            ) for i in items if not getattr(i, 'collected', False)
        ]

        new_snapshot = WorldStateSnapshot(
            tick=world.current_tick,
            timestamp=getattr(world, 'current_time', 0.0),
            survivors=surv_snapshots,
            zombies=zomb_snapshots,
            vehicles=veh_snapshots,
            items=item_snapshots,
        )

        with self._lock:
            self._back_buffer = new_snapshot
            self._front_buffer = copy.copy(self._back_buffer)
            self._updated = True

    def get_render_snapshot(self) -> WorldStateSnapshot:
        """Render Thread: Safely reads the front buffer snapshot for rendering."""
        with self._lock:
            self._updated = False
            return self._front_buffer
