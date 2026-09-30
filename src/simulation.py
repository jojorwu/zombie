import random
import math
from src.world import World, TileType, TILE_COLORS
from src.entities import Survivor, Zombie, Animal, Vehicle, ItemEntity, ResourceItem
from src.brain import BrainNet, extract_survivor_inputs, GeneticEvolutionManager

class SimulationEngine:
    def __init__(self, config):
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

        walkable_coords = []
        for y in range(self.world.height):
            for x in range(self.world.width):
                if self.world.is_walkable(x, y):
                    walkable_coords.append((x, y))

        random.shuffle(walkable_coords)

        for i in range(min(self.sim_cfg["num_survivors"], len(walkable_coords))):
            coord = walkable_coords.pop()
            s = Survivor(coord[0] + 0.5, coord[1] + 0.5)
            self.survivors.append(s)

        for _ in range(min(self.sim_cfg["num_zombies"], len(walkable_coords))):
            coord = walkable_coords.pop()
            z = Zombie(coord[0] + 0.5, coord[1] + 0.5)
            self.zombies.append(z)

        for _ in range(min(self.sim_cfg["num_animals"], len(walkable_coords))):
            coord = walkable_coords.pop()
            a = Animal(coord[0] + 0.5, coord[1] + 0.5)
            self.animals.append(a)

        for _ in range(min(self.sim_cfg["num_vehicles"], len(walkable_coords))):
            coord = walkable_coords.pop()
            v = Vehicle(coord[0] + 0.5, coord[1] + 0.5, fuel=random.uniform(30.0, 80.0))
            self.vehicles.append(v)

        item_types = [ResourceItem.FOOD, ResourceItem.WATER, ResourceItem.WOOD, ResourceItem.METAL, ResourceItem.FUEL]
        for _ in range(min(40, len(walkable_coords))):
            coord = walkable_coords.pop()
            itype = random.choice(item_types)
            item = ItemEntity(coord[0] + 0.5, coord[1] + 0.5, itype, amount=random.randint(1, 3))
            self.items.append(item)

    def tick(self):
        self.world.update_day_night()

        alive_count = 0
        for i, survivor in enumerate(self.survivors):
            if not survivor.is_alive:
                continue

            alive_count += 1
            survivor.update_needs()

            brain = self.brains[i]
            inputs = extract_survivor_inputs(survivor, self.world, self.items, self.vehicles, self.zombies, self.animals)
            dx, dy, action = brain.get_action_and_movement(inputs)

            survivor.move(dx, dy, self.world)
            survivor.perform_action(action, self.world, self.items, self.vehicles, self.zombies, self.animals, self.survivors)

        for zombie in self.zombies:
            zombie.update(self.world, self.survivors, self.vehicles)

        for animal in self.animals:
            animal.update(self.world)

        if self.world.current_tick % 100 == 0:
            active_items = [item for item in self.items if not item.collected]
            if len(active_items) < 20:
                rx, ry = random.randint(0, self.world.width - 1), random.randint(0, self.world.height - 1)
                if self.world.is_walkable(rx, ry):
                    itype = random.choice([ResourceItem.FOOD, ResourceItem.WATER, ResourceItem.WOOD, ResourceItem.METAL, ResourceItem.FUEL])
                    self.items.append(ItemEntity(rx + 0.5, ry + 0.5, itype, amount=random.randint(1, 2)))

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
