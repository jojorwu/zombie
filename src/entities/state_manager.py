from enum import Enum, auto
from typing import Any


def _container_utility():
    """Resolve ContainerUtility lazily (inside methods only).

    src.systems.container imports src.entities.item, which triggers the
    src.entities package barrel; a module-level import here would close the
    cycle entities -> state_manager -> systems.container -> entities (partial).
    """
    from src.systems.container import ContainerUtility
    return ContainerUtility


class FurnitureCondition(Enum):
    INTACT = auto()
    DAMAGED = auto()
    BARRICADED = auto()
    DESTROYED = auto()


class FurnitureState:
    __slots__ = (
        'building_id',
        'building_type',
        'condition',
        'contents',
        'durability',
        'is_locked',
        'is_pushed',
        'is_searched',
        'max_durability',
        'tile_type',
        'x',
        'y',
        'z'
    )

    def __init__(self, x: int, y: int, z: int, tile_type: int, building_id: str | None = None, building_type: str | None = None, durability: float = 100.0) -> None:
        self.x: int = int(x)
        self.y: int = int(y)
        self.z: int = int(z)
        self.tile_type: int = tile_type
        self.building_id: str | None = building_id
        self.building_type: str | None = building_type
        self.durability: float = durability
        self.max_durability: float = durability
        self.condition: FurnitureCondition = FurnitureCondition.INTACT
        self.is_searched: bool = False
        self.is_locked: bool = False
        self.is_pushed: bool = False
        self.contents: dict[str, int] = {}

    @property
    def capacity(self) -> float:
        """Returns maximum container capacity in kg for this furniture item."""
        return _container_utility().get_container_capacity(self)

    @property
    def contents_weight(self) -> float:
        """Calculates total weight in kg of items stored inside this furniture container."""
        return _container_utility().get_container_weight(self)

    def can_fit_item(self, item_type: str, amount: int = 1) -> bool:
        """Checks if adding amount units of item_type exceeds container capacity."""
        return _container_utility().can_fit_item(self, item_type, amount)

    def add_item(self, item_type: str, amount: int = 1) -> tuple[bool, int]:
        """Adds item to container using ContainerUtility capacity rules."""
        return _container_utility().add_item_to_container(self, item_type, amount)

    def remove_item(self, item_type: str, amount: int = 1) -> int:
        """Removes item from container using _container_utility()."""
        return _container_utility().remove_item_from_container(self, item_type, amount)

    def take_damage(self, amount: float) -> bool:
        """Applies damage to furniture. Returns True if destroyed."""
        self.durability = max(0.0, self.durability - amount)
        if self.durability <= 0.0:
            self.condition = FurnitureCondition.DESTROYED
            return True
        elif self.durability < self.max_durability * 0.5:
            self.condition = FurnitureCondition.DAMAGED
        return False

    def mark_searched(self) -> None:
        self.is_searched = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "pos": (self.x, self.y, self.z),
            "tile_type": self.tile_type,
            "building_id": self.building_id,
            "building_type": self.building_type,
            "durability": self.durability,
            "max_durability": self.max_durability,
            "condition": self.condition.name,
            "capacity_kg": self.capacity,
            "contents_weight_kg": self.contents_weight,
            "is_searched": self.is_searched,
            "is_locked": self.is_locked,
            "is_pushed": self.is_pushed,
            "contents": dict(self.contents),
        }


