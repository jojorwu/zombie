import random
from typing import List, Tuple
from src.world import TileType, BuildingType
from src.entities import Vehicle, ResourceItem


class EntitySpawner:
    """Handles scanning walkable world coordinates and contextual spawner routines for entities and loot."""
    __slots__ = ("world", "factory")

    def __init__(self, world, factory):
        self.world = world
        self.factory = factory

    def scan_walkable_coordinates(self) -> Tuple[List[Tuple[int, int, int]], List[Tuple[int, int, int]], List[Tuple[int, int, int]]]:
        """Scans grid for walkable coordinates, parking spots, and trash cans."""
        walkable_coords, parking_coords, trash_coords = [], [], []

        for z in range(self.world.z_min, self.world.z_max + 1):
            z_idx = self.world.z_to_idx(z)
            for y in range(self.world.height):
                for x in range(self.world.width):
                    if self.world.is_walkable(x, y, z):
                        coord = (x, y, z)
                        walkable_coords.append(coord)
                        tile = self.world.grid[z_idx, y, x]
                        if tile == TileType.PARKING:
                            parking_coords.append(coord)
                        elif tile == TileType.TRASH_CAN:
                            trash_coords.append(coord)

        random.shuffle(walkable_coords)
        random.shuffle(parking_coords)
        random.shuffle(trash_coords)
        return walkable_coords, parking_coords, trash_coords

    def spawn_street_corpses_and_loot(self, items_list: list, num_corpses: int = 15) -> None:
        """Spawns lootable dead human corpses on streets and sidewalks containing random gear and ammo."""
        walkable, parking, trash = self.scan_walkable_coordinates()
        street_coords = [(x, y, z) for x, y, z in walkable if z == 0 and self.world.grid[self.world.z_to_idx(z), y, x] in (TileType.ROAD, TileType.SIDEWALK, TileType.CROSSWALK)]
        random.shuffle(street_coords)

        for _ in range(min(num_corpses, len(street_coords))):
            cx, cy, cz = street_coords.pop()
            corpse_loot = random.choice([
                ResourceItem.PISTOL_AMMO, ResourceItem.SHOTGUN_SHELLS, ResourceItem.RIFLE_AMMO,
                ResourceItem.CANNED_FOOD, ResourceItem.WATER_BOTTLE, ResourceItem.KNIFE,
                ResourceItem.MONEY, ResourceItem.CLOTHES, ResourceItem.MEDKIT
            ])
            # Container item representing lootable human corpse
            items_list.append(self.factory.create_item(cx + 0.5, cy + 0.5, ResourceItem.CRATE, amount=1, z=cz, contents={corpse_loot: random.randint(1, 3)}))

    def spawn_building_loot(self, items_list: list) -> None:
        """Spawns contextual loot across floors and basements in buildings."""
        for b in self.world.buildings:
            bx, by, btype = b["x"], b["y"], b["type"]
            possible_loot = [ResourceItem.FOOD, ResourceItem.WATER, ResourceItem.CANNED_BEANS, ResourceItem.CHOCOLATE]

            if btype in (BuildingType.GUN_STORE, BuildingType.POLICE_STATION):
                possible_loot = [
                    ResourceItem.PISTOL, ResourceItem.SHOTGUN, ResourceItem.RIFLE,
                    ResourceItem.MAGNUM, ResourceItem.SMG, ResourceItem.SNIPER_RIFLE, ResourceItem.ASSAULT_RIFLE, ResourceItem.CROSSBOW,
                    ResourceItem.PISTOL_AMMO, ResourceItem.SHOTGUN_SHELLS, ResourceItem.RIFLE_AMMO, ResourceItem.MAGNUM_AMMO, ResourceItem.SNIPER_AMMO, ResourceItem.BOLTS,
                    ResourceItem.KATANA, ResourceItem.MACHETE, ResourceItem.CROWBAR, ResourceItem.KNIFE
                ]
            elif btype == BuildingType.HOSPITAL:
                possible_loot = [ResourceItem.MEDKIT, ResourceItem.WATER_BOTTLE]
            elif btype == BuildingType.GAS_STATION:
                possible_loot = [ResourceItem.FUEL, ResourceItem.CROWBAR, ResourceItem.PIPE, ResourceItem.CANNED_FOOD, ResourceItem.WATER_BOTTLE]
            elif btype in (BuildingType.SUPERMARKET, BuildingType.STORE):
                possible_loot = [
                    ResourceItem.CANNED_FOOD, ResourceItem.CANNED_BEANS, ResourceItem.CANNED_TUNA, ResourceItem.CHOCOLATE,
                    ResourceItem.CEREAL, ResourceItem.CHEESE, ResourceItem.BREAD, ResourceItem.APPLE, ResourceItem.MRE,
                    ResourceItem.WATER_BOTTLE, ResourceItem.CAN_OPENER
                ]
            elif btype in (BuildingType.RESIDENTIAL, BuildingType.DORMITORY, BuildingType.SCHOOL):
                possible_loot = [
                    ResourceItem.BREAD, ResourceItem.APPLE, ResourceItem.MEAT, ResourceItem.STEAK, ResourceItem.POTATO, ResourceItem.STEW,
                    ResourceItem.CHEF_KNIFE, ResourceItem.FRYING_PAN, ResourceItem.POT, ResourceItem.KATANA,
                    ResourceItem.CAN_OPENER, ResourceItem.WATER_BOTTLE, ResourceItem.CUTTING_BOARD,
                    ResourceItem.BASEBALL_BAT, ResourceItem.AXE, ResourceItem.PIPE
                ]
            elif btype in (BuildingType.WAREHOUSE, BuildingType.FACTORY):
                possible_loot = [ResourceItem.AXE, ResourceItem.SLEDGEHAMMER, ResourceItem.CROWBAR, ResourceItem.SPEAR, ResourceItem.WOOD, ResourceItem.METAL, ResourceItem.FUEL]

            b_bottom = b.get("bottom_floor", 0)
            b_top = b.get("top_floor", 0)

            for floor_z in range(b_bottom, b_top + 1):
                lx, ly = bx + 2, by + 1
                if floor_z < 0:
                    if btype in (BuildingType.GUN_STORE, BuildingType.POLICE_STATION, BuildingType.RESIDENTIAL):
                        base_loot = [
                            ResourceItem.PISTOL, ResourceItem.SHOTGUN, ResourceItem.RIFLE,
                            ResourceItem.SNIPER_RIFLE, ResourceItem.ASSAULT_RIFLE, ResourceItem.MAGNUM,
                            ResourceItem.PISTOL_AMMO, ResourceItem.RIFLE_AMMO, ResourceItem.SHOTGUN_SHELLS,
                            ResourceItem.KATANA, ResourceItem.MACHETE, ResourceItem.AXE
                        ]
                    elif btype in (BuildingType.WAREHOUSE, BuildingType.FACTORY):
                        base_loot = [ResourceItem.FUEL, ResourceItem.SLEDGEHAMMER, ResourceItem.AXE, ResourceItem.CROWBAR, ResourceItem.METAL]
                    else:
                        base_loot = [ResourceItem.CANNED_FOOD, ResourceItem.CANNED_TUNA, ResourceItem.MRE, ResourceItem.MEDKIT, ResourceItem.CAN_OPENER, ResourceItem.WATER_BOTTLE]
                    loot_type = random.choice(base_loot)
                else:
                    loot_type = random.choice(possible_loot)

                amt = random.randint(2, 6) if "ammo" in loot_type or loot_type == ResourceItem.BOLTS else random.randint(1, 2)
                items_list.append(self.factory.create_item(lx + 0.5, ly + 0.5, loot_type, amount=amt, z=floor_z))
