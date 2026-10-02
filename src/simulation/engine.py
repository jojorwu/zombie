import random
import time
from concurrent.futures import ThreadPoolExecutor
from src.world import World
from src.entities import Survivor, Vehicle, ResourceItem, EntityFactory
from src.ai.brain import BrainNet, extract_survivor_inputs, GeneticEvolutionManager, batch_get_action_and_movement
from src.modding.manager import LuaModManager
from src.simulation.spawner import EntitySpawner
from src.simulation.environment import EnvironmentManager
from utils.memory_monitor_utility import MemoryMonitorUtility
from utils.electricity_utility import ElectricityUtility

SIM_EXECUTOR = ThreadPoolExecutor(max_workers=4)


class SimulationEngine:
    """Main simulation controller coordinating world ticks, AI decisions, entity updates, and evolution."""
    def __init__(self, config):
        self.mod_manager = LuaModManager()
        self.factory = EntityFactory(config=config)
        self.memory_monitor = MemoryMonitorUtility()
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

        self.electricity_utility = ElectricityUtility(
            cutoff_day=self.sim_cfg.get("electricity_cutoff_day", 7),
            grid_enabled=self.sim_cfg.get("electricity_enabled", True)
        )

        self.spawner = EntitySpawner(self.world, self.factory)
        self.env_manager = EnvironmentManager(self.world, self.electricity_utility)

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

    def _recycle_entities(self):
        import gc
        import torch

        if hasattr(self, 'zombies'):
            for z in self.zombies:
                self.factory.release_zombie(z)
        if hasattr(self, 'items'):
            for item in self.items:
                self.factory.release_item(item)
        if hasattr(self, 'scent_trails'):
            for st in self.scent_trails:
                self.factory.release_scent_trail(st)
        if hasattr(self, 'noise_events'):
            for ne in self.noise_events:
                self.factory.release_noise_event(ne)

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def reset_generation(self):
        self._recycle_entities()
        self.world.generate_world()

        self.survivors, self.zombies, self.animals, self.vehicles, self.items = [], [], [], [], []
        self.noise_events, self.scent_trails = [], []
        self.hidden_states = [brain.init_hidden() for brain in self.brains]

        walkable_coords, parking_coords, trash_coords = self.spawner.scan_walkable_coordinates()
        ground_walkable = [(x, y, z) for x, y, z in walkable_coords if z == 0]
        random.shuffle(ground_walkable)

        # 1. Spawn Animals
        for _ in range(min(self.sim_cfg["num_animals"], len(ground_walkable))):
            coord = ground_walkable.pop()
            self.animals.append(self.factory.create_animal(coord[0] + 0.5, coord[1] + 0.5, z=coord[2]))

        # 2. Spawn Vehicles
        vehicle_spawns = parking_coords if parking_coords else ground_walkable
        for _ in range(min(self.sim_cfg["num_vehicles"], len(vehicle_spawns))):
            coord = vehicle_spawns.pop()
            self.vehicles.append(Vehicle(coord[0] + 0.5, coord[1] + 0.5, fuel=random.uniform(30.0, 80.0), z=coord[2]))

        # 3. Spawn Zombies
        for _ in range(min(self.sim_cfg["num_zombies"], len(walkable_coords))):
            coord = walkable_coords.pop()
            self.zombies.append(self.factory.create_zombie(coord[0] + 0.5, coord[1] + 0.5, z=coord[2]))

        # 4. Spawn Trash Can Loot
        for tc in trash_coords:
            itype = random.choice([ResourceItem.CANNED_FOOD, ResourceItem.CANNED_BEANS, ResourceItem.CAN_OPENER, ResourceItem.WATER_BOTTLE, ResourceItem.METAL, ResourceItem.FRYING_PAN])
            self.items.append(self.factory.create_item(tc[0] + 0.5, tc[1] + 0.5, itype, amount=random.randint(1, 2), z=tc[2]))

        # 5. Spawn Building Contextual Loot & Street Corpses
        self.spawner.spawn_building_loot(self.items)
        self.spawner.spawn_street_corpses_and_loot(self.items, num_corpses=20)

        # 6. Spawn Survivors
        for _ in range(min(self.sim_cfg["num_survivors"], len(walkable_coords))):
            coord = walkable_coords.pop()
            self.survivors.append(Survivor(coord[0] + 0.5, coord[1] + 0.5, z=coord[2]))

    def tick(self):
        t0 = time.time()
        self.env_manager.tick_environment()
        self.mod_manager.trigger_event("on_tick", self.world.current_tick)

        active_noises = []
        for ne in self.noise_events:
            ne.update()
            if ne.lifetime <= 0 or ne.volume <= 0.0:
                self.factory.release_noise_event(ne)
            else:
                active_noises.append(ne)
        self.noise_events = active_noises

        entity_positions = [(s.x, s.y) for s in self.survivors if s.is_alive]
        if entity_positions:
            self.world.chunk_manager.update_active_chunks(entity_positions, view_distance_chunks=2)

        alive_indices = [i for i, s in enumerate(self.survivors) if s.is_alive]
        alive_count = len(alive_indices)

        if alive_count > 0:
            active_brains = [self.brains[i] for i in alive_indices]
            active_inputs = [extract_survivor_inputs(self.survivors[i], self.world, self.items, self.vehicles, self.zombies, self.animals) for i in alive_indices]
            active_hiddens = [self.hidden_states[i] for i in alive_indices]

            step_outputs = batch_get_action_and_movement(active_brains, active_inputs, active_hiddens)

            for idx, orig_i in enumerate(alive_indices):
                survivor = self.survivors[orig_i]
                survivor.update_needs()

                if not survivor.is_alive and survivor.is_infected:
                    new_z = self.factory.create_zombie(survivor.x, survivor.y, z=survivor.z)
                    self.zombies.append(new_z)
                    continue

                dx, dy, action, new_hidden = step_outputs[idx]
                self.hidden_states[orig_i] = new_hidden

                survivor.move(dx, dy, self.world, noise_events=self.noise_events)
                survivor.perform_action(action, self.world, self.items, self.vehicles, self.zombies, self.animals, self.survivors, noise_events=self.noise_events)

        for s in self.survivors:
            if s.is_alive and not s.in_vehicle and self.world.current_tick % 5 == 0:
                self.scent_trails.append(self.factory.create_scent_trail(s.x, s.y, s.z, intensity=100.0))

        active_scents = []
        for st in self.scent_trails:
            st.update(world=self.world)
            if st.intensity <= 0.0:
                self.factory.release_scent_trail(st)
            else:
                active_scents.append(st)
        self.scent_trails = active_scents

        active_chunk_coords = self.world.chunk_manager.active_chunks
        chunk_size = self.world.chunk_manager.chunk_size

        active_zombies = [
            z for z in self.zombies
            if z.is_alive and (int(z.x) // chunk_size, int(z.y) // chunk_size) in active_chunk_coords
        ]

        z_grid = {}
        for z in active_zombies:
            cell = (int(z.x // 6.0), int(z.y // 6.0), z.z)
            if cell not in z_grid:
                z_grid[cell] = []
            z_grid[cell].append(z)

        if len(active_zombies) > 8:
            def _update_zombie_chunk(z_sublist):
                for z in z_sublist:
                    z.update(self.world, self.survivors, self.vehicles, noise_events=self.noise_events, scent_trails=self.scent_trails, all_zombies=self.zombies, spatial_grid=z_grid)

            c_size = max(1, len(active_zombies) // 4)
            z_chunks = [active_zombies[i:i + c_size] for i in range(0, len(active_zombies), c_size)]
            futures = [SIM_EXECUTOR.submit(_update_zombie_chunk, zc) for zc in z_chunks]
            for f in futures:
                f.result()
        else:
            for zombie in active_zombies:
                zombie.update(self.world, self.survivors, self.vehicles, noise_events=self.noise_events, scent_trails=self.scent_trails, all_zombies=self.zombies, spatial_grid=z_grid)

        # Vehicle-Zombie Momentum Collision Processing
        for v in self.vehicles:
            if v.is_occupied() and v.speed > 0.05:
                v_x, v_y, v_sp = v.x, v.y, v.speed
                for z in active_zombies:
                    if z.is_alive and z.z == v.z and (z.x - v_x)**2 + (z.y - v_y)**2 < 1.44:
                        collision_damage = v_sp * 250.0 * (v.physics.mass / 1000.0)
                        z.take_targeted_damage(collision_damage)
                        v.physics.velocity_x *= 0.85
                        v.physics.velocity_y *= 0.85
                        if "bumper" in v.parts:
                            v.parts["bumper"].damage(10.0)

        for animal in self.animals:
            animal.update(self.world)

        self.env_manager.check_dynamic_item_respawn(self.items, self.factory)
        self.memory_monitor.record_tick_time(time.time() - t0)

        # Max simulation length = 1 month (108,000 ticks)
        max_ticks = self.sim_cfg.get("max_ticks_per_gen", 108000)
        if alive_count == 0 or self.world.current_tick >= max_ticks:
            self.end_generation()

    def end_generation(self):
        brains_and_fitnesses = []
        for i, s in enumerate(self.survivors):
            fitness = s.calculate_fitness()
            brains_and_fitnesses.append((self.brains[i], fitness))

        self.brains, max_fit = self.evolution_manager.evolve_population(brains_and_fitnesses)
        if max_fit > self.best_historical_score:
            self.best_historical_score = max_fit
            self.evolution_manager.save_best_brain(self.brains[0], "best_brain.zbrain")

        self.reset_generation()
