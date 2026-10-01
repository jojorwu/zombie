import random
import torch
import torch.nn as nn
from utils.p_np_math import PNPComplexityEngine

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
PNP_ENGINE = PNPComplexityEngine(degree=2)


class BrainNet(nn.Module):
    def __init__(self, input_size=25, hidden_size=32, output_size=13):
        super(BrainNet, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.gru = nn.GRUCell(hidden_size, hidden_size)
        self.fc_out = nn.Linear(hidden_size, output_size)
        self.to(DEVICE)

    def forward(self, x, h):
        out = self.fc1(x)
        out = self.relu(out)
        h_next = self.gru(out, h)
        out = self.fc_out(h_next)
        return out, h_next

    def init_hidden(self):
        return torch.zeros(1, self.hidden_size, dtype=torch.float32, device=DEVICE)

    def get_action_and_movement(self, inputs, prev_hidden=None):
        import numpy as np
        self.eval()
        if prev_hidden is None:
            prev_hidden = self.init_hidden()

        with torch.inference_mode():
            inp_tensor = torch.tensor(inputs, dtype=torch.float32, device=DEVICE)
            if inp_tensor.dim() == 1:
                inp_tensor = inp_tensor.unsqueeze(0)
            if prev_hidden.dim() == 3:
                prev_hidden = prev_hidden.squeeze(1)
            if prev_hidden.device != DEVICE:
                prev_hidden = prev_hidden.to(DEVICE)
            outputs, new_hidden = self.forward(inp_tensor, prev_hidden)
            out_arr = outputs.squeeze(0).cpu().numpy()

        dx = float(np.tanh(out_arr[0]))
        dy = float(np.tanh(out_arr[1]))
        action_idx = int(np.argmax(out_arr[2:]))
        return dx, dy, action_idx, new_hidden


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