class FurnitureStateManager:
    def __init__(self) -> None:
        self.states: dict[tuple[int, int, int], FurnitureState] = {}

    def register_furniture(self, x: int, y: int, z: int, tile_type: int, building_id: str | None = None, building_type: str | None = None, durability: float = 100.0) -> FurnitureState:
        pos = (int(x), int(y), int(z))
        state = FurnitureState(x, y, z, tile_type, building_id, building_type, durability)
        self.states[pos] = state
        return state

    def get_state(self, x: int, y: int, z: int) -> FurnitureState | None:
        return self.states.get((int(x), int(y), int(z)))

    def remove_state(self, x: int, y: int, z: int) -> FurnitureState | None:
        return self.states.pop((int(x), int(y), int(z)), None)

    def move_state(self, old_x: int, old_y: int, new_x: int, new_y: int, z: int) -> FurnitureState | None:
        old_pos = (int(old_x), int(old_y), int(z))
        new_pos = (int(new_x), int(new_y), int(z))
        state = self.states.pop(old_pos, None)
        if state:
            state.x = int(new_x)
            state.y = int(new_y)
            state.is_pushed = True
            self.states[new_pos] = state
        return state

    def get_furniture_by_building(self, building_id: str) -> list[FurnitureState]:
        return [f for f in self.states.values() if f.building_id == building_id]

    def purge_destroyed_and_stale(self) -> int:
        """Purges DESTROYED furniture states to prevent memory leaks."""
        to_remove = [pos for pos, state in self.states.items() if state.condition == FurnitureCondition.DESTROYED]
        for pos in to_remove:
            del self.states[pos]
        return len(to_remove)

    def clear(self) -> None:
        self.states.clear()


class ItemCondition(Enum):
    PRISTINE = auto()
    USED = auto()
    DAMAGED = auto()
    SPOILED = auto()


class ExtendedItemState:
    __slots__ = ('building_id', 'building_type', 'condition', 'durability', 'freshness', 'item_entity')

    def __init__(self, item_entity: Any, building_id: str | None = None, building_type: str | None = None) -> None:
        self.item_entity: Any = item_entity
        self.building_id: str | None = building_id
        self.building_type: str | None = building_type
        self.durability: float = 100.0
        self.freshness: float = 100.0
        self.condition: ItemCondition = ItemCondition.PRISTINE

    def update_spoilage(self, rate: float) -> None:
        self.freshness = max(0.0, self.freshness - rate)
        if self.freshness <= 0.0:
            self.condition = ItemCondition.SPOILED


class ItemStateManager:
    def __init__(self) -> None:
        self.states: dict[Any, ExtendedItemState] = {}

    def register_item(self, item_entity: Any, building_id: str | None = None, building_type: str | None = None) -> ExtendedItemState:
        state = ExtendedItemState(item_entity, building_id, building_type)
        self.states[item_entity] = state
        return state

    def get_state(self, item_entity: Any) -> ExtendedItemState | None:
        return self.states.get(item_entity)

    def remove_item(self, item_entity: Any) -> ExtendedItemState | None:
        return self.states.pop(item_entity, None)

    def purge_stale(self, active_item_entities: set | None = None) -> int:
        """Removes item states for destroyed or collected items."""
        if active_item_entities is None:
            return 0
        to_remove = [item for item in self.states if item not in active_item_entities]
        for item in to_remove:
            del self.states[item]
        return len(to_remove)

    def clear(self) -> None:
        self.states.clear()


class LazyChunkStatePersistence:
    """
    Lazy State Inflation & Delta Change Log Persistence.
    Stores lightweight delta logs for unvisited/inactive chunks and inflates full states on demand.
    """
    __slots__ = ('_delta_logs', '_inflated_chunks')

    def __init__(self) -> None:
        self._delta_logs: dict[tuple[int, int], list[dict[str, Any]]] = {}
        self._inflated_chunks: dict[tuple[int, int], bool] = {}

    def is_inflated(self, chunk_x: int, chunk_y: int) -> bool:
        return self._inflated_chunks.get((chunk_x, chunk_y), False)

    def log_delta_change(self, chunk_x: int, chunk_y: int, delta_type: str, data: dict[str, Any]) -> None:
        key = (chunk_x, chunk_y)
        if key not in self._delta_logs:
            self._delta_logs[key] = []
        self._delta_logs[key].append({"type": delta_type, "data": data})

    def inflate_chunk_states(self, chunk_x: int, chunk_y: int) -> list[dict[str, Any]]:
        """Inflates full objects for a chunk from its delta log on demand."""
        key = (chunk_x, chunk_y)
        self._inflated_chunks[key] = True
        return self._delta_logs.get(key, [])

    def deflate_chunk_states(self, chunk_x: int, chunk_y: int) -> None:
        """Deflates active objects into lightweight delta records when unloading a chunk."""
        key = (chunk_x, chunk_y)
        self._inflated_chunks[key] = False

    def clear(self) -> None:
        self._delta_logs.clear()
        self._inflated_chunks.clear()
