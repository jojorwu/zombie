import math
import random
import torch
import torch.nn as nn
import numpy as np

class BrainNet(nn.Module):
    def __init__(self, input_size=18, hidden_size=24, output_size=9):
        super(BrainNet, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        out = self.relu(out)
        out = self.fc3(out)
        return out

    def get_action_and_movement(self, inputs):
        self.eval()
        with torch.no_grad():
            inp_tensor = torch.tensor(inputs, dtype=torch.float32).unsqueeze(0)
            outputs = self.forward(inp_tensor).squeeze(0).numpy()

        dx = float(np.tanh(outputs[0]))
        dy = float(np.tanh(outputs[1]))
        action_idx = int(np.argmax(outputs[2:]))  # logits 2..8 map to action 0..6
        return dx, dy, action_idx

def extract_survivor_inputs(survivor, world, items, vehicles, zombies, animals):
    """
    Inputs vector (length 18):
    0: Health (0..1)
    1: Hunger (0..1)
    2: Thirst (0..1)
    3: Sleep (0..1)
    4: Light level (0..1)
    5: In vehicle (0 or 1)
    6: Has weapon (0 or 1)
    7: Has medkit (0 or 1)
    8,9: Closest Zombie dx, dy (normalized)
    10,11: Closest Item dx, dy (normalized)
    12,13: Closest Vehicle dx, dy (normalized)
    14,15: Closest Animal dx, dy (normalized)
    16,17: Tile Walkable ahead / center offset
    """
    inputs = np.zeros(18, dtype=np.float32)
    inputs[0] = survivor.health / 100.0
    inputs[1] = survivor.hunger / 100.0
    inputs[2] = survivor.thirst / 100.0
    inputs[3] = survivor.sleep / 100.0
    inputs[4] = world.get_light_level()
    inputs[5] = 1.0 if survivor.in_vehicle else 0.0
    inputs[6] = 1.0 if survivor.inventory.get("weapon", 0) > 0 else 0.0
    inputs[7] = 1.0 if survivor.inventory.get("medkit", 0) > 0 else 0.0

    def find_closest(entities, max_dist=15.0):
        closest_dx, closest_dy = 0.0, 0.0
        min_d = max_dist
        for e in entities:
            if hasattr(e, 'is_alive') and not e.is_alive:
                continue
            if hasattr(e, 'collected') and e.collected:
                continue
            d = math.hypot(e.x - survivor.x, e.y - survivor.y)
            if d < min_d:
                min_d = d
                closest_dx = (e.x - survivor.x) / max_dist
                closest_dy = (e.y - survivor.y) / max_dist
        return closest_dx, closest_dy

    inputs[8], inputs[9] = find_closest(zombies)
    inputs[10], inputs[11] = find_closest(items)
    inputs[12], inputs[13] = find_closest(vehicles)
    inputs[14], inputs[15] = find_closest(animals)
    inputs[16] = 1.0 if world.is_walkable(survivor.x + 0.5, survivor.y) else 0.0
    inputs[17] = 1.0 if world.is_walkable(survivor.x, survivor.y + 0.5) else 0.0

    return inputs

class GeneticEvolutionManager:
    def __init__(self, population_size=20, mutation_rate=0.1, mutation_scale=0.2, elite_fraction=0.2):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.mutation_scale = mutation_scale
        self.elite_fraction = elite_fraction
        self.generation = 1

    def create_initial_brains(self):
        return [BrainNet() for _ in range(self.population_size)]

    def mutate_net(self, net):
        mutated_net = BrainNet()
        mutated_net.load_state_dict(net.state_dict())
        with torch.no_grad():
            for param in mutated_net.parameters():
                if random.random() < self.mutation_rate:
                    noise = torch.randn_like(param) * self.mutation_scale
                    param.add_(noise)
        return mutated_net

    def crossover_nets(self, parent1, parent2):
        child = BrainNet()
        p1_dict = parent1.state_dict()
        p2_dict = parent2.state_dict()
        child_dict = child.state_dict()

        with torch.no_grad():
            for key in p1_dict:
                mask = torch.rand_like(p1_dict[key]) > 0.5
                child_dict[key] = torch.where(mask, p1_dict[key], p2_dict[key])
        child.load_state_dict(child_dict)
        return child

    def evolve_population(self, brains_and_fitnesses):
        brains_and_fitnesses.sort(key=lambda x: x[1], reverse=True)
        sorted_brains = [b for b, f in brains_and_fitnesses]

        num_elites = max(1, int(self.population_size * self.elite_fraction))
        new_population = []

        for i in range(num_elites):
            elite_copy = BrainNet()
            elite_copy.load_state_dict(sorted_brains[i].state_dict())
            new_population.append(elite_copy)

        while len(new_population) < self.population_size:
            p1 = random.choice(sorted_brains[:num_elites + 2])
            p2 = random.choice(sorted_brains[:num_elites + 2])
            child = self.crossover_nets(p1, p2)
            child = self.mutate_net(child)
            new_population.append(child)

        self.generation += 1
        return new_population, brains_and_fitnesses[0][1]

    def save_best_brain(self, brain, filepath="best_brain.pth"):
        torch.save(brain.state_dict(), filepath)

    def load_best_brain(self, brain, filepath="best_brain.pth"):
        brain.load_state_dict(torch.load(filepath))
