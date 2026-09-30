class ResourceItem:
    # Generic Resources
    FOOD = "food"
    WATER = "water"
    WOOD = "wood"
    METAL = "metal"
    FUEL = "fuel"
    MEDKIT = "medkit"
    WEAPON = "weapon"

    # 4 Melee Weapons
    KNIFE = "knife"
    AXE = "axe"
    BASEBALL_BAT = "baseball_bat"
    CROWBAR = "crowbar"

    # 3 Firearms
    PISTOL = "pistol"
    SHOTGUN = "shotgun"
    RIFLE = "rifle"

    # Ammunition
    PISTOL_AMMO = "pistol_ammo"
    SHOTGUN_SHELLS = "shotgun_shells"
    RIFLE_AMMO = "rifle_ammo"

    # 5 Specific Foods
    CANNED_FOOD = "canned_food"
    BREAD = "bread"
    APPLE = "apple"
    MEAT = "meat"
    MRE = "mre"

    # 6 Kitchen Items
    FRYING_PAN = "frying_pan"
    POT = "pot"
    CHEF_KNIFE = "chef_knife"
    CAN_OPENER = "can_opener"
    WATER_BOTTLE = "water_bottle"
    CUTTING_BOARD = "cutting_board"


# Detailed Properties for Weapons & Tools
WEAPON_STATS = {
    # Melee
    ResourceItem.KNIFE: {"damage": 25.0, "range": 1.2, "noise": 3.0, "type": "melee"},
    ResourceItem.CHEF_KNIFE: {"damage": 22.0, "range": 1.2, "noise": 3.0, "type": "melee"},
    ResourceItem.AXE: {"damage": 45.0, "range": 1.5, "noise": 8.0, "type": "melee"},
    ResourceItem.BASEBALL_BAT: {"damage": 30.0, "range": 1.6, "noise": 6.0, "type": "melee"},
    ResourceItem.CROWBAR: {"damage": 35.0, "range": 1.4, "noise": 7.0, "type": "melee"},
    ResourceItem.FRYING_PAN: {"damage": 28.0, "range": 1.3, "noise": 10.0, "type": "melee"},
    ResourceItem.WEAPON: {"damage": 35.0, "range": 1.8, "noise": 6.0, "type": "melee"},

    # Firearms
    ResourceItem.PISTOL: {"damage": 50.0, "range": 8.0, "ammo": ResourceItem.PISTOL_AMMO, "noise": 35.0, "type": "firearm"},
    ResourceItem.SHOTGUN: {"damage": 90.0, "range": 5.0, "ammo": ResourceItem.SHOTGUN_SHELLS, "noise": 55.0, "type": "firearm"},
    ResourceItem.RIFLE: {"damage": 120.0, "range": 14.0, "ammo": ResourceItem.RIFLE_AMMO, "noise": 45.0, "type": "firearm"},
}


class ItemEntity:
    def __init__(self, x, y, item_type, amount=1, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.item_type = item_type
        self.amount = amount
        self.collected = False
