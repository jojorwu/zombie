import math
import random
from src.world.tiles import TileType
from src.entities.zombie.zombie_perception import ZombiePerception
from src.entities.zombie.zombie_flock import ZombieFlocking
from src.entities.sensory import NoiseEvent
from src.ai.pathfinding import AStar3D
from src.entities.health import AnatomicalHealth, BodyPart


class ZombieState:
    IDLE = "idle"
    INVESTIGATE = "investigate"
    CHASE = "chase"
    ATTACK = "attack"
    BREAK_OBSTACLE = "break_obstacle"


class Zombie:
    def __init__(self, x, y, hp=50.0, z=0, config=None):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.body = AnatomicalHealth(max_head=25.0, max_torso=60.0, max_arm=25.0, max_leg=30.0)
        self.hp = self.body.overall_health_percent
        self.max_hp = 100.0
        self.is_alive = True

        z_cfg = config.get("zombie", {}) if config else {}
        self.speed = z_cfg.get("speed", 0.07)
        self.damage = z_cfg.get("damage", 12.0)
        self.bite_infection_chance = z_cfg.get("bite_infection_chance", 0.25)
        self.grab_slowdown = z_cfg.get("grab_slowdown", 0.5)
        self.memory_duration_ticks = z_cfg.get("memory_duration_ticks", 150)
        self.pathfinding_max_nodes = z_cfg.get("pathfinding_max_nodes", 300)

        self.state = ZombieState.IDLE
        self.target = None
        self.investigate_pos = None

        self.memory_timer = 0
        self.last_known_target_pos = None
        self.current_path = []
        self.path_target_pos = None
        self.astar_engine = None

    def take_targeted_damage(self, amount, target_part=None):
        hit_part, actual_damage, crippled = self.body.apply_targeted_damage(amount, target_part)
        self.hp = self.body.overall_health_percent
        if self.body.is_dead:
            self.is_alive = False
        return actual_damage

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

    def attack_or_break_obstacle(self, world, nx, ny, noise_events=None):
        """Attacks and breaks doors, windows, and barricades blocking path."""
        z_idx = world.z_to_idx(self.z)
        ix, iy = int(nx), int(ny)

        if not (0 <= ix < world.width and 0 <= iy < world.height):
            return False

        tile = world.grid[z_idx, iy, ix]

        BREAKABLE_OBSTACLES = {
            TileType.DOOR: TileType.DOOR_OPEN,
            TileType.DOOR_LOCKED: TileType.DOOR_OPEN,
            TileType.WINDOW: TileType.WINDOW_BROKEN,
            TileType.CURTAIN_CLOSED: TileType.CURTAIN_OPEN,
        }

        if tile in BREAKABLE_OBSTACLES:
            world.grid[z_idx, iy, ix] = BREAKABLE_OBSTACLES[tile]
            if noise_events is not None:
                noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=22.0, source_type="wood_snap"))
            return True

        return False

    def update(self, world, survivors, vehicles, noise_events=None, scent_trails=None, all_zombies=None, spatial_grid=None):
        if not self.is_alive:
            return

        if self.astar_engine is None or self.astar_engine.world is not world:
            self.astar_engine = AStar3D(world)

        seen_survivor = self.check_vision(world, survivors)
        if seen_survivor:
            self.state = ZombieState.CHASE
            self.target = (seen_survivor.x, seen_survivor.y, seen_survivor.z)
            self.last_known_target_pos = self.target
            self.memory_timer = self.memory_duration_ticks
        else:
            if self.state == ZombieState.CHASE:
                if self.memory_timer > 0 and self.last_known_target_pos:
                    self.memory_timer -= 1
                    self.state = ZombieState.INVESTIGATE
                    self.investigate_pos = self.last_known_target_pos
                else:
                    self.state = ZombieState.IDLE
                    self.target = None
                    self.investigate_pos = None
                    self.last_known_target_pos = None

            heard_noise = self.check_hearing(noise_events, world=world)
            if heard_noise and self.state != ZombieState.CHASE:
                self.state = ZombieState.INVESTIGATE
                self.investigate_pos = (heard_noise.x, heard_noise.y, heard_noise.z)
                self.last_known_target_pos = self.investigate_pos
                self.memory_timer = self.memory_duration_ticks

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
                if self.memory_timer > 0:
                    self.memory_timer -= 1
                else:
                    self.state = ZombieState.IDLE
                    self.investigate_pos = None

        flock_dx, flock_dy = 0.0, 0.0
        if all_zombies:
            flock_dx, flock_dy = self.compute_flocking_vector(all_zombies, spatial_grid=spatial_grid)

        if dest_pos:
            target_grid_pos = (int(dest_pos[0]), int(dest_pos[1]), int(dest_pos[2]))
            dist_to_dest = math.hypot(dest_pos[0] - self.x, dest_pos[1] - self.y)

            # Recalculate A* path if target moved or no path
            if (not self.current_path or self.path_target_pos != target_grid_pos) and dist_to_dest > 1.2:
                start_pos = (self.x, self.y, self.z)
                self.current_path = self.astar_engine.find_path(start_pos, dest_pos, max_nodes=self.pathfinding_max_nodes)
                self.path_target_pos = target_grid_pos

            next_waypoint = None
            if self.current_path:
                while self.current_path:
                    wp = self.current_path[0]
                    if math.hypot(wp[0] - self.x, wp[1] - self.y) < 0.4 and int(wp[2]) == self.z:
                        self.current_path.pop(0)
                    else:
                        next_waypoint = wp
                        break

            if next_waypoint:
                tx, ty, tz = next_waypoint
            else:
                tx, ty, tz = dest_pos

            angle = math.atan2(ty - self.y, tx - self.x)
            tile_mod = world.get_tile_speed_modifier(self.x, self.y, self.z)
            cur_speed = self.speed * tile_mod * self.body.movement_speed_multiplier

            vx = math.cos(angle) + flock_dx * 0.5
            vy = math.sin(angle) + flock_dy * 0.5
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
                self.attack_or_break_obstacle(world, nx, ny, noise_events=noise_events)
                self.current_path = []
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
                    applied_dmg = self.damage * self.body.attack_damage_multiplier
                    survivor.take_damage(applied_dmg)
                    survivor.grab_slowdown_timer = 20
                    slow_fac = self.grab_slowdown if self.body.attack_damage_multiplier > 0.5 else 0.8
                    survivor.grab_slowdown_factor = min(survivor.grab_slowdown_factor, slow_fac)
                    if not survivor.is_infected and random.random() < self.bite_infection_chance:
                        survivor.is_infected = True
                    self.state = ZombieState.ATTACK
