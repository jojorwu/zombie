from src.entities.item import ResourceItem
from src.world.tiles import TileType


class ItemCategory:
    FIREARM = "firearm"
    WEAPON = "weapon"
    FOOD = "food"
    MEDICAL = "medical"


ITEM_WEIGHTS = {
    ResourceItem.PISTOL: 1.2,
    ResourceItem.RIFLE: 3.5,
    ResourceItem.SHOTGUN: 3.8,
    ResourceItem.PISTOL_AMMO: 0.01,
    ResourceItem.RIFLE_AMMO: 0.012,
    ResourceItem.SHOTGUN_SHELLS: 0.04,
    ResourceItem.KNIFE: 0.4,
    ResourceItem.AXE: 2.5,
    ResourceItem.KATANA: 1.5,
    ResourceItem.SLEDGEHAMMER: 4.5,
    ResourceItem.CANNED_FOOD: 0.8,
    ResourceItem.BREAD: 0.3,
    ResourceItem.APPLE: 0.2,
    ResourceItem.WATER_BOTTLE: 1.0,
    ResourceItem.MEDKIT: 1.5,
    ResourceItem.BACKPACK: 1.0,
    ResourceItem.DUFFEL_BAG: 1.2,
    ResourceItem.GAS_CANISTER: 4.0,
    ResourceItem.CAR_BATTERY: 10.0,
    ResourceItem.SPARE_WHEEL: 8.0,
    ResourceItem.ENGINE_PARTS: 12.0,
    ResourceItem.LOCKPICK: 0.05,
    ResourceItem.MONEY: 0.001,
    ResourceItem.GOLD_INGOT: 1.0,
    ResourceItem.JEWELRY: 0.1,
    ResourceItem.STICK: 0.3,
    ResourceItem.STONE: 0.5,
    ResourceItem.RAGS: 0.1,
    ResourceItem.CLOTHES: 0.8,
    ResourceItem.STONE_AXE: 2.0,
    ResourceItem.BOOK: 0.5,
    ResourceItem.SKILL_BOOK: 0.6,
}


class ContainerUtility:
    @staticmethod
    def get_item_weight(item_type: str) -> float:
        return ITEM_WEIGHTS.get(item_type, 1.0)

    @staticmethod
    def get_item_category(item_type: str) -> str:
        if "pistol" in item_type or "rifle" in item_type or item_type == ResourceItem.PISTOL:
            return ItemCategory.FIREARM
        if item_type in (ResourceItem.AXE, ResourceItem.KNIFE, ResourceItem.KATANA, ResourceItem.SLEDGEHAMMER):
            return ItemCategory.WEAPON
        if item_type in (ResourceItem.CANNED_FOOD, ResourceItem.MEAT, ResourceItem.BREAD, ResourceItem.APPLE, ResourceItem.FOOD):
            return ItemCategory.FOOD
        if item_type in (ResourceItem.MEDKIT, getattr(ResourceItem, 'BANDAGE', 'bandage')):
            return ItemCategory.MEDICAL
        return "general"

    @staticmethod
    def get_container_capacity(furniture) -> float:
        ttype = getattr(furniture, 'tile_type', None)
        if ttype == TileType.CABINET:
            return 50.0
        if ttype == TileType.REFRIGERATOR:
            return 40.0
        if ttype == TileType.WEAPON_SAFE:
            return 35.0
        if isinstance(furniture, dict) and "capacity" in furniture:
            return float(furniture["capacity"])
        return 30.0

    @staticmethod
    def get_container_weight(container, inside_bag: bool = False) -> float:
        if isinstance(container, dict):
            contents = container.get("contents", container)
        elif hasattr(container, "contents"):
            contents = container.contents
        elif hasattr(container, "inventory"):
            contents = container.inventory
        else:
            contents = {}

        if not isinstance(contents, dict):
            contents = {}

        total = 0.0
        for itype, amt in contents.items():
            if not isinstance(amt, (int, float)):
                continue
            w = ITEM_WEIGHTS.get(itype, 1.0) * float(amt)
            if inside_bag and itype == ResourceItem.SLEDGEHAMMER:
                w *= 0.3
            total += w
        return round(total, 2)

    @classmethod
    def can_fit_item(cls, container, item_type: str, amount: int = 1) -> bool:
        cap = cls.get_container_capacity(container)
        curr = cls.get_container_weight(container)
        add_w = cls.get_item_weight(item_type) * amount
        return (curr + add_w) <= cap

    @classmethod
    def add_item_to_container(cls, container, item_type: str, amount: int = 1):
        if isinstance(container, dict):
            if "contents" in container:
                contents = container["contents"]
            else:
                contents = container
        elif hasattr(container, "contents"):
            contents = container.contents
        elif hasattr(container, "inventory"):
            contents = container.inventory
        else:
            contents = {}

        cap = cls.get_container_capacity(container)
        curr = cls.get_container_weight(container)
        w_per_item = cls.get_item_weight(item_type)

        rem_cap = max(0.0, cap - curr)
        max_fit = int(rem_cap // w_per_item)
        to_add = min(amount, max_fit)

        if to_add > 0:
            contents[item_type] = contents.get(item_type, 0) + to_add
            return True, to_add
        return False, 0

    @classmethod
    def remove_item_from_container(cls, container, item_type: str, amount: int = 1) -> int:
        if isinstance(container, dict):
            contents = container.get("contents", container)
        elif hasattr(container, "contents"):
            contents = container.contents
        elif hasattr(container, "inventory"):
            contents = container.inventory
        else:
            contents = {}

        curr = contents.get(item_type, 0)
        taken = min(curr, amount)
        if taken > 0:
            contents[item_type] -= taken
            if contents[item_type] <= 0:
                del contents[item_type]
        return taken

    @classmethod
    def transfer_item(cls, source, target, item_type: str, amount: int = 1) -> int:
        taken = cls.remove_item_from_container(source, item_type, amount)
        if taken > 0:
            ok, added = cls.add_item_to_container(target, item_type, taken)
            if added < taken:
                cls.add_item_to_container(source, item_type, taken - added)
            return added
        return 0
