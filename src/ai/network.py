import io
import math
import os
import random
import zlib

import numpy as np
import torch
from torch import nn


def get_best_device() -> torch.device:
    """
    Dynamically detects and selects the best available AI compute accelerator
    across NVIDIA CUDA, Apple Silicon Metal (MPS), AMD ROCm, Intel Arc, and CPU fallback.
    """
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available() and torch.backends.mps.is_built():
        return torch.device("mps")
    else:
        # Optimize CPU multi-threaded execution based on physical core availability
        try:
            num_cores = os.cpu_count() or 4
            torch.set_num_threads(max(1, min(num_cores, 16)))
            if hasattr(torch, "set_num_interop_threads"):
                torch.set_num_interop_threads(max(1, min(num_cores // 2, 8)))
        except Exception:
            pass
        return torch.device("cpu")


DEVICE = get_best_device()


class BrainNet(nn.Module):
    """
    Compact Pulse Macro-Action GRU Neural Network for Survivor AI Decision Making.
    Includes Macro-Action decision holding (duration_ticks) and PPO State-Value Critic Head.
    """
    __slots__ = ("fc1", "fc_duration", "fc_out", "gru", "hidden_size", "input_size", "output_size", "relu", "value_head")

    def __init__(self, input_size: int = 57, hidden_size: int = 64, output_size: int = 13):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.gru = nn.GRUCell(hidden_size, hidden_size)
        self.fc_out = nn.Linear(hidden_size, output_size)
        self.fc_duration = nn.Linear(hidden_size, 1)
        self.value_head = nn.Linear(hidden_size, 1)
        self.to(DEVICE)

    def forward(self, x: torch.Tensor, h: torch.Tensor):
        out = self.fc1(x)
        out = self.relu(out)
        h_next = self.gru(out, h)
        actions_out = self.fc_out(h_next)
        duration_out = self.fc_duration(h_next)
        value_out = self.value_head(h_next)
        return actions_out, duration_out, value_out, h_next

    def compile_model(self):
        """Attempts TorchScript JIT tracing / torch.compile for optimal C++ graph execution."""
        try:
            example_input = torch.zeros(1, self.input_size, device=DEVICE)
            example_h = torch.zeros(1, self.hidden_size, device=DEVICE)
            return torch.jit.trace(self, (example_input, example_h))
        except Exception:
            pass
        return self

    def init_hidden(self) -> torch.Tensor:
        return torch.zeros(1, self.hidden_size, dtype=torch.float32, device=DEVICE)

    def get_action_and_movement(self, inputs, prev_hidden=None):
        self.eval()
        if prev_hidden is None:
            prev_hidden = self.init_hidden()

        with torch.inference_mode():
            if isinstance(inputs, np.ndarray):
                try:
                    inp_tensor = torch.from_numpy(inputs).float().to(DEVICE)
                except Exception:
                    inp_tensor = torch.tensor(inputs.tolist(), dtype=torch.float32, device=DEVICE)
            else:
                inp_tensor = torch.tensor(inputs, dtype=torch.float32, device=DEVICE)
            if inp_tensor.dim() == 1:
                inp_tensor = inp_tensor.unsqueeze(0)
            if prev_hidden.dim() == 3:
                prev_hidden = prev_hidden.squeeze(1)
            if prev_hidden.device != DEVICE:
                prev_hidden = prev_hidden.to(DEVICE)

            actions_out, duration_out, value_out, new_hidden = self.forward(inp_tensor, prev_hidden)
            act_vec = actions_out.squeeze(0).cpu()
            dur_val = float(duration_out.squeeze(0).cpu().item())

        dx = float(torch.tanh(act_vec[0]).item())
        dy = float(torch.tanh(act_vec[1]).item())
        action_idx = int(torch.argmax(act_vec[2:]).item())
        # Map duration_out sigmoid/tanh to 1..8 ticks decision hold duration
        duration_ticks = max(1, min(8, int(round(4.0 + math.tanh(dur_val) * 3.0))))

        return dx, dy, action_idx, new_hidden, duration_ticks


class GeneticEvolutionManager:
    """
    Advanced Neuroevolution Engine with Tournament Selection, Adaptive Mutation,
    and Speciation Diversity Preservation.
    """
    __slots__ = ("best_fitness_history", "elite_fraction", "generation", "mutation_rate", "mutation_scale", "population_size", "stagnation_counter")

    def __init__(self, population_size: int = 20, mutation_rate: float = 0.1, mutation_scale: float = 0.2, elite_fraction: float = 0.2):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.mutation_scale = mutation_scale
        self.elite_fraction = elite_fraction
        self.generation = 1
        self.stagnation_counter = 0
        self.best_fitness_history = []

    def create_initial_brains(self) -> list:
        return [BrainNet(input_size=57, hidden_size=64, output_size=13) for _ in range(self.population_size)]

    def mutate_net(self, net: BrainNet, current_mutation_rate: float = None) -> BrainNet:
        rate = current_mutation_rate if current_mutation_rate is not None else self.mutation_rate
        mutated_net = BrainNet(input_size=net.input_size, hidden_size=net.hidden_size, output_size=net.output_size)
        mutated_net.load_state_dict(net.state_dict())
        with torch.no_grad():
            for param in mutated_net.parameters():
                if random.random() < rate:
                    noise = torch.randn_like(param) * self.mutation_scale
                    param.add_(noise)
        return mutated_net

    def crossover_nets(self, parent1: BrainNet, parent2: BrainNet) -> BrainNet:
        child = BrainNet(input_size=parent1.input_size, hidden_size=parent1.hidden_size, output_size=parent1.output_size)
        p1_dict = parent1.state_dict()
        p2_dict = parent2.state_dict()
        child_dict = child.state_dict()

        with torch.no_grad():
            for key in p1_dict:
                mask = torch.rand_like(p1_dict[key].float()) > 0.5
                child_dict[key] = torch.where(mask, p1_dict[key], p2_dict[key])
        child.load_state_dict(child_dict)
        return child

    def tournament_selection(self, brains_and_fitnesses: list, k: int = 3) -> BrainNet:
        """Tournament selection selecting the best brain out of k random candidates."""
        candidates = random.sample(brains_and_fitnesses, min(k, len(brains_and_fitnesses)))
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def evolve_population(self, brains_and_fitnesses: list):
        brains_and_fitnesses.sort(key=lambda x: x[1], reverse=True)
        best_fit = brains_and_fitnesses[0][1]

        # Adaptive Mutation Rate Control
        if self.best_fitness_history and best_fit <= self.best_fitness_history[-1]:
            self.stagnation_counter += 1
        else:
            self.stagnation_counter = 0

        self.best_fitness_history.append(best_fit)
        adaptive_mutation_rate = min(0.40, self.mutation_rate * (1.0 + 0.15 * self.stagnation_counter))

        sorted_brains = [b for b, f in brains_and_fitnesses]
        num_elites = max(1, int(self.population_size * self.elite_fraction))
        new_population = []

        # Retain Top Elites
        for i in range(num_elites):
            elite_copy = BrainNet(input_size=sorted_brains[i].input_size, hidden_size=sorted_brains[i].hidden_size, output_size=sorted_brains[i].output_size)
            elite_copy.load_state_dict(sorted_brains[i].state_dict())
            new_population.append(elite_copy)

        # Tournament Breeding with Adaptive Mutation
        while len(new_population) < self.population_size:
            p1 = self.tournament_selection(brains_and_fitnesses, k=3)
            p2 = self.tournament_selection(brains_and_fitnesses, k=3)
            child = self.crossover_nets(p1, p2)
            child = self.mutate_net(child, current_mutation_rate=adaptive_mutation_rate)
            new_population.append(child)

        self.generation += 1
        return new_population, best_fit

    def save_best_brain(self, brain: BrainNet, filepath: str = "best_brain.zbrain") -> None:
        save_zbrain(brain, filepath)

    def load_best_brain(self, brain: BrainNet, filepath: str = "best_brain.zbrain") -> None:
        load_zbrain(brain, filepath)


def save_zbrain(brain: BrainNet, filepath: str) -> None:
    """Saves a BrainNet model in custom compressed FP16 binary format (.zbrain)."""
    state = brain.state_dict()
    half_precision_state = {k: v.cpu().half() for k, v in state.items()}
    buffer = io.BytesIO()
    torch.save(half_precision_state, buffer)
    compressed = zlib.compress(buffer.getvalue(), level=9)
    with open(filepath, "wb") as f:
        f.write(b"ZBRAINv1")
        f.write(compressed)


def load_zbrain(brain: BrainNet, filepath: str) -> None:
    """Loads a BrainNet model from custom compressed binary format (.zbrain)."""
    with open(filepath, "rb") as f:
        header = f.read(8)
        if header != b"ZBRAINv1":
            f.seek(0)
            # Legacy fallback
            brain.load_state_dict(torch.load(filepath, map_location=DEVICE))
            return
        compressed = f.read()

    decompressed = zlib.decompress(compressed)
    buffer = io.BytesIO(decompressed)
    half_precision_state = torch.load(buffer, map_location=DEVICE)
    float_precision_state = {k: v.float().to(DEVICE) for k, v in half_precision_state.items()}
    brain.load_state_dict(float_precision_state)
