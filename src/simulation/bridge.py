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
    providing zero-copy flat observation arrays for Python neural networks.
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

    def sync_entities_to_rust(self, survivors: list, zombies: list):
        """Synchronizes Python survivors and zombies into RustFullSimulationCore using batched NumPy vectors."""
        if not self.full_sim_core:
            return

        if hasattr(self.full_sim_core, 'sync_survivors_batch') and survivors:
            s_arr = np.empty((len(survivors), 6), dtype=np.float32)
            for i, s in enumerate(survivors):
                s_arr[i, 0] = float(s.x)
                s_arr[i, 1] = float(s.y)
                s_arr[i, 2] = float(s.z)
                s_arr[i, 3] = float(getattr(s, 'health', 100.0))
                s_arr[i, 4] = float(getattr(s, 'hunger', 100.0))
                s_arr[i, 5] = float(getattr(s, 'thirst', 100.0))
            self.full_sim_core.sync_survivors_batch(s_arr)

        if hasattr(self.full_sim_core, 'sync_zombies_batch') and zombies:
            z_arr = np.empty((len(zombies), 5), dtype=np.float32)
            for i, z in enumerate(zombies):
                z_arr[i, 0] = float(z.x)
                z_arr[i, 1] = float(z.y)
                z_arr[i, 2] = float(z.z)
                z_arr[i, 3] = float(getattr(z, 'hp', getattr(z, 'health', 50.0)))
                z_arr[i, 4] = float(getattr(z, 'speed', 0.08))
            self.full_sim_core.sync_zombies_batch(z_arr)

    def step_full_simulation(self, actions: list, movements: list) -> np.ndarray:
        """Executes full simulation step in Rust and returns 2D observation tensor for PyTorch."""
        if self.full_sim_core:
            self.full_sim_core.step_simulation(actions, movements)
            return self.full_sim_core.get_observations_matrix()
        return np.zeros((len(actions), 57), dtype=np.float32)

    def sync_rust_to_entities(self, survivors: list, zombies: list):
        """Synchronizes updated positions and vitals back from Rust to Python entities in batch."""
        if not self.full_sim_core:
            return

        if hasattr(self.full_sim_core, 'get_survivors_batch') and survivors:
            s_arr = self.full_sim_core.get_survivors_batch()
            for idx, s in enumerate(survivors):
                if idx < s_arr.shape[0]:
                    s.x, s.y, s.z = float(s_arr[idx, 0]), float(s_arr[idx, 1]), int(s_arr[idx, 2])

        if hasattr(self.full_sim_core, 'get_zombies_batch') and zombies:
            z_arr = self.full_sim_core.get_zombies_batch()
            for idx, z in enumerate(zombies):
                if idx < z_arr.shape[0]:
                    z.x, z.y, z.z = float(z_arr[idx, 0]), float(z_arr[idx, 1]), int(z_arr[idx, 2])
                    zhp = float(z_arr[idx, 3])
                    zalive = bool(z_arr[idx, 4] > 0.5)
                    z.hp = zhp
                    z.health = zhp
                    z.is_alive = zalive

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
