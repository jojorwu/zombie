import math
import random
import numpy as np

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
}

class Chunk:
    def __init__(self, chunk_x, chunk_y, size=16):
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.size = size
        self.buildings = []

class ChunkManager:
    def __init__(self, world_width, world_height, chunk_size=16):
        self.chunk_size = chunk_size
        self.num_chunks_x = int(math.ceil(world_width / chunk_size))
        self.num_chunks_y = int(math.ceil(world_height / chunk_size))
        self.chunks = {}
        for cy in range(self.num_chunks_y):
            for cx in range(self.num_chunks_x):
                self.chunks[(cx, cy)] = Chunk(cx, cy, chunk_size)

    def get_chunk_coords(self, world_x, world_y):
        cx = int(world_x) // self.chunk_size
        cy = int(world_y) // self.chunk_size
        return cx, cy

    def get_chunk(self, cx, cy):
        return self.chunks.get((cx, cy))

    def get_chunk_at(self, world_x, world_y):
        cx, cy = self.get_chunk_coords(world_x, world_y)
        return self.get_chunk(cx, cy)

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

        top_floor = random.randint(min(1, self.z_max), max(0, self.z_max))
        bottom_floor = random.randint(min(0, self.z_min), max(0, self.z_min))

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
                self.grid[z_idx, min(self.height - 1, by + 1), min(self.width - 1, bx + 1)] = TileType.FURNITURE
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
                self.grid[z_idx, min(self.height - 1, by + 1), min(self.width - 1, bx + 1)] = TileType.FURNITURE

            # Stairs & Ladders
            self.grid[z_idx, min(self.height - 1, by + 3), min(self.width - 1, bx + 3)] = TileType.STAIRS if (z % 2 == 0) else TileType.LADDER

    def generate_world(self):
        # Base tile setup
        g_idx = self.z_to_idx(0)
        self.grid[g_idx].fill(TileType.GRASS)

        for z in range(1, self.z_max + 1):
            self.grid[self.z_to_idx(z)].fill(TileType.AIR)
        for z in range(self.z_min, 0):
            self.grid[self.z_to_idx(z)].fill(TileType.UNDERGROUND_WALL)

        # ----------------------------------------------------
        # PHASE 1: Roads, Bridges, Rivers, Forests & Parking
        # ----------------------------------------------------
        num_rivers = random.randint(1, 2)
        for _ in range(num_rivers):
            rx = random.randint(4, self.width - 5)
            ry = 0
            for _step in range(self.height):
                if 0 <= rx < self.width and 0 <= ry < self.height:
                    self.grid[g_idx, ry, rx] = TileType.WATER
                    if rx + 1 < self.width:
                        self.grid[g_idx, ry, rx + 1] = TileType.WATER
                ry += 1
                rx += random.choice([-1, 0, 1])

        num_forests = random.randint(4, 7)
        for _ in range(num_forests):
            cx = random.randint(2, self.width - 3)
            cy = random.randint(2, self.height - 3)
            radius = random.randint(3, 6)
            for y in range(max(0, cy - radius), min(self.height, cy + radius + 1)):
                for x in range(max(0, cx - radius), min(self.width, cx + radius + 1)):
                    if (x - cx)**2 + (y - cy)**2 <= radius**2:
                        if self.grid[g_idx, y, x] != TileType.WATER:
                            self.grid[g_idx, y, x] = TileType.FOREST

        # City Main Roads & Bridges
        for x in range(0, self.width):
            for y in range(0, self.height):
                if x % 8 == 0 or y % 8 == 0:
                    if self.grid[g_idx, y, x] == TileType.WATER:
                        self.grid[g_idx, y, x] = TileType.BRIDGE
                    else:
                        self.grid[g_idx, y, x] = TileType.ROAD

        # ----------------------------------------------------
        # PHASE 2: Small Details (Trash Cans, Mailboxes, Crates)
        # ----------------------------------------------------
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.grid[g_idx, y, x] == TileType.ROAD:
                    if random.random() < 0.03 and self.grid[g_idx, y, x + 1] == TileType.GRASS:
                        self.grid[g_idx, y, x + 1] = TileType.TRASH_CAN
                    elif random.random() < 0.03 and self.grid[g_idx, y + 1, x] == TileType.GRASS:
                        self.grid[g_idx, y + 1, x] = TileType.MAILBOX
                    elif random.random() < 0.02 and self.grid[g_idx, y - 1, x] == TileType.GRASS:
                        self.grid[g_idx, y - 1, x] = TileType.CONTAINER_BOX

        # ----------------------------------------------------
        # PHASE 3: Commercial & Specialized Buildings
        # (Supermarket, Stores, Gas Station, Hospital, Police)
        # ----------------------------------------------------
        commercial_types = [
            BuildingType.SUPERMARKET,
            BuildingType.STORE,
            BuildingType.GAS_STATION,
            BuildingType.HOSPITAL,
            BuildingType.POLICE_STATION
        ]

        # Place commercial buildings fitted in chunks
        for cy in range(self.chunk_manager.num_chunks_y):
            for cx in range(self.chunk_manager.num_chunks_x):
                if (cx + cy) % 2 == 0:
                    bx = cx * 16 + 2
                    by = cy * 16 + 2
                    if bx + 6 < self.width and by + 6 < self.height:
                        btype = random.choice(commercial_types)
                        self.build_chunk_building(bx, by, 5, 5, btype)

        # ----------------------------------------------------
        # PHASE 4: Residential & Institutional Buildings
        # (Houses, Dormitories, Schools)
        # ----------------------------------------------------
        residential_types = [
            BuildingType.RESIDENTIAL,
            BuildingType.DORMITORY,
            BuildingType.SCHOOL
        ]

        for cy in range(self.chunk_manager.num_chunks_y):
            for cx in range(self.chunk_manager.num_chunks_x):
                if (cx + cy) % 2 != 0:
                    bx = cx * 16 + 2
                    by = cy * 16 + 2
                    if bx + 6 < self.width and by + 6 < self.height:
                        btype = random.choice(residential_types)
                        self.build_chunk_building(bx, by, 5, 5, btype)

    def is_walkable(self, x, y, z=0):
        ix, iy = int(x), int(y)
        z_idx = self.z_to_idx(z)
        if 0 <= z_idx < self.num_levels and 0 <= ix < self.width and 0 <= iy < self.height:
            tile = self.grid[z_idx, iy, ix]
            return TILE_WALKABLE.get(tile, False)
        return False

    def update_day_night(self):
        self.current_tick += 1

    def get_time_components(self):
        # 1 real hour (108,000 ticks) = 1 month (30 days)
        # 1 in-game day = 3,600 ticks (24 hours)
        # 1 in-game hour = 150 ticks (60 minutes)
        # 1 in-game minute = 2.5 ticks
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

    def get_light_level(self):
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
