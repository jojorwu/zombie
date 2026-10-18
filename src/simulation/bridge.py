from typing import Any

import numpy as np

try:
    from rust_engine import RustEngineCore, RustFullSimulationCore
    RUST_ENGINE_AVAILABLE: bool = True
except ImportError:
    RUST_ENGINE_AVAILABLE: bool = False


# Ground item type ids understood by the Rust world-item registry.
# Kept here (bridge layer) so the engine never touches raw ints.
ITEM_TYPE_FOOD = 1
ITEM_TYPE_WATER = 2
ITEM_TYPE_MEDKIT = 3
ITEM_TYPE_AMMO = 4
ITEM_TYPE_MATERIAL = 5
ITEM_TYPE_WEAPON = 6


def map_item_type_to_rust(item_type_name: str) -> int:
    """Maps a Python ``ResourceItem`` type name to the Rust numeric item kind.

    Unknown types fall back to FOOD so stray spawns still land in the Rust
    loot registry instead of being silently dropped.
    """
    mapping: dict[str, int] = {
        "canned_food": ITEM_TYPE_FOOD,
        "food": ITEM_TYPE_FOOD,
        "steak": ITEM_TYPE_FOOD,
        "cereal": ITEM_TYPE_FOOD,
        "water": ITEM_TYPE_WATER,
        "medkit": ITEM_TYPE_MEDKIT,
        "pistol_ammo": ITEM_TYPE_AMMO,
        "shotgun_shells": ITEM_TYPE_AMMO,
        "rifle_ammo": ITEM_TYPE_AMMO,
        "wood": ITEM_TYPE_MATERIAL,
        "metal": ITEM_TYPE_MATERIAL,
        "weapon": ITEM_TYPE_WEAPON,
        "pistol": ITEM_TYPE_WEAPON,
        "shotgun": ITEM_TYPE_WEAPON,
        "rifle": ITEM_TYPE_WEAPON,
    }
    return mapping.get(item_type_name, ITEM_TYPE_FOOD)


