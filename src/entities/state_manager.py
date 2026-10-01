from enum import Enum, auto
from typing import Dict, Tuple, Optional, Any, List


class FurnitureCondition(Enum):
    INTACT = auto()
    DAMAGED = auto()
    BARRICADED = auto()
    DESTROYED = auto()


class FurnitureState:
    def __init__(self, x: int, y: int, z: int, tile_type: int, building_id: Optional[str] = None, building_type: Optional[str] = None, durability: float = 100.0) -> None:
        self.x: int = int(x)
        self.y: int = int(y)
        self.z: int = int(z)
        self.tile_type: int = tile_type
        self.building_id: Optional[str] = building_id
        self.building_type: Optional[str] = building_type
        self.durability: float = durability
        self.max_durability: float = durability
        self.condition: FurnitureCondition = FurnitureCondition.INTACT
        self.is_searched: bool = False
        self.is_locked: bool = False
        self.is_pushed: bool = False
        self.contents: Dict[str, int] = {}

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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pos": (self.x, self.y, self.z),
            "tile_type": self.tile_type,
            "building_id": self.building_id,
            "building_type": self.building_type,
            "durability": self.durability,
            "max_durability": self.max_durability,
            "condition": self.condition.name,
            "is_searched": self.is_searched,
            "is_locked": self.is_locked,
            "is_pushed": self.is_pushed,
            "contents": dict(self.contents),
        }


class FurnitureStateManager:
    def __init__(self) -> None:
        self.states: Dict[Tuple[int, int, int], FurnitureState] = {}

    def register_furniture(self, x: int, y: int, z: int, tile_type: int, building_id: Optional[str] = None, building_type: Optional[str] = None, durability: float = 100.0) -> FurnitureState:
        pos = (int(x), int(y), int(z))
        state = FurnitureState(x, y, z, tile_type, building_id, building_type, durability)
        self.states[pos] = state
        return state

    def get_state(self, x: int, y: int, z: int) -> Optional[FurnitureState]:
        return self.states.get((int(x), int(y), int(z)))

    def remove_state(self, x: int, y: int, z: int) -> Optional[FurnitureState]:
        return self.states.pop((int(x), int(y), int(z)), None)

    def move_state(self, old_x: int, old_y: int, new_x: int, new_y: int, z: int) -> Optional[FurnitureState]:
        old_pos = (int(old_x), int(old_y), int(z))
        new_pos = (int(new_x), int(new_y), int(z))
        state = self.states.pop(old_pos, None)
        if state:
            state.x = int(new_x)
            state.y = int(new_y)
            state.is_pushed = True
            self.states[new_pos] = state
        return state

    def get_furniture_by_building(self, building_id: str) -> List[FurnitureState]:
        return [f for f in self.states.values() if f.building_id == building_id]


class ItemCondition(Enum):
    PRISTINE = auto()
    USED = auto()
    DAMAGED = auto()
    SPOILED = auto()


class ExtendedItemState:
    def __init__(self, item_entity: Any, building_id: Optional[str] = None, building_type: Optional[str] = None) -> None:
        self.item_entity: Any = item_entity
        self.building_id: Optional[str] = building_id
        self.building_type: Optional[str] = building_type
        self.durability: float = 100.0
        self.freshness: float = 100.0
        self.condition: ItemCondition = ItemCondition.PRISTINE

    def update_spoilage(self, rate: float) -> None:
        self.freshness = max(0.0, self.freshness - rate)
        if self.freshness <= 0.0:
            self.condition = ItemCondition.SPOILED


class ItemStateManager:
    def __init__(self) -> None:
        self.states: Dict[Any, ExtendedItemState] = {}

    def register_item(self, item_entity: Any, building_id: Optional[str] = None, building_type: Optional[str] = None) -> ExtendedItemState:
        state = ExtendedItemState(item_entity, building_id, building_type)
        self.states[item_entity] = state
        return state

    def get_state(self, item_entity: Any) -> Optional[ExtendedItemState]:
        return self.states.get(item_entity)

    def remove_item(self, item_entity: Any) -> Optional[ExtendedItemState]:
        return self.states.pop(item_entity, None)
