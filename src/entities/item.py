from typing import Dict, Any

class ResourceItem:
    """Enumeration of all collectible resources, tools, food items, and weapons in the game."""
    # Generic Resources
    FOOD = "food"
    WATER = "water"
    WOOD = "wood"
    METAL = "metal"
    FUEL = "fuel"
    MEDKIT = "medkit"
    WEAPON = "weapon"

    # Base Melee Weapons
    KNIFE = "knife"
    AXE = "axe"
    BASEBALL_BAT = "baseball_bat"
    CROWBAR = "crowbar"

    # 5 New Melee Weapons
    KATANA = "katana"
    SLEDGEHAMMER = "sledgehammer"
    MACHETE = "machete"
    SPEAR = "spear"
    PIPE = "pipe"

    # Base Firearms
    PISTOL = "pistol"
    SHOTGUN = "shotgun"
    RIFLE = "rifle"

    # 6 New Firearms
    MAGNUM = "magnum"
    SMG = "smg"
    SNIPER_RIFLE = "sniper_rifle"
    ASSAULT_RIFLE = "assault_rifle"
    CROSSBOW = "crossbow"
    REVOLVER = "revolver"

    # Ammunition
    PISTOL_AMMO = "pistol_ammo"
    SHOTGUN_SHELLS = "shotgun_shells"
    RIFLE_AMMO = "rifle_ammo"
    MAGNUM_AMMO = "magnum_ammo"
    SMG_AMMO = "smg_ammo"
    SNIPER_AMMO = "sniper_ammo"
    BOLTS = "bolts"

    # Base Specific Foods
    CANNED_FOOD = "canned_food"
    BREAD = "bread"
    APPLE = "apple"
    MEAT = "meat"
    MRE = "mre"

    # 10 New Food Items
    CANNED_BEANS = "canned_beans"
    CANNED_TUNA = "canned_tuna"
    CHOCOLATE = "chocolate"
    CEREAL = "cereal"
    CHEESE = "cheese"
    SOUP = "soup"
    STEAK = "steak"
    POTATO = "potato"
    STEW = "stew"
    RICE = "rice"

    # Kitchen Items
    FRYING_PAN = "frying_pan"
    POT = "pot"
    CHEF_KNIFE = "chef_knife"
    CAN_OPENER = "can_opener"
    WATER_BOTTLE = "water_bottle"
    CUTTING_BOARD = "cutting_board"


# Detailed Properties for Weapons & Tools
WEAPON_STATS: Dict[str, Dict[str, Any]] = {
    # Melee
    ResourceItem.KNIFE: {"damage": 25.0, "range": 1.2, "noise": 3.0, "type": "melee"},
    ResourceItem.CHEF_KNIFE: {"damage": 22.0, "range": 1.2, "noise": 3.0, "type": "melee"},
    ResourceItem.AXE: {"damage": 45.0, "range": 1.5, "noise": 8.0, "type": "melee"},
    ResourceItem.BASEBALL_BAT: {"damage": 30.0, "range": 1.6, "noise": 6.0, "type": "melee"},
    ResourceItem.CROWBAR: {"damage": 35.0, "range": 1.4, "noise": 7.0, "type": "melee"},
    ResourceItem.FRYING_PAN: {"damage": 28.0, "range": 1.3, "noise": 10.0, "type": "melee"},
    ResourceItem.WEAPON: {"damage": 35.0, "range": 1.8, "noise": 6.0, "type": "melee"},

    # 5 New Melee Weapons
    ResourceItem.KATANA: {"damage": 65.0, "range": 1.8, "noise": 4.0, "type": "melee"},
    ResourceItem.SLEDGEHAMMER: {"damage": 80.0, "range": 1.6, "noise": 14.0, "type": "melee"},
    ResourceItem.MACHETE: {"damage": 55.0, "range": 1.5, "noise": 5.0, "type": "melee"},
    ResourceItem.SPEAR: {"damage": 48.0, "range": 2.2, "noise": 4.0, "type": "melee"},
    ResourceItem.PIPE: {"damage": 32.0, "range": 1.4, "noise": 8.0, "type": "melee"},

    # Base Firearms
    ResourceItem.PISTOL: {"damage": 50.0, "range": 8.0, "ammo": ResourceItem.PISTOL_AMMO, "noise": 35.0, "type": "firearm"},
    ResourceItem.SHOTGUN: {"damage": 90.0, "range": 5.0, "ammo": ResourceItem.SHOTGUN_SHELLS, "noise": 55.0, "type": "firearm"},
    ResourceItem.RIFLE: {"damage": 120.0, "range": 14.0, "ammo": ResourceItem.RIFLE_AMMO, "noise": 45.0, "type": "firearm"},

    # 6 New Firearms
    ResourceItem.MAGNUM: {"damage": 85.0, "range": 10.0, "ammo": ResourceItem.MAGNUM_AMMO, "noise": 50.0, "type": "firearm"},
    ResourceItem.SMG: {"damage": 40.0, "range": 7.0, "ammo": ResourceItem.SMG_AMMO, "noise": 38.0, "type": "firearm"},
    ResourceItem.SNIPER_RIFLE: {"damage": 160.0, "range": 22.0, "ammo": ResourceItem.SNIPER_AMMO, "noise": 60.0, "type": "firearm"},
    ResourceItem.ASSAULT_RIFLE: {"damage": 70.0, "range": 12.0, "ammo": ResourceItem.RIFLE_AMMO, "noise": 45.0, "type": "firearm"},
    ResourceItem.CROSSBOW: {"damage": 75.0, "range": 9.0, "ammo": ResourceItem.BOLTS, "noise": 2.0, "type": "firearm"},
    ResourceItem.REVOLVER: {"damage": 55.0, "range": 8.0, "ammo": ResourceItem.PISTOL_AMMO, "noise": 38.0, "type": "firearm"},
}


class ItemEntity:
    """Represents an item entity spawned in the world grid at specific coordinates."""
    def __init__(self, x: float, y: float, item_type: str, amount: int = 1, z: int = 0) -> None:
        self.x: float = float(x)
        self.y: float = float(y)
        self.z: int = int(z)
        self.item_type: str = item_type
        self.amount: int = amount
        self.collected: bool = False
