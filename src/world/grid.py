import math
import random
import numpy as np
from src.world.chunk import ChunkManager
from src.world.weather import WeatherManager
from src.world.lighting import DynamicLight

class TileType:
    GRASS = 0
    ROAD = 1
    BUILDING_WALL = 2
    BUILDING_FLOOR = 3
    WATER = 4
    FOREST = 5
    FURNITURE = 6
    DOOR = 7
    STAIRS = 8
    AIR = 9
    BRIDGE = 10
    UNDERGROUND_WALL = 11
    UNDERGROUND_FLOOR = 12
    LADDER = 13
    PARKING = 14
    ROOF = 15
    TRASH_CAN = 16
    CONTAINER_BOX = 17
    MAILBOX = 18
    # New realistic road and terrain tile variants
    ROAD_HIGHWAY = 19
    SIDEWALK = 20
    CROSSWALK = 21
    DIRT_ROAD = 22
    FOREST_DENSE = 23
    FOREST_SPARSE = 24
    DEAD_TREE = 25
    GRASS_DENSE = 26
    GRASS_DRY = 27
    SAND = 28

    # Specific Furniture Types
    TABLE = 29
    CHAIR = 30
    SOFA = 31
    BED = 32
    CABINET = 33
    REFRIGERATOR = 34
    KITCHEN_COUNTER = 35


class BuildingType:
    SUPERMARKET = "supermarket"
    STORE = "store"
    HOSPITAL = "hospital"
    POLICE_STATION = "police_station"
    GAS_STATION = "gas_station"
    GUN_STORE = "gun_store"
    RESIDENTIAL = "residential"
    DORMITORY = "dormitory"
    SCHOOL = "school"
    WAREHOUSE = "warehouse"
    FACTORY = "factory"


TILE_COLORS = {
    TileType.GRASS: (34, 139, 34),
    TileType.ROAD: (105, 105, 105),
    TileType.BUILDING_WALL: (100, 50, 20),
    TileType.BUILDING_FLOOR: (210, 180, 140),
    TileType.WATER: (65, 105, 225),
    TileType.FOREST: (0, 100, 0),
    TileType.FURNITURE: (139, 115, 85),
    TileType.DOOR: (160, 82, 45),
    TileType.STAIRS: (255, 140, 0),
    TileType.AIR: (15, 15, 25),
    TileType.BRIDGE: (139, 90, 43),
    TileType.UNDERGROUND_WALL: (50, 50, 55),
    TileType.UNDERGROUND_FLOOR: (90, 90, 100),
    TileType.LADDER: (218, 165, 32),
    TileType.PARKING: (70, 70, 75),
    TileType.ROOF: (160, 140, 120),
    TileType.TRASH_CAN: (80, 90, 80),
    TileType.CONTAINER_BOX: (180, 130, 70),
    TileType.MAILBOX: (70, 130, 180),
    # Visual colors for new tile variants
    TileType.ROAD_HIGHWAY: (50, 50, 55),
    TileType.SIDEWALK: (180, 180, 185),
    TileType.CROSSWALK: (220, 220, 220),
    TileType.DIRT_ROAD: (139, 105, 20),
    TileType.FOREST_DENSE: (0, 70, 0),
    TileType.FOREST_SPARSE: (46, 139, 87),
    TileType.DEAD_TREE: (100, 80, 60),
    TileType.GRASS_DENSE: (0, 110, 0),
    TileType.GRASS_DRY: (189, 183, 107),
    TileType.SAND: (238, 214, 139),
    # Furniture visual colors
    TileType.TABLE: (160, 120, 80),
    TileType.CHAIR: (180, 140, 90),
    TileType.SOFA: (100, 60, 140),
    TileType.BED: (70, 110, 160),
    TileType.CABINET: (120, 80, 40),
    TileType.REFRIGERATOR: (220, 225, 230),
    TileType.KITCHEN_COUNTER: (150, 150, 150),
}

BUILDING_COLORS = {
    BuildingType.SUPERMARKET: (255, 215, 0),
    BuildingType.STORE: (240, 230, 140),
    BuildingType.HOSPITAL: (220, 240, 255),
    BuildingType.POLICE_STATION: (180, 200, 230),
    BuildingType.GAS_STATION: (255, 220, 180),
    BuildingType.GUN_STORE: (180, 160, 140),
    BuildingType.RESIDENTIAL: (210, 180, 140),
    BuildingType.DORMITORY: (190, 160, 120),
    BuildingType.SCHOOL: (200, 190, 170),
    BuildingType.WAREHOUSE: (120, 110, 100),
    BuildingType.FACTORY: (140, 130, 110),
}

