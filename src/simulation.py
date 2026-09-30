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
            width=self.sim_cfg.get("map_width", 1000),
            height=self.sim_cfg.get("map_height", 1000),
            day_length_ticks=self.sim_cfg.get("day_length_ticks", 3600),
            electricity_cutoff_day=self.sim_cfg.get("electricity_cutoff_day", 7),
            water_cutoff_day=self.sim_cfg.get("water_cutoff_day", 14),
            electricity_enabled=self.sim_cfg.get("electricity_enabled", True),
            water_enabled=self.sim_cfg.get("water_enabled", True)
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
        # Explicit memory cleanup on generation reset
        import gc
        import torch
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

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

        # 4. Contextual Realistic Item & Loot Spawning
        for tc in trash_coords:
            itype = random.choice([ResourceItem.CANNED_FOOD, ResourceItem.CAN_OPENER, ResourceItem.WATER_BOTTLE, ResourceItem.METAL, ResourceItem.FRYING_PAN])
            self.items.append(ItemEntity(tc[0] + 0.5, tc[1] + 0.5, itype, amount=random.randint(1, 2), z=tc[2]))

        for b in self.world.buildings:
            bx, by, bw, bh, btype = b["x"], b["y"], b["w"], b["h"], b["type"]
            possible_loot = [ResourceItem.FOOD, ResourceItem.WATER]

            if btype in (BuildingType.GUN_STORE, BuildingType.POLICE_STATION):
                possible_loot = [
                    ResourceItem.PISTOL, ResourceItem.SHOTGUN, ResourceItem.RIFLE,
                    ResourceItem.PISTOL_AMMO, ResourceItem.SHOTGUN_SHELLS, ResourceItem.RIFLE_AMMO,
                    ResourceItem.CROWBAR, ResourceItem.KNIFE
                ]
            elif btype == BuildingType.HOSPITAL:
                possible_loot = [ResourceItem.MEDKIT, ResourceItem.WATER_BOTTLE]
            elif btype == BuildingType.GAS_STATION:
                possible_loot = [ResourceItem.FUEL, ResourceItem.CROWBAR, ResourceItem.CANNED_FOOD, ResourceItem.WATER_BOTTLE]
            elif btype in (BuildingType.SUPERMARKET, BuildingType.STORE):
                possible_loot = [
                    ResourceItem.CANNED_FOOD, ResourceItem.BREAD, ResourceItem.APPLE, ResourceItem.MRE,
                    ResourceItem.WATER_BOTTLE, ResourceItem.CAN_OPENER
                ]
            elif btype in (BuildingType.RESIDENTIAL, BuildingType.DORMITORY, BuildingType.SCHOOL):
                # Residential Kitchens
                possible_loot = [
                    ResourceItem.BREAD, ResourceItem.APPLE, ResourceItem.MEAT,
                    ResourceItem.CHEF_KNIFE, ResourceItem.FRYING_PAN, ResourceItem.POT,
                    ResourceItem.CAN_OPENER, ResourceItem.WATER_BOTTLE, ResourceItem.CUTTING_BOARD,
                    ResourceItem.BASEBALL_BAT, ResourceItem.AXE
                ]
            elif btype in (BuildingType.WAREHOUSE, BuildingType.FACTORY):
                possible_loot = [ResourceItem.AXE, ResourceItem.CROWBAR, ResourceItem.WOOD, ResourceItem.METAL, ResourceItem.FUEL]

            for floor_z in range(self.world.z_min, self.world.z_max + 1):
                lx, ly = bx + 2, by + 1
                if self.world.is_walkable(lx, ly, floor_z):
                    loot_type = random.choice(possible_loot)
                    amt = random.randint(2, 6) if "ammo" in loot_type else random.randint(1, 2)
                    self.items.append(ItemEntity(lx + 0.5, ly + 0.5, loot_type, amount=amt, z=floor_z))

        item_types = [
            ResourceItem.BREAD, ResourceItem.APPLE, ResourceItem.WOOD, ResourceItem.METAL,
            ResourceItem.WATER_BOTTLE, ResourceItem.KNIFE, ResourceItem.PISTOL_AMMO
        ]
        for _ in range(min(40, len(walkable_coords))):
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

        # Update dynamic chunk activation for entities
        entity_positions = [(s.x, s.y) for s in self.survivors if s.is_alive]
        entity_positions.extend([(z.x, z.y) for z in self.zombies if z.is_alive])
        if entity_positions:
            self.world.chunk_manager.update_active_chunks(entity_positions, view_distance_chunks=2)

        alive_indices = [i for i, s in enumerate(self.survivors) if s.is_alive]
        alive_count = len(alive_indices)

        if alive_count > 0:
            active_brains = [self.brains[i] for i in alive_indices]
            active_inputs = [extract_survivor_inputs(self.survivors[i], self.world, self.items, self.vehicles, self.zombies, self.animals) for i in alive_indices]
            active_hiddens = [self.hidden_states[i] for i in alive_indices]

            from src.brain import batch_get_action_and_movement
            step_outputs = batch_get_action_and_movement(active_brains, active_inputs, active_hiddens)

            for idx, orig_i in enumerate(alive_indices):
                survivor = self.survivors[orig_i]
                survivor.update_needs()

                dx, dy, action, new_hidden = step_outputs[idx]
                self.hidden_states[orig_i] = new_hidden

                survivor.move(dx, dy, self.world, noise_events=self.noise_events)
                survivor.perform_action(action, self.world, self.items, self.vehicles, self.zombies, self.animals, self.survivors, noise_events=self.noise_events)

        # Scent trail management
        if not hasattr(self, 'scent_trails'):
            self.scent_trails = []

        # Leave scent trails for moving survivors
        for s in self.survivors:
            if s.is_alive and not s.in_vehicle:
                if self.world.current_tick % 5 == 0:
                    from src.entities import ScentTrail
                    self.scent_trails.append(ScentTrail(s.x, s.y, s.z, intensity=100.0))

        # Update scent trails
        for st in self.scent_trails:
            st.update(world=self.world)
        self.scent_trails = [st for st in self.scent_trails if st.intensity > 0.0]

        for zombie in self.zombies:
            zombie.update(self.world, self.survivors, self.vehicles, noise_events=self.noise_events, scent_trails=self.scent_trails, all_zombies=self.zombies)

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
