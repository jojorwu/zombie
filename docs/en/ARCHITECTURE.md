# Architecture Overview

## Subpackage Directory Structure (`src/`)

The simulation engine is organized into modular subpackages under `src/`:

### 1. `src/world/`
- **`grid.py`**: Core `World` grid class managing 3D spatial dimensions ($X \times Y \times Z$).
- **`chunk.py`**: `ChunkManager` and `ChunkState` handling 16x16 chunk dynamic loading, activation, and multi-chunk building footprint registration.
- **`generation.py`**: `WorldGenerator` generating vector terrain, road grids, district zoning, BSP interior building rooms, basements, and auto repair shops.
- **`tiles.py`**: `TileType` enumerations, interaction flags, and terrain movement speed modifiers (`TILE_SPEED_MODIFIERS`).
- **`lighting.py`**: `LightingManager` managing solar zenith elevation angles, 29.5-day synodic lunar cycles, dynamic point/cone light sources, and `compute_fog_of_war`.
- **`weather.py`**: `WeatherManager` driving dynamic wind vectors, 100x100 moving rainstorms, and 4-season climate cycles.

### 2. `src/ai/`
- **`brain_net.py`**: PyTorch GRU `BrainNet` architecture processing 57 spatial/status sensory inputs with 64 hidden units. Supports compressed `.zbrain` binary serialization.
- **`brain_actions.py`**: Batched tensor matrix multiplication (`batch_get_action_and_movement`) for parallel neural evaluation across active survivors.
- **`pathfinding.py`**: `AStar3D` priority-queue navigation across 3D terrain, stairs, ladders, doors, and windows.
- **`brain.py`**: Decision-making wrappers and survivor action selection logic.

### 3. `src/entities/`
- **`survivor/`**: `Survivor` entity, `survivor_looting.py` (knapsack optimization looting), and crafting mechanics.
- **`zombie/`**: Zombie AI behavior (`zombie_entity.py`), light-sensitive vision perception (`zombie_perception.py`), acoustic noise tracking, scent trailing, and spatial grid bucketing flocking (`zombie_flock.py`).
- **`animal.py`**: `Animal` base class and `Rat` entity with fast interior navigation and trash scavenging.
- **`vehicle.py`**: `Vehicle` entity, CDDA-style `VehiclePart` modular components, vector physics (`VehiclePhysics`), and momentum collision damage.
- **`item.py`**: `ResourceItem`, ballistics specifications, `MetalQuality` tiers, and perishable food properties.
- **`factory.py`**: `EntityFactory` with high-performance `ObjectPool` allocation for zombies, scents, noises, items, and animals.
- **`health.py`**: `AnatomicalHealth` model tracking head, torso, and limb health pools, dismemberment, and crippling.
- **`state_manager.py`**: `FurnitureStateManager` and `ItemStateManager` maintaining detailed conditions, durability, spoilage, and container inventories.

### 4. `src/simulation/`
- **`engine.py`**: `SimulationEngine` running tick updates, active chunk management, entity state updates, loot spawning, and generation resets.
- **`spawner.py`**: `EntitySpawner` for procedural entity placement.
- **`environment.py`**: Environmental event propagation.

### 5. `src/ui/`
- **`renderer.py`**: `RendererUI` Pygame viewport rendering with camera culling and theme toggles.
- **`hud_renderer.py`**: Heads-Up Display (HUD) rendering health, emotional states, time, weather, and inventory.
- **`vulkan_bridge.py`**: `VulkanBridge` interface connecting to the native Rust Vulkan rendering engine (`rust_vulkan_render`).
- **`menu.py`**: `MainMenuUI` for world parameters and generation options.
- **`camera.py`**: `Camera` viewport panning and zooming logic.

### 6. `src/modding/`
- **`manager.py`**: `LuaModManager` loading and executing Lua mod scripts in `mods/` using `lupa`.

### 7. `utils/`
Extensible utility tools including `tile_interaction_utility.py`, `p_np_math.py`, `vehicle_utility.py`, `ballistics_utility.py`, `food_spoilage_utility.py`, `electricity_utility.py`, `sound_utility.py`, `item_state_utility.py`, `mod_utility.py`, `dev_utility.py`, `memory_monitor_utility.py`, `plant_utility.py`, `animal_utility.py`, and `pathfinding_utility.py`.
