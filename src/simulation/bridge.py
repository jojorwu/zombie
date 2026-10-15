import numpy as np
from typing import Any, Tuple, Optional, List

try:
    from rust_engine import RustEngineCore, RustFullSimulationCore
    RUST_ENGINE_AVAILABLE: bool = True
except ImportError:
    RUST_ENGINE_AVAILABLE: bool = False


class PythonRustEngineBridge:
    """
    Python-Rust Engine Bridge interface with strict type annotations.
    Delegates world, entity, physics, and pathfinding logic execution to Rust,
    providing zero-copy flat observation arrays for Python neural networks.
    """
    width: int
    height: int
    native_core: Optional[Any]
    full_sim_core: Optional[Any]
    _surv_buf: np.ndarray
    _zomb_buf: np.ndarray

    def __init__(self, width: int = 1000, height: int = 1000, num_survivors: int = 1, num_zombies: int = 20) -> None:
        self.width = width
        self.height = height
        if RUST_ENGINE_AVAILABLE:
            self.native_core = RustEngineCore(width, height)
            self.full_sim_core = RustFullSimulationCore(width, height, num_survivors, num_zombies)
        else:
            self.native_core = None
            self.full_sim_core = None

    def sync_survivor_state(self, survivor: Any, current_tick: int = 0) -> None:
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

    def sync_entities_to_rust(self, survivors: List[Any], zombies: List[Any]) -> None:
        """Synchronizes Python survivors and zombies into RustFullSimulationCore using cached NumPy buffers."""
        if not self.full_sim_core:
            return

        if hasattr(self.full_sim_core, 'sync_survivors_batch') and survivors:
            n_s: int = len(survivors)
            if not hasattr(self, '_surv_buf') or self._surv_buf.shape[0] != n_s:
                self._surv_buf = np.empty((n_s, 6), dtype=np.float32)

            for i, s in enumerate(survivors):
                self._surv_buf[i, 0] = float(s.x)
                self._surv_buf[i, 1] = float(s.y)
                self._surv_buf[i, 2] = float(s.z)
                self._surv_buf[i, 3] = float(getattr(s, 'health', 100.0))
                self._surv_buf[i, 4] = float(getattr(s, 'hunger', 100.0))
                self._surv_buf[i, 5] = float(getattr(s, 'thirst', 100.0))
            self.full_sim_core.sync_survivors_batch(self._surv_buf)

        if hasattr(self.full_sim_core, 'sync_zombies_batch') and zombies:
            n_z: int = len(zombies)
            if not hasattr(self, '_zomb_buf') or self._zomb_buf.shape[0] != n_z:
                self._zomb_buf = np.empty((n_z, 5), dtype=np.float32)

            for i, z in enumerate(zombies):
                self._zomb_buf[i, 0] = float(z.x)
                self._zomb_buf[i, 1] = float(z.y)
                self._zomb_buf[i, 2] = float(z.z)
                self._zomb_buf[i, 3] = float(getattr(z, 'hp', getattr(z, 'health', 50.0)))
                self._zomb_buf[i, 4] = float(getattr(z, 'speed', 0.08))
            self.full_sim_core.sync_zombies_batch(self._zomb_buf)

    def step_full_simulation(self, actions: List[int], movements: List[Tuple[float, float]]) -> np.ndarray:
        """Executes full simulation step in Rust and returns 2D observation tensor for PyTorch."""
        if self.full_sim_core:
            self.full_sim_core.step_simulation(actions, movements)
            return self.full_sim_core.get_observations_matrix()
        return np.zeros((len(actions), 57), dtype=np.float32)

    def sync_rust_to_entities(self, survivors: List[Any], zombies: List[Any]) -> None:
        """Synchronizes updated positions and vitals back from Rust to Python entities in batch."""
        if not self.full_sim_core:
            return

        if hasattr(self.full_sim_core, 'get_survivors_batch') and survivors:
            s_arr: np.ndarray = self.full_sim_core.get_survivors_batch()
            for idx, s in enumerate(survivors):
                if idx < s_arr.shape[0]:
                    s.x, s.y, s.z = float(s_arr[idx, 0]), float(s_arr[idx, 1]), int(s_arr[idx, 2])
                    salive: bool = bool(s_arr[idx, 3] > 0.5)
                    s.is_alive = salive

        if hasattr(self.full_sim_core, 'get_zombies_batch') and zombies:
            z_arr: np.ndarray = self.full_sim_core.get_zombies_batch()
            for idx, z in enumerate(zombies):
                if idx < z_arr.shape[0]:
                    z.x, z.y, z.z = float(z_arr[idx, 0]), float(z_arr[idx, 1]), int(z_arr[idx, 2])
                    zhp: float = float(z_arr[idx, 3])
                    zalive: bool = bool(z_arr[idx, 4] > 0.5)
                    z.hp = zhp
                    z.health = zhp
                    z.is_alive = zalive

    def step(self, dx: float = 0.0, dy: float = 0.0, action: int = 0) -> Tuple[np.ndarray, bool]:
        """Executes one simulation tick step in Rust and extracts zero-copy observations."""
        if self.native_core:
            self.native_core.step(dx, dy, action)
            obs: np.ndarray = self.native_core.get_observation_flat()
            done: bool = False
            return obs, done
        else:
            obs = np.zeros(57, dtype=np.float32)
            return obs, False

    def get_current_tick(self) -> int:
        if self.native_core:
            return int(self.native_core.get_current_tick())
        return 0

    def get_survivor_pos(self) -> Tuple[float, float, int]:
        if self.native_core:
            pos = self.native_core.get_survivor_pos()
            return (float(pos[0]), float(pos[1]), int(pos[2]))
        return (0.0, 0.0, 0)
