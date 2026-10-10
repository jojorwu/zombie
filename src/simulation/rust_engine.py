import numpy as np
from typing import Dict, Any, Tuple, Optional

try:
    from rust_engine import RustEngineCore, RustFullSimulationCore
    RUST_ENGINE_AVAILABLE = True
except ImportError:
    RUST_ENGINE_AVAILABLE = False


class PythonRustEngineBridge:
    """
    Python-Rust Engine Bridge interface.
    Delegates world, entity, physics, and pathfinding logic execution to Rust,
    providing flat observation arrays for Python neural networks.
    """
    def __init__(self, width: int = 1000, height: int = 1000, num_survivors: int = 1, num_zombies: int = 20):
        self.width = width
        self.height = height
        if RUST_ENGINE_AVAILABLE:
            self.native_core = RustEngineCore(width, height)
            self.full_sim_core = RustFullSimulationCore(width, height, num_survivors, num_zombies)
        else:
            self.native_core = None
            self.full_sim_core = None

    def sync_survivor_state(self, survivor, current_tick: int = 0):
        """Synchronize Python survivor entity state into RustEngineCore."""
        if self.native_core and survivor:
            self.native_core.sync_survivor_state(
                float(survivor.x),
                float(survivor.y),
                int(survivor.z),
                float(getattr(survivor, 'health', 100.0)),
                float(getattr(survivor, 'hunger', 100.0)),
                float(getattr(survivor, 'thirst', 100.0)),
                int(current_tick)
            )

    def step_full_simulation(self, actions: list, movements: list) -> np.ndarray:
        """Executes full simulation step in Rust and returns 2D observation tensor for PyTorch."""
        if self.full_sim_core:
            self.full_sim_core.step_simulation(actions, movements)
            return self.full_sim_core.get_observations_matrix()
        return np.zeros((len(actions), 57), dtype=np.float32)

    def step(self, dx: float = 0.0, dy: float = 0.0, action: int = 0) -> Tuple[np.ndarray, bool]:
        """Executes one simulation tick step in Rust and extracts zero-copy observations."""
        if self.native_core:
            self.native_core.step(dx, dy, action)
            obs = self.native_core.get_observation_flat()
            done = False
            return obs, done
        else:
            obs = np.zeros(57, dtype=np.float32)
            return obs, False

    def get_current_tick(self) -> int:
        if self.native_core:
            return self.native_core.get_current_tick()
        return 0

    def get_survivor_pos(self) -> Tuple[float, float, int]:
        if self.native_core:
            return self.native_core.get_survivor_pos()
        return (0.0, 0.0, 0)
