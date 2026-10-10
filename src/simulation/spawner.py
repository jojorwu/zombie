import random
import numpy as np
from typing import List, Tuple
from src.world import TileType, BuildingType, TILE_WALKABLE
from src.entities import Vehicle, ResourceItem

_WALKABLE_TILE_LIST = [t for t, w in TILE_WALKABLE.items() if w]


class EntitySpawner:
    """Handles scanning walkable world coordinates and contextual spawner routines for entities and loot."""
    __slots__ = ("world", "factory")

    def __init__(self, world, factory):
        self.world = world
        self.factory = factory

    def scan_walkable_coordinates(self) -> Tuple[List[Tuple[int, int, int]], List[Tuple[int, int, int]], List[Tuple[int, int, int]]]:
        """Scans grid for walkable coordinates, parking spots, and trash cans using fast NumPy lookups."""
        walkable_coords, parking_coords, trash_coords = [], [], []

        # 1. Vectorized lookup for Z=0 ground_grid
        ground = self.world.ground_grid
        walkable_mask = np.isin(ground, _WALKABLE_TILE_LIST)
        ys, xs = np.where(walkable_mask)
        for y, x in zip(ys, xs):
            walkable_coords.append((int(x), int(y), 0))

        py, px = np.where(ground == TileType.PARKING)
        for y, x in zip(py, px):
            parking_coords.append((int(x), int(y), 0))

        ty, tx = np.where(ground == TileType.TRASH_CAN)
        for y, x in zip(ty, tx):
            trash_coords.append((int(x), int(y), 0))

        # 2. Fast sparse Hash Map lookup for non-zero Z levels
        for (z_idx, y, x), tile in self.world.sparse_z_grid.items():
            z = self.world.idx_to_z(z_idx)
            if TILE_WALKABLE.get(tile, False):
                coord = (x, y, z)
                walkable_coords.append(coord)
                if tile == TileType.PARKING:
                    parking_coords.append(coord)
                elif tile == TileType.TRASH_CAN:
                    trash_coords.append(coord)

        random.shuffle(walkable_coords)
        random.shuffle(parking_coords)
        random.shuffle(trash_coords)
        return walkable_coords, parking_coords, trash_coords

    def spawn_street_corpses_and_loot(self, items_list: list, walkable_coords: list = None, num_corpses: int = 15) -> None:
        """Spawns lootable dead human corpses on streets and sidewalks containing random gear and ammo."""
        if walkable_coords is None:
            walkable_coords, _, _ = self.scan_walkable_coordinates()

        street_coords = [
            (x, y, z) for x, y, z in walkable_coords
            if z == 0 and self.world.ground_grid[y, x] in (TileType.ROAD, TileType.SIDEWALK, TileType.CROSSWALK)
        ]
        random.shuffle(street_coords)

        for _ in range(min(num_corpses, len(street_coords))):
            cx, cy, cz = street_coords.pop()
            corpse_loot = random.choice([
                ResourceItem.PISTOL_AMMO, ResourceItem.SHOTGUN_SHELLS, ResourceItem.RIFLE_AMMO,
                ResourceItem.CANNED_FOOD, ResourceItem.WATER_BOTTLE, ResourceItem.KNIFE,
                ResourceItem.MONEY, ResourceItem.CLOTHES, ResourceItem.MEDKIT
            ])
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
