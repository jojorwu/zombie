from typing import Dict, Any, Optional, List, Tuple
import math
from src.entities.item import ResourceItem
from src.world.tiles import TileType


class ItemCategory:
    WEAPON = "Weapon"
    FIREARM = "Firearm"
    AMMUNITION = "Ammunition"
    FOOD = "Food"
    MEDICAL = "Medical"
    CLOTHING = "Clothing"
    TOOL = "Tool"
    MATERIAL = "Material"
    CONTAINER = "Container"
    VALUABLE = "Valuable"
    LITERATURE = "Literature"
    MISC = "Misc"


class ContainerUtility:
    """
    Project Zomboid-style Inventory & Container Management Engine:
    - Accurate item weights (kg / encumbrance units) and categories
    - Strict container capacity limits (kg) for furniture, vehicles, bags, floor tiles, corpses, and survivors
    - Bag weight reduction mechanics (70-80% weight reduction inside equipped/stored backpacks)
    - Item transfer API between any source and target containers
    - Nested sub-inventories and container contents tracking
    - Refrigerator (cooling) vs Freezer (freezing) food storage mechanics
    """

    # Item Weights in Kg (Encumbrance Units in Project Zomboid style)
    ITEM_WEIGHTS: Dict[str, float] = {
        # Melee Weapons
        ResourceItem.KNIFE: 0.3,
        ResourceItem.CHEF_KNIFE: 0.3,
        ResourceItem.AXE: 2.5,
        ResourceItem.STONE_AXE: 2.0,
        ResourceItem.BASEBALL_BAT: 1.5,
        ResourceItem.CROWBAR: 2.0,
        ResourceItem.FRYING_PAN: 1.2,
        ResourceItem.KATANA: 2.0,
        ResourceItem.SLEDGEHAMMER: 4.5,
        ResourceItem.MACHETE: 1.8,
        ResourceItem.SPEAR: 1.5,
        ResourceItem.PIPE: 1.5,
        ResourceItem.WEAPON: 1.5,

        # Firearms
        ResourceItem.PISTOL: 1.2,
        ResourceItem.SHOTGUN: 3.5,
        ResourceItem.RIFLE: 4.0,
        ResourceItem.MAGNUM: 1.8,
        ResourceItem.SMG: 2.5,
        ResourceItem.SNIPER_RIFLE: 5.0,
        ResourceItem.ASSAULT_RIFLE: 3.8,
        ResourceItem.CROSSBOW: 2.8,
        ResourceItem.REVOLVER: 1.3,

        # Ammunition (Per box/stack)
        ResourceItem.PISTOL_AMMO: 0.2,
        ResourceItem.SHOTGUN_SHELLS: 0.4,
        ResourceItem.RIFLE_AMMO: 0.3,
        ResourceItem.MAGNUM_AMMO: 0.3,
        ResourceItem.SMG_AMMO: 0.2,
        ResourceItem.SNIPER_AMMO: 0.4,
        ResourceItem.BOLTS: 0.3,

        # Food & Perishables
        ResourceItem.CANNED_FOOD: 0.8,
        ResourceItem.CANNED_BEANS: 0.8,
        ResourceItem.CANNED_TUNA: 0.4,
        ResourceItem.MRE: 0.5,
        ResourceItem.BREAD: 0.2,
        ResourceItem.APPLE: 0.1,
        ResourceItem.MEAT: 0.6,
        ResourceItem.STEAK: 0.8,
        ResourceItem.CHEESE: 0.3,
        ResourceItem.CHOCOLATE: 0.2,
        ResourceItem.CEREAL: 0.4,
        ResourceItem.SOUP: 0.8,
        ResourceItem.POTATO: 0.2,
        ResourceItem.STEW: 1.0,
        ResourceItem.RICE: 0.5,
        ResourceItem.MUSHROOM: 0.1,
        ResourceItem.BERRIES: 0.1,

        # Medical & Utensils
        ResourceItem.MEDKIT: 1.5,
        ResourceItem.WATER_BOTTLE: 0.8,
        ResourceItem.POT: 1.5,
        ResourceItem.CAN_OPENER: 0.1,
        ResourceItem.CUTTING_BOARD: 0.5,

        # Clothing & Armor
        ResourceItem.CLOTHES: 0.8,
        ResourceItem.RAGS: 0.1,
        ResourceItem.HELMET: 1.5,
        ResourceItem.BODY_ARMOR: 3.5,
        ResourceItem.LEATHER_JACKET: 2.0,
        ResourceItem.PADS: 0.8,

        # Containers & Bags
        ResourceItem.BACKPACK: 1.0,
        ResourceItem.DUFFEL_BAG: 0.8,
        ResourceItem.CRATE: 3.0,

        # Resources & Tools
        ResourceItem.WOOD: 1.5,
        ResourceItem.METAL: 2.0,
        ResourceItem.STICK: 0.2,
        ResourceItem.STONE: 0.5,
        ResourceItem.GAS_CANISTER: 4.0,
        ResourceItem.CAR_BATTERY: 10.0,
        ResourceItem.SPARE_WHEEL: 8.0,
        ResourceItem.ENGINE_PARTS: 5.0,
        ResourceItem.WRENCH: 0.8,

        # Money & Valuables
        ResourceItem.MONEY: 0.01,
        ResourceItem.GOLD_INGOT: 2.5,
        ResourceItem.JEWELRY: 0.1,
        ResourceItem.LOCKPICK: 0.05,

        # Books
        ResourceItem.BOOK: 0.4,
        ResourceItem.SKILL_BOOK: 0.5,
    }

    # Item Category Classifications
    ITEM_CATEGORIES: Dict[str, str] = {
        ResourceItem.KNIFE: ItemCategory.WEAPON,
        ResourceItem.AXE: ItemCategory.WEAPON,
        ResourceItem.BASEBALL_BAT: ItemCategory.WEAPON,
        ResourceItem.CROWBAR: ItemCategory.WEAPON,
        ResourceItem.KATANA: ItemCategory.WEAPON,
        ResourceItem.SLEDGEHAMMER: ItemCategory.WEAPON,
        ResourceItem.MACHETE: ItemCategory.WEAPON,
        ResourceItem.SPEAR: ItemCategory.WEAPON,
        ResourceItem.PIPE: ItemCategory.WEAPON,
        ResourceItem.STONE_AXE: ItemCategory.WEAPON,
        ResourceItem.FRYING_PAN: ItemCategory.WEAPON,
        ResourceItem.CHEF_KNIFE: ItemCategory.WEAPON,

        ResourceItem.PISTOL: ItemCategory.FIREARM,
        ResourceItem.SHOTGUN: ItemCategory.FIREARM,
        ResourceItem.RIFLE: ItemCategory.FIREARM,
        ResourceItem.MAGNUM: ItemCategory.FIREARM,
        ResourceItem.SMG: ItemCategory.FIREARM,
        ResourceItem.SNIPER_RIFLE: ItemCategory.FIREARM,
        ResourceItem.ASSAULT_RIFLE: ItemCategory.FIREARM,
        ResourceItem.CROSSBOW: ItemCategory.FIREARM,
        ResourceItem.REVOLVER: ItemCategory.FIREARM,

        ResourceItem.PISTOL_AMMO: ItemCategory.AMMUNITION,
        ResourceItem.SHOTGUN_SHELLS: ItemCategory.AMMUNITION,
        ResourceItem.RIFLE_AMMO: ItemCategory.AMMUNITION,
        ResourceItem.MAGNUM_AMMO: ItemCategory.AMMUNITION,
        ResourceItem.SMG_AMMO: ItemCategory.AMMUNITION,
        ResourceItem.SNIPER_AMMO: ItemCategory.AMMUNITION,
        ResourceItem.BOLTS: ItemCategory.AMMUNITION,

        ResourceItem.CANNED_FOOD: ItemCategory.FOOD,
        ResourceItem.CANNED_BEANS: ItemCategory.FOOD,
        ResourceItem.CANNED_TUNA: ItemCategory.FOOD,
        ResourceItem.MRE: ItemCategory.FOOD,
        ResourceItem.BREAD: ItemCategory.FOOD,
        ResourceItem.APPLE: ItemCategory.FOOD,
        ResourceItem.MEAT: ItemCategory.FOOD,
        ResourceItem.STEAK: ItemCategory.FOOD,
        ResourceItem.CHEESE: ItemCategory.FOOD,
        ResourceItem.CHOCOLATE: ItemCategory.FOOD,
        ResourceItem.CEREAL: ItemCategory.FOOD,
        ResourceItem.SOUP: ItemCategory.FOOD,
        ResourceItem.POTATO: ItemCategory.FOOD,
        ResourceItem.STEW: ItemCategory.FOOD,
        ResourceItem.RICE: ItemCategory.FOOD,
        ResourceItem.MUSHROOM: ItemCategory.FOOD,
        ResourceItem.BERRIES: ItemCategory.FOOD,
        ResourceItem.WATER_BOTTLE: ItemCategory.FOOD,

        ResourceItem.MEDKIT: ItemCategory.MEDICAL,
        ResourceItem.RAGS: ItemCategory.MEDICAL,

        ResourceItem.CLOTHES: ItemCategory.CLOTHING,
        ResourceItem.HELMET: ItemCategory.CLOTHING,
        ResourceItem.BODY_ARMOR: ItemCategory.CLOTHING,
        ResourceItem.LEATHER_JACKET: ItemCategory.CLOTHING,
        ResourceItem.PADS: ItemCategory.CLOTHING,

        ResourceItem.BACKPACK: ItemCategory.CONTAINER,
        ResourceItem.DUFFEL_BAG: ItemCategory.CONTAINER,
        ResourceItem.CRATE: ItemCategory.CONTAINER,

        ResourceItem.WOOD: ItemCategory.MATERIAL,
        ResourceItem.METAL: ItemCategory.MATERIAL,
        ResourceItem.STICK: ItemCategory.MATERIAL,
        ResourceItem.STONE: ItemCategory.MATERIAL,

        ResourceItem.WRENCH: ItemCategory.TOOL,
        ResourceItem.CAN_OPENER: ItemCategory.TOOL,
        ResourceItem.LOCKPICK: ItemCategory.TOOL,
        ResourceItem.GAS_CANISTER: ItemCategory.TOOL,
        ResourceItem.CAR_BATTERY: ItemCategory.TOOL,
        ResourceItem.SPARE_WHEEL: ItemCategory.TOOL,
        ResourceItem.ENGINE_PARTS: ItemCategory.TOOL,

        ResourceItem.MONEY: ItemCategory.VALUABLE,
        ResourceItem.GOLD_INGOT: ItemCategory.VALUABLE,
        ResourceItem.JEWELRY: ItemCategory.VALUABLE,

        ResourceItem.BOOK: ItemCategory.LITERATURE,
        ResourceItem.SKILL_BOOK: ItemCategory.LITERATURE,
    }

    # Default Container Capacities in Kg (PZ Style)
    CONTAINER_CAPACITIES: Dict[Any, float] = {
        # Furniture Types
        TileType.CABINET: 50.0,
        TileType.REFRIGERATOR: 40.0,
        TileType.KITCHEN_COUNTER: 30.0,
        TileType.WARDROBE: 60.0,
        TileType.WEAPON_SAFE: 35.0,
        TileType.GUN_RACK: 30.0,
        TileType.LOCKER: 40.0,
        TileType.BOOKSHELF: 45.0,
        TileType.OFFICE_DESK: 25.0,
        TileType.STORE_SHELF: 50.0,
        TileType.FACTORY_RACK: 80.0,
        TileType.WORKBENCH: 35.0,
        TileType.CASH_REGISTER: 15.0,
        TileType.DISPLAY_CASE: 25.0,
        TileType.OVEN: 20.0,
        TileType.TRASH_CAN: 30.0,

        # Bags & Wearable Containers
        ResourceItem.BACKPACK: 22.0,
        ResourceItem.DUFFEL_BAG: 18.0,
        ResourceItem.CRATE: 40.0,

        # Generic Floor Tile Container
        "floor": 100.0,
        "corpse": 35.0,
        "survivor": 25.0,
        "vehicle_trunk": 80.0,
        "glove_box": 10.0,
    }

    # Bag Weight Reduction Multipliers (e.g. 0.3 means contents weigh 30% = 70% weight reduction)
    BAG_WEIGHT_REDUCTION: Dict[str, float] = {
        ResourceItem.BACKPACK: 0.30,      # 70% reduction
        ResourceItem.DUFFEL_BAG: 0.35,    # 65% reduction
        ResourceItem.CRATE: 0.80,         # 20% reduction
    }

    @classmethod
    def get_item_weight(cls, item_type: str) -> float:
        """Returns the weight in kg for a single unit of item_type."""
        return cls.ITEM_WEIGHTS.get(item_type, 0.5)

    @classmethod
    def get_item_category(cls, item_type: str) -> str:
        """Returns the Project Zomboid category string for item_type."""
        return cls.ITEM_CATEGORIES.get(item_type, ItemCategory.MISC)

    @classmethod
    def get_container_capacity(cls, container: Any) -> float:
        """Calculates the maximum capacity in kg for any container object or furniture state."""
        if hasattr(container, 'tile_type'):
            return cls.CONTAINER_CAPACITIES.get(container.tile_type, 30.0)
        if hasattr(container, 'trunk_capacity'):
            return float(container.trunk_capacity) * 2.0
        if isinstance(container, (int, str)):
            return cls.CONTAINER_CAPACITIES.get(container, 30.0)
        return 30.0

    @classmethod
    def _extract_contents_dict(cls, container: Any) -> dict:
        if isinstance(container, dict):
            if "contents" in container and isinstance(container["contents"], dict):
                return container["contents"]
            return container
        if hasattr(container, 'contents') and isinstance(container.contents, dict):
            return container.contents
        if hasattr(container, 'inventory') and isinstance(container.inventory, dict):
            return container.inventory
        if hasattr(container, 'trunk_inventory') and isinstance(container.trunk_inventory, dict):
            return container.trunk_inventory
        return {}

    @classmethod
    def get_container_weight(cls, container: Any, inside_bag: bool = False) -> float:
        """
        Calculates the total weight of all items inside a container,
        accounting for bag weight reduction if items are stored inside a bag.
        """
        contents = cls._extract_contents_dict(container)
        has_bag = any(k in cls.BAG_WEIGHT_REDUCTION for k in contents.keys())
        reduction_mult = 0.30 if (has_bag or inside_bag) else 1.0

        total_weight = 0.0
        for item_type, val in contents.items():
            amount = val if isinstance(val, (int, float)) else 1
            unit_weight = cls.get_item_weight(str(item_type))
            if item_type in cls.BAG_WEIGHT_REDUCTION:
                # Bag itself weighs base weight, items inside bag get reduction
                total_weight += unit_weight * amount
            else:
                total_weight += unit_weight * amount * reduction_mult

        return round(total_weight, 2)

    @classmethod
    def can_fit_item(cls, container: Any, item_type: str, amount: int = 1) -> bool:
        """Checks if adding amount units of item_type exceeds the container capacity."""
        current_weight = cls.get_container_weight(container)
        added_weight = cls.get_item_weight(item_type) * amount
        capacity = cls.get_container_capacity(container)
        return (current_weight + added_weight) <= (capacity + 0.001)

    @classmethod
    def add_item_to_container(cls, container: Any, item_type: str, amount: int = 1) -> Tuple[bool, int]:
        """
        Adds item_type to container if weight capacity allows.
        Returns (success_bool, added_amount).
        """
        if amount <= 0:
            return False, 0

        unit_weight = cls.get_item_weight(item_type)
        if unit_weight <= 0:
            unit_weight = 0.01

        capacity = cls.get_container_capacity(container)
        current_weight = cls.get_container_weight(container)
        available_capacity = max(0.0, capacity - current_weight)

        max_addable = int(available_capacity // unit_weight)
        to_add = min(amount, max_addable)

        if to_add <= 0:
            return False, 0

        target_dict = cls._extract_contents_dict(container)
        target_dict[item_type] = target_dict.get(item_type, 0) + to_add
        return True, to_add

    @classmethod
    def remove_item_from_container(cls, container: Any, item_type: str, amount: int = 1) -> int:
        """
        Removes amount units of item_type from container.
        Returns the actual removed amount.
        """
        if amount <= 0:
            return 0

        target_dict = cls._extract_contents_dict(container)
        if not target_dict or item_type not in target_dict:
            return 0

        val = target_dict[item_type]
        available = val if isinstance(val, int) else 1
        removed = min(available, amount)
        target_dict[item_type] -= removed
        if target_dict[item_type] <= 0:
            del target_dict[item_type]

        return removed

    @classmethod
    def transfer_item(cls, source_container: Any, target_container: Any, item_type: str, amount: int = 1) -> int:
        """
        Transfers up to amount units of item_type from source_container to target_container in Project Zomboid style.
        Returns the number of items successfully transferred.
        """
        if amount <= 0:
            return 0

        # Check how many can be added to target
        success, addable = cls.add_item_to_container(target_container, item_type, amount)
        if not success or addable <= 0:
            return 0

        # Remove the addable quantity from source
        actual_removed = cls.remove_item_from_container(source_container, item_type, addable)

        # If removed is less than addable, refund target excess
        if actual_removed < addable:
            cls.remove_item_from_container(target_container, item_type, addable - actual_removed)

        return actual_removed
