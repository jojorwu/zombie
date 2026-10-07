import math
import random
import numpy as np
from src.world.tiles import TileType

try:
    from rust_engine import check_line_of_sight_rust
    RUST_LOS_AVAILABLE = True
except ImportError:
    RUST_LOS_AVAILABLE = False

_OPAQUE_VIS_TILES = {
    TileType.BUILDING_WALL,
    TileType.UNDERGROUND_WALL,
    TileType.WALL_BRICK,
    TileType.WALL_CONCRETE,
    TileType.WALL_WOOD,
    TileType.WALL_REINFORCED,
    TileType.FURNITURE
}

_WALL_TILES = {
    TileType.BUILDING_WALL,
    TileType.UNDERGROUND_WALL,
    TileType.WALL_BRICK,
    TileType.WALL_CONCRETE,
    TileType.WALL_WOOD,
    TileType.WALL_REINFORCED
}


class ZombiePerception:
    """Handles vision raycasting, acoustic hearing attenuation, and scent trail detection."""
    @staticmethod
    def has_line_of_sight(zombie, tx, ty, tz, world):
        if abs(tz - zombie.z) > 1:
            return False

        if RUST_LOS_AVAILABLE:
            if hasattr(world, 'get_3d_grid_array'):
                grid_3d = world.get_3d_grid_array()
            else:
                grid_3d = world.grid.astype(np.int64)
            return check_line_of_sight_rust(float(zombie.x), float(zombie.y), int(zombie.z), float(tx), float(ty), int(tz), grid_3d, world.z_min)

        dist = math.hypot(tx - zombie.x, ty - zombie.y)
        if dist < 0.1:
            return True
        steps = int(math.ceil(dist * 2.0))
        dx = (tx - zombie.x) / steps
        dy = (ty - zombie.y) / steps
        cx, cy = zombie.x, zombie.y
        z_idx = world.z_to_idx(zombie.z)
        w, h = world.width, world.height
        grid_z = world.grid[z_idx]

        for _ in range(steps):
            cx += dx
            cy += dy
            ix, iy = int(cx), int(cy)
            if 0 <= ix < w and 0 <= iy < h:
                if grid_z[iy, ix] in _OPAQUE_VIS_TILES:
                    return False
        return True

    @staticmethod
    def check_vision(zombie, world, survivors):
        base_range = max(3.0, 14.0 * world.get_light_level())
        closest_surv = None
        min_d = base_range
        zx, zy, zz = zombie.x, zombie.y, zombie.z

        for s in survivors:
            if s.is_alive:
                # Zombies notice survivors even inside vehicles
                range_bonus = 3.0 if s.in_vehicle else 0.0
                d = math.hypot(s.x - zx, s.y - zy) + abs(s.z - zz) * 3.0
                if d <= (min_d + range_bonus) and ZombiePerception.has_line_of_sight(zombie, s.x, s.y, s.z, world):
                    min_d = d
                    closest_surv = s
        return closest_surv

    @staticmethod
    def check_hearing(zombie, noise_events, world=None):
        if not noise_events:
            return None
        best_event = None
        max_audible = 0.0
        zx, zy, zz = zombie.x, zombie.y, zombie.z

        for ne in noise_events:
            dist = math.hypot(ne.x - zx, ne.y - zy) + abs(ne.z - zz) * 2.0
            if dist <= ne.volume:
                attenuated_vol = ne.volume
                if world and abs(ne.z - zz) <= 1:
                    steps = max(1, int(dist))
                    dx = (zx - ne.x) / steps
                    dy = (zy - ne.y) / steps
                    cx, cy = ne.x, ne.y
                    z_idx = world.z_to_idx(zz)
                    w, h = world.width, world.height
                    grid_z = world.grid[z_idx]

                    for _ in range(steps):
                        cx += dx
                        cy += dy
                        ix, iy = int(cx), int(cy)
                        if 0 <= ix < w and 0 <= iy < h:
                            tile = grid_z[iy, ix]
                            if tile in _WALL_TILES:
                                attenuated_vol *= 0.35
                            elif tile == TileType.DOOR:
                                attenuated_vol *= 0.65

                audible_val = attenuated_vol - dist
                if audible_val > max_audible:
                    max_audible = audible_val
                    best_event = ne
        return best_event

    @staticmethod
    def check_scent(zombie, scent_trails):
        if not scent_trails:
            return None
        best_trail = None
        max_scent = 0.0
        zx, zy, zz = zombie.x, zombie.y, zombie.z

        for st in scent_trails:
            if st.z == zz and st.intensity > 10.0:
                d = math.hypot(st.x - zx, st.y - zy)
                if d < 10.0:
                    scent_score = st.intensity / (d + 1.0)
                    if scent_score > max_scent:
                        max_scent = scent_score
                        best_trail = st
        return best_trail
