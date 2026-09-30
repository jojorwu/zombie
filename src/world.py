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

class BuildingType:
    RESIDENTIAL = "residential"
    HOSPITAL = "hospital"
    GUN_STORE = "gun_store"
    GAS_STATION = "gas_station"
    POLICE_STATION = "police_station"

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
}

BUILDING_COLORS = {
    BuildingType.RESIDENTIAL: (210, 180, 140),
    BuildingType.HOSPITAL: (220, 240, 255),
    BuildingType.GUN_STORE: (180, 160, 140),
    BuildingType.GAS_STATION: (255, 220, 180),
    BuildingType.POLICE_STATION: (180, 200, 230),
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
}

class World:
    def __init__(self, width=60, height=40, day_length_ticks=600, z_min=-20, z_max=20):
        self.width = max(30, width)
        self.height = max(30, height)
        self.z_min = z_min
        self.z_max = z_max
        self.num_levels = self.z_max - self.z_min + 1  # Total 41 height levels (-20 to +20)
        self.depth = self.num_levels
        self.day_length_ticks = day_length_ticks
        self.current_tick = 0
        self.grid = np.zeros((self.num_levels, self.height, self.width), dtype=int)
        self.building_grid = {}  # (x, y, z) -> BuildingType
        self.buildings = []  # List of building info dicts
        self.generate_world()

    def z_to_idx(self, z):
        return max(0, min(self.num_levels - 1, int(z) - self.z_min))

    def idx_to_z(self, idx):
        return idx + self.z_min

    def generate_world(self):
        # Ground level z=0 defaults to GRASS
        g_idx = self.z_to_idx(0)
        self.grid[g_idx].fill(TileType.GRASS)

        # Above-ground levels default to AIR
        for z in range(1, self.z_max + 1):
            self.grid[self.z_to_idx(z)].fill(TileType.AIR)

        # Underground levels default to UNDERGROUND_WALL
        for z in range(self.z_min, 0):
            self.grid[self.z_to_idx(z)].fill(TileType.UNDERGROUND_WALL)

        # Generate rivers on ground level (z=0)
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

        # Generate forests on ground level (z=0)
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

        # Generate cities, roads, and bridges on ground level (z=0)
        num_cities = random.randint(1, 2)
        building_types = [
            BuildingType.RESIDENTIAL,
            BuildingType.HOSPITAL,
            BuildingType.GUN_STORE,
            BuildingType.GAS_STATION,
            BuildingType.POLICE_STATION
        ]

        for _ in range(num_cities):
            max_x = max(1, self.width - 18)
            max_y = max(1, self.height - 18)
            city_x = random.randint(2, max_x)
            city_y = random.randint(2, max_y)
            city_w = random.randint(14, 18)
            city_h = random.randint(14, 18)

            # Draw main city roads and build BRIDGES over water intersections
            for x in range(city_x, min(self.width, city_x + city_w)):
                for y in range(city_y, min(self.height, city_y + city_h)):
                    if x == city_x or x == city_x + city_w - 1 or y == city_y or y == city_y + city_h - 1 or x % 6 == 0 or y % 6 == 0:
                        if self.grid[g_idx, y, x] == TileType.WATER:
                            self.grid[g_idx, y, x] = TileType.BRIDGE
                        else:
                            self.grid[g_idx, y, x] = TileType.ROAD

            # Construct structured 3D buildings extending from z = -20 to +20
            for bx in range(city_x + 1, min(self.width - 6, city_x + city_w - 6), 6):
                for by in range(city_y + 1, min(self.height - 6, city_y + city_h - 6), 6):
                    bw, bh = 5, 5
                    btype = random.choice(building_types)
                    self.buildings.append({
                        "x": bx, "y": by, "w": bw, "h": bh, "type": btype
                    })

                    # Construct floors from underground (-20) up to upper towers (+20)
                    top_floor = random.randint(3, self.z_max)
                    bottom_floor = random.randint(self.z_min, -1)

                    for z in range(bottom_floor, top_floor + 1):
                        z_idx = self.z_to_idx(z)
                        is_underground = (z < 0)

                        for y in range(by, by + bh):
                            for x in range(bx, bx + bw):
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

                        # Doors & furniture
                        if z == 0:
                            self.grid[z_idx, by + bh - 1, bx + 2] = TileType.DOOR
                            self.grid[z_idx, by + 1, bx + 1] = TileType.FURNITURE
                        elif z < top_floor:
                            self.grid[z_idx, by + 1, bx + 1] = TileType.FURNITURE

                        # STAIRS & LADDERS connecting all vertical levels z in [bottom_floor, top_floor]
                        self.grid[z_idx, by + 3, bx + 3] = TileType.STAIRS if (z % 2 == 0) else TileType.LADDER

    def is_walkable(self, x, y, z=0):
        ix, iy = int(x), int(y)
        z_idx = self.z_to_idx(z)
        if 0 <= z_idx < self.num_levels and 0 <= ix < self.width and 0 <= iy < self.height:
            tile = self.grid[z_idx, iy, ix]
            return TILE_WALKABLE.get(tile, False)
        return False

    def update_day_night(self):
        self.current_tick += 1

    def get_light_level(self):
        progress = (self.current_tick % self.day_length_ticks) / self.day_length_ticks
        sine_val = math.sin(progress * 2 * math.pi)
        light = 0.6 + 0.4 * sine_val
        return max(0.2, min(1.0, light))

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
