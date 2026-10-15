try:
    from rust_engine import RustAnatomicalHealth as AnatomicalHealth
except ImportError:
    class AnatomicalHealth:
        def __init__(self, head=35.0, torso=100.0, left_arm=40.0, right_arm=40.0, left_leg=45.0, right_leg=45.0):
            self.head = head
            self.torso = torso
            self.left_arm = left_arm
            self.right_arm = right_arm
            self.left_leg = left_leg
            self.right_leg = right_leg
            self.bleeding_rate = 0.0

        def apply_targeted_damage(self, part, raw_damage, armor_reduction=0.0):
            actual = max(0.0, raw_damage * (1.0 - armor_reduction))
            self.torso = max(0.0, self.torso - actual)
            return actual

        def tick_bleeding(self):
            return 0.0

        def get_total_health(self):
            return max(0.0, self.head + self.torso + self.left_arm + self.right_arm + self.left_leg + self.right_leg)

        def get_speed_multiplier(self):
            return 1.0

class BodyPart:
    HEAD = "head"
    TORSO = "torso"
    LEFT_ARM = "left_arm"
    RIGHT_ARM = "right_arm"
    LEFT_LEG = "left_leg"
    RIGHT_LEG = "right_leg"

from src.entities.animal import Animal, Rat
from src.entities.ballistics_utility import BallisticsUtility, MaterialResistance
from src.entities.container_utility import ContainerUtility, ItemCategory
from src.entities.crafting import CraftingSystem
from src.entities.factory import EntityFactory, ObjectPool
from src.entities.food_spoilage_utility import FoodSpoilageUtility
from src.entities.item import ARMOR_STATS, WEAPON_STATS, ItemEntity, ResourceItem
from src.entities.item_state_utility import ItemConditionState, ItemStateUtility
from src.entities.sensory import NoiseEvent, ScentTrail
from src.entities.sound_utility import SoundUtility
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
from src.entities.vehicle_utility import (
    VehiclePhysicsUtility,
    VehicleRegistry,
    VehicleType,
)
from src.entities.zombie import Zombie, ZombieState

__all__ = [
    "ARMOR_STATS",
    "WEAPON_STATS",
    "AnatomicalHealth",
    "Animal",
    "BallisticsUtility",
    "BodyPart",
    "ContainerUtility",
    "CraftingSystem",
    "EmotionalState",
    "EntityFactory",
    "ExtendedItemState",
    "FoodSpoilageUtility",
    "FurnitureCondition",
    "FurnitureState",
    "FurnitureStateManager",
    "ItemCategory",
    "ItemCondition",
    "ItemConditionState",
    "ItemEntity",
    "ItemStateManager",
    "ItemStateUtility",
    "MaterialResistance",
    "NoiseEvent",
    "ObjectPool",
    "Rat",
    "ResourceItem",
    "ScentTrail",
    "SoundUtility",
    "Survivor",
    "Vehicle",
    "VehiclePhysicsUtility",
    "VehicleRegistry",
    "VehicleType",
    "Zombie",
    "ZombieState",
]
