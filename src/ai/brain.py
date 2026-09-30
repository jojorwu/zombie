import math
import random
import torch
import torch.nn as nn
import numpy as np
from utils.p_np_math import PNPComplexityEngine, PolynomialVerifier

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


def batch_get_action_and_movement(brains, inputs_list, prev_hiddens):
    """
    High-performance batched PyTorch inference over active survivors.
    Executes batched tensor matrix multiplication (BMM) for max speed and zero memory allocation churn.
    """
    if not brains or not inputs_list:
        return []

    num_survivors = len(brains)

    if num_survivors == 1:
        return [brains[0].get_action_and_movement(inputs_list[0], prev_hiddens[0])]

    w_fc1 = torch.stack([b.fc1.weight for b in brains])
    b_fc1 = torch.stack([b.fc1.bias for b in brains])
    w_ih = torch.stack([b.gru.weight_ih for b in brains])
    w_hh = torch.stack([b.gru.weight_hh for b in brains])
    b_ih = torch.stack([b.gru.bias_ih for b in brains])
    b_hh = torch.stack([b.gru.bias_hh for b in brains])
    w_out = torch.stack([b.fc_out.weight for b in brains])
    b_out = torch.stack([b.fc_out.bias for b in brains])

    inp_np = np.ascontiguousarray(np.array(inputs_list, dtype=np.float32))
    x = torch.from_numpy(inp_np).to(DEVICE).unsqueeze(1)

    valid_hiddens = []
    for h in prev_hiddens:
        if h is None:
            valid_hiddens.append(brains[0].init_hidden())
        else:
            if h.dim() == 3:
                h = h.squeeze(1)
            elif h.dim() == 1:
                h = h.unsqueeze(0)
            if h.device != DEVICE:
                h = h.to(DEVICE)
            valid_hiddens.append(h)

    h_cat = torch.cat(valid_hiddens, dim=0).to(DEVICE)

    with torch.inference_mode():
        out = torch.bmm(x, w_fc1.transpose(1, 2)).squeeze(1) + b_fc1
        out = torch.relu(out)

        gi = torch.bmm(out.unsqueeze(1), w_ih.transpose(1, 2)).squeeze(1) + b_ih
        gh = torch.bmm(h_cat.unsqueeze(1), w_hh.transpose(1, 2)).squeeze(1) + b_hh

        i_r, i_i, i_n = gi.chunk(3, 1)
        h_r, h_i, h_n = gh.chunk(3, 1)

        resetgate = torch.sigmoid(i_r + h_r)
        inputgate = torch.sigmoid(i_i + h_i)
        newgate = torch.tanh(i_n + resetgate * h_n)
        h_next = newgate + inputgate * (h_cat - newgate)

        out_final = torch.bmm(h_next.unsqueeze(1), w_out.transpose(1, 2)).squeeze(1) + b_out
        out_arr = out_final.cpu().numpy()

        dxs = np.tanh(out_arr[:, 0])
        dys = np.tanh(out_arr[:, 1])
        actions = np.argmax(out_arr[:, 2:], axis=1)

        results = []
        for i in range(num_survivors):
            results.append((
                float(dxs[i]),
                float(dys[i]),
                int(actions[i]),
                h_next[i:i + 1]
            ))
        return results


def extract_survivor_inputs(survivor, world, items, vehicles, zombies, animals):
    inputs = np.zeros(25, dtype=np.float32)
    inputs[0] = survivor.health / 100.0
    inputs[1] = survivor.hunger / 100.0
    inputs[2] = survivor.thirst / 100.0
    inputs[3] = survivor.sleep / 100.0
    inputs[4] = world.get_light_level()
    inputs[5] = 1.0 if survivor.in_vehicle else 0.0
    inputs[6] = 1.0 if survivor.inventory.get("weapon", 0) > 0 or survivor.inventory.get("pistol", 0) > 0 else 0.0
    inputs[7] = 1.0 if survivor.inventory.get("medkit", 0) > 0 else 0.0

    def find_closest_fast(entities, max_dist=15.0):
        min_dist = max_dist
        best_dx, best_dy, best_dz = 0.0, 0.0, 0.0
        sx, sy, sz = survivor.x, survivor.y, survivor.z

        for e in entities:
            if getattr(e, 'is_alive', True) and not getattr(e, 'collected', False):
                dx = e.x - sx
                dy = e.y - sy
                dz = getattr(e, 'z', 0) - sz
                d = math.hypot(dx, dy) + abs(dz) * 2.0
                if d < min_dist:
                    min_dist = d
                    best_dx = dx / max_dist
                    best_dy = dy / max_dist
                    best_dz = dz / 20.0

        return best_dx, best_dy, best_dz

    inputs[8], inputs[9], inputs[10] = find_closest_fast(zombies)
    inputs[11], inputs[12], inputs[13] = find_closest_fast(items)
    inputs[14], inputs[15], inputs[16] = find_closest_fast(vehicles)
    inputs[17], inputs[18], inputs[19] = find_closest_fast(animals)
    inputs[20] = 1.0 if world.is_walkable(survivor.x + 0.5, survivor.y, survivor.z) else 0.0
    inputs[21] = 1.0 if world.is_walkable(survivor.x, survivor.y + 0.5, survivor.z) else 0.0
    inputs[22] = float(survivor.z) / 20.0

    from utils.tile_interaction_utility import TileInteractionUtility
    z_idx = world.z_to_idx(survivor.z)
    has_furniture_adj = 0.0
    sx, sy = int(survivor.x), int(survivor.y)

    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        fx, fy = sx + dx, sy + dy
        if 0 <= fx < world.width and 0 <= fy < world.height:
            if world.grid[z_idx, fy, fx] in TileInteractionUtility.MOVABLE_FURNITURE_TILES:
                has_furniture_adj = 1.0
                break

    inputs[23] = has_furniture_adj
    inputs[24] = min(1.0, (survivor.inventory.get("wood", 0) + survivor.inventory.get("metal", 0)) / 10.0)

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
