import math
import random
from src.world.tiles import TileType

try:
    from rust_engine import RustBallisticsUtility
    RUST_BALLISTICS_AVAILABLE = True
except ImportError:
    RUST_BALLISTICS_AVAILABLE = False


class MaterialResistance:
    """Material penetration energy thresholds (Joules) and ricochet hardness factors."""
    GLASS = {"resistance_j": 30.0, "ricochet_chance": 0.05, "hardness": 0.1, "breaks": True, "name": "Glass"}
    WOOD = {"resistance_j": 160.0, "ricochet_chance": 0.15, "hardness": 0.3, "breaks": False, "name": "Wood"}
    BRICK = {"resistance_j": 420.0, "ricochet_chance": 0.40, "hardness": 0.7, "breaks": False, "name": "Brick"}
    CONCRETE = {"resistance_j": 850.0, "ricochet_chance": 0.70, "hardness": 0.9, "breaks": False, "name": "Concrete"}
    REINFORCED_METAL = {"resistance_j": 1200.0, "ricochet_chance": 0.85, "hardness": 1.0, "breaks": False, "name": "Reinforced Metal"}
    FLESH = {"resistance_j": 100.0, "ricochet_chance": 0.0, "hardness": 0.0, "breaks": False, "name": "Flesh"}


class BallisticsUtility:
    """
    Advanced Firearm Ballistics & Projectile Simulation Engine:
    - Caliber specifications (mass, v0, drag coefficient, base damage)
    - Aerodynamic air drag & gravitational bullet drop
    - Wind deflection and crosswind drift
    - Material overpenetration (Glass, Wood, Brick, Concrete, Metal, Flesh)
    - Window shattering on bullet impact
    - Shallow-angle ricochet deflections and energy loss
    - Multi-target penetrating hits across line of fire
    """

    CALIBERS = {
        "9mm": {
            "mass_kg": 0.008,          # 8 grams (124 grain)
            "muzzle_velocity": 360.0,   # m/s
            "drag_coeff": 0.15,
            "max_range": 50.0,
            "base_damage": 35.0,
            "initial_energy_j": 518.4,  # 0.5 * m * v^2
        },
        "5.56mm": {
            "mass_kg": 0.004,          # 4 grams (62 grain)
            "muzzle_velocity": 940.0,   # m/s
            "drag_coeff": 0.25,
            "max_range": 150.0,
            "base_damage": 75.0,
            "initial_energy_j": 1767.2,
        },
        "12gauge": {
            "mass_kg": 0.028,          # 28 grams (1 oz slug)
            "muzzle_velocity": 475.0,   # m/s
            "drag_coeff": 0.35,
            "max_range": 35.0,
            "base_damage": 110.0,
            "initial_energy_j": 3158.75,
        },
        ".357magnum": {
            "mass_kg": 0.010,
            "muzzle_velocity": 440.0,
            "drag_coeff": 0.18,
            "max_range": 65.0,
            "base_damage": 85.0,
            "initial_energy_j": 968.0,
        },
        ".308sniper": {
            "mass_kg": 0.011,
            "muzzle_velocity": 850.0,
            "drag_coeff": 0.30,
            "max_range": 300.0,
            "base_damage": 160.0,
            "initial_energy_j": 3973.75,
        },
        "arrow": {
            "mass_kg": 0.025,
            "muzzle_velocity": 90.0,
            "drag_coeff": 0.40,
            "max_range": 40.0,
            "base_damage": 75.0,
            "initial_energy_j": 101.25,
        },
    }

    TILE_MATERIALS = {
        TileType.WINDOW: MaterialResistance.GLASS,
        TileType.WINDOW_OPEN: MaterialResistance.GLASS,
        TileType.WINDOW_BROKEN: MaterialResistance.GLASS,
        TileType.CURTAIN_CLOSED: MaterialResistance.GLASS,

        TileType.DOOR: MaterialResistance.WOOD,
        TileType.DOOR_LOCKED: MaterialResistance.WOOD,
        TileType.WALL_WOOD: MaterialResistance.WOOD,
        TileType.FURNITURE: MaterialResistance.WOOD,
        TileType.TABLE: MaterialResistance.WOOD,
        TileType.CABINET: MaterialResistance.WOOD,
        TileType.BOOKSHELF: MaterialResistance.WOOD,
        TileType.OFFICE_DESK: MaterialResistance.WOOD,

        TileType.BUILDING_WALL: MaterialResistance.BRICK,
        TileType.WALL_BRICK: MaterialResistance.BRICK,

        TileType.UNDERGROUND_WALL: MaterialResistance.CONCRETE,
        TileType.WALL_CONCRETE: MaterialResistance.CONCRETE,

        TileType.WALL_REINFORCED: MaterialResistance.REINFORCED_METAL,
        TileType.WEAPON_SAFE: MaterialResistance.REINFORCED_METAL,
        TileType.GAS_PUMP: MaterialResistance.REINFORCED_METAL,
        TileType.LOCKER: MaterialResistance.REINFORCED_METAL,
    }

    @classmethod
    def get_tile_material(cls, tile_type: int) -> dict:
        """Returns the MaterialResistance properties dict for a given TileType."""
        return cls.TILE_MATERIALS.get(tile_type, MaterialResistance.BRICK)

    @classmethod
    def calculate_trajectory(cls, caliber: str, distance_m: float, wind_speed_kmh: float = 0.0, wind_angle_rad: float = 0.0) -> dict:
        """Calculates trajectory velocity decay, flight time, kinetic energy, wind drift, and bullet drop."""
        data = cls.CALIBERS.get(caliber, cls.CALIBERS["9mm"])
        v0 = data["muzzle_velocity"]
        m = data["mass_kg"]

        if RUST_BALLISTICS_AVAILABLE:
            b_drop, w_drift, final_v = RustBallisticsUtility.calculate_trajectory(v0, float(distance_m), float(wind_speed_kmh))
            damage_scale = max(0.2, final_v / v0)
            final_damage = data["base_damage"] * damage_scale
            return {
                "terminal_velocity_ms": round(final_v, 1),
                "flight_time_s": round(distance_m / max(50.0, (v0 + final_v) / 2.0), 3),
                "kinetic_energy_j": round(0.5 * m * (final_v ** 2), 1),
                "wind_drift_m": round(w_drift, 2),
                "bullet_drop_m": round(b_drop, 2),
                "damage": round(final_damage, 1),
            }

        cd = data["drag_coeff"]
        dist = max(0.1, float(distance_m))
        decay_factor = math.exp(-cd * (dist / 100.0))
        terminal_velocity = v0 * decay_factor
        flight_time = dist / max(50.0, (v0 + terminal_velocity) / 2.0)

        kinetic_energy = 0.5 * m * (terminal_velocity ** 2)

        crosswind_m_s = (wind_speed_kmh / 3.6) * math.sin(wind_angle_rad)
        wind_drift_m = 0.1 * crosswind_m_s * (flight_time ** 1.5)
        bullet_drop_m = 0.5 * 9.81 * (flight_time ** 2)

        damage_scale = max(0.2, terminal_velocity / v0)
        final_damage = data["base_damage"] * damage_scale

        return {
            "terminal_velocity_ms": round(terminal_velocity, 1),
            "flight_time_s": round(flight_time, 3),
            "kinetic_energy_j": round(kinetic_energy, 1),
            "wind_drift_m": round(wind_drift_m, 2),
            "bullet_drop_m": round(bullet_drop_m, 2),
            "damage": round(final_damage, 1),
        }

    @classmethod
    def simulate_bullet_flight(cls, world, start_x: float, start_y: float, start_z: int, angle_rad: float, caliber: str = "9mm",
                               wind_speed_kmh: float = 0.0, wind_angle_rad: float = 0.0,
                               targets: list = None, noise_events: list = None) -> dict:
        """
        Executes a step-by-step raycast projectile simulation:
        - Evaluates aerodynamic velocity decay, wind drift, bullet drop
        - Shatters glass windows (`WINDOW` -> `WINDOW_BROKEN`)
        - Overpenetrates walls/doors if kinetic energy > material resistance threshold
        - Performs shallow-angle (<35°) ricochet reflections on hard materials
        - Applies multi-target penetrating damage to entities in line of fire
        """
        data = cls.CALIBERS.get(caliber, cls.CALIBERS["9mm"])
        v0 = data["muzzle_velocity"]
        m = data["mass_kg"]
        cd = data["drag_coeff"]
        max_dist = data["max_range"]
        base_dmg = data["base_damage"]

        cur_x, cur_y, cur_z = float(start_x), float(start_y), int(start_z)
        cur_angle = float(angle_rad)
        cur_v = float(v0)
        cur_energy = 0.5 * m * (cur_v ** 2)

        w, h = world.width, world.height
        z_idx = world.z_to_idx(cur_z)
        grid_z = world.grid[z_idx]

        step_dist = 0.5  # 0.5m raycast increments
        traversed_dist = 0.0

        hits = []  # List of target hit dicts
        path = [(cur_x, cur_y, cur_z)]
        shattered_windows = []
        ricochets = []

        max_steps = int(max_dist / step_dist)
        ricochet_count = 0

        for step in range(max_steps):
            if cur_energy <= 10.0 or cur_v <= 15.0:
                break  # Bullet spent

            # Wind deflection drift
            crosswind_m_s = (wind_speed_kmh / 3.6) * math.sin(wind_angle_rad - cur_angle)
            drift_step = 0.005 * crosswind_m_s

            dx = math.cos(cur_angle) * step_dist - math.sin(cur_angle) * drift_step
            dy = math.sin(cur_angle) * step_dist + math.cos(cur_angle) * drift_step

            cur_x += dx
            cur_y += dy
            traversed_dist += step_dist

            tx, ty = int(cur_x), int(cur_y)
            path.append((cur_x, cur_y, cur_z))

            if not (0 <= tx < w and 0 <= ty < h):
                break  # Out of map bounds

            tile = grid_z[ty, tx]

            # 1. Check Tile Obstacle Collision
            from src.world.tiles import TILE_WALKABLE
            if not TILE_WALKABLE.get(tile, True) or tile in (TileType.WINDOW, TileType.DOOR, TileType.DOOR_LOCKED):
                mat = cls.get_tile_material(tile)
                req_energy = mat["resistance_j"]

                # Calculate incident surface angle relative to tile face
                normal_angle = math.atan2(float(ty - int(cur_y)), float(tx - int(cur_x)))
                incident_angle_deg = abs(math.degrees(cur_angle - normal_angle) % 180.0)

                # Check for Shallow Angle Ricochet (< 35° or > 145°)
                is_shallow = (incident_angle_deg < 35.0 or incident_angle_deg > 145.0)
                ricochet_prob = mat["ricochet_chance"] if is_shallow else (mat["ricochet_chance"] * 0.2)

                if is_shallow and ricochet_count < 2 and random.random() < ricochet_prob and cur_energy > 50.0 and not mat["breaks"]:
                    # Execute Ricochet Reflection
                    ricochet_count += 1
                    reflection_angle = (2.0 * normal_angle - cur_angle) + random.uniform(-0.1, 0.1)
                    cur_angle = reflection_angle % (2.0 * math.pi)

                    # Ricochet energy loss (40% energy retained)
                    cur_energy *= 0.40
                    cur_v = math.sqrt((2.0 * cur_energy) / m)

                    ricochets.append({
                        "pos": (cur_x, cur_y, cur_z),
                        "surface": mat["name"],
                        "remaining_energy_j": round(cur_energy, 1)
                    })

                    if noise_events is not None:
                        from src.entities.sensory import NoiseEvent
                        noise_events.append(NoiseEvent(cur_x, cur_y, cur_z, volume=25.0, source_type="ricochet"))
                    continue

                # Check Penetration
                if cur_energy >= req_energy:
                    # Overpenetrate material
                    cur_energy -= req_energy
                    cur_v = math.sqrt((2.0 * cur_energy) / m)

                    if mat["breaks"] and tile == TileType.WINDOW:
                        grid_z[ty, tx] = TileType.WINDOW_BROKEN
                        shattered_windows.append((tx, ty, cur_z))
                        if noise_events is not None:
                            from src.entities.sensory import NoiseEvent
                            noise_events.append(NoiseEvent(tx + 0.5, ty + 0.5, cur_z, volume=20.0, source_type="glass_shatter"))
                else:
                    # Bullet stopped by obstacle
                    break

            # 2. Check Entity Hits (Multi-Target Overpenetration)
            if targets:
                for target in targets:
                    if getattr(target, 'is_alive', True) and getattr(target, 'z', 0) == cur_z:
                        tdist = math.hypot(target.x - cur_x, target.y - cur_y)
                        if tdist < 0.6 and target not in [h["target"] for h in hits]:
                            dmg_scale = max(0.2, cur_v / v0)
                            hit_damage = base_dmg * dmg_scale * (cur_energy / data["initial_energy_j"])

                            actual_dmg = 0.0
                            if hasattr(target, 'take_targeted_damage'):
                                actual_dmg = target.take_targeted_damage(hit_damage, attacker_pos=(start_x, start_y, start_z))
                            elif hasattr(target, 'take_damage'):
                                target.take_damage(hit_damage)
                                actual_dmg = hit_damage

                            hits.append({
                                "target": target,
                                "damage": round(hit_damage, 1),
                                "actual_damage": round(actual_dmg, 1),
                                "pos": (cur_x, cur_y, cur_z),
                            })

                            # Overpenetration flesh resistance loss (100 Joules lost per entity hit)
                            cur_energy = max(0.0, cur_energy - MaterialResistance.FLESH["resistance_j"])
                            cur_v = math.sqrt((2.0 * cur_energy) / m) if cur_energy > 0 else 0.0

        return {
            "caliber": caliber,
            "traversed_distance_m": round(traversed_dist, 1),
            "final_velocity_ms": round(cur_v, 1),
            "final_energy_j": round(cur_energy, 1),
            "hits": hits,
            "ricochets": ricochets,
            "shattered_windows": shattered_windows,
            "path": path,
        }
