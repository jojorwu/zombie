from src.entities.anatomy import AnatomicalHealth, BodyPart  # noqa: F401 (re-export)

# NOTE: do NOT import any src.systems.* names at module level here.
# Some systems modules depend on src.world / src.entities leaves
# (e.g. src.systems.ballistics -> src.world.tiles -> src.world.grid ->
# src.entities.*), so eager re-exports from this barrel would recreate the
# circular-import chain:
#   src.entities.__init__ -> src.systems.X -> src.world... -> src.entities (partial)
# Consumers must import concrete utility classes from their canonical
# src.systems.<module> path directly.

from src.entities.animal import Animal, Rat
from src.entities.crafting import CraftingSystem
from src.entities.factory import EntityFactory, ObjectPool
from src.entities.item import ARMOR_STATS, WEAPON_STATS, ItemEntity, ResourceItem
from src.entities.events import NoiseEvent, ScentTrail
from src.entities.state_manager import (
    ExtendedItemState,
    FurnitureCondition,
    FurnitureState,
    FurnitureStateManager,
    ItemCondition,
    ItemStateManager,
)
from src.entities.survivor import EmotionalState, Survivor
from src.entities.vehicle import Vehicle
from src.entities.zombie import Zombie, ZombieState

# NOTE: src.systems.* re-exports were removed from this barrel. They created a
# circular-import chain (src.entities -> src.systems.X -> src.world -> leaf
# modules of src.entities). Import utilities directly from their canonical
# module path instead, e.g.:
#   from src.systems.ballistics import BallisticsUtility
#   from src.systems.sound import SoundUtility

__all__ = [
    "ARMOR_STATS",
    "WEAPON_STATS",
    "AnatomicalHealth",
    "Animal",
    "BodyPart",
    "CraftingSystem",
    "EmotionalState",
    "EntityFactory",
    "ExtendedItemState",
    "FurnitureCondition",
    "FurnitureState",
    "FurnitureStateManager",
    "ItemCondition",
    "ItemEntity",
    "ItemStateManager",
    "NoiseEvent",
    "ObjectPool",
    "Rat",
    "ResourceItem",
    "ScentTrail",
    "Survivor",
    "Vehicle",
    "Zombie",
    "ZombieState",
]
