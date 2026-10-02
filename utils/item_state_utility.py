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
    def set_metal_quality(cls, item_key: str, quality: str):
        cls._item_metal_quality[item_key] = quality

    @classmethod
    def get_metal_quality(cls, item_key: str) -> str:
        return cls._item_metal_quality.get(item_key, MetalQuality.IRON)

    @classmethod
    def get_metal_damage_multiplier(cls, item_key: str) -> float:
        q = cls.get_metal_quality(item_key)
        return METAL_QUALITY_MULTIPLIERS.get(q, {}).get("damage_mult", 1.0)

    @classmethod
    def get_condition(cls, item_key: str) -> ItemConditionState:
        dur = cls._item_durability.get(item_key, 100.0)
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
    def set_durability(cls, item_key: str, durability: float):
        cls._item_durability[item_key] = max(0.0, min(100.0, float(durability)))

    @classmethod
    def get_durability(cls, item_key: str) -> float:
        return cls._item_durability.get(item_key, 100.0)

    @classmethod
    def damage_item(cls, item_key: str, amount: float) -> float:
        current = cls.get_durability(item_key)
        new_dur = max(0.0, current - amount)
        cls._item_durability[item_key] = new_dur
        return new_dur

    @classmethod
    def repair_item(cls, item_key: str, amount: float) -> float:
        current = cls.get_durability(item_key)
        new_dur = min(100.0, current + amount)
        cls._item_durability[item_key] = new_dur
        return new_dur