TILE_WALKABLE = {
    TileType.GRASS: True,
    TileType.ROAD: True,
    TileType.BUILDING_WALL: False,
    TileType.BUILDING_FLOOR: True,
    TileType.WATER: False,
    TileType.FOREST: True,
    TileType.FURNITURE: False,
    TileType.DOOR: True,
    TileType.STAIRS: True,
    TileType.AIR: False,
    TileType.BRIDGE: True,
    TileType.UNDERGROUND_WALL: False,
    TileType.UNDERGROUND_FLOOR: True,
    TileType.LADDER: True,
    TileType.PARKING: True,
    TileType.ROOF: True,
    TileType.TRASH_CAN: True,
    TileType.CONTAINER_BOX: True,
    TileType.MAILBOX: True,
    TileType.ROAD_HIGHWAY: True,
    TileType.SIDEWALK: True,
    TileType.CROSSWALK: True,
    TileType.DIRT_ROAD: True,
    TileType.FOREST_DENSE: True,
    TileType.FOREST_SPARSE: True,
    TileType.DEAD_TREE: False,
    TileType.GRASS_DENSE: True,
    TileType.GRASS_DRY: True,
    TileType.SAND: True,
    # Furniture Walkability
    TileType.TABLE: False,
    TileType.CHAIR: True,
    TileType.SOFA: False,
    TileType.BED: False,
    TileType.CABINET: False,
    TileType.REFRIGERATOR: False,
    TileType.KITCHEN_COUNTER: False,
}

TILE_SPEED_MODIFIERS = {
    TileType.ROAD_HIGHWAY: 1.25,
    TileType.ROAD: 1.1,
    TileType.CROSSWALK: 1.1,
    TileType.SIDEWALK: 1.05,
    TileType.PARKING: 1.05,
    TileType.BRIDGE: 1.0,
    TileType.BUILDING_FLOOR: 1.0,
    TileType.UNDERGROUND_FLOOR: 1.0,
    TileType.GRASS: 0.95,
    TileType.GRASS_DRY: 0.9,
    TileType.DIRT_ROAD: 0.9,
    TileType.FOREST_SPARSE: 0.85,
    TileType.SAND: 0.8,
    TileType.GRASS_DENSE: 0.75,
    TileType.FOREST: 0.75,
    TileType.FOREST_DENSE: 0.6,
}