class PythonRustEngineBridge:
    """
    Single Python↔Rust boundary for the simulation ("Rust owns logic,
    Python owns UI + neural nets" architecture).

    Responsibilities:
      * push survivor/zombie rosters into the Rust core using a stable
        identity mapping (entity_id = py_entity.uid, a monotonic unique id —
        never ``id()`` and never index alignment);
      * run the full simulation step inside Rust;
      * hand the neural network a zero-copy (N, 57) observation matrix;
      * harvest updated state back onto Python view entities (UI only);
      * own fitness-score retrieval and ground-item registration.

    The engine should call these high-level methods instead of reaching into
    ``full_sim_core`` directly — keeps the spaghetti out of both sides.
    """
    width: int
    height: int
    native_core: Any | None
    full_sim_core: Any | None
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

    @property
    def rust_active(self) -> bool:
        """True when the native Rust simulation core is loaded and usable."""
        return self.full_sim_core is not None

    # ------------------------------------------------------------------ #
    # High-level tick API used by SimulationEngine                        #
    # ------------------------------------------------------------------ #

    def get_observations(self) -> np.ndarray:
        """Zero-copy (N, 57) observation matrix computed in Rust (Rayon-parallel)."""
        return self.full_sim_core.get_observations_matrix()

    def emit_noise(self, x: float, y: float, z: int, volume: float) -> None:
        """Registers an acoustic noise event inside the Rust simulation memory."""
        if self.rust_active:
            self.full_sim_core.emit_noise(float(x), float(y), int(z), float(volume))

    def add_world_items(self, items: list[Any]) -> None:
        """Registers Python-spawned ground items into the Rust loot registry."""
        if not self.rust_active:
            return
        for item in items:
            itype = map_item_type_to_rust(getattr(item, "item_type", ""))
            self.add_item_to_rust(
                item.x, item.y, item.z, itype, getattr(item, "amount", 1)
            )

    def step_survivor_tick(
        self,
        survivors: list[Any],
        zombies: list[Any],
        actions: list[int],
        movements: list[tuple[float, float]],
    ) -> np.ndarray:
        """One Rust-owned tick for the survivor phase.

        Syncs rosters (identity-mapped), executes all game logic in Rust
        (vitals, movement, looting, crafting, combat, flocking, noise),
        harvests state back onto the Python view entities, and returns the
        fresh observation matrix for the next neural-network pass.
        """
        self.sync_entities_to_rust(survivors, zombies)
        self.full_sim_core.step_simulation(actions, movements)
        self.sync_rust_to_entities(survivors, zombies)
        return self.full_sim_core.get_observations_matrix()

    def step_zombie_phase_tick(self, survivors: list[Any], zombies: list[Any]) -> None:
        """Rust zombie-AI/flocking tick with idle survivor actions.

        Called after the survivor phase: sync pushes the current active
        zombie window (chunk freeze/rehydrate may have changed it), Rust
        steps flocking/combat with no-op survivor input, then live state is
        harvested back onto the Python view objects.
        """
        n_s: int = len(survivors)
        self.sync_entities_to_rust(survivors, zombies)
        self.full_sim_core.step_simulation([0] * n_s, [(0.0, 0.0)] * n_s)
        self.sync_rust_to_entities(survivors, zombies)

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

    def sync_entities_to_rust(
        self,
        survivors: list[Any],
        zombies: list[Any],
        full_roster: bool = False,
    ) -> None:
        """Synchronizes Python survivors and zombies into RustFullSimulationCore.

        Zombies are synced through a stable identity mapping: each row carries
        the entity's monotonic ``uid`` as `entity_id` (never ``id()``, which is
        recycled after GC and loses precision through float32), so the Rust
        roster matches entities by id instead of row position. This keeps chunk
        freeze/rehydrate and death cleanup (which reorder or resize the Python
        active list) from ever mapping wrong slots onto entities. Pass
        `full_roster=True` on world reset/generation start to rebuild the Rust
        roster from scratch.
        """
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
            # Row layout: [entity_id, x, y, z_level, hp, speed] — 6 columns.
            # entity_id is the monotonic uid; uids stay below 2**24 in any
            # realistic run so they are exact even through the float32 buffer.
            if not hasattr(self, '_zomb_buf') or self._zomb_buf.shape[0] != n_z:
                self._zomb_buf = np.empty((n_z, 6), dtype=np.float32)

            for i, z in enumerate(zombies):
                self._zomb_buf[i, 0] = float(getattr(z, 'uid', 0))
                self._zomb_buf[i, 1] = float(z.x)
                self._zomb_buf[i, 2] = float(z.y)
                self._zomb_buf[i, 3] = float(z.z)
                self._zomb_buf[i, 4] = float(getattr(z, 'hp', getattr(z, 'health', 50.0)))
                self._zomb_buf[i, 5] = float(getattr(z, 'speed', 0.08))
            self.full_sim_core.sync_zombies_batch(self._zomb_buf, full_roster)

    def step_full_simulation(self, actions: list[int], movements: list[tuple[float, float]]) -> np.ndarray:
        """Executes full simulation step in Rust and returns 2D observation tensor for PyTorch."""
        if self.full_sim_core:
            self.full_sim_core.step_simulation(actions, movements)
            return self.full_sim_core.get_observations_matrix()
        return np.zeros((len(actions), 57), dtype=np.float32)

    def get_fitness_scores(self) -> np.ndarray:
        """Retrieves 1D NumPy array of survivor fitness scores computed purely in Rust."""
        if self.full_sim_core and hasattr(self.full_sim_core, 'get_fitness_scores'):
            return self.full_sim_core.get_fitness_scores()
        return np.array([], dtype=np.float32)

    def get_survivors_detailed(self) -> np.ndarray:
        """Retrieves detailed survivor attributes matrix (N, 12) from Rust."""
        if self.full_sim_core and hasattr(self.full_sim_core, 'get_survivors_detailed_batch'):
            return self.full_sim_core.get_survivors_detailed_batch()
        return np.zeros((0, 12), dtype=np.float32)

    def get_items_batch(self) -> np.ndarray:
        """Retrieves active ground items matrix (K, 5) [x, y, z, type, amount] from Rust."""
        if self.full_sim_core and hasattr(self.full_sim_core, 'get_items_batch'):
            return self.full_sim_core.get_items_batch()
        return np.zeros((0, 5), dtype=np.float32)

    def add_item_to_rust(self, x: float, y: float, z: int, item_type: int, amount: int = 1) -> None:
        """Registers a world item directly in Rust simulation memory."""
        if self.full_sim_core and hasattr(self.full_sim_core, 'add_item'):
            self.full_sim_core.add_item(float(x), float(y), int(z), int(item_type), int(amount))

    def sync_rust_to_entities(self, survivors: list[Any], zombies: list[Any]) -> None:
        """Synchronizes updated positions and vitals back from Rust to Python entities in batch."""
        if not self.full_sim_core:
            return

        if hasattr(self.full_sim_core, 'get_survivors_detailed_batch') and survivors:
            s_arr: np.ndarray = self.full_sim_core.get_survivors_detailed_batch()
            for idx, s in enumerate(survivors):
                if idx < s_arr.shape[0]:
                    s.x, s.y, s.z = float(s_arr[idx, 0]), float(s_arr[idx, 1]), int(s_arr[idx, 2])
                    s.health = float(s_arr[idx, 3])
                    s.hunger = float(s_arr[idx, 4])
                    s.thirst = float(s_arr[idx, 5])
                    s.is_alive = bool(s_arr[idx, 6] > 0.5)
                    s.score = float(s_arr[idx, 7])
                    s.kills = int(s_arr[idx, 8])
        elif hasattr(self.full_sim_core, 'get_survivors_batch') and survivors:
            s_arr: np.ndarray = self.full_sim_core.get_survivors_batch()
            for idx, s in enumerate(survivors):
                if idx < s_arr.shape[0]:
                    s.x, s.y, s.z = float(s_arr[idx, 0]), float(s_arr[idx, 1]), int(s_arr[idx, 2])
                    salive: bool = bool(s_arr[idx, 3] > 0.5)
                    s.is_alive = salive

        if hasattr(self.full_sim_core, 'get_zombies_batch') and zombies:
            # Rust returns only the ACTIVE window; rows are keyed by entity_id.
            # Match back to Python objects by their stable monotonic uid so
            # reordering on either side never misaligns state (variant A).
            z_arr: np.ndarray = self.full_sim_core.get_zombies_batch()
            by_uid: dict[int, int] = {getattr(z, 'uid', 0): i for i, z in enumerate(zombies)}
            for row in range(z_arr.shape[0]):
                py_idx = by_uid.get(int(z_arr[row, 0]))
                if py_idx is None:
                    continue
                z = zombies[py_idx]
                z.x, z.y, z.z = float(z_arr[row, 1]), float(z_arr[row, 2]), int(z_arr[row, 3])
                zhp: float = float(z_arr[row, 4])
                zalive: bool = bool(z_arr[row, 5] > 0.5)
                z.hp = zhp
                z.health = zhp
                z.is_alive = zalive

    def step(self, dx: float = 0.0, dy: float = 0.0, action: int = 0) -> tuple[np.ndarray, bool]:
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

    def get_survivor_pos(self) -> tuple[float, float, int]:
        if self.native_core:
            pos = self.native_core.get_survivor_pos()
            return (float(pos[0]), float(pos[1]), int(pos[2]))
        return (0.0, 0.0, 0)
