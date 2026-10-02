from enum import Enum, auto
from typing import Dict, Any


class ItemConditionState(Enum):
    PRISTINE = auto()
    GOOD = auto()
    WORN = auto()
    DAMAGED = auto()
    BROKEN = auto()


from src.entities.item import MetalQuality, METAL_QUALITY_MULTIPLIERS


class ItemStateUtility:
    """Developer utility for managing item conditions, metal quality purity, durability decay, spoilage, and repair."""
    _item_durability: Dict[str, float] = {}
    _item_metal_quality: Dict[str, str] = {}

    @classmethod
    def _get_key(cls, item: Any) -> str:
        if isinstance(item, str):
            return item
        if hasattr(item, "item_id"):
            return str(item.item_id)
        if hasattr(item, "id"):
            return str(item.id)
        return f"{getattr(item, 'item_type', 'item')}_{id(item)}"

    @classmethod
    def set_metal_quality(cls, item: Any, quality: str):
        k = cls._get_key(item)
        cls._item_metal_quality[k] = quality

    @classmethod
    def get_metal_quality(cls, item: Any) -> str:
        k = cls._get_key(item)
        return cls._item_metal_quality.get(k, MetalQuality.IRON)

    @classmethod
    def get_metal_damage_multiplier(cls, item: Any) -> float:
        q = cls.get_metal_quality(item)
        return METAL_QUALITY_MULTIPLIERS.get(q, {}).get("damage_mult", 1.0)

    @classmethod
    def get_condition(cls, item: Any) -> ItemConditionState:
        dur = cls.get_durability(item)
        if dur >= 90.0:
            return ItemConditionState.PRISTINE
        elif dur >= 65.0:
            return ItemConditionState.GOOD
        elif dur >= 35.0:
            return ItemConditionState.WORN
        elif dur > 0.0:
            return ItemConditionState.DAMAGED
        return ItemConditionState.BROKEN

    @classmethod
    def set_durability(cls, item: Any, durability: float):
        k = cls._get_key(item)
        cls._item_durability[k] = max(0.0, min(100.0, float(durability)))

    @classmethod
    def get_durability(cls, item: Any) -> float:
        k = cls._get_key(item)
        return cls._item_durability.get(k, 100.0)

    @classmethod
    def damage_item(cls, item: Any, amount: float) -> float:
        k = cls._get_key(item)
        current = cls.get_durability(k)
        new_dur = max(0.0, current - amount)
        cls._item_durability[k] = new_dur
        return new_dur

    @classmethod
    def repair_item(cls, item: Any, amount: float) -> float:
        k = cls._get_key(item)
        current = cls.get_durability(k)
        new_dur = min(100.0, current + amount)
        cls._item_durability[k] = new_dur
        return new_dur
