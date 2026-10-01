import math
import random
from src.world import TileType

_OPAQUE_VIS_TILES = {TileType.BUILDING_WALL, TileType.UNDERGROUND_WALL, TileType.FURNITURE}
_WALL_TILES = {TileType.BUILDING_WALL, TileType.UNDERGROUND_WALL}


class ZombieState:
    IDLE = "idle"
    INVESTIGATE = "investigate"
    CHASE = "chase"
    ATTACK = "attack"


class Zombie:
    def __init__(self, x, y, hp=50.0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.hp = hp
        self.max_hp = hp
        self.is_alive = True
        self.speed = 0.06
        self.damage = 12.0
        self.state = ZombieState.IDLE
        self.target = None
        self.investigate_pos = None

    def take_targeted_damage(self, amount, target_part=None):
        if target_part == "head" or (target_part is None and random.random() < 0.25):
            damage = amount * 2.0
        else:
            damage = amount

        self.hp -= damage
        if self.hp <= 0:
            self.is_alive = False
        return damage

    def has_line_of_sight(self, tx, ty, tz, world):
        if abs(tz - self.z) > 1:
            return False
        dist = math.hypot(tx - self.x, ty - self.y)
        if dist < 0.1:
            return True
        steps = int(math.ceil(dist * 2.0))
        dx = (tx - self.x) / steps
        dy = (ty - self.y) / steps
        cx, cy = self.x, self.y
        z_idx = world.z_to_idx(self.z)
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

    def check_vision(self, world, survivors):
        base_range = max(3.0, 14.0 * world.get_light_level())
        closest_surv = None
        min_d = base_range
        zx, zy, zz = self.x, self.y, self.z

        for s in survivors:
            if s.is_alive and not s.in_vehicle:
                d = math.hypot(s.x - zx, s.y - zy) + abs(s.z - zz) * 3.0
                if d <= min_d and self.has_line_of_sight(s.x, s.y, s.z, world):
                    min_d = d
                    closest_surv = s
        return closest_surv

    def check_hearing(self, noise_events, world=None):
        if not noise_events:
            return None
        best_event = None
        max_audible = 0.0
        zx, zy, zz = self.x, self.y, self.z

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

    def check_scent(self, scent_trails):
        if not scent_trails:
            return None
        best_trail = None
        max_scent = 0.0
        zx, zy, zz = self.x, self.y, self.z

        for st in scent_trails:
            if st.z == zz and st.intensity > 10.0:
                d = math.hypot(st.x - zx, st.y - zy)
                if d < 10.0:
                    scent_score = st.intensity / (d + 1.0)
                    if scent_score > max_scent:
                        max_scent = scent_score
                        best_trail = st
        return best_trail

    def compute_flocking_vector(self, all_zombies, neighbor_radius=6.0, spatial_grid=None):
        if not all_zombies:
            return 0.0, 0.0

        sep_x, sep_y = 0.0, 0.0
        align_x, align_y = 0.0, 0.0
        count = 0
        rad_sq = neighbor_radius * neighbor_radius
        zx, zy, zz = self.x, self.y, self.z

        if spatial_grid is not None:
            cx, cy = int(zx // neighbor_radius), int(zy // neighbor_radius)
            for dcx in (-1, 0, 1):
                for dcy in (-1, 0, 1):
                    neighbors = spatial_grid.get((cx + dcx, cy + dcy, zz), None)
                    if neighbors:
                        for other in neighbors:
                            if other is not self and other.is_alive:
                                dx = other.x - zx
                                dy = other.y - zy
                                d_sq = dx * dx + dy * dy
                                if 0.01 < d_sq < rad_sq:
                                    d = math.sqrt(d_sq)
                                    count += 1
                                    sep_x -= dx / d
                                    sep_y -= dy / d
                                    align_x += dx
                                    align_y += dy
        else:
            for other in all_zombies:
                if other is not self and other.is_alive and other.z == zz:
                    dx = other.x - zx
                    dy = other.y - zy
                    if abs(dx) < neighbor_radius and abs(dy) < neighbor_radius:
                        d_sq = dx * dx + dy * dy
                        if 0.01 < d_sq < rad_sq:
                            d = math.sqrt(d_sq)
                            count += 1
                            sep_x -= dx / d
                            sep_y -= dy / d
                            align_x += dx
                            align_y += dy

        if count > 0:
            return (sep_x * 0.4 + align_x * 0.2), (sep_y * 0.4 + align_y * 0.2)
        return 0.0, 0.0

    def update(self, world, survivors, vehicles, noise_events=None, scent_trails=None, all_zombies=None, spatial_grid=None):
        if not self.is_alive:
            return

        seen_survivor = self.check_vision(world, survivors)
        if seen_survivor:
            self.state = ZombieState.CHASE
            self.target = (seen_survivor.x, seen_survivor.y, seen_survivor.z)
        else:
            if self.state == ZombieState.CHASE:
                self.state = ZombieState.INVESTIGATE
                self.investigate_pos = self.target
                self.target = None

            heard_noise = self.check_hearing(noise_events, world=world)
            if heard_noise and self.state != ZombieState.CHASE:
                self.state = ZombieState.INVESTIGATE
                self.investigate_pos = (heard_noise.x, heard_noise.y, heard_noise.z)

            elif self.state == ZombieState.IDLE and scent_trails:
                picked_scent = self.check_scent(scent_trails)
                if picked_scent:
                    self.state = ZombieState.INVESTIGATE
                    self.investigate_pos = (picked_scent.x, picked_scent.y, picked_scent.z)

        dest_pos = None
        if self.state == ZombieState.CHASE and self.target:
            dest_pos = self.target
        elif self.state == ZombieState.INVESTIGATE and self.investigate_pos:
            dest_pos = self.investigate_pos
            if math.hypot(self.x - dest_pos[0], self.y - dest_pos[1]) < 0.8 and self.z == dest_pos[2]:
                self.state = ZombieState.IDLE
                self.investigate_pos = None

        flock_dx, flock_dy = 0.0, 0.0
        if all_zombies:
            flock_dx, flock_dy = self.compute_flocking_vector(all_zombies, spatial_grid=spatial_grid)

        if dest_pos:
            tx, ty, tz = dest_pos
            angle = math.atan2(ty - self.y, tx - self.x)
            tile_mod = world.get_tile_speed_modifier(self.x, self.y, self.z)
            cur_speed = self.speed * tile_mod

            vx = math.cos(angle) + flock_dx
            vy = math.sin(angle) + flock_dy
            norm = math.hypot(vx, vy)
            if norm > 0.001:
                vx = (vx / norm) * cur_speed
                vy = (vy / norm) * cur_speed

            nx = self.x + vx
            ny = self.y + vy

            nz = self.z
            ix, iy = int(self.x), int(self.y)
            z_idx = world.z_to_idx(self.z)
            if 0 <= ix < world.width and 0 <= iy < world.height:
                tile = world.grid[z_idx, iy, ix]
                if tz > self.z and tile in (TileType.STAIRS, TileType.LADDER):
                    nz = min(world.z_max, self.z + 1)
                elif tz < self.z and tile in (TileType.STAIRS, TileType.LADDER):
                    nz = max(world.z_min, self.z - 1)

            if world.is_walkable(nx, ny, nz):
                self.x, self.y, self.z = nx, ny, nz
            elif world.is_walkable(nx, self.y, nz):
                self.x, self.z = nx, nz
            elif world.is_walkable(self.x, ny, nz):
                self.y, self.z = ny, nz
        else:
            if random.random() < 0.3:
                angle = random.uniform(0, 2 * math.pi)
                tile_mod = world.get_tile_speed_modifier(self.x, self.y, self.z)
                cur_speed = self.speed * tile_mod
                nx = self.x + (math.cos(angle) + flock_dx) * cur_speed
                ny = self.y + (math.sin(angle) + flock_dy) * cur_speed
                if world.is_walkable(nx, ny, self.z):
                    self.x, self.y = nx, ny

        for survivor in survivors:
            if survivor.is_alive and not survivor.in_vehicle and survivor.z == self.z:
                dist = math.hypot(survivor.x - self.x, survivor.y - self.y)
                if dist < 0.8:
                    survivor.take_damage(self.damage)
                    self.state = ZombieState.ATTACK
