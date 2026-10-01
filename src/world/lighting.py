import math
from src.world.tiles import TileType

_FOW_NUM_RAYS = 36
_FOW_RAYS = tuple(
    (math.cos(i * (2 * math.pi / _FOW_NUM_RAYS)), math.sin(i * (2 * math.pi / _FOW_NUM_RAYS)))
    for i in range(_FOW_NUM_RAYS)
)
_OPAQUE_FOW_TILES = {
    TileType.BUILDING_WALL,
    TileType.UNDERGROUND_WALL,
    TileType.FURNITURE,
    TileType.AIR,
    TileType.TABLE,
    TileType.CABINET,
    TileType.REFRIGERATOR,
    TileType.KITCHEN_COUNTER,
    TileType.SOFA,
    TileType.BED,
}


class DynamicLight:
    """Represents a localized dynamic point/cone light source (muzzle flash, flashlight, headlight, lightning)."""
    def __init__(self, x, y, z, radius=8.0, color=(255, 255, 200), intensity=1.0, lifetime=1):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.radius = float(radius)
        self.color = color
        self.intensity = float(intensity)
        self.lifetime = lifetime

    def update(self):
        self.lifetime -= 1


class LightingEngine:
    """Handles ambient illumination (solar zenith & moon phases) and raycasted Fog of War (FOW)."""
    def __init__(self, world):
        self.world = world

    def get_light_level(self, z=0):
        """Calculates solar zenith elevation angle and 29.5-day moon phase illumination."""
        if z < 0:
            return 0.05 if not self.world.is_power_out() else 0.02

        y, m, d, hh, mm = self.world.get_time_components()
        time_hours = hh + (mm / 60.0)

        solar_angle = ((time_hours - 6.0) / 24.0) * 2.0 * math.pi
        solar_elevation = math.sin(solar_angle)

        solar_light = 0.0
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

    def compute_fog_of_war(self, x, y, radius=8, z=0):
        ix, iy = int(x), int(y)
        z_idx = self.world.z_to_idx(z)
        visible_tiles = {(ix, iy)}
        w, h = self.world.width, self.world.height
        grid_z = self.world.grid[z_idx]
        r_int = int(radius)

        for dx, dy in _FOW_RAYS:
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
