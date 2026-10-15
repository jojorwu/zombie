import math
import random
from src.world.tiles import TileType
from src.entities.sensory import NoiseEvent
from src.ai.pathfinding import AStar3D
from src.entities import AnatomicalHealth
from src.ai.inference import check_line_of_sight

try:
    from rust_engine import RustZombieEngine
    RUST_ZOMBIE_AVAILABLE = True
except ImportError:
    RUST_ZOMBIE_AVAILABLE = False


class ZombieType:
    STANDARD = "standard"


class ZombieState:
    IDLE = "idle"
    INVESTIGATE = "investigate"
    CHASE = "chase"
    ATTACK = "attack"
    BREAK_OBSTACLE = "break_obstacle"


class Zombie:
    def __init__(self, x, y, hp=50.0, z=0, config=None, zombie_type: str = ZombieType.STANDARD):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.zombie_type = ZombieType.STANDARD
        self.is_crawler = False

        self.body = AnatomicalHealth(35.0, 100.0, 40.0, 40.0, 45.0, 45.0)
        self.hp = hp if hp > 0.0 else 50.0
        self.max_hp = 100.0
        self.is_alive = True

        z_cfg = config.get("zombie", {}) if config else {}
        self.damage = z_cfg.get("damage", 12.0)
        self.bite_infection_chance = z_cfg.get("bite_infection_chance", 0.25)
        self.grab_slowdown = z_cfg.get("grab_slowdown", 0.5)
        self.memory_duration_ticks = z_cfg.get("memory_duration_ticks", 150)
        self.pathfinding_max_nodes = z_cfg.get("pathfinding_max_nodes", 300)
        self.speed = z_cfg.get("speed", 0.08)

        self.state = ZombieState.IDLE
        self.target = None
        self.investigate_pos = None

        self.memory_timer = 0
        self.last_known_target_pos = None
        self.current_path = []
        self.path_target_pos = None
        self.astar_engine = None

        from src.simulation.p_np_math import PNPComplexityEngine
        self.pnp_engine = PNPComplexityEngine(degree=3)

        if RUST_ZOMBIE_AVAILABLE:
            self.rust_zombie = RustZombieEngine(self.x, self.y, self.z, self.hp, self.speed)
        else:
            self.rust_zombie = None

    def take_targeted_damage(self, amount, target_part=None, attacker_pos=None):
        if hasattr(self.body, 'apply_targeted_damage'):
            actual_damage = self.body.apply_targeted_damage(target_part or "torso", amount, 0.0)
            if target_part in ("left_leg", "right_leg") and (self.body.left_leg <= 0 or self.body.right_leg <= 0):
                self.is_crawler = True
                if self.rust_zombie:
                    self.rust_zombie.dismember_legs()
        else:
            actual_damage = amount

        self.hp = max(0.0, self.hp - actual_damage)
        if self.hp <= 0.0:
            self.is_alive = False
            if self.rust_zombie:
                self.rust_zombie.is_alive = False
        elif attacker_pos:
            self.state = ZombieState.INVESTIGATE
            self.investigate_pos = (attacker_pos[0], attacker_pos[1], attacker_pos[2])
            self.memory_timer = self.memory_duration_ticks
        return actual_damage

    def has_line_of_sight(self, tx, ty, tz, world):
        if self.z != tz:
            return False
        return check_line_of_sight(world, self.x, self.y, tx, ty, int(self.z))

    def check_vision(self, world, survivors):
        sight_range = 15.0
        if not survivors:
            return None

        targets_vec = []
        for s in survivors:
            if s.is_alive and s.z == self.z:
                dx = s.x - self.x
                dy = s.y - self.y
                if abs(dx) < sight_range and abs(dy) < sight_range:
                    val = 100.0 - (s.health if hasattr(s, 'health') else 100.0)
                    targets_vec.append((float(s.x), float(s.y), int(s.z), float(val)))

        # Native Rust P=NP Polynomial O(N^3) Target Selection Evaluation
        if self.rust_zombie and targets_vec:
            best_pos = self.rust_zombie.select_target_p_np(targets_vec)
            if best_pos:
                for s in survivors:
                    if s.is_alive and abs(s.x - best_pos[0]) < 0.2 and abs(s.y - best_pos[1]) < 0.2:
                        if self.has_line_of_sight(s.x, s.y, s.z, world):
                            return s

        best_s = None
        min_d = sight_range
        candidates = []
        for s in survivors:
            if s.is_alive and s.z == self.z:
                dx = s.x - self.x
                dy = s.y - self.y
                if abs(dx) < sight_range and abs(dy) < sight_range:
                    candidates.append((math.hypot(dx, dy), s))

        candidates.sort(key=lambda c: c[0])
        for d, s in candidates:
            if d >= min_d:
                break
            if self.has_line_of_sight(s.x, s.y, s.z, world):
                min_d = d
                best_s = s
                break

        return best_s

    def check_hearing(self, noise_events, world=None):
        if not noise_events:
            return None
        loudest = None
        max_vol = 0.0

        for ne in noise_events:
            if ne.z == self.z:
                dx = ne.x - self.x
                dy = ne.y - self.y
                if abs(dx) <= ne.volume and abs(dy) <= ne.volume:
                    d = math.hypot(dx, dy)
                    if d <= ne.volume:
                        att_vol = max(0.0, ne.volume - d)
                        if att_vol > max_vol:
                            max_vol = att_vol
                            loudest = ne
        return loudest

    def check_scent(self, scent_trails):
        if not scent_trails:
            return None
        best = None
        max_i = 0.0

        for st in scent_trails:
            if st.z == self.z:
                dx = st.x - self.x
                dy = st.y - self.y
                if abs(dx) <= 5.0 and abs(dy) <= 5.0:
                    d = math.hypot(dx, dy)
                    if d <= 5.0 and st.intensity > max_i:
                        max_i = st.intensity
                        best = st
        return best

    def compute_flocking_vector(self, all_zombies, neighbor_radius=6.0, spatial_grid=None):
        sep_x, sep_y = 0.0, 0.0
        for z2 in all_zombies:
            if z2 is not self and z2.is_alive and z2.z == self.z:
                dx = self.x - z2.x
                dy = self.y - z2.y
                if abs(dx) < 2.0 and abs(dy) < 2.0:
                    d2 = dx * dx + dy * dy
                    if 0.0001 < d2 < 2.25:
                        d = math.sqrt(d2)
                        sep_x += (dx / d) * (1.5 - d)
                        sep_y += (dy / d) * (1.5 - d)
        return sep_x, sep_y

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

        if self.rust_zombie:
            self.rust_zombie.x = self.x
            self.rust_zombie.y = self.y
            self.rust_zombie.z = self.z
            self.rust_zombie.hp = self.hp

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
                self.state = ZombieState.INVESTIGATE
                self.investigate_pos = self.last_known_target_pos or self.target
                self.target = None

            if self.state == ZombieState.INVESTIGATE:
                if self.memory_timer > 0:
                    self.memory_timer -= 1
                else:
                    self.state = ZombieState.IDLE
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

        effective_speed = self.speed * 0.4 if self.is_crawler else self.speed

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
            cur_speed = effective_speed * tile_mod

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
                if not self.attack_or_break_obstacle(world, nx, ny, noise_events=noise_events):
                    for off_x, off_y in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        if self.attack_or_break_obstacle(world, self.x + off_x, self.y + off_y, noise_events=noise_events):
                            break
                self.current_path = []
        else:
            if random.random() < 0.3:
                angle = random.uniform(0, 2 * math.pi)
                tile_mod = world.get_tile_speed_modifier(self.x, self.y, self.z)
                cur_speed = effective_speed * tile_mod
                nx = self.x + (math.cos(angle) + flock_dx) * cur_speed
                ny = self.y + (math.sin(angle) + flock_dy) * cur_speed
                if world.is_walkable(nx, ny, self.z):
                    self.x, self.y = nx, ny

        if self.rust_zombie:
            self.rust_zombie.x = self.x
            self.rust_zombie.y = self.y

        for survivor in survivors:
            if survivor.is_alive and not survivor.in_vehicle and survivor.z == self.z:
                dist = math.hypot(survivor.x - self.x, survivor.y - self.y)
                if dist < 0.8:
                    survivor.take_damage(self.damage)
                    survivor.grab_slowdown_timer = 20
                    survivor.grab_slowdown_factor = min(survivor.grab_slowdown_factor, self.grab_slowdown)
                    if not survivor.is_infected and random.random() < self.bite_infection_chance:
                        survivor.is_infected = True
                    self.state = ZombieState.ATTACK
