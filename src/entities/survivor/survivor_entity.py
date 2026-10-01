import math
import threading
from src.entities.item import ResourceItem
from src.entities.sensory import NoiseEvent
from src.entities.crafting import CraftingSystem
from src.entities.health import AnatomicalHealth, BodyPart
from src.entities.survivor.survivor_state import EmotionalState
from src.entities.survivor.survivor_looting import SurvivorLooting
from src.entities.survivor.survivor_actions import SurvivorActions


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

        self.is_infected = False
        self.infection_progress = 0.0
        self.grab_slowdown_timer = 0
        self.grab_slowdown_factor = 1.0

        self.facing_angle = 0.0
        self.visited_tiles = set()
        self.discovered_tiles = set()
        self.visited_tiles.add((int(x), int(y), int(z)))
        self.discovered_tiles.add((int(x), int(y), int(z)))

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

    def calculate_fitness(self) -> float:
        """
        Calculates holistic evolution fitness:
        - Survival duration
        - Exploration coverage (visited unique tiles)
        - Zombie kill efficiency
        - Average physiological & mental state (health, hunger, thirst, sleep, morale)
        """
        exploration_score = len(self.visited_tiles) * 1.5
        avg_condition = (self.health + self.hunger + self.thirst + self.sleep + self.morale) / 5.0
        condition_bonus = (avg_condition / 100.0) * (self.time_survived * 0.2)
        kill_score = self.kills * 40.0
        survival_score = self.time_survived * 0.5

        return survival_score + exploration_score + kill_score + condition_bonus + self.score

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

        nearby_zombie_count = sum(1 for z in zombies if z.is_alive and z.z == self.z and math.hypot(z.x - self.x, z.y - self.y) < 8.0)

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

        if self.grab_slowdown_timer > 0:
            self.grab_slowdown_timer -= 1
            if self.grab_slowdown_timer <= 0:
                self.grab_slowdown_factor = 1.0

        if self.is_infected:
            self.infection_progress = min(100.0, self.infection_progress + 0.1)
            self.take_damage(0.1, BodyPart.TORSO)
            if self.infection_progress >= 100.0:
                self.is_alive = False

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
            food_items = [
                ResourceItem.STEAK, ResourceItem.STEW, ResourceItem.CANNED_TUNA, ResourceItem.CANNED_BEANS,
                ResourceItem.MRE, ResourceItem.CANNED_FOOD, ResourceItem.CHOCOLATE, ResourceItem.CEREAL,
                ResourceItem.BREAD, ResourceItem.MEAT, ResourceItem.APPLE, ResourceItem.FOOD, ResourceItem.BERRIES, ResourceItem.MUSHROOM
            ]
            for f_item in food_items:
                if self.inventory.get(f_item, 0) > 0:
                    if f_item in (ResourceItem.CANNED_FOOD, ResourceItem.CANNED_BEANS, ResourceItem.CANNED_TUNA):
                        if self.inventory.get(ResourceItem.CAN_OPENER, 0) > 0 or self.inventory.get(ResourceItem.CHEF_KNIFE, 0) > 0 or self.inventory.get(ResourceItem.KNIFE, 0) > 0:
                            self.inventory[f_item] -= 1
                            self.hunger = min(100.0, self.hunger + 55)
                            break
                    else:
                        gain = 55.0 if f_item in (ResourceItem.STEAK, ResourceItem.STEW, ResourceItem.MRE, ResourceItem.MEAT) else 35.0
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
        base_speed = 0.15 * self.body.movement_speed_multiplier * self.grab_slowdown_factor

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

        if abs(dx) > 0.001 or abs(dy) > 0.001:
            self.facing_angle = math.atan2(dy, dx)

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
        elif world.is_walkable(nx, self.y, self.z):
            self.x = nx
            moved = True
            if self.in_vehicle:
                self.in_vehicle.x = self.x
        elif world.is_walkable(self.x, ny, self.z):
            self.y = ny
            moved = True
            if self.in_vehicle:
                self.in_vehicle.y = self.y

        if moved:
            self.visited_tiles.add((int(self.x), int(self.y), int(self.z)))
            current_fov = world.compute_fog_of_war(self.x, self.y, radius=8, z=self.z, facing_angle=self.facing_angle, fov_degrees=180.0)
            for tx, ty in current_fov:
                self.discovered_tiles.add((tx, ty, self.z))
            if noise_events is not None:
                vol = 17.0 if self.in_vehicle else 8.0
                stype = "vehicle_engine" if self.in_vehicle else "footsteps"
                noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=vol, source_type=stype))

    def perform_action(self, action, world, items, vehicles, zombies, animals, survivors, noise_events=None):
        """Action dispatcher executing survivor AI decisions."""
        if not self.is_alive:
            return

        self.update_emotions(world, zombies, noise_events=noise_events)

        if action == 1:
            SurvivorLooting.gather(self, world, items, noise_events)
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
            SurvivorActions.attack(self, world, zombies, animals, survivors, noise_events)
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
            SurvivorActions.push_furniture(self, world, noise_events)
        elif action == 10:
            SurvivorActions.dismantle_furniture(self, world, noise_events)
