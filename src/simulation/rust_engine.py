import numpy as np
from typing import Dict, Any, Tuple, Optional

try:
    from rust_vulkan_render import RustEngineCore
    RUST_ENGINE_AVAILABLE = True
except ImportError:
    RUST_ENGINE_AVAILABLE = False


class PythonRustEngineBridge:
    """
    Python-Rust Engine Bridge interface.
    Delegates world, entity, physics, and pathfinding logic execution to Rust,
    providing flat observation arrays for Python neural networks.
    """
    def __init__(self, width: int = 1000, height: int = 1000):
        self.width = width
        self.height = height
        if RUST_ENGINE_AVAILABLE:
            self.native_core = RustEngineCore(width, height)
        else:
            self.native_core = None

    def step(self, dx: float = 0.0, dy: float = 0.0, action: int = 0) -> Tuple[np.ndarray, bool]:
        """Executes one simulation tick step in Rust and extracts zero-copy observations."""
        if self.native_core:
            self.native_core.step(dx, dy, action)
            obs = np.array(self.native_core.get_observation_flat(), dtype=np.float32)
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
