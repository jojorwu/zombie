# Architecture Overview

## Project Structure
- `src/world.py`: Core `World`, `ChunkManager`, tile properties, terrain speed modifiers, and city zoning generators.
- `src/brain.py`: `BrainNet` GRU-based PyTorch network, batched inference routines, and `GeneticEvolutionManager`.
- `src/entities.py`: Entities including `Survivor`, `Zombie`, `Animal`, `Vehicle`, `ItemEntity`, and noise acoustic propagation.
- `src/pathfinding.py`: 3D A* navigation supporting stairs, ladders, and surface terrain speed costs.
- `src/simulation.py`: `SimulationEngine` running the simulation loop, tick management, and generation resets.
- `src/ui.py`: Pygame user interface, main menu, settings, and camera viewports.
- `src/modding.py`: Lua modding engine powered by `lupa`.
