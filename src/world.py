import math
import random
import numpy as np

class TileType:
    GRASS = 0
    ROAD = 1
    BUILDING = 2
    WATER = 3
    FOREST = 4

TILE_COLORS = {
    TileType.GRASS: (34, 139, 34),
    TileType.ROAD: (105, 105, 105),
    TileType.BUILDING: (139, 69, 19),
    TileType.WATER: (65, 105, 225),
    TileType.FOREST: (0, 100, 0),
}

TILE_WALKABLE = {
    TileType.GRASS: True,
    TileType.ROAD: True,
    TileType.BUILDING: False,  # Building walls/structures block movement unless inside/doors
    TileType.WATER: False,
    TileType.FOREST: True,
}

class World:
    def __init__(self, width=60, height=40, day_length_ticks=600):
        self.width = max(20, width)
        self.height = max(20, height)
        self.day_length_ticks = day_length_ticks
        self.current_tick = 0
        self.grid = np.zeros((self.height, self.width), dtype=int)
        self.generate_world()

    def generate_world(self):
        # Fill with grass
        self.grid.fill(TileType.GRASS)

        # Generate forests
        num_forests = random.randint(3, 6)
        for _ in range(num_forests):
            cx = random.randint(2, self.width - 3)
            cy = random.randint(2, self.height - 3)
            radius = random.randint(2, 5)
            for y in range(max(0, cy - radius), min(self.height, cy + radius + 1)):
                for x in range(max(0, cx - radius), min(self.width, cx + radius + 1)):
                    if (x - cx)**2 + (y - cy)**2 <= radius**2:
                        self.grid[y, x] = TileType.FOREST

        # Generate rivers
        num_rivers = random.randint(1, 2)
        for _ in range(num_rivers):
            rx = random.randint(0, self.width - 1)
            ry = 0
            for _step in range(self.height):
                if 0 <= rx < self.width and 0 <= ry < self.height:
                    self.grid[ry, rx] = TileType.WATER
                    if rx + 1 < self.width:
                        self.grid[ry, rx + 1] = TileType.WATER
                ry += 1
                rx += random.choice([-1, 0, 1])

        # Generate cities (roads + buildings)
        num_cities = random.randint(1, 3)
        for _ in range(num_cities):
            max_x = max(1, self.width - 12)
            max_y = max(1, self.height - 12)
            city_x = random.randint(1, max_x)
            city_y = random.randint(1, max_y)
            city_w = random.randint(8, 12)
            city_h = random.randint(8, 12)

            # Roads grid
            for x in range(city_x, min(self.width, city_x + city_w)):
                for y in range(city_y, min(self.height, city_y + city_h)):
                    if x % 4 == 0 or y % 4 == 0:
                        self.grid[y, x] = TileType.ROAD
                    else:
                        # Buildings in blocks
                        self.grid[y, x] = TileType.BUILDING

            # Openings/Doors in buildings
            for x in range(city_x, min(self.width, city_x + city_w)):
                for y in range(city_y, min(self.height, city_y + city_h)):
                    if self.grid[y, x] == TileType.BUILDING and random.random() < 0.25:
                        self.grid[y, x] = TileType.ROAD

    def is_walkable(self, x, y):
        ix, iy = int(x), int(y)
        if 0 <= ix < self.width and 0 <= iy < self.height:
            tile = self.grid[iy, ix]
            return TILE_WALKABLE.get(tile, True)
        return False

    def update_day_night(self):
        self.current_tick += 1

    def get_light_level(self):
        # Returns float between 0.2 (midnight) and 1.0 (noon)
        progress = (self.current_tick % self.day_length_ticks) / self.day_length_ticks
        sine_val = math.sin(progress * 2 * math.pi)
        light = 0.6 + 0.4 * sine_val
        return max(0.2, min(1.0, light))

    def compute_fog_of_war(self, x, y, radius):
        ix, iy = int(x), int(y)
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
                if self.grid[ty, tx] == TileType.BUILDING:
                    break  # Building wall blocks vision
        return visible_tiles
