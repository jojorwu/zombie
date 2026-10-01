import math
import random
from src.world.tiles import TileType
from src.entities.zombie.zombie_perception import ZombiePerception
from src.entities.zombie.zombie_flock import ZombieFlocking


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
        return ZombiePerception.has_line_of_sight(self, tx, ty, tz, world)

    def check_vision(self, world, survivors):
        return ZombiePerception.check_vision(self, world, survivors)

    def check_hearing(self, noise_events, world=None):
        return ZombiePerception.check_hearing(self, noise_events, world)

    def check_scent(self, scent_trails):
        return ZombiePerception.check_scent(self, scent_trails)

    def compute_flocking_vector(self, all_zombies, neighbor_radius=6.0, spatial_grid=None):
        return ZombieFlocking.compute_flocking_vector(self, all_zombies, neighbor_radius, spatial_grid)

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
