import random
import math
from src.world import World, TileType, BuildingType
from src.entities import Survivor, Zombie, Animal, Vehicle, ItemEntity, ResourceItem
from src.brain import BrainNet, extract_survivor_inputs, GeneticEvolutionManager
from src.modding import LuaModManager

class SimulationEngine:
    def __init__(self, config):
        self.mod_manager = LuaModManager()
        self.config = config
        self.sim_cfg = config["simulation"]
        self.evo_cfg = config["evolution"]

        self.world = World(
            width=self.sim_cfg["map_width"],
            height=self.sim_cfg["map_height"],
            day_length_ticks=self.sim_cfg["day_length_ticks"]
        )

        self.evolution_manager = GeneticEvolutionManager(
            population_size=self.sim_cfg["num_survivors"],
            mutation_rate=self.evo_cfg["mutation_rate"],
            mutation_scale=self.evo_cfg["mutation_scale"],
            elite_fraction=self.evo_cfg["elite_fraction"]
        )

        self.brains = self.evolution_manager.create_initial_brains()
        self.hidden_states = [brain.init_hidden() for brain in self.brains]
        self.selected_survivor_idx = 0
        self.best_historical_score = 0.0

        self.reset_generation()

    def reset_generation(self):
        self.world.generate_world()
        self.survivors = []
        self.zombies = []
        self.animals = []
        self.vehicles = []
        self.items = []
        self.noise_events = []

        self.hidden_states = [brain.init_hidden() for brain in self.brains]

        walkable_coords = []
        parking_coords = []
        trash_coords = []

        for z in range(self.world.z_min, self.world.z_max + 1):
            z_idx = self.world.z_to_idx(z)
            for y in range(self.world.height):
                for x in range(self.world.width):
                    if self.world.is_walkable(x, y, z):
                        coord = (x, y, z)
                        walkable_coords.append(coord)
                        tile = self.world.grid[z_idx, y, x]
                        if tile == TileType.PARKING:
                            parking_coords.append(coord)
                        elif tile == TileType.TRASH_CAN:
                            trash_coords.append(coord)

        random.shuffle(walkable_coords)
        random.shuffle(parking_coords)
        random.shuffle(trash_coords)

        ground_walkable = [(x, y, z) for x, y, z in walkable_coords if z == 0]
        random.shuffle(ground_walkable)

        # 1. Spawn Animals (Животные)
        for _ in range(min(self.sim_cfg["num_animals"], len(ground_walkable))):
            coord = ground_walkable.pop()
            a = Animal(coord[0] + 0.5, coord[1] + 0.5, z=coord[2])
            self.animals.append(a)

        # 2. Spawn Vehicles (Транспорт - preferring parking lots)
        vehicle_spawns = parking_coords if parking_coords else ground_walkable
        for _ in range(min(self.sim_cfg["num_vehicles"], len(vehicle_spawns))):
            coord = vehicle_spawns.pop()
            v = Vehicle(coord[0] + 0.5, coord[1] + 0.5, fuel=random.uniform(30.0, 80.0), z=coord[2])
            self.vehicles.append(v)

        # 3. Spawn Zombies (Зомби)
        for _ in range(min(self.sim_cfg["num_zombies"], len(walkable_coords))):
            coord = walkable_coords.pop()
            z_ent = Zombie(coord[0] + 0.5, coord[1] + 0.5, z=coord[2])
            self.zombies.append(z_ent)

        # 4. Spawn Items & Detail Loot (Trash Cans, Mailboxes, Containers, Building Loot)
        for tc in trash_coords:
            itype = random.choice([ResourceItem.FOOD, ResourceItem.WATER, ResourceItem.METAL])
            self.items.append(ItemEntity(tc[0] + 0.5, tc[1] + 0.5, itype, amount=random.randint(1, 3), z=tc[2]))

        for b in self.world.buildings:
            bx, by, bw, bh, btype = b["x"], b["y"], b["w"], b["h"], b["type"]
            loot_type = ResourceItem.FOOD
            if btype in (BuildingType.HOSPITAL,):
                loot_type = ResourceItem.MEDKIT
            elif btype in (BuildingType.GUN_STORE, BuildingType.POLICE_STATION):
                loot_type = ResourceItem.WEAPON if random.random() < 0.6 else ResourceItem.METAL
            elif btype == BuildingType.GAS_STATION:
                loot_type = ResourceItem.FUEL
            elif btype in (BuildingType.SUPERMARKET, BuildingType.STORE):
                loot_type = ResourceItem.FOOD if random.random() < 0.5 else ResourceItem.WATER
            elif btype in (BuildingType.RESIDENTIAL, BuildingType.DORMITORY, BuildingType.SCHOOL):
                loot_type = ResourceItem.FOOD if random.random() < 0.7 else ResourceItem.WATER

            for floor_z in range(self.world.z_min, self.world.z_max + 1):
                lx, ly = bx + 2, by + 1
                if self.world.is_walkable(lx, ly, floor_z):
                    self.items.append(ItemEntity(lx + 0.5, ly + 0.5, loot_type, amount=random.randint(1, 3), z=floor_z))

        item_types = [ResourceItem.FOOD, ResourceItem.WATER, ResourceItem.WOOD, ResourceItem.METAL, ResourceItem.FUEL]
        for _ in range(min(30, len(walkable_coords))):
            coord = walkable_coords.pop()
            itype = random.choice(item_types)
            item = ItemEntity(coord[0] + 0.5, coord[1] + 0.5, itype, amount=random.randint(1, 2), z=coord[2])
            self.items.append(item)

        # 5. Spawn Survivors (Выжившие - AT THE VERY END!)
        for i in range(min(self.sim_cfg["num_survivors"], len(walkable_coords))):
            coord = walkable_coords.pop()
            s = Survivor(coord[0] + 0.5, coord[1] + 0.5, z=coord[2])
            self.survivors.append(s)

    def tick(self):
        self.world.update_day_night()
        self.mod_manager.trigger_event("on_tick", self.world.current_tick)

        # Update active noise events
        for ne in self.noise_events:
            ne.update()
        self.noise_events = [ne for ne in self.noise_events if ne.lifetime > 0 and ne.volume > 0.0]

        alive_count = 0
        import torch
        with torch.inference_mode():
            for i, survivor in enumerate(self.survivors):
                if not survivor.is_alive:
                    continue

                alive_count += 1
                survivor.update_needs()

                brain = self.brains[i]
                prev_hidden = self.hidden_states[i]
                inputs = extract_survivor_inputs(survivor, self.world, self.items, self.vehicles, self.zombies, self.animals)
                dx, dy, action, new_hidden = brain.get_action_and_movement(inputs, prev_hidden)
                self.hidden_states[i] = new_hidden

                survivor.move(dx, dy, self.world, noise_events=self.noise_events)
                survivor.perform_action(action, self.world, self.items, self.vehicles, self.zombies, self.animals, self.survivors, noise_events=self.noise_events)

        for zombie in self.zombies:
            zombie.update(self.world, self.survivors, self.vehicles, noise_events=self.noise_events)

        for animal in self.animals:
            animal.update(self.world)

        if self.world.current_tick % 100 == 0:
            active_items = [item for item in self.items if not item.collected]
            if len(active_items) < 20:
                rx, ry = random.randint(0, self.world.width - 1), random.randint(0, self.world.height - 1)
                rz = random.randint(self.world.z_min, self.world.z_max)
                if self.world.is_walkable(rx, ry, rz):
                    itype = random.choice([ResourceItem.FOOD, ResourceItem.WATER, ResourceItem.WOOD, ResourceItem.METAL, ResourceItem.FUEL])
                    self.items.append(ItemEntity(rx + 0.5, ry + 0.5, itype, amount=random.randint(1, 2), z=rz))

        if alive_count == 0 or self.world.current_tick >= 1200:
            self.end_generation()

    def end_generation(self):
        brains_and_fitnesses = []
        for i, s in enumerate(self.survivors):
            fitness = s.score + (s.time_survived * 0.5) + (s.kills * 25.0)
            brains_and_fitnesses.append((self.brains[i], fitness))

        self.brains, max_fit = self.evolution_manager.evolve_population(brains_and_fitnesses)
        if max_fit > self.best_historical_score:
            self.best_historical_score = max_fit
            self.evolution_manager.save_best_brain(self.brains[0], "best_brain.pth")

        self.reset_generation()