class World:
    def __init__(self, width=1000, height=1000, day_length_ticks=3600, z_min=0, z_max=2,
                 electricity_cutoff_day=7, water_cutoff_day=14, electricity_enabled=True, water_enabled=True):
        self.width = max(30, width)
        self.height = max(30, height)
        self.z_min = z_min
        self.z_max = z_max
        self.num_levels = self.z_max - self.z_min + 1
        self.depth = self.num_levels
        self.day_length_ticks = day_length_ticks
        self.electricity_cutoff_day = electricity_cutoff_day
        self.water_cutoff_day = water_cutoff_day
        self.electricity_enabled = electricity_enabled
        self.water_enabled = water_enabled
        self.current_tick = 0
        self.chunk_manager = ChunkManager(self.width, self.height, chunk_size=16)
        self.weather = WeatherManager(self.width, self.height)
        self.dynamic_lights = []
        self.grid = np.zeros((self.num_levels, self.height, self.width), dtype=int)
        self.building_grid = {}  # (x, y, z) -> BuildingType
        self.buildings = []  # List of building info dicts
        self.generate_world()

    def z_to_idx(self, z):
        return max(0, min(self.num_levels - 1, int(z) - self.z_min))

    def idx_to_z(self, idx):
        return idx + self.z_min

    def build_chunk_building(self, bx, by, bw, bh, btype):
        """Constructs a building fitted wholly inside its chunk."""
        self.buildings.append({
            "x": bx, "y": by, "w": bw, "h": bh, "type": btype
        })
        chunk = self.chunk_manager.get_chunk_at(bx, by)
        if chunk:
            chunk.buildings.append(self.buildings[-1])

        has_basement = False
        if btype in (BuildingType.RESIDENTIAL, BuildingType.POLICE_STATION) and random.random() < 0.20:
            has_basement = True
        elif btype in (BuildingType.WAREHOUSE, BuildingType.GUN_STORE) and random.random() < 0.40:
            has_basement = True

        bottom_floor = -1 if (has_basement and self.z_min <= -1) else 0

        if btype in (BuildingType.HOSPITAL, BuildingType.POLICE_STATION, BuildingType.DORMITORY, BuildingType.SCHOOL):
            top_floor = min(self.z_max, max(1, random.randint(1, max(1, self.z_max))))
        else:
            top_floor = min(self.z_max, random.randint(0, max(0, self.z_max)))

        self.buildings[-1]["has_basement"] = has_basement
        self.buildings[-1]["top_floor"] = top_floor
        self.buildings[-1]["bottom_floor"] = bottom_floor

        for z in range(bottom_floor, top_floor + 1):
            z_idx = self.z_to_idx(z)
            is_underground = (z < 0)

            for y in range(by, min(self.height, by + bh)):
                for x in range(bx, min(self.width, bx + bw)):
                    if is_underground:
                        if x == bx or x == bx + bw - 1 or y == by or y == by + bh - 1:
                            self.grid[z_idx, y, x] = TileType.UNDERGROUND_WALL
                        else:
                            self.grid[z_idx, y, x] = TileType.UNDERGROUND_FLOOR
                    else:
                        if x == bx or x == bx + bw - 1 or y == by or y == by + bh - 1:
                            self.grid[z_idx, y, x] = TileType.BUILDING_WALL
                        else:
                            self.grid[z_idx, y, x] = TileType.BUILDING_FLOOR
                    self.building_grid[(x, y, z)] = btype

            if z == 0:
                self.grid[z_idx, min(self.height - 1, by + bh - 1), min(self.width - 1, bx + 2)] = TileType.DOOR
                self.grid[z_idx, min(self.height - 1, by + 1), min(self.width - 1, bx + 1)] = TileType.CABINET
                self.grid[z_idx, min(self.height - 1, by + 1), min(self.width - 1, bx + 2)] = TileType.REFRIGERATOR if btype in (BuildingType.RESIDENTIAL, BuildingType.SUPERMARKET) else TileType.TABLE
                self.grid[z_idx, min(self.height - 1, by + 2), min(self.width - 1, bx + 1)] = TileType.KITCHEN_COUNTER if btype == BuildingType.RESIDENTIAL else TileType.SOFA
                self.grid[z_idx, min(self.height - 1, by + 2), min(self.width - 1, bx + 3)] = TileType.BED if btype in (BuildingType.RESIDENTIAL, BuildingType.DORMITORY) else TileType.CHAIR

                if bx + bw + 1 < self.width and by + bh < self.height:
                    for px in range(bx + bw, min(self.width, bx + bw + 2)):
                        for py in range(by, min(self.height, by + bh)):
                            if self.grid[z_idx, py, px] in (TileType.GRASS, TileType.ROAD):
                                self.grid[z_idx, py, px] = TileType.PARKING
                    self.grid[z_idx, min(self.height - 1, by + bh - 1), min(self.width - 1, bx + bw)] = TileType.TRASH_CAN
            elif z == top_floor and z > 0:
                for ry in range(by + 1, min(self.height - 1, by + bh - 1)):
                    for rx in range(bx + 1, min(self.width - 1, bx + bw - 1)):
                        self.grid[z_idx, ry, rx] = TileType.ROOF
            elif z < top_floor:
                self.grid[z_idx, min(self.height - 1, by + 1), min(self.width - 1, bx + 1)] = TileType.CABINET
                self.grid[z_idx, min(self.height - 1, by + 2), min(self.width - 1, bx + 1)] = TileType.BED

            self.grid[z_idx, min(self.height - 1, by + 3), min(self.width - 1, bx + 3)] = TileType.STAIRS if (z % 2 == 0) else TileType.LADDER

    def generate_world(self):
        g_idx = self.z_to_idx(0)
        self.grid[g_idx].fill(TileType.GRASS)

        for z in range(1, self.z_max + 1):
            self.grid[self.z_to_idx(z)].fill(TileType.AIR)
        for z in range(self.z_min, 0):
            self.grid[self.z_to_idx(z)].fill(TileType.UNDERGROUND_WALL)

        chunk_districts = {}
        center_cx = self.chunk_manager.num_chunks_x // 2
        center_cy = self.chunk_manager.num_chunks_y // 2

        for cy in range(self.chunk_manager.num_chunks_y):
            for cx in range(self.chunk_manager.num_chunks_x):
                dist_from_center = math.hypot(cx - center_cx, cy - center_cy)
                if dist_from_center <= max(2, self.chunk_manager.num_chunks_x * 0.25):
                    chunk_districts[(cx, cy)] = "commercial"
                elif cx < self.chunk_manager.num_chunks_x * 0.4 and cy < self.chunk_manager.num_chunks_y * 0.4:
                    chunk_districts[(cx, cy)] = "industrial"
                elif cx >= self.chunk_manager.num_chunks_x * 0.6 and cy >= self.chunk_manager.num_chunks_y * 0.6:
                    chunk_districts[(cx, cy)] = "park"
                else:
                    chunk_districts[(cx, cy)] = "residential"

        num_rivers = random.randint(1, 2)
        for _ in range(num_rivers):
            rx = random.randint(4, self.width - 5)
            ry = 0
            for _step in range(self.height):
                if 0 <= rx < self.width and 0 <= ry < self.height:
                    self.grid[g_idx, ry, rx] = TileType.WATER
                    if rx + 1 < self.width:
                        self.grid[g_idx, ry, rx + 1] = TileType.WATER
                    if rx - 1 >= 0 and random.random() < 0.3:
                        self.grid[g_idx, ry, rx - 1] = TileType.SAND
                    if rx + 2 < self.width and random.random() < 0.3:
                        self.grid[g_idx, ry, rx + 2] = TileType.SAND
                ry += 1
                rx += random.choice([-1, 0, 1])

        for cy in range(self.chunk_manager.num_chunks_y):
            for cx in range(self.chunk_manager.num_chunks_x):
                district = chunk_districts[(cx, cy)]
                base_x, base_y = cx * 16, cy * 16
                if district == "park":
                    for y in range(base_y, min(self.height, base_y + 16)):
                        for x in range(base_x, min(self.width, base_x + 16)):
                            if self.grid[g_idx, y, x] == TileType.GRASS:
                                r = random.random()
                                if r < 0.35:
                                    self.grid[g_idx, y, x] = TileType.FOREST_DENSE
                                elif r < 0.65:
                                    self.grid[g_idx, y, x] = TileType.FOREST_SPARSE
                                elif r < 0.8:
                                    self.grid[g_idx, y, x] = TileType.GRASS_DENSE
                                elif r < 0.88:
                                    self.grid[g_idx, y, x] = TileType.DEAD_TREE
                elif district == "residential":
                    for y in range(base_y, min(self.height, base_y + 16)):
                        for x in range(base_x, min(self.width, base_x + 16)):
                            if self.grid[g_idx, y, x] == TileType.GRASS and random.random() < 0.15:
                                self.grid[g_idx, y, x] = TileType.GRASS_DRY

        for x in range(0, self.width):
            for y in range(0, self.height):
                cx, cy = x // 16, y // 16
                district = chunk_districts.get((cx, cy), "residential")

                if x % 16 == 0 or y % 16 == 0:
                    if self.grid[g_idx, y, x] == TileType.WATER:
                        self.grid[g_idx, y, x] = TileType.BRIDGE
                    elif district == "park" or district == "industrial":
                        self.grid[g_idx, y, x] = TileType.DIRT_ROAD if district == "industrial" else TileType.ROAD
                    else:
                        self.grid[g_idx, y, x] = TileType.ROAD_HIGHWAY
                elif x % 8 == 0 or y % 8 == 0:
                    if self.grid[g_idx, y, x] == TileType.WATER:
                        self.grid[g_idx, y, x] = TileType.BRIDGE
                    else:
                        self.grid[g_idx, y, x] = TileType.ROAD

        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.grid[g_idx, y, x] in (TileType.ROAD, TileType.ROAD_HIGHWAY):
                    if (x % 8 == 0 and y % 16 == 0) or (x % 16 == 0 and y % 8 == 0):
                        self.grid[g_idx, y, x] = TileType.CROSSWALK

                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        adj_x, adj_y = x + dx, y + dy
                        if 0 <= adj_x < self.width and 0 <= adj_y < self.height:
                            if self.grid[g_idx, adj_y, adj_x] in (TileType.GRASS, TileType.GRASS_DRY):
                                self.grid[g_idx, adj_y, adj_x] = TileType.SIDEWALK

        commercial_types = [BuildingType.SUPERMARKET, BuildingType.STORE, BuildingType.GAS_STATION, BuildingType.HOSPITAL, BuildingType.POLICE_STATION, BuildingType.GUN_STORE]
        residential_types = [BuildingType.RESIDENTIAL, BuildingType.DORMITORY, BuildingType.SCHOOL]
        industrial_types = [BuildingType.WAREHOUSE, BuildingType.FACTORY, BuildingType.GAS_STATION]

        for cy in range(self.chunk_manager.num_chunks_y):
            for cx in range(self.chunk_manager.num_chunks_x):
                district = chunk_districts[(cx, cy)]
                if district == "park":
                    continue

                bx = cx * 16 + 2
                by = cy * 16 + 2
                if bx + 6 < self.width and by + 6 < self.height:
                    if district == "commercial":
                        btype = random.choice(commercial_types)
                    elif district == "industrial":
                        btype = random.choice(industrial_types)
                    else:
                        btype = random.choice(residential_types)

                    self.build_chunk_building(bx, by, 5, 5, btype)

        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.grid[g_idx, y, x] in (TileType.ROAD, TileType.SIDEWALK):
                    if random.random() < 0.02 and self.grid[g_idx, y, x + 1] == TileType.SIDEWALK:
                        self.grid[g_idx, y, x + 1] = TileType.TRASH_CAN
                    elif random.random() < 0.02 and self.grid[g_idx, y + 1, x] == TileType.SIDEWALK:
                        self.grid[g_idx, y + 1, x] = TileType.MAILBOX
                    elif random.random() < 0.015 and self.grid[g_idx, y - 1, x] == TileType.SIDEWALK:
                        self.grid[g_idx, y - 1, x] = TileType.CONTAINER_BOX

    def is_walkable(self, x, y, z=0):
        ix, iy = int(x), int(y)
        z_idx = self.z_to_idx(z)
        if 0 <= z_idx < self.num_levels and 0 <= ix < self.width and 0 <= iy < self.height:
            tile = self.grid[z_idx, iy, ix]
            return TILE_WALKABLE.get(tile, False)
        return False

    def get_tile_speed_modifier(self, x, y, z=0):
        ix, iy = int(x), int(y)
        z_idx = self.z_to_idx(z)
        if 0 <= z_idx < self.num_levels and 0 <= ix < self.width and 0 <= iy < self.height:
            tile = self.grid[z_idx, iy, ix]
            return TILE_SPEED_MODIFIERS.get(tile, 1.0)
        return 1.0

    def update_day_night(self):
        self.current_tick += 1
        self.weather.update(self.current_tick)

        for dl in self.dynamic_lights:
            dl.update()
        self.dynamic_lights = [dl for dl in self.dynamic_lights if dl.lifetime > 0]

        if self.weather.rain_front and random.random() < 0.03:
            rf = self.weather.rain_front
            lx = rf["x"] + random.uniform(0, 100)
            ly = rf["y"] + random.uniform(0, 100)
            self.dynamic_lights.append(DynamicLight(lx, ly, z=0, radius=25.0, color=(200, 220, 255), intensity=2.0, lifetime=2))

    def get_time_components(self):
        total_mins = self.current_tick / 2.5
        minute = int(total_mins % 60)
        total_hours = total_mins / 60.0
        hour = int(total_hours % 24)
        total_days = total_hours / 24.0
        day = int(total_days % 30) + 1
        total_months = total_days / 30.0
        month = int(total_months % 12) + 1
        year = int(total_months / 12) + 1
        return year, month, day, hour, minute

    def get_time_string(self):
        y, m, d, hh, mm = self.get_time_components()
        return f"Y{y}-M{m:02d}-D{d:02d} {hh:02d}:{mm:02d}"

    def is_power_out(self):
        if not self.electricity_enabled:
            return True
        y, m, d, hh, mm = self.get_time_components()
        current_day_total = (y - 1) * 360 + (m - 1) * 30 + d
        return current_day_total >= self.electricity_cutoff_day

    def is_water_out(self):
        if not self.water_enabled:
            return True
        y, m, d, hh, mm = self.get_time_components()
        current_day_total = (y - 1) * 360 + (m - 1) * 30 + d
        return current_day_total >= self.water_cutoff_day

    def get_light_level(self, z=0):
        if z < 0:
            return 0.08 if not self.is_power_out() else 0.03
        y, m, d, hh, mm = self.get_time_components()
        progress = (hh * 60 + mm) / 1440.0
        sine_val = math.sin((progress - 0.25) * 2 * math.pi)
        light = 0.55 + 0.45 * sine_val
        if self.is_power_out():
            light *= 0.7
        return max(0.12, min(1.0, light))

    def compute_fog_of_war(self, x, y, radius=8, z=0):
        ix, iy = int(x), int(y)
        z_idx = self.z_to_idx(z)
        visible_tiles = set()
        visible_tiles.add((ix, iy))

        num_rays = 36
        for i in range(num_rays):
            angle = i * (2 * math.pi / num_rays)
            dx = math.cos(angle)
            dy = math.sin(angle)
            cx, cy = float(x), float(y)
            for _step in range(int(radius)):
                cx += dx
                cy += dy
                tx, ty = int(cx), int(cy)
                if not (0 <= tx < self.width and 0 <= ty < self.height):
                    break
                visible_tiles.add((tx, ty))
                t = self.grid[z_idx, ty, tx]
                if t in (TileType.BUILDING_WALL, TileType.UNDERGROUND_WALL, TileType.FURNITURE, TileType.AIR):
                    break
        return visible_tiles
