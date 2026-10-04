import math
import random
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from src.world.tiles import TileType, BuildingType, TILE_COLORS, BUILDING_COLORS, TILE_WALKABLE, TILE_SPEED_MODIFIERS
from src.world.chunk import ChunkManager
from src.world.weather import WeatherManager
from src.world.lighting import DynamicLight, LightingEngine
from src.world.generation import WorldGenerator
from src.entities.state_manager import FurnitureStateManager, ItemStateManager

WORLD_EXECUTOR = ThreadPoolExecutor(max_workers=4)


class World:
    """
    World representation featuring Sparse Spatial Hashing:
    - Ground level (Z=0) is stored in a dense 2D Flat-NumPy array.
    - Vertical levels (Z > 0 and Z < 0) are stored in a sparse spatial hash map dictionary.
    """
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
        self.lighting_engine = LightingEngine(self)
        self.furniture_state_manager = FurnitureStateManager()
        self.item_state_manager = ItemStateManager()
        self.generator = WorldGenerator(self)
        self.dynamic_lights = []

        # Dense 2D Flat-NumPy array for Z=0 (Ground)
        self.ground_grid = np.zeros((self.height, self.width), dtype=int)
        # Sparse Spatial Hash Map for non-zero Z levels: {(z_idx, y, x): tile_type_int}
        self.sparse_z_grid = {}

        self.building_grid = {}
        self.buildings = []
        self.generate_world()

    @property
    def grid(self):
        """Proxy array interface providing backwards-compatible [z_idx, y, x] array access."""
        class GridProxy:
            def __init__(self, world):
                self.world = world
                self.shape = (self.world.num_levels, self.world.height, self.world.width)
                self.dtype = int

            def fill(self, val):
                tile_val = val.value if hasattr(val, 'value') else int(val)
                self.world.ground_grid.fill(tile_val)
                self.world.sparse_z_grid.clear()

            def __getitem__(self, key):
                if isinstance(key, int):
                    # Handle 1D indexing: world.grid[z_idx]
                    z_idx = key
                    if z_idx == self.world.z_to_idx(0):
                        return self.world.ground_grid
                    else:
                        layer = np.zeros((self.world.height, self.world.width), dtype=int)
                        for (z, y, x), val in self.world.sparse_z_grid.items():
                            if z == z_idx:
                                layer[y, x] = val
                        return layer

                if isinstance(key, tuple):
                    if len(key) == 3:
                        z_idx, y, x = key
                        if isinstance(z_idx, slice) or isinstance(y, slice) or isinstance(x, slice):
                            layer = self.__getitem__(z_idx if not isinstance(z_idx, slice) else self.world.z_to_idx(0))
                            return layer[y, x]
                        if z_idx == self.world.z_to_idx(0):
                            return self.world.ground_grid[y, x]
                        return self.world.sparse_z_grid.get((z_idx, y, x), TileType.EMPTY.value if hasattr(TileType, 'EMPTY') else 0)
                    elif len(key) == 2:
                        z_idx, slice_spec = key
                        layer = self.__getitem__(z_idx)
                        return layer[slice_spec]

                return self.world.ground_grid

            def __setitem__(self, key, value):
                tile_val = value.value if hasattr(value, 'value') else int(value)
                if isinstance(key, int):
                    z_idx = key
                    if z_idx == self.world.z_to_idx(0):
                        self.world.ground_grid.fill(tile_val)
                    else:
                        for y in range(self.world.height):
                            for x in range(self.world.width):
                                self.world.sparse_z_grid[(z_idx, y, x)] = tile_val
                    return

                if isinstance(key, tuple):
                    if len(key) == 3:
                        z_idx, y, x = key
                        if isinstance(z_idx, slice) or isinstance(y, slice) or isinstance(x, slice):
                            if z_idx == self.world.z_to_idx(0):
                                self.world.ground_grid[y, x] = tile_val
                            return
                        if z_idx == self.world.z_to_idx(0):
                            self.world.ground_grid[y, x] = tile_val
                        else:
                            if tile_val == 0:
                                self.world.sparse_z_grid.pop((z_idx, y, x), None)
                            else:
                                self.world.sparse_z_grid[(z_idx, y, x)] = tile_val
                    elif len(key) == 2:
                        z_idx, slice_spec = key
                        if z_idx == self.world.z_to_idx(0):
                            self.world.ground_grid[slice_spec] = tile_val

        return GridProxy(self)

    def z_to_idx(self, z):
        return max(0, min(self.num_levels - 1, int(z) - self.z_min))

    def idx_to_z(self, idx):
        return idx + self.z_min

    def build_chunk_building(self, bx, by, bw, bh, btype):
        self.generator.build_chunk_building(bx, by, bw, bh, btype)

    def generate_world(self):
        self.generator.generate()

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
        return self.lighting_engine.get_light_level(z)

    def compute_fog_of_war(self, x, y, radius=8, z=0, facing_angle=None, fov_degrees=180.0):
        return self.lighting_engine.compute_fog_of_war(x, y, radius, z, facing_angle=facing_angle, fov_degrees=fov_degrees)
