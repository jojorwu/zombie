import numpy as np
from typing import Tuple, Dict, Any, Optional
from src.ai.brain_actions import extract_survivor_inputs


class SurvivorGymEnv:
    """
    Gymnasium-compatible Environment Wrapper for SimulationEngine
    supporting vector observations, multi-channel spatial sensors, and PPO rewards.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        from src.simulation.engine import SimulationEngine
        if config is None:
            config = {
                "simulation": {
                    "map_width": 100,
                    "map_height": 100,
                    "num_survivors": 1,
                    "num_zombies": 20,
                    "num_animals": 5,
                    "num_vehicles": 2,
                    "day_length_ticks": 3600,
                    "max_ticks_per_gen": 1000,
                },
                "evolution": {
                    "mutation_rate": 0.1,
                    "mutation_scale": 0.2,
                    "elite_fraction": 0.2,
                }
            }
        self.config = config
        self.engine = SimulationEngine(config)
        self.action_space_size = 13
        self.observation_space_size = 57

    def reset(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Resets the simulation environment and returns initial observation."""
        self.engine.reset_generation()
        survivor = self.engine.survivors[0] if self.engine.survivors else None
        if survivor:
            obs = extract_survivor_inputs(
                survivor, self.engine.world, self.engine.items,
                self.engine.vehicles, self.engine.zombies, self.engine.animals
            )
        else:
            obs = np.zeros(self.observation_space_size, dtype=np.float32)
        return obs, {}

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Executes one simulation tick step with discrete action choice and calculates PPO reward."""
        if not self.engine.survivors:
            return np.zeros(self.observation_space_size, dtype=np.float32), 0.0, True, False, {}

        survivor = self.engine.survivors[0]
        prev_health = survivor.health
        prev_visited = len(survivor.visited_tiles)
        prev_kills = survivor.kills

        survivor.update_needs()
        survivor.perform_action(
            action, self.engine.world, self.engine.items,
            self.engine.vehicles, self.engine.zombies, self.engine.animals,
            self.engine.survivors, noise_events=self.engine.noise_events
        )

        self.engine.world.current_tick += 1
        terminated = not survivor.is_alive
        truncated = self.engine.world.current_tick >= self.config["simulation"].get("max_ticks_per_gen", 1000)

        # Calculate PPO Dense Reward
        reward = 0.1  # Survival tick reward
        if survivor.health < prev_health:
            reward -= (prev_health - survivor.health) * 2.0
        if len(survivor.visited_tiles) > prev_visited:
            reward += 1.5  # Exploration reward
        if survivor.kills > prev_kills:
            reward += 10.0  # Zombie kill reward

        obs = extract_survivor_inputs(
            survivor, self.engine.world, self.engine.items,
            self.engine.vehicles, self.engine.zombies, self.engine.animals
        )

        return obs, reward, terminated, truncated, {"kills": survivor.kills, "visited": len(survivor.visited_tiles)}
