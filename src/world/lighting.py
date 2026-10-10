import math
import numpy as np
from src.world.tiles import TileType

try:
    from rust_engine import compute_fog_of_war_rust
    RUST_FOW_AVAILABLE = True
except ImportError:
    RUST_FOW_AVAILABLE = False

_FOW_NUM_RAYS = 36
_FOW_RAYS = tuple(
    (math.cos(i * (2 * math.pi / _FOW_NUM_RAYS)), math.sin(i * (2 * math.pi / _FOW_NUM_RAYS)))
    for i in range(_FOW_NUM_RAYS)
)

_OPAQUE_FOW_TILES = frozenset({
    TileType.BUILDING_WALL,
    TileType.UNDERGROUND_WALL,
    TileType.WALL_BRICK,
    TileType.WALL_CONCRETE,
    TileType.WALL_WOOD,
    TileType.WALL_REINFORCED,
    TileType.FURNITURE,
    TileType.TABLE,
    TileType.CABINET,
    TileType.REFRIGERATOR,
    TileType.KITCHEN_COUNTER,
    TileType.SOFA,
    TileType.BED,
    TileType.BOOKSHELF,
    TileType.OFFICE_DESK,
    TileType.MEDICAL_BED,
    TileType.GUN_RACK,
    TileType.WEAPON_SAFE,
    TileType.CASH_REGISTER,
    TileType.STORE_SHELF,
    TileType.SCHOOL_DESK,
    TileType.WORKBENCH,
    TileType.LOCKER,
    TileType.TV_STAND,
    TileType.DISPLAY_CASE,
    TileType.FACTORY_RACK,
})


class DynamicLight:
    """Represents a localized dynamic point/cone light source (muzzle flash, flashlight, headlight, lightning)."""
    __slots__ = ("x", "y", "z", "radius", "color", "intensity", "lifetime")

    def __init__(self, x: float, y: float, z: int, radius: float = 8.0, color=(255, 255, 200), intensity: float = 1.0, lifetime: int = 1):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.radius = float(radius)
        self.color = color
        self.intensity = float(intensity)
        self.lifetime = lifetime

    def update(self) -> None:
        self.lifetime -= 1


class LightingEngine:
    """Handles ambient illumination (solar zenith & moon phases) and raycasted/shadowcast Fog of War (FOW)."""
    __slots__ = ("world",)

    def __init__(self, world):
        self.world = world

    def get_light_level(self, z: int = 0) -> float:
        """Calculates solar zenith elevation angle and 29.5-day moon phase illumination."""
        if z < 0:
            return 0.05 if not self.world.is_power_out() else 0.02

        y, m, d, hh, mm = self.world.get_time_components()
        time_hours = hh + (mm / 60.0)

        solar_angle = ((time_hours - 6.0) / 24.0) * 2.0 * math.pi
        solar_elevation = math.sin(solar_angle)

        if solar_elevation > 0:
            solar_light = math.sin(solar_elevation * (math.pi / 2.0)) * 0.85 + 0.15
        else:
            solar_light = max(0.0, 0.15 + solar_elevation * 0.3)

        day_total = (y - 1) * 360 + (m - 1) * 30 + d
        lunar_phase_day = (day_total % 29.5)
        moon_fullness = 0.5 + 0.5 * math.cos(((lunar_phase_day - 14.75) / 29.5) * 2.0 * math.pi)

        lunar_angle = solar_angle + math.pi
        lunar_elevation = math.sin(lunar_angle)

        lunar_light = 0.0
        if lunar_elevation > 0 and solar_elevation < 0:
            lunar_light = (0.05 + 0.20 * moon_fullness) * math.sin(lunar_elevation * (math.pi / 2.0))

        ambient = max(solar_light, lunar_light)
        if self.world.is_power_out():
            ambient *= 0.75

        return max(0.08, min(1.0, ambient))

    def compute_fog_of_war(self, x: float, y: float, radius: int = 8, z: int = 0, facing_angle: float = None, fov_degrees: float = 180.0) -> set:
        """
        Dynamic raycasted Fog of War with weather/darkness sight radius constraints and FOV cone filtering.
        """
        ix, iy = int(x), int(y)
        z_idx = self.world.z_to_idx(z)
        w, h = self.world.width, self.world.height

        # Constrain sight radius dynamically based on ambient lighting and heavy rain/snowstorms
        ambient_light = self.get_light_level(z)
        weather_penalty = 2 if self.world.weather.is_in_rain(x, y) else 0
        effective_radius = max(3, int(radius * ambient_light) - weather_penalty)

        if RUST_FOW_AVAILABLE:
            if hasattr(self.world, 'get_3d_grid_array'):
                grid_3d = self.world.get_3d_grid_array()
            else:
                grid_3d = self.world.grid.astype(np.int64)
            rust_res = compute_fog_of_war_rust(float(x), float(y), effective_radius, int(z), grid_3d, self.world.z_min, facing_angle=facing_angle, fov_degrees=fov_degrees)
            return set(rust_res)

        visible_tiles = {(ix, iy)}
        grid_z = self.world.grid[z_idx]
        r_int = effective_radius

        half_fov = math.radians(fov_degrees / 2.0) if facing_angle is not None else None

        for dx, dy in _FOW_RAYS:
            if facing_angle is not None and half_fov is not None:
                ray_angle = math.atan2(dy, dx)
                diff = (ray_angle - facing_angle + math.pi) % (2 * math.pi) - math.pi
                if abs(diff) > half_fov:
                    continue

            cx, cy = float(x), float(y)
            for _step in range(r_int):
                cx += dx
                cy += dy
                tx, ty = int(cx), int(cy)
                if not (0 <= tx < w and 0 <= ty < h):
                    break
                visible_tiles.add((tx, ty))
                if grid_z[ty, tx] in _OPAQUE_FOW_TILES:
                    break
        return visible_tiles
