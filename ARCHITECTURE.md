# Zombie AI Simulation - Architecture & Developer Guide

## 1. High-Level Architecture Overview

The Zombie AI Simulation Engine is built on a **Hybrid Python-Rust High-Performance Architecture**:
* **Python Subsystem (`src/ai/`, `src/ui/`, `src/simulation/`)**: Manages neural network inference (PyTorch BMM, GRU, neuroevolution), Pygame GUI rendering, event bus dispatch, and user interactions.
* **Rust Core Subsystem (`src/rust/`)**: Native multi-threaded compiled engine (`rust_engine`) compiled via Maturin/PyO3. Executes 3D pathfinding (A*), zombie flocking steering, Vulkan composite viewport rendering, acoustic noise propagation, and parallel environment simulation (Rayon).

```
                      +------------------------------------------+
                      |         Pygame Main Menu & GUI           |
                      +--------------------+---------------------+
                                           |
                                           v
                      +--------------------+---------------------+
                      |    SimulationEngine & EventBus           |
                      +----------+-------------------+-----------+
                                 |                   |
                                 v                   v
+--------------------------------+---+   +-----------+----------------------+
|     Python PyTorch AI Engine       |   |       Native Rust Crate          |
|  - BrainNet (57 Inputs, GRU)       |   |  - RustFullSimulationCore        |
|  - Multi-Device Accelerator        |   |  - Zero-Copy PyO3 Memory Views   |
|    (CUDA / MPS / DirectML / CPU)   |   |  - Vulkan Composite Tile Render  |
|  - Neuroevolution & PPO Training   |   |  - 3D A* Pathfinding (Rayon)     |
+------------------------------------+   +----------------------------------+
```

---

## 2. Core Subsystems

### A. Python-Rust Bridge (`src/simulation/bridge.py`)
Provides zero-copy direct memory array conversion between Python NumPy buffer slices and Rust C-API (`PyReadonlyArray2`, `PyArray2`).
- **`sync_zombies_batch(data)`**: Synchronizes entity vectors $(N, 5)$ in a single PyO3 FFI call.
- **`sync_survivors_batch(data)`**: Synchronizes survivor states $(N, 6)$ in a single PyO3 FFI call.
- **`get_observations_matrix(py)`**: Allocates a zero-copy $(N, 57)$ float32 NumPy matrix directly filled by Rayon parallel threads in Rust.

### B. AI Perception & Neural Network (`src/ai/network.py` & `src/ai/inference.py`)
- **Accelerator Selection**: Auto-detects NVIDIA CUDA, Apple Silicon Metal (`mps`), AMD ROCm, and multi-threaded CPU (`os.cpu_count()`).
- **Weight Caching**: `get_cached_stacked_weights()` caches stacked tensor matrices for population brains, bypassing per-tick GPU allocation overhead.
- **Macro-Action Decision Holding**: Outputs action predictions alongside `duration_ticks` (holding decisions for 1..10 ticks) to eliminate movement jitter.

### C. Sparse Spatial Hash Grid & Chunk Persistence (`src/world/grid.py` & `src/world/chunk.py`)
- **Ground Level ($Z=0$)**: Dense 2D Flat-NumPy array (`ground_grid`) for $O(1)$ tile lookups.
- **Vertical Levels ($Z \neq 0$)**: Sparse Spatial Hash dictionary (`sparse_z_grid`).
- **Chunk State Persistence**: Active chunks ($16 \times 16$) update using $O(N_{\text{changed}})$ delta state tracking. Unloaded entities (zombies, vehicles, items) freeze into chunk stores with unique ID deduplication (`seen_ids`) to eliminate memory overhead.

### D. Engine Utility Facade (`src/simulation/utility_facade.py`)
Centralized facade API for domain utilities:
- Container Transfers (`ContainerUtility`)
- Tile Interactions (`TileInteractionUtility`)
- Acoustic SPL Scaling (`SoundUtility`)
- Ballistics Flight (`BallisticsUtility`)
- Vehicle Physics (`VehiclePhysicsUtility`)
- Power Grid Status (`ElectricityUtility`)

---

## 3. Directory Layout

```
├── main.py                       # Application Entry Point
├── train.py                      # Neuroevolution & PPO CLI Trainer
├── build.py                      # Cross-Platform 64-bit Executable Builder
├── zombie_sim.spec               # PyInstaller Cross-Platform Configuration
├── config.json                   # Simulation & World Configuration
├── ARCHITECTURE.md               # Architectural Reference Guide
├── src/
│   ├── ai/                       # BrainNet, Inference, PPO, Pathfinding
│   ├── entities/                 # Survivor, Zombie, Vehicle, Item, State Managers
│   ├── world/                    # Grid, Chunk Persistence, Generation, Weather
│   ├── ui/                       # Pygame GUI, Camera, Main Menu, Vulkan Bridge
│   ├── simulation/               # Engine, Bridge, Utility Facade, Event Bus
│   └── rust/                     # Native Rust Engine Crate (src/rust/src/)
│       ├── ai/                   # Native Neural Inference & Target Selection
│       ├── world/                # Native Grid & Procedural Generator
│       ├── renderer/             # Vulkan RGBA Viewport Renderer
│       └── simulation/           # Native Full Simulation Core & Parallel Manager
└── tests/                        # Domain Unit & Max-Load Stress Benchmarks
```

---

## 4. Verification & Testing

Run all unit tests and stress benchmarks:
```bash
python3 tests/run_tests.py
```
Or launch the main menu (`python main.py`) and press **`[T]`** / click **Run Automated Tests** to execute the test suite directly from the GUI.
