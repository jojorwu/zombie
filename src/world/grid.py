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
        class LayerProxy:
            def __init__(self, world, z_idx):
                self.world = world
                self.z_idx = z_idx
                self.shape = (world.height, world.width)

            def __eq__(self, other):
                val = other.value if hasattr(other, 'value') else int(other)
                if self.z_idx == self.world.z_to_idx(0):
                    return self.world.ground_grid == val
                arr = np.zeros(self.shape, dtype=int)
                for (z, y, x), tile_val in self.world.sparse_z_grid.items():
                    if z == self.z_idx:
                        arr[y, x] = tile_val
                return arr == val

            def __getitem__(self, key):
                if self.z_idx == self.world.z_to_idx(0):
                    return self.world.ground_grid[key]
                if isinstance(key, tuple) and len(key) == 2:
                    y, x = key
                    return self.world.sparse_z_grid.get((self.z_idx, y, x), 0)
                return 0

            def __setitem__(self, key, value):
                tile_val = value.value if hasattr(value, 'value') else int(value)
                if self.z_idx == self.world.z_to_idx(0):
                    self.world.ground_grid[key] = tile_val
                    return

                if isinstance(key, tuple) and len(key) == 2:
                    y, x = key
                    ys = range(self.world.height) if isinstance(y, slice) else [y]
                    xs = range(self.world.width) if isinstance(x, slice) else [x]
                    for y_curr in ys:
                        for x_curr in xs:
                            if tile_val == 0:
                                self.world.sparse_z_grid.pop((self.z_idx, y_curr, x_curr), None)
                            else:
                                self.world.sparse_z_grid[(self.z_idx, y_curr, x_curr)] = tile_val

            def fill(self, val):
                tile_val = val.value if hasattr(val, 'value') else int(val)
                if self.z_idx == self.world.z_to_idx(0):
                    self.world.ground_grid.fill(tile_val)
                else:
                    keys_to_del = [k for k in self.world.sparse_z_grid if k[0] == self.z_idx]
                    for k in keys_to_del:
                        del self.world.sparse_z_grid[k]
                    if tile_val != 0:
                        for y in range(self.world.height):
                            for x in range(self.world.width):
                                self.world.sparse_z_grid[(self.z_idx, y, x)] = tile_val

        class GridProxy:
            def __init__(self, world):
                self.world = world
                self.shape = (self.world.num_levels, self.world.height, self.world.width)
                self.dtype = int

            def fill(self, val):
                tile_val = val.value if hasattr(val, 'value') else int(val)
                self.world.ground_grid.fill(tile_val)
                self.world.sparse_z_grid.clear()

            def astype(self, dtype):
                arr = np.zeros(self.shape, dtype=dtype)
                arr[self.world.z_to_idx(0)] = self.world.ground_grid.astype(dtype)
                for (z, y, x), val in self.world.sparse_z_grid.items():
                    arr[z, y, x] = val
                return arr

            def __getitem__(self, key):
                if isinstance(key, int):
                    return LayerProxy(self.world, key)

                if isinstance(key, tuple):
                    if len(key) == 3:
                        z_idx, y, x = key
                        if isinstance(z_idx, slice) or isinstance(y, slice) or isinstance(x, slice):
                            ys = list(range(self.world.height)[y]) if isinstance(y, slice) else [y]
                            xs = list(range(self.world.width)[x]) if isinstance(x, slice) else [x]
                            zs = list(range(self.world.num_levels)[z_idx]) if isinstance(z_idx, slice) else [z_idx]
                            res = np.zeros((len(zs), len(ys), len(xs)), dtype=int)
                            for i, z_curr in enumerate(zs):
                                if z_curr == self.world.z_to_idx(0):
                                    res[i] = self.world.ground_grid[y, x]
                                else:
                                    for j, y_curr in enumerate(ys):
                                        for k, x_curr in enumerate(xs):
                                            res[i, j, k] = self.world.sparse_z_grid.get((z_curr, y_curr, x_curr), 0)
                            return res.squeeze()
                        if z_idx == self.world.z_to_idx(0):
                            return self.world.ground_grid[y, x]
                        return self.world.sparse_z_grid.get((z_idx, y, x), TileType.EMPTY.value if hasattr(TileType, 'EMPTY') else 0)
                    elif len(key) == 2:
                        z_idx, slice_spec = key
                        return LayerProxy(self.world, z_idx)[slice_spec]

                return LayerProxy(self.world, self.world.z_to_idx(0))

            def __setitem__(self, key, value):
                tile_val = value.value if hasattr(value, 'value') else int(value)
                if isinstance(key, int):
                    LayerProxy(self.world, key).fill(tile_val)
                    return

                if isinstance(key, tuple):
                    if len(key) == 3:
                        z_idx, y, x = key
                        if isinstance(z_idx, slice) or isinstance(y, slice) or isinstance(x, slice):
                            ys = list(range(self.world.height)[y]) if isinstance(y, slice) else [y]
                            xs = list(range(self.world.width)[x]) if isinstance(x, slice) else [x]
                            zs = list(range(self.world.num_levels)[z_idx]) if isinstance(z_idx, slice) else [z_idx]
                            for z_curr in zs:
                                if z_curr == self.world.z_to_idx(0):
                                    self.world.ground_grid[y, x] = tile_val
                                else:
                                    for y_curr in ys:
                                        for x_curr in xs:
                                            if tile_val == 0:
                                                self.world.sparse_z_grid.pop((z_curr, y_curr, x_curr), None)
                                            else:
                                                self.world.sparse_z_grid[(z_curr, y_curr, x_curr)] = tile_val
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
                        LayerProxy(self.world, z_idx)[slice_spec] = tile_val

        return GridProxy(self)

    def get_3d_grid_array(self) -> np.ndarray:
        """Returns a dense 3D NumPy array [num_levels, height, width] of tile integers for Rust C-API."""
        arr = np.zeros((self.num_levels, self.height, self.width), dtype=np.int64)
        arr[self.z_to_idx(0)] = self.ground_grid.astype(np.int64)
        for (z, y, x), val in self.sparse_z_grid.items():
            arr[z, y, x] = val
        return arr

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
