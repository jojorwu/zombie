# Neural Networks & Simulation Optimizations

## Batched Neural Inference & GRU Memory
- **Batched Matrix Multiplication (BMM)**: `BrainNet` processes all active survivors in a single batched PyTorch forward pass (`batch_get_action_and_movement` in `src/ai/brain_actions.py`), eliminating Python thread pool overhead.
- **GRU Recurrent State**: Recurrent neural network hidden states (`h_next`) maintain memory of past environmental stimuli across ticks.
- **Compressed Binary Model Checkpoints (`.zbrain`)**: FP16 weight quantization combined with zlib compression for compact neural model saving (`save_zbrain`, `load_zbrain`).

## Spatial Chunking & Entity Object Pooling
- **Spatial Chunk Partitioning (`ChunkManager`)**: Maps are dynamically divided into 16x16 chunk grids with explicit `ChunkState` transitions (`UNLOADED`, `GENERATED`, `INACTIVE`, `ACTIVE`).
- **Entity Freezing Outside Active Chunks**: Simulation ticks freeze entity processing (e.g. distant zombies) located in inactive chunks to maximize tick framerates.
- **High-Performance Object Pooling (`ObjectPool`)**: `EntityFactory` recycles zombies, scent trails, noise events, items, and animals, preventing garbage collection stutter.

## Python, Vector & Native Vulkan Acceleration
- **Memory Slot Optimization**: `__slots__` declared across core data structures (`WorldGenerator`, `AnatomicalHealth`) to reduce memory footprints and accelerate attribute access.
- **Vectorized Generation**: NumPy array operations accelerate terrain placement, road grid layout, and sidewalk drawing.
- **O(1) Spatial Lookups**: `frozenset` collections optimize tile opacity checks for Fog of War (`compute_fog_of_war`).
- **Native Vulkan Crate Acceleration**: C-speed viewport tile rendering via PyO3 Rust extension crate (`rust_engine`) connected through `VulkanBridge`.

## Combinatorial Optimization Algorithms (`utils/p_np_math.py`)
- **Polynomial Knapsack Solver (`PolynomialKnapsackSolver`)**: $O(N \cdot W)$ Dynamic Programming solver optimizing survivor item looting by evaluating weight vs survival utility values.
- **Polynomial 2-Opt TSP Solver (`PolynomialTSPSolver`)**: $O(N^2)$ heuristic solver optimizing multi-destination looting waypoint routes between buildings.
