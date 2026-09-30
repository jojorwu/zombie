import math
import random

class ResourceItem:
    # Generic Resources
    FOOD = "food"
    WATER = "water"
    WOOD = "wood"
    METAL = "metal"
    FUEL = "fuel"
    MEDKIT = "medkit"
    WEAPON = "weapon"

    # 4 Melee Weapons
    KNIFE = "knife"
    AXE = "axe"
    BASEBALL_BAT = "baseball_bat"
    CROWBAR = "crowbar"

    # 3 Firearms
    PISTOL = "pistol"
    SHOTGUN = "shotgun"
    RIFLE = "rifle"

    # Ammunition
    PISTOL_AMMO = "pistol_ammo"
    SHOTGUN_SHELLS = "shotgun_shells"
    RIFLE_AMMO = "rifle_ammo"

    # 5 Specific Foods
    CANNED_FOOD = "canned_food"
    BREAD = "bread"
    APPLE = "apple"
    MEAT = "meat"
    MRE = "mre"

    # 6 Kitchen Items
    FRYING_PAN = "frying_pan"
    POT = "pot"
    CHEF_KNIFE = "chef_knife"
    CAN_OPENER = "can_opener"
    WATER_BOTTLE = "water_bottle"
    CUTTING_BOARD = "cutting_board"

# Detailed Properties for Weapons & Tools
WEAPON_STATS = {
    # Melee
    ResourceItem.KNIFE: {"damage": 25.0, "range": 1.2, "noise": 3.0, "type": "melee"},
    ResourceItem.CHEF_KNIFE: {"damage": 22.0, "range": 1.2, "noise": 3.0, "type": "melee"},
    ResourceItem.AXE: {"damage": 45.0, "range": 1.5, "noise": 8.0, "type": "melee"},
    ResourceItem.BASEBALL_BAT: {"damage": 30.0, "range": 1.6, "noise": 6.0, "type": "melee"},
    ResourceItem.CROWBAR: {"damage": 35.0, "range": 1.4, "noise": 7.0, "type": "melee"},
    ResourceItem.FRYING_PAN: {"damage": 28.0, "range": 1.3, "noise": 10.0, "type": "melee"},
    ResourceItem.WEAPON: {"damage": 35.0, "range": 1.8, "noise": 6.0, "type": "melee"},

    # Firearms
    ResourceItem.PISTOL: {"damage": 50.0, "range": 8.0, "ammo": ResourceItem.PISTOL_AMMO, "noise": 35.0, "type": "firearm"},
    ResourceItem.SHOTGUN: {"damage": 90.0, "range": 5.0, "ammo": ResourceItem.SHOTGUN_SHELLS, "noise": 55.0, "type": "firearm"},
    ResourceItem.RIFLE: {"damage": 120.0, "range": 14.0, "ammo": ResourceItem.RIFLE_AMMO, "noise": 45.0, "type": "firearm"},
}

from src.world import TileType

class NoiseEvent:
    def __init__(self, x, y, z, volume=10.0, lifetime=5, source_type="general"):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.volume = float(volume)
        self.lifetime = lifetime
        self.source_type = source_type

    def update(self):
        self.lifetime -= 1
        self.volume = max(0.0, self.volume - 0.5)

class ZombieState:
    IDLE = "idle"
    INVESTIGATE = "investigate"
    CHASE = "chase"
    ATTACK = "attack"

