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
}

class World:
    def __init__(self, width=60, height=40, day_length_ticks=600, num_levels=3):
        self.width = max(30, width)
        self.height = max(30, height)
        self.num_levels = max(1, num_levels)  # World height = 3 levels (z=0, z=1, z=2)
        self.depth = self.num_levels
        self.day_length_ticks = day_length_ticks
        self.current_tick = 0
        self.grid = np.zeros((self.num_levels, self.height, self.width), dtype=int)
        self.building_grid = {}  # (x, y, z) -> BuildingType
        self.buildings = []  # List of building info dicts
        self.generate_world()

    def generate_world(self):
        # Level 0 is Ground level
        self.grid[0].fill(TileType.GRASS)
        # Upper levels (Level 1, Level 2) default to AIR
        for z in range(1, self.num_levels):
            self.grid[z].fill(TileType.AIR)

        # Generate forests on level 0
        num_forests = random.randint(3, 6)
        for _ in range(num_forests):
            cx = random.randint(2, self.width - 3)
            cy = random.randint(2, self.height - 3)
            radius = random.randint(2, 5)
            for y in range(max(0, cy - radius), min(self.height, cy + radius + 1)):
                for x in range(max(0, cx - radius), min(self.width, cx + radius + 1)):
                    if (x - cx)**2 + (y - cy)**2 <= radius**2:
                        self.grid[0, y, x] = TileType.FOREST

        # Generate rivers on level 0
        num_rivers = random.randint(1, 2)
        for _ in range(num_rivers):
            rx = random.randint(0, self.width - 1)
            ry = 0
            for _step in range(self.height):
                if 0 <= rx < self.width and 0 <= ry < self.height:
                    self.grid[0, ry, rx] = TileType.WATER
                    if rx + 1 < self.width:
                        self.grid[0, ry, rx + 1] = TileType.WATER
                ry += 1
                rx += random.choice([-1, 0, 1])

        # Generate cities and multi-level buildings across height levels z=0,1,2
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

            # Draw main city roads on ground level z=0
            for x in range(city_x, min(self.width, city_x + city_w)):
                for y in range(city_y, min(self.height, city_y + city_h)):
                    if x == city_x or x == city_x + city_w - 1 or y == city_y or y == city_y + city_h - 1 or x % 6 == 0 or y % 6 == 0:
                        self.grid[0, y, x] = TileType.ROAD

            # Construct structured detailed 3D multi-level buildings
            for bx in range(city_x + 1, min(self.width - 6, city_x + city_w - 6), 6):
                for by in range(city_y + 1, min(self.height - 6, city_y + city_h - 6), 6):
                    bw, bh = 5, 5
                    btype = random.choice(building_types)
                    self.buildings.append({
                        "x": bx, "y": by, "w": bw, "h": bh, "type": btype
                    })

                    # Construct Floors across 3 height levels (z=0, z=1, z=2)
                    for z in range(min(3, self.num_levels)):
                        for y in range(by, by + bh):
                            for x in range(bx, bx + bw):
                                if x == bx or x == bx + bw - 1 or y == by or y == by + bh - 1:
                                    self.grid[z, y, x] = TileType.BUILDING_WALL
                                else:
                                    self.grid[z, y, x] = TileType.BUILDING_FLOOR
                                self.building_grid[(x, y, z)] = btype

                        # Internal partitions
                        if z < 2:
                            for x in range(bx + 1, bx + bw - 1):
                                self.grid[z, by + 2, x] = TileType.BUILDING_WALL
                            self.grid[z, by + bh - 1, bx + 2] = TileType.DOOR
                            self.grid[z, by + 2, bx + 2] = TileType.DOOR
                            self.grid[z, by + 1, bx + 1] = TileType.FURNITURE
                        else:
                            # Level 2 Rooftop terrace
                            self.grid[z, by + 2, bx + 2] = TileType.BUILDING_FLOOR

                    # Add STAIRS connecting level 0 <-> level 1 and level 1 <-> level 2
                    if self.num_levels >= 2:
                        self.grid[0, by + 3, bx + 3] = TileType.STAIRS
                        self.grid[1, by + 3, bx + 3] = TileType.STAIRS
                    if self.num_levels >= 3:
                        self.grid[1, by + 1, bx + 3] = TileType.STAIRS
                        self.grid[2, by + 1, bx + 3] = TileType.STAIRS

    def is_walkable(self, x, y, z=0):
        ix, iy, iz = int(x), int(y), int(z)
        if 0 <= iz < self.num_levels and 0 <= ix < self.width and 0 <= iy < self.height:
            tile = self.grid[iz, iy, ix]
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
        ix, iy, iz = int(x), int(y), int(z)
        if not (0 <= iz < self.num_levels):
            iz = 0
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
                if self.grid[iz, ty, tx] == TileType.BUILDING_WALL or self.grid[iz, ty, tx] == TileType.FURNITURE or self.grid[iz, ty, tx] == TileType.AIR:
                    break
        return visible_tiles
