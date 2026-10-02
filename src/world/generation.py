import math
import random
import uuid
import numpy as np
from src.world.tiles import TileType, BuildingType, SettlementType
from utils.p_np_math import PolynomialVerifier


class WorldGenerator:
    """Handles terrain generation, settlement classification, winding rivers, dense forest biomes, and multi-floor buildings."""
    __slots__ = ("world", "settlement_type")

    def __init__(self, world, settlement_type: str = SettlementType.STANDARD_CITY):
        self.world = world
        self.settlement_type = settlement_type

    def _place_and_register_furniture(self, x: int, y: int, z: int, tile: int, b_id: str, btype: str) -> None:
        world = self.world
        z_idx = world.z_to_idx(z)
        world.grid[z_idx, y, x] = tile
        if hasattr(world, "furniture_state_manager"):
            world.furniture_state_manager.register_furniture(
                x=x, y=y, z=z, tile_type=tile, building_id=b_id, building_type=btype, durability=100.0
            )

    def build_chunk_building(self, bx: int, by: int, bw: int, bh: int, btype: str) -> None:
        world = self.world
        b_id = f"bldg_{bx}_{by}_{uuid.uuid4().hex[:6]}"
        building_info = {
            "id": b_id, "x": bx, "y": by, "w": bw, "h": bh, "type": btype
        }
        world.buildings.append(building_info)

        # Register building across all chunks that its area overlaps
        world.chunk_manager.register_building(building_info)

        has_basement = False
        if btype in (BuildingType.RESIDENTIAL, BuildingType.POLICE_STATION) and random.random() < 0.20:
            has_basement = True
        elif btype in (BuildingType.WAREHOUSE, BuildingType.GUN_STORE) and random.random() < 0.40:
            has_basement = True

        bottom_floor = -1 if (has_basement and world.z_min <= -1) else 0

        if self.settlement_type == SettlementType.MEGALOPOLIS:
            max_sky_floor = min(world.z_max, 5)
            top_floor = random.randint(2, max_sky_floor) if world.z_max >= 2 else world.z_max
        elif self.settlement_type == SettlementType.VILLAGE:
            top_floor = 0
        else:
            top_floor = min(world.z_max, random.randint(0, max(0, world.z_max)))

        is_house_locked = (random.random() < 0.35)
        building_info["has_basement"] = has_basement
        building_info["top_floor"] = top_floor
        building_info["bottom_floor"] = bottom_floor
        building_info["is_locked"] = is_house_locked

        door_tile = TileType.DOOR_LOCKED if is_house_locked else TileType.DOOR

        for z in range(bottom_floor, top_floor + 1):
            z_idx = world.z_to_idx(z)
            is_underground = (z < 0)

            for y in range(by, min(world.height, by + bh)):
                for x in range(bx, min(world.width, bx + bw)):
                    if is_underground:
                        tile = TileType.UNDERGROUND_WALL if (x == bx or x == bx + bw - 1 or y == by or y == by + bh - 1) else TileType.UNDERGROUND_FLOOR
                    else:
                        tile = TileType.BUILDING_WALL if (x == bx or x == bx + bw - 1 or y == by or y == by + bh - 1) else TileType.BUILDING_FLOOR
                    world.grid[z_idx, y, x] = tile
                    world.building_grid[(x, y, z)] = btype

            if z == 0:
                world.grid[z_idx, min(world.height - 1, by + bh - 1), min(world.width - 1, bx + 2)] = door_tile
                world.grid[z_idx, min(world.height - 1, by), min(world.width - 1, bx + 2)] = TileType.WINDOW

                if has_basement:
                    # Place trapdoor leading down to hidden basement
                    world.grid[z_idx, min(world.height - 1, by + 1), min(world.width - 1, bx + bw - 2)] = TileType.TRAPDOOR

                if btype in (BuildingType.SUPERMARKET, BuildingType.STORE):
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 1), z, TileType.STORE_SHELF, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 2), min(world.height - 1, by + 1), z, TileType.REFRIGERATOR, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 2), z, TileType.STORE_SHELF, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 3), z, TileType.CASH_REGISTER, b_id, btype)
                elif btype in (BuildingType.GUN_STORE, BuildingType.POLICE_STATION):
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 1), z, TileType.GUN_RACK, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 2), min(world.height - 1, by + 1), z, TileType.WEAPON_SAFE, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 2), z, TileType.LOCKER, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 3), min(world.height - 1, by + 2), z, TileType.OFFICE_DESK, b_id, btype)
                elif btype == BuildingType.HOSPITAL:
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 1), z, TileType.MEDICAL_BED, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 2), min(world.height - 1, by + 1), z, TileType.CABINET, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 2), z, TileType.MEDICAL_BED, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 3), min(world.height - 1, by + 2), z, TileType.OFFICE_DESK, b_id, btype)
                elif btype in (BuildingType.SCHOOL, BuildingType.DORMITORY):
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 1), z, TileType.SCHOOL_DESK, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 2), min(world.height - 1, by + 1), z, TileType.BOOKSHELF, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 2), z, TileType.LOCKER, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 3), min(world.height - 1, by + 2), z, TileType.BED, b_id, btype)
                elif btype == BuildingType.GAS_STATION:
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 1), z, TileType.STORE_SHELF, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 2), min(world.height - 1, by + 1), z, TileType.CASH_REGISTER, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 2), z, TileType.REFRIGERATOR, b_id, btype)
                    # Outdoor Gas Pumps
                    if bx + bw < world.width and by + bh < world.height:
                        world.grid[z_idx, min(world.height - 1, by + bh), min(world.width - 1, bx + 1)] = TileType.GAS_PUMP
                        world.grid[z_idx, min(world.height - 1, by + bh), min(world.width - 1, bx + 3)] = TileType.GAS_PUMP
                elif btype == BuildingType.AUTO_REPAIR_SHOP:
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 1), z, TileType.WORKBENCH, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 2), min(world.height - 1, by + 1), z, TileType.LOCKER, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 2), z, TileType.CONTAINER_BOX, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 3), min(world.height - 1, by + 2), z, TileType.FACTORY_RACK, b_id, btype)
                elif btype in (BuildingType.WAREHOUSE, BuildingType.FACTORY):
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 1), z, TileType.FACTORY_RACK, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 2), min(world.height - 1, by + 1), z, TileType.WORKBENCH, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 2), z, TileType.CONTAINER_BOX, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 3), min(world.height - 1, by + 2), z, TileType.LOCKER, b_id, btype)
                else:
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 1), z, TileType.CABINET, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 2), min(world.height - 1, by + 1), z, TileType.REFRIGERATOR, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 2), z, TileType.KITCHEN_COUNTER, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 3), min(world.height - 1, by + 2), z, TileType.SOFA, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 3), min(world.height - 1, by + 1), z, TileType.TV_STAND, b_id, btype)
                    # Bathroom & Appliance Furniture
                    self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 3), z, TileType.TOILET, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 2), min(world.height - 1, by + 3), z, TileType.BATHTUB, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 3), min(world.height - 1, by + 3), z, TileType.SINK, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 4), min(world.height - 1, by + 1), z, TileType.WARDROBE, b_id, btype)
                    self._place_and_register_furniture(min(world.width - 1, bx + 4), min(world.height - 1, by + 2), z, TileType.OVEN, b_id, btype)
                    # Light Switch & Fixture
                    world.grid[z_idx, min(world.height - 1, by + 1), min(world.width - 1, bx + 2)] = TileType.LIGHT_SWITCH
                    world.grid[z_idx, min(world.height - 1, by + 2), min(world.width - 1, bx + 2)] = TileType.LIGHT_FIXTURE

                if bx + bw + 1 < world.width and by + bh < world.height:
                    for px in range(bx + bw, min(world.width, bx + bw + 2)):
                        for py in range(by, min(world.height, by + bh)):
                            if world.grid[z_idx, py, px] in (TileType.GRASS, TileType.ROAD):
                                world.grid[z_idx, py, px] = TileType.PARKING
                    world.grid[z_idx, min(world.height - 1, by + bh - 1), min(world.width - 1, bx + bw)] = TileType.TRASH_CAN
            elif z == top_floor and z > 0:
                for ry in range(by + 1, min(world.height - 1, by + bh - 1)):
                    for rx in range(bx + 1, min(world.width - 1, bx + bw - 1)):
                        world.grid[z_idx, ry, rx] = TileType.ROOF
            elif z < top_floor:
                self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 1), z, TileType.CABINET, b_id, btype)
                self._place_and_register_furniture(min(world.width - 1, bx + 1), min(world.height - 1, by + 2), z, TileType.BED, b_id, btype)

            world.grid[z_idx, min(world.height - 1, by + 3), min(world.width - 1, bx + 3)] = TileType.STAIRS if (z % 2 == 0) else TileType.LADDER

    def generate(self) -> None:
        """High-performance vectorized world generator."""
        world = self.world
        g_idx = world.z_to_idx(0)
        world.grid[g_idx].fill(TileType.GRASS)

        for z in range(1, world.z_max + 1):
            world.grid[world.z_to_idx(z)].fill(TileType.AIR)
        for z in range(world.z_min, 0):
            world.grid[world.z_to_idx(z)].fill(TileType.UNDERGROUND_WALL)

        num_cx = world.chunk_manager.num_chunks_x
        num_cy = world.chunk_manager.num_chunks_y
        center_cx, center_cy = num_cx // 2, num_cy // 2

        chunk_districts = {}
        for cy in range(num_cy):
            for cx in range(num_cx):
                dist = math.hypot(cx - center_cx, cy - center_cy)
                if dist <= max(2, num_cx * 0.25):
                    chunk_districts[(cx, cy)] = "commercial"
                elif cx < num_cx * 0.4 and cy < num_cy * 0.4:
                    chunk_districts[(cx, cy)] = "industrial"
                elif cx >= num_cx * 0.6 and cy >= num_cy * 0.6:
                    chunk_districts[(cx, cy)] = "park"
                else:
                    chunk_districts[(cx, cy)] = "residential"

        # Simplex/Perlin-style organic river and terrain noise generation
        num_rivers = random.randint(1, 2)
        for _ in range(num_rivers):
            rx = float(random.randint(10, world.width - 11))
            ry = 0
            freq_a = random.uniform(0.02, 0.05)
            freq_b = random.uniform(0.08, 0.12)
            amplitude = random.uniform(12.0, 25.0)

            for step_y in range(world.height):
                offset = math.sin(step_y * freq_a) * amplitude + math.cos(step_y * freq_b) * (amplitude * 0.5)
                cur_x = int(rx + offset)
                for w_off in range(-1, 2):
                    tx = cur_x + w_off
                    if 0 <= tx < world.width and 0 <= step_y < world.height:
                        world.grid[g_idx, step_y, tx] = TileType.WATER
                for s_off in (-2, 2):
                    tx = cur_x + s_off
                    if 0 <= tx < world.width and 0 <= step_y < world.height and random.random() < 0.4:
                        world.grid[g_idx, step_y, tx] = TileType.SAND

        # Spawn forest bushes and stones across forest biomes
        for y_f in range(world.height):
            for x_f in range(world.width):
                if world.grid[g_idx, y_f, x_f] in (TileType.FOREST, TileType.FOREST_DENSE, TileType.FOREST_SPARSE):
                    if random.random() < 0.15:
                        world.grid[g_idx, y_f, x_f] = TileType.BUSH

        road_tile = TileType.DIRT_ROAD if self.settlement_type == SettlementType.VILLAGE else TileType.ROAD
        world.grid[g_idx, ::16, :] = TileType.ROAD_HIGHWAY if self.settlement_type != SettlementType.VILLAGE else TileType.DIRT_ROAD
        world.grid[g_idx, :, ::16] = TileType.ROAD_HIGHWAY if self.settlement_type != SettlementType.VILLAGE else TileType.DIRT_ROAD

        road_mask_8_x = (world.grid[g_idx, ::8, :] == TileType.GRASS)
        world.grid[g_idx, ::8, :][road_mask_8_x] = road_tile
        road_mask_8_y = (world.grid[g_idx, :, ::8] == TileType.GRASS)
        world.grid[g_idx, :, ::8][road_mask_8_y] = road_tile

        if self.settlement_type != SettlementType.VILLAGE:
            road_tiles = (world.grid[g_idx] == TileType.ROAD) | (world.grid[g_idx] == TileType.ROAD_HIGHWAY)
            grass_tiles = (world.grid[g_idx] == TileType.GRASS) | (world.grid[g_idx] == TileType.GRASS_DRY)

            pad_r = np.pad(road_tiles[:, 1:], ((0, 0), (0, 1)), mode='constant')
            pad_l = np.pad(road_tiles[:, :-1], ((0, 0), (1, 0)), mode='constant')
            pad_d = np.pad(road_tiles[1:, :], ((0, 1), (0, 0)), mode='constant')
            pad_u = np.pad(road_tiles[:-1, :], ((1, 0), (0, 0)), mode='constant')

            adjacent_grass = grass_tiles & (pad_r | pad_l | pad_d | pad_u)
            world.grid[g_idx, adjacent_grass] = TileType.SIDEWALK

        commercial_types = [BuildingType.SUPERMARKET, BuildingType.STORE, BuildingType.GAS_STATION, BuildingType.HOSPITAL, BuildingType.POLICE_STATION, BuildingType.GUN_STORE]
        residential_types = [BuildingType.RESIDENTIAL, BuildingType.DORMITORY, BuildingType.SCHOOL]
        industrial_types = [BuildingType.WAREHOUSE, BuildingType.FACTORY, BuildingType.GAS_STATION, BuildingType.AUTO_REPAIR_SHOP]

        buildings_to_construct = []
        for cy in range(num_cy):
            for cx in range(num_cx):
                district = chunk_districts[(cx, cy)]
                if district == "park" and self.settlement_type != SettlementType.MEGALOPOLIS:
                    continue

                bx = cx * 16 + 2
                by = cy * 16 + 2
                if bx + 6 < world.width and by + 6 < world.height:
                    if district == "commercial":
                        btype = random.choice(commercial_types)
                    elif district == "industrial":
                        btype = random.choice(industrial_types)
                    else:
                        btype = random.choice(residential_types)
                    buildings_to_construct.append((bx, by, 5, 5, btype))

        for bx, by, bw, bh, btype in buildings_to_construct:
            self.build_chunk_building(bx, by, bw, bh, btype)

        # Spawn Post-Apocalyptic Ruin/Decay Barricades and Blockades
        for _ in range(int(world.width * world.height * 0.0003)):
            rx = random.randint(10, world.width - 10)
            ry = random.randint(10, world.height - 10)
            if world.grid[g_idx, ry, rx] == TileType.ROAD:
                world.grid[g_idx, ry, rx] = TileType.SANDBAG
                if rx + 1 < world.width:
                    world.grid[g_idx, ry, rx + 1] = TileType.BARBED_WIRE

        PolynomialVerifier.verify_spatial_partitioning([(b["x"], b["y"]) for b in world.buildings])
