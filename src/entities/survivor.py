import math
import random
import threading
from src.world import TileType, DynamicLight
from src.entities.item import ResourceItem, WEAPON_STATS
from src.entities.sensory import NoiseEvent
from src.entities.crafting import CraftingSystem
from src.entities.health import AnatomicalHealth, BodyPart
from utils.ballistics_utility import BallisticsUtility
from utils.sound_utility import SoundUtility


class EmotionalState:
    CALM = "CALM"
    CONFIDENT = "CONFIDENT"
    PANICKED = "PANICKED"
    TERRIFIED = "TERRIFIED"
    ENRAGED = "ENRAGED"


class Survivor:
    def __init__(self, x, y, z=0):
        self._lock = threading.Lock()
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)

        self.body = AnatomicalHealth()
        self.hunger = 100.0
        self.thirst = 100.0
        self.sleep = 100.0
        self.energy = 100.0
        self.is_alive = True
        self.in_vehicle = None

        self.fear = 0.0
        self.panic = 0.0
        self.morale = 80.0
        self.emotional_state = EmotionalState.CALM

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

    @property
    def health(self):
        return self.body.overall_health_percent

    @health.setter
    def health(self, val):
        pass

    def take_damage(self, amount, target_part=None):
        with self._lock:
            hit_part, actual_damage, crippled = self.body.apply_targeted_damage(amount, target_part)
            self.fear = min(100.0, self.fear + actual_damage * 1.2)
            self.panic = min(100.0, self.panic + actual_damage * 1.5)
            self.morale = max(0.0, self.morale - actual_damage * 0.5)

            if self.body.is_dead:
                self.is_alive = False

    def update_emotions(self, world, zombies, noise_events=None):
        light = world.get_light_level(self.z)
        if light < 0.3:
            self.fear = min(100.0, self.fear + 0.15)

        nearby_zombie_count = 0
        for z in zombies:
            if z.is_alive and z.z == self.z:
                d = math.hypot(z.x - self.x, z.y - self.y)
                if d < 8.0:
                    nearby_zombie_count += 1

        if nearby_zombie_count > 0:
            self.fear = min(100.0, self.fear + nearby_zombie_count * 0.4)
            if nearby_zombie_count >= 3:
                self.panic = min(100.0, self.panic + 0.8)
        else:
            self.fear = max(0.0, self.fear - 0.2)
            self.panic = max(0.0, self.panic - 0.3)

        if self.kills > 0 and self.fear < 30.0:
            self.morale = min(100.0, self.morale + 0.05)

        if self.panic > 70.0 or self.fear > 80.0:
            self.emotional_state = EmotionalState.TERRIFIED
        elif self.panic > 40.0:
            self.emotional_state = EmotionalState.PANICKED
        elif self.morale > 75.0 and self.fear < 20.0:
            self.emotional_state = EmotionalState.CONFIDENT
        elif self.panic > 20.0 and self.morale < 30.0:
            self.emotional_state = EmotionalState.ENRAGED
        else:
            self.emotional_state = EmotionalState.CALM

    def update_needs(self):
        if not self.is_alive:
            return
        self.time_survived += 1

        self.body.update_bleeding()
        if self.body.is_dead:
            self.is_alive = False
            return

        self.hunger -= 0.025
        self.thirst -= 0.035
        self.sleep -= 0.025

        if self.hunger <= 0:
            self.hunger = 0
            self.take_damage(0.2, BodyPart.TORSO)
        if self.thirst <= 0:
            self.thirst = 0
            self.take_damage(0.3, BodyPart.TORSO)
        if self.sleep <= 0:
            self.sleep = 0
            self.energy = max(0.0, self.energy - 0.2)

        if self.hunger < 35:
            food_items = [ResourceItem.MRE, ResourceItem.CANNED_FOOD, ResourceItem.BREAD, ResourceItem.MEAT, ResourceItem.APPLE, ResourceItem.FOOD]
            for f_item in food_items:
                if self.inventory.get(f_item, 0) > 0:
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

        if self.inventory.get(ResourceItem.MEDKIT, 0) > 0 and self.body.total_bleeding > 0:
            self.inventory[ResourceItem.MEDKIT] -= 1
            self.body.treat_wounds()

        self.score += 0.1

    def move(self, dx, dy, world, noise_events=None, dz=0):
        if not self.is_alive:
            return
        base_speed = 0.15 * self.body.movement_speed_multiplier

        if self.emotional_state == EmotionalState.PANICKED:
            base_speed *= 1.15
        elif self.emotional_state == EmotionalState.TERRIFIED:
            base_speed *= 0.85

        if self.in_vehicle:
            if self.in_vehicle.fuel > 0:
                base_speed = self.in_vehicle.speed
                self.in_vehicle.fuel -= 0.05
            else:
                base_speed = 0.05

        tile_mod = world.get_tile_speed_modifier(self.x, self.y, self.z)

        wind_vx = math.cos(world.weather.wind_angle)
        wind_vy = math.sin(world.weather.wind_angle)
        move_dot_wind = dx * wind_vx + dy * wind_vy
        wind_factor = 1.0 + (move_dot_wind * (world.weather.wind_speed / 200.0))

        is_raining = world.weather.is_in_rain(self.x, self.y)
        rain_factor = 0.85 if (is_raining and not self.in_vehicle) else 1.0

        season_factor = 0.8 if getattr(world.weather, 'season', None) == "Winter" else 1.0

        speed = base_speed * tile_mod * wind_factor * rain_factor * season_factor

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
            vol = 17.0 if self.in_vehicle else 8.0
            stype = "vehicle_engine" if self.in_vehicle else "footsteps"
            noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=vol, source_type=stype))

    def perform_action(self, action, world, items, vehicles, zombies, animals, survivors, noise_events=None):
        if not self.is_alive:
            return

        self.update_emotions(world, zombies, noise_events=noise_events)

        if action == 1:
            from utils.p_np_math import PolynomialKnapsackSolver
            nearby_items = [
                item for item in items
                if not item.collected and item.z == self.z and math.hypot(item.x - self.x, item.y - self.y) < 1.5
            ]

            if nearby_items:
                optimal_subset = PolynomialKnapsackSolver.optimize_inventory(nearby_items, max_capacity=15)
                for item in optimal_subset:
                    item.collected = True
                    self.inventory[item.item_type] = self.inventory.get(item.item_type, 0) + item.amount
                    self.score += 5.0
            else:
                if world:
                    z_idx = world.z_to_idx(self.z)
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        fx, fy = int(self.x + dx), int(self.y + dy)
                        if 0 <= fx < world.width and 0 <= fy < world.height:
                            ftile = world.grid[z_idx, fy, fx]
                            if ftile in (TileType.CABINET, TileType.REFRIGERATOR, TileType.KITCHEN_COUNTER, TileType.TABLE):
                                if ftile == TileType.REFRIGERATOR:
                                    found_item = random.choice([ResourceItem.MEAT, ResourceItem.BREAD, ResourceItem.WATER_BOTTLE, ResourceItem.APPLE])
                                elif ftile == TileType.CABINET:
                                    found_item = random.choice([ResourceItem.CANNED_FOOD, ResourceItem.CAN_OPENER, ResourceItem.PISTOL_AMMO, ResourceItem.MEDKIT])
                                else:
                                    found_item = random.choice([ResourceItem.CHEF_KNIFE, ResourceItem.FRYING_PAN, ResourceItem.POT, ResourceItem.CUTTING_BOARD])

                                self.inventory[found_item] = self.inventory.get(found_item, 0) + 1
                                self.score += 10.0
                                if noise_events is not None:
                                    noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=11.0, source_type="dismantling"))
                                break

        elif action == 2:
            if CraftingSystem.craft(self.inventory, ResourceItem.MEDKIT):
                self.score += 10.0
                if noise_events is not None:
                    noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=11.0, source_type="crafting"))

        elif action == 3:
            if CraftingSystem.craft(self.inventory, ResourceItem.WEAPON):
                self.score += 10.0
                if noise_events is not None:
                    noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=11.0, source_type="crafting"))

        elif action == 4:
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

        elif action == 5:
            self.sleep = min(100.0, self.sleep + 1.0)
            self.energy = min(100.0, self.energy + 1.0)
            self.fear = max(0.0, self.fear - 0.5)
            self.panic = max(0.0, self.panic - 0.8)

        elif action == 6:
            best_weapon = None
            is_firearm = False
            ammo_type = None

            firearms = [ResourceItem.RIFLE, ResourceItem.SHOTGUN, ResourceItem.PISTOL]
            for fa in firearms:
                if self.inventory.get(fa, 0) > 0:
                    req_ammo = WEAPON_STATS[fa]["ammo"]
                    if self.inventory.get(req_ammo, 0) > 0:
                        best_weapon = fa
                        is_firearm = True
                        ammo_type = req_ammo
                        break

            if not best_weapon:
                melee_options = [ResourceItem.AXE, ResourceItem.CROWBAR, ResourceItem.BASEBALL_BAT, ResourceItem.FRYING_PAN, ResourceItem.KNIFE, ResourceItem.CHEF_KNIFE, ResourceItem.WEAPON]
                for mw in melee_options:
                    if self.inventory.get(mw, 0) > 0:
                        best_weapon = mw
                        break

            w_stats = WEAPON_STATS.get(best_weapon, {"damage": 15.0, "range": 1.0, "noise": 4.0})
            attack_range = w_stats["range"]
            damage = w_stats["damage"] * self.body.attack_damage_multiplier
            stype = "pistol_shot"

            if is_firearm and ammo_type:
                caliber_map = {
                    ResourceItem.RIFLE: "5.56mm",
                    ResourceItem.SHOTGUN: "12gauge",
                    ResourceItem.PISTOL: "9mm",
                }
                stype_map = {
                    ResourceItem.RIFLE: "rifle_shot",
                    ResourceItem.SHOTGUN: "shotgun_shot",
                    ResourceItem.PISTOL: "pistol_shot",
                }
                stype = stype_map.get(best_weapon, "pistol_shot")
                caliber = caliber_map.get(best_weapon, "9mm")
                ballistics = BallisticsUtility.calculate_trajectory(
                    caliber,
                    distance_m=attack_range * 10.0,
                    wind_speed_kmh=world.weather.wind_speed,
                    wind_angle_rad=world.weather.wind_angle
                )
                damage = ballistics["damage"] * self.body.attack_damage_multiplier

            if self.emotional_state == EmotionalState.PANICKED and random.random() < 0.25:
                damage *= 0.5
            elif self.emotional_state == EmotionalState.TERRIFIED and random.random() < 0.50:
                damage = 0.0

            if is_firearm and ammo_type:
                self.inventory[ammo_type] -= 1
                world.dynamic_lights.append(DynamicLight(self.x, self.y, self.z, radius=12.0, color=(255, 200, 100), intensity=1.5, lifetime=2))

            if self.in_vehicle and self.in_vehicle.fuel > 0:
                attack_range = 1.5
                damage = 60.0

            attacked = False
            for z in zombies:
                if z.is_alive and z.z == self.z and math.hypot(z.x - self.x, z.y - self.y) <= attack_range:
                    z.take_targeted_damage(damage)
                    if not z.is_alive:
                        self.kills += 1
                        self.score += 20.0
                        self.fear = max(0.0, self.fear - 15.0)
                        self.panic = max(0.0, self.panic - 20.0)
                        self.morale = min(100.0, self.morale + 10.0)
                    attacked = True
                    if noise_events is not None:
                        noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=31.0, source_type=stype))
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
                            noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=31.0, source_type=stype))
                        break

            if not attacked:
                for other in survivors:
                    if other is not self and other.is_alive and other.z == self.z and math.hypot(other.x - self.x, other.y - self.y) <= attack_range:
                        other.take_damage(damage)
                        if not other.is_alive:
                            self.kills += 1
                            self.score += 30.0
                        if noise_events is not None:
                            noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=31.0, source_type=stype))
                        break

        elif action == 7:
            if self.z < world.num_levels - 1 and world.is_walkable(self.x, self.y, self.z + 1):
                self.z += 1
                if self.in_vehicle:
                    self.in_vehicle.z = self.z

        elif action == 8:
            if self.z > 0 and world.is_walkable(self.x, self.y, self.z - 1):
                self.z -= 1
                if self.in_vehicle:
                    self.in_vehicle.z = self.z

        elif action == 9:
            from utils.tile_interaction_utility import TileInteractionUtility
            pushed = False
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                fx, fy = int(self.x + dx), int(self.y + dy)
                if TileInteractionUtility.push_furniture(world, fx, fy, self.z, dx, dy):
                    self.score += 8.0
                    pushed = True
                    if noise_events is not None:
                        noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=14.0, source_type="furniture_push"))
                    break

        elif action == 10:
            from utils.tile_interaction_utility import TileInteractionUtility
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                fx, fy = int(self.x + dx), int(self.y + dy)
                success, w_amt, m_amt = TileInteractionUtility.dismantle_furniture(world, fx, fy, self.z, self.inventory)
                if success:
                    self.score += 12.0
                    if noise_events is not None:
                        noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=15.0, source_type="dismantling"))
                    break
