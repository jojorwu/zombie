import math
import random

class ResourceItem:
    FOOD = "food"
    WATER = "water"
    WOOD = "wood"
    METAL = "metal"
    FUEL = "fuel"
    MEDKIT = "medkit"
    WEAPON = "weapon"

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
        steps = int(ceil(dist * 2)) if 'ceil' in globals() else int(dist * 2) + 1
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
        base_range = max(3.0, 12.0 * world.get_light_level())
        closest_surv = None
        min_d = base_range
        for s in survivors:
            if s.is_alive and not s.in_vehicle:
                d = math.hypot(s.x - self.x, s.y - self.y) + abs(s.z - self.z) * 3.0
                if d <= min_d and self.has_line_of_sight(s.x, s.y, s.z, world):
                    min_d = d
                    closest_surv = s
        return closest_surv

    def check_hearing(self, noise_events):
        if not noise_events:
            return None
        best_event = None
        max_audible = 0.0
        for ne in noise_events:
            d = math.hypot(ne.x - self.x, ne.y - self.y) + abs(ne.z - self.z) * 2.0
            if d <= ne.volume:
                audible_val = ne.volume - d
                if audible_val > max_audible:
                    max_audible = audible_val
                    best_event = ne
        return best_event

    def update(self, world, survivors, vehicles, noise_events=None):
        if not self.is_alive:
            return

        # 1. Vision Check
        seen_survivor = self.check_vision(world, survivors)
        if seen_survivor:
            self.state = ZombieState.CHASE
            self.target = (seen_survivor.x, seen_survivor.y, seen_survivor.z)
        else:
            if self.state == ZombieState.CHASE:
                self.state = ZombieState.INVESTIGATE
                self.investigate_pos = self.target
                self.target = None

            # 2. Hearing Check
            heard_noise = self.check_hearing(noise_events)
            if heard_noise and self.state != ZombieState.CHASE:
                self.state = ZombieState.INVESTIGATE
                self.investigate_pos = (heard_noise.x, heard_noise.y, heard_noise.z)

        # 3. State Execution
        dest_pos = None
        if self.state == ZombieState.CHASE and self.target:
            dest_pos = self.target
        elif self.state == ZombieState.INVESTIGATE and self.investigate_pos:
            dest_pos = self.investigate_pos
            if math.hypot(self.x - dest_pos[0], self.y - dest_pos[1]) < 0.8 and self.z == dest_pos[2]:
                self.state = ZombieState.IDLE
                self.investigate_pos = None

        if dest_pos:
            tx, ty, tz = dest_pos
            angle = math.atan2(ty - self.y, tx - self.x)
            nx = self.x + math.cos(angle) * self.speed
            ny = self.y + math.sin(angle) * self.speed

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
            elif world.is_walkable(nx, ny, self.z):
                self.x, self.y = nx, ny
        else:
            # Idle wander
            if random.random() < 0.2:
                angle = random.uniform(0, 2 * math.pi)
                nx = self.x + math.cos(angle) * self.speed
                ny = self.y + math.sin(angle) * self.speed
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
        if self.hunger < 30 and self.inventory.get(ResourceItem.FOOD, 0) > 0:
            self.inventory[ResourceItem.FOOD] -= 1
            self.hunger = min(100.0, self.hunger + 40)
        if self.thirst < 30 and self.inventory.get(ResourceItem.WATER, 0) > 0:
            self.inventory[ResourceItem.WATER] -= 1
            self.thirst = min(100.0, self.thirst + 40)

        self.score += 0.1

    def move(self, dx, dy, world, noise_events=None, dz=0):
        if not self.is_alive:
            return
        speed = 0.15
        if self.in_vehicle:
            if self.in_vehicle.fuel > 0:
                speed = self.in_vehicle.speed
                self.in_vehicle.fuel -= 0.05
            else:
                speed = 0.05  # Slow without fuel

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

        if action == 1:  # Gather nearby items
            for item in items:
                if not item.collected and item.z == self.z and math.hypot(item.x - self.x, item.y - self.y) < 1.2:
                    item.collected = True
                    self.inventory[item.item_type] = self.inventory.get(item.item_type, 0) + item.amount
                    self.score += 5.0

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

        elif action == 6:  # Attack closest zombie, animal, or rival survivor
            has_weapon = self.inventory.get(ResourceItem.WEAPON, 0) > 0
            attack_range = 2.5 if has_weapon else 1.0
            damage = 35.0 if has_weapon else 15.0

            if self.in_vehicle and self.in_vehicle.fuel > 0:
                attack_range = 1.5
                damage = 60.0

            attacked = False
            for z in zombies:
                if z.is_alive and z.z == self.z and math.hypot(z.x - self.x, z.y - self.y) <= attack_range:
                    z.hp -= damage
                    if z.hp <= 0:
                        z.is_alive = False
                        self.kills += 1
                        self.score += 20.0
                    attacked = True
                    if noise_events is not None:
                        vol = 25.0 if has_weapon else 6.0
                        noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=vol, source_type="attack"))
                    break

            if not attacked:
                for a in animals:
                    if a.is_alive and a.z == self.z and math.hypot(a.x - self.x, a.y - self.y) <= attack_range:
                        a.hp -= damage
                        if a.hp <= 0:
                            a.is_alive = False
                            self.inventory[ResourceItem.FOOD] = self.inventory.get(ResourceItem.FOOD, 0) + 3
                            self.score += 15.0
                        attacked = True
                        break

            if not attacked:
                for other in survivors:
                    if other is not self and other.is_alive and other.z == self.z and math.hypot(other.x - self.x, other.y - self.y) <= attack_range:
                        other.take_damage(damage)
                        if not other.is_alive:
                            self.kills += 1
                            self.score += 30.0
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