class ItemEntity:
    def __init__(self, x, y, item_type, amount=1, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.item_type = item_type
        self.amount = amount
        self.collected = False

class Vehicle:
    def __init__(self, x, y, fuel=100.0, max_fuel=100.0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.fuel = fuel
        self.max_fuel = max_fuel
        self.speed = 0.3
        self.driver = None  # Reference to Survivor if inside

    def is_occupied(self):
        return self.driver is not None

class Animal:
    def __init__(self, x, y, hp=30.0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.hp = hp
        self.max_hp = hp
        self.is_alive = True
        self.speed = 0.08

    def update(self, world):
        if not self.is_alive:
            return
        # Random wander
        angle = random.uniform(0, 2 * math.pi)
        nx = self.x + math.cos(angle) * self.speed
        ny = self.y + math.sin(angle) * self.speed
        if world.is_walkable(nx, ny, self.z):
            self.x, self.y = nx, ny

class ScentTrail:
    """Represents a survivor's olfactory trail left behind in the environment."""
    def __init__(self, x, y, z, intensity=100.0):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.intensity = intensity

    def update(self, world=None):
        decay = 1.0
        if world and world.weather.is_in_rain(self.x, self.y):
            decay = 4.0  # Rain rapidly washes away scent trails
        self.intensity -= decay

        if world and world.weather.wind_speed > 5.0:
            # Drift scent trail along wind vector
            drift_speed = (world.weather.wind_speed / 100.0) * 0.05
            self.x += math.cos(world.weather.wind_angle) * drift_speed
            self.y += math.sin(world.weather.wind_angle) * drift_speed

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
        for _ in range(steps):
            cx += dx
            cy += dy
            ix, iy = int(cx), int(cy)
            if 0 <= ix < world.width and 0 <= iy < world.height:
                tile = world.grid[z_idx, iy, ix]
                if tile in (TileType.BUILDING_WALL, TileType.UNDERGROUND_WALL, TileType.FURNITURE):
                    return False
        return True

    def check_vision(self, world, survivors):
        # Light sensitivity: Higher vision range during day/bright light, lower at night
        base_range = max(3.0, 14.0 * world.get_light_level())
        closest_surv = None
        min_d = base_range
        for s in survivors:
            if s.is_alive and not s.in_vehicle:
                d = math.hypot(s.x - self.x, s.y - self.y) + abs(s.z - self.z) * 3.0
                if d <= min_d and self.has_line_of_sight(s.x, s.y, s.z, world):
                    min_d = d
                    closest_surv = s
        return closest_surv

    def check_hearing(self, noise_events, world=None):
        """
        Evaluates acoustic propagation accounting for wall/door sound occlusion and distance attenuation.
        """
        if not noise_events:
            return None
        best_event = None
        max_audible = 0.0
        for ne in noise_events:
            dist = math.hypot(ne.x - self.x, ne.y - self.y) + abs(ne.z - self.z) * 2.0
            if dist <= ne.volume:
                attenuated_vol = ne.volume
                if world and abs(ne.z - self.z) <= 1:
                    # Raycast ray-attenuation through walls and doors
                    steps = max(1, int(dist))
                    dx = (self.x - ne.x) / steps
                    dy = (self.y - ne.y) / steps
                    cx, cy = ne.x, ne.y
                    z_idx = world.z_to_idx(self.z)
                    for _ in range(steps):
                        cx += dx
                        cy += dy
                        ix, iy = int(cx), int(cy)
                        if 0 <= ix < world.width and 0 <= iy < world.height:
                            tile = world.grid[z_idx, iy, ix]
                            if tile in (TileType.BUILDING_WALL, TileType.UNDERGROUND_WALL):
                                attenuated_vol *= 0.35  # Wall dampens 65% volume
                            elif tile == TileType.DOOR:
                                attenuated_vol *= 0.65  # Door dampens 35% volume

                audible_val = attenuated_vol - dist
                if audible_val > max_audible:
                    max_audible = audible_val
                    best_event = ne
        return best_event

    def check_scent(self, scent_trails):
        """Scans for nearby survivor scent trails to track prey by smell."""
        if not scent_trails:
            return None
        best_trail = None
        max_scent = 0.0
        for st in scent_trails:
            if st.z == self.z and st.intensity > 10.0:
                d = math.hypot(st.x - self.x, st.y - self.y)
                if d < 10.0:
                    scent_score = st.intensity / (d + 1.0)
                    if scent_score > max_scent:
                        max_scent = scent_score
                        best_trail = st
        return best_trail

    def compute_flocking_vector(self, all_zombies, neighbor_radius=6.0):
        """Horde / Flocking behavior: Cohesion and alignment with neighboring zombies."""
        sep_x, sep_y = 0.0, 0.0
        align_x, align_y = 0.0, 0.0
        count = 0
        for other in all_zombies:
            if other is not self and other.is_alive and other.z == self.z:
                d = math.hypot(other.x - self.x, other.y - self.y)
                if 0.1 < d < neighbor_radius:
                    count += 1
                    # Separation
                    sep_x += (self.x - other.x) / d
                    sep_y += (self.y - other.y) / d
                    # Cohesion towards horde center
                    align_x += (other.x - self.x)
                    align_y += (other.y - self.y)

        if count > 0:
            return (sep_x * 0.4 + align_x * 0.2), (sep_y * 0.4 + align_y * 0.2)
        return 0.0, 0.0

    def update(self, world, survivors, vehicles, noise_events=None, scent_trails=None, all_zombies=None):
        if not self.is_alive:
            return

        # 1. Vision Check (Light sensitive)
        seen_survivor = self.check_vision(world, survivors)
        if seen_survivor:
            self.state = ZombieState.CHASE
            self.target = (seen_survivor.x, seen_survivor.y, seen_survivor.z)
        else:
            if self.state == ZombieState.CHASE:
                self.state = ZombieState.INVESTIGATE
                self.investigate_pos = self.target
                self.target = None

            # 2. Hearing Check (Acoustics with wall occlusion)
            heard_noise = self.check_hearing(noise_events, world=world)
            if heard_noise and self.state != ZombieState.CHASE:
                self.state = ZombieState.INVESTIGATE
                self.investigate_pos = (heard_noise.x, heard_noise.y, heard_noise.z)

            # 3. Smell / Scent Trail Check
            elif self.state == ZombieState.IDLE and scent_trails:
                picked_scent = self.check_scent(scent_trails)
                if picked_scent:
                    self.state = ZombieState.INVESTIGATE
                    self.investigate_pos = (picked_scent.x, picked_scent.y, picked_scent.z)

        # 4. Movement Execution & Obstacle Avoidance
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
            flock_dx, flock_dy = self.compute_flocking_vector(all_zombies)

        if dest_pos:
            tx, ty, tz = dest_pos
            dir_x = ty - self.y
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

            # Smart obstacle avoidance step
            if world.is_walkable(nx, ny, nz):
                self.x, self.y, self.z = nx, ny, nz
            elif world.is_walkable(nx, self.y, nz):
                self.x, self.z = nx, nz
            elif world.is_walkable(self.x, ny, nz):
                self.y, self.z = ny, nz
        else:
            # Horde alignment during wandering
            if random.random() < 0.3:
                angle = random.uniform(0, 2 * math.pi)
                tile_mod = world.get_tile_speed_modifier(self.x, self.y, self.z)
                cur_speed = self.speed * tile_mod
                nx = self.x + (math.cos(angle) + flock_dx) * cur_speed
                ny = self.y + (math.sin(angle) + flock_dy) * cur_speed
                if world.is_walkable(nx, ny, self.z):
                    self.x, self.y = nx, ny

        # Attack adjacent survivor on same z level
        for survivor in survivors:
            if survivor.is_alive and not survivor.in_vehicle and survivor.z == self.z:
                dist = math.hypot(survivor.x - self.x, survivor.y - self.y)
                if dist < 0.8:
                    survivor.take_damage(self.damage)
                    self.state = ZombieState.ATTACK

class CraftingSystem:
    RECIPES = {
        ResourceItem.MEDKIT: {ResourceItem.WOOD: 1, ResourceItem.WATER: 1},
        ResourceItem.WEAPON: {ResourceItem.WOOD: 2, ResourceItem.METAL: 2},
    }

    @staticmethod
    def can_craft(inventory, item_type):
        recipe = CraftingSystem.RECIPES.get(item_type)
        if not recipe:
            return False
        for req_item, req_amount in recipe.items():
            if inventory.get(req_item, 0) < req_amount:
                return False
        return True

    @staticmethod
    def craft(inventory, item_type):
        if not CraftingSystem.can_craft(inventory, item_type):
            return False
        recipe = CraftingSystem.RECIPES[item_type]
        for req_item, req_amount in recipe.items():
            inventory[req_item] -= req_amount
        inventory[item_type] = inventory.get(item_type, 0) + 1
        return True

class Survivor:
    def __init__(self, x, y, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.health = 100.0
        self.hunger = 100.0
        self.thirst = 100.0
        self.sleep = 100.0
        self.energy = 100.0
        self.is_alive = True
        self.in_vehicle = None
        self.inventory = {
            ResourceItem.FOOD: 2,
            ResourceItem.WATER: 2,
            ResourceItem.WOOD: 0,
            ResourceItem.METAL: 0,
            ResourceItem.FUEL: 0,
            ResourceItem.MEDKIT: 0,
            ResourceItem.WEAPON: 0,
        }
        self.score = 0.0
        self.time_survived = 0
        self.kills = 0

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.is_alive = False

    def update_needs(self):
        if not self.is_alive:
            return
        self.time_survived += 1
        # Circadian decay rates calibrated for 24-hour in-game day (3,600 ticks)
        self.hunger -= 0.025
        self.thirst -= 0.035
        self.sleep -= 0.025

        if self.hunger <= 0:
            self.hunger = 0
            self.take_damage(0.2)
        if self.thirst <= 0:
            self.thirst = 0
            self.take_damage(0.3)
        if self.sleep <= 0:
            self.sleep = 0
            self.energy = max(0.0, self.energy - 0.2)

        # Auto consume food/water if severely depleted
        if self.hunger < 35:
            # Check specific foods first
            food_items = [ResourceItem.MRE, ResourceItem.CANNED_FOOD, ResourceItem.BREAD, ResourceItem.MEAT, ResourceItem.APPLE, ResourceItem.FOOD]
            for f_item in food_items:
                if self.inventory.get(f_item, 0) > 0:
                    # If canned food, check for can opener/chef knife or crowbar
                    if f_item == ResourceItem.CANNED_FOOD:
                        if self.inventory.get(ResourceItem.CAN_OPENER, 0) > 0 or self.inventory.get(ResourceItem.CHEF_KNIFE, 0) > 0 or self.inventory.get(ResourceItem.KNIFE, 0) > 0:
                            self.inventory[f_item] -= 1
                            self.hunger = min(100.0, self.hunger + 50)
                            break
                    else:
                        gain = 50.0 if f_item in (ResourceItem.MRE, ResourceItem.MEAT) else 35.0
                        self.inventory[f_item] -= 1
                        self.hunger = min(100.0, self.hunger + gain)
                        break

        if self.thirst < 35:
            water_items = [ResourceItem.WATER_BOTTLE, ResourceItem.WATER]
            for w_item in water_items:
                if self.inventory.get(w_item, 0) > 0:
                    self.inventory[w_item] -= 1
                    self.thirst = min(100.0, self.thirst + 45)
                    break

        self.score += 0.1

    def move(self, dx, dy, world, noise_events=None, dz=0):
        if not self.is_alive:
            return
        base_speed = 0.15
        if self.in_vehicle:
            if self.in_vehicle.fuel > 0:
                base_speed = self.in_vehicle.speed
                self.in_vehicle.fuel -= 0.05
            else:
                base_speed = 0.05  # Slow without fuel

        # Factor in wind speed/direction and rain wetness
        tile_mod = world.get_tile_speed_modifier(self.x, self.y, self.z)

        # Calculate movement vector dot product with wind vector
        wind_vx = math.cos(world.weather.wind_angle)
        wind_vy = math.sin(world.weather.wind_angle)
        move_dot_wind = dx * wind_vx + dy * wind_vy
        wind_factor = 1.0 + (move_dot_wind * (world.weather.wind_speed / 200.0))  # Tailward boost vs headwind resistance

        # Check wetness in rain
        is_raining = world.weather.is_in_rain(self.x, self.y)
        rain_factor = 0.85 if (is_raining and not self.in_vehicle) else 1.0

        speed = base_speed * tile_mod * wind_factor * rain_factor

        nx = self.x + dx * speed
        ny = self.y + dy * speed
        target_z = max(world.z_min, min(world.z_max, int(round(self.z + dz))))

        moved = False
        if world.is_walkable(nx, ny, target_z):
            self.x, self.y = nx, ny
            self.z = target_z
            moved = True
            if self.in_vehicle:
                self.in_vehicle.x, self.in_vehicle.y, self.in_vehicle.z = self.x, self.y, self.z
        elif world.is_walkable(nx, ny, self.z):
            self.x, self.y = nx, ny
            moved = True
            if self.in_vehicle:
                self.in_vehicle.x, self.in_vehicle.y, self.in_vehicle.z = self.x, self.y, self.z

        if moved and noise_events is not None:
            vol = 15.0 if self.in_vehicle else 3.0
            noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=vol, source_type="movement"))

    def perform_action(self, action, world, items, vehicles, zombies, animals, survivors, noise_events=None):
        # Actions:
        # 0 = None
        # 1 = Gather
        # 2 = Craft Medkit
        # 3 = Craft Weapon
        # 4 = Enter/Exit Vehicle
        # 5 = Sleep
        # 6 = Attack Zombie/Animal/Survivor
        # 7 = Stairs Up (Go up floor)
        # 8 = Stairs Down (Go down floor)
        if not self.is_alive:
            return

        if action == 1:  # Gather nearby items & search adjacent furniture containers
            gathered = False
            for item in items:
                if not item.collected and item.z == self.z and math.hypot(item.x - self.x, item.y - self.y) < 1.5:
                    item.collected = True
                    self.inventory[item.item_type] = self.inventory.get(item.item_type, 0) + item.amount
                    self.score += 5.0
                    gathered = True

            # Search adjacent furniture containers (Cabinets, Refrigerators, Counters)
            if not gathered and world:
                z_idx = world.z_to_idx(self.z)
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    fx, fy = int(self.x + dx), int(self.y + dy)
                    if 0 <= fx < world.width and 0 <= fy < world.height:
                        ftile = world.grid[z_idx, fy, fx]
                        if ftile in (TileType.CABINET, TileType.REFRIGERATOR, TileType.KITCHEN_COUNTER, TileType.TABLE):
                            # Spawn searched container loot on survivor
                            if ftile == TileType.REFRIGERATOR:
                                found_item = random.choice([ResourceItem.MEAT, ResourceItem.BREAD, ResourceItem.WATER_BOTTLE, ResourceItem.APPLE])
                            elif ftile == TileType.CABINET:
                                found_item = random.choice([ResourceItem.CANNED_FOOD, ResourceItem.CAN_OPENER, ResourceItem.PISTOL_AMMO, ResourceItem.MEDKIT])
                            else:
                                found_item = random.choice([ResourceItem.CHEF_KNIFE, ResourceItem.FRYING_PAN, ResourceItem.POT, ResourceItem.CUTTING_BOARD])

                            self.inventory[found_item] = self.inventory.get(found_item, 0) + 1
                            self.score += 10.0
                            if noise_events is not None:
                                noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=5.0, source_type="searching"))
                            break

        elif action == 2:  # Craft Medkit
            if CraftingSystem.craft(self.inventory, ResourceItem.MEDKIT):
                self.score += 10.0
                if noise_events is not None:
                    noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=8.0, source_type="crafting"))

        elif action == 3:  # Craft Weapon
            if CraftingSystem.craft(self.inventory, ResourceItem.WEAPON):
                self.score += 10.0
                if noise_events is not None:
                    noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=8.0, source_type="crafting"))

        elif action == 4:  # Enter/Exit Vehicle
            if self.in_vehicle:
                self.in_vehicle.driver = None
                self.in_vehicle = None
            else:
                for v in vehicles:
                    if not v.is_occupied() and v.z == self.z and math.hypot(v.x - self.x, v.y - self.y) < 1.5:
                        if self.inventory.get(ResourceItem.FUEL, 0) > 0 and v.fuel < v.max_fuel:
                            fuel_needed = v.max_fuel - v.fuel
                            have_fuel = self.inventory[ResourceItem.FUEL] * 20.0
                            added = min(fuel_needed, have_fuel)
                            v.fuel += added
                            self.inventory[ResourceItem.FUEL] -= int(added / 20.0)
                        self.in_vehicle = v
                        v.driver = self
                        break

        elif action == 5:  # Sleep
            self.sleep = min(100.0, self.sleep + 1.0)
            self.energy = min(100.0, self.energy + 1.0)

        elif action == 6:  # Attack closest zombie, animal, or rival survivor using best available weapon/firearm
            best_weapon = None
            is_firearm = False
            ammo_type = None

            # Check Firearms first if ammo is available
            firearms = [ResourceItem.RIFLE, ResourceItem.SHOTGUN, ResourceItem.PISTOL]
            for fa in firearms:
                if self.inventory.get(fa, 0) > 0:
                    req_ammo = WEAPON_STATS[fa]["ammo"]
                    if self.inventory.get(req_ammo, 0) > 0:
                        best_weapon = fa
                        is_firearm = True
                        ammo_type = req_ammo
                        break

            # Fallback to melee weapons
            if not best_weapon:
                melee_options = [ResourceItem.AXE, ResourceItem.CROWBAR, ResourceItem.BASEBALL_BAT, ResourceItem.FRYING_PAN, ResourceItem.KNIFE, ResourceItem.CHEF_KNIFE, ResourceItem.WEAPON]
                for mw in melee_options:
                    if self.inventory.get(mw, 0) > 0:
                        best_weapon = mw
                        break

            w_stats = WEAPON_STATS.get(best_weapon, {"damage": 15.0, "range": 1.0, "noise": 4.0})
            attack_range = w_stats["range"]
            damage = w_stats["damage"]
            noise_vol = w_stats["noise"]

            if is_firearm and ammo_type:
                self.inventory[ammo_type] -= 1  # Consume ammo round

                # Wind deflection on bullet ballistics
                wind_deflect_x = math.cos(world.weather.wind_angle) * (world.weather.wind_speed / 100.0) * 0.5
                wind_deflect_y = math.sin(world.weather.wind_angle) * (world.weather.wind_speed / 100.0) * 0.5

                # Spawn muzzle flash dynamic light source
                from src.world import DynamicLight
                world.dynamic_lights.append(DynamicLight(self.x, self.y, self.z, radius=12.0, color=(255, 200, 100), intensity=1.5, lifetime=2))

            if self.in_vehicle and self.in_vehicle.fuel > 0:
                attack_range = 1.5
                damage = 60.0
                noise_vol = 20.0

            attacked = False
            # Bullet raycast / hit detection for closest hostile target
            for z in zombies:
                if z.is_alive and z.z == self.z and math.hypot(z.x - self.x, z.y - self.y) <= attack_range:
                    z.hp -= damage
                    if z.hp <= 0:
                        z.is_alive = False
                        self.kills += 1
                        self.score += 20.0
                    attacked = True
                    if noise_events is not None:
                        noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=noise_vol, source_type="attack"))
                    break

            if not attacked:
                for a in animals:
                    if a.is_alive and a.z == self.z and math.hypot(a.x - self.x, a.y - self.y) <= attack_range:
                        a.hp -= damage
                        if a.hp <= 0:
                            a.is_alive = False
                            self.inventory[ResourceItem.MEAT] = self.inventory.get(ResourceItem.MEAT, 0) + 2
                            self.score += 15.0
                        attacked = True
                        if noise_events is not None:
                            noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=noise_vol, source_type="attack"))
                        break

            if not attacked:
                for other in survivors:
                    if other is not self and other.is_alive and other.z == self.z and math.hypot(other.x - self.x, other.y - self.y) <= attack_range:
                        other.take_damage(damage)
                        if not other.is_alive:
                            self.kills += 1
                            self.score += 30.0
                        if noise_events is not None:
                            noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=noise_vol, source_type="attack"))
                        break

        elif action == 7:  # Stairs Up
            if self.z < world.num_levels - 1 and world.is_walkable(self.x, self.y, self.z + 1):
                self.z += 1
                if self.in_vehicle:
                    self.in_vehicle.z = self.z

        elif action == 8:  # Stairs Down
            if self.z > 0 and world.is_walkable(self.x, self.y, self.z - 1):
                self.z -= 1
                if self.in_vehicle:
                    self.in_vehicle.z = self.z
