# Multi-Floor & Basement Generation

## Underground Basements ($Z < 0$)
Building generators evaluate exact basement spawning probabilities based on building classification:
- **Residential Buildings, Apartments, Dormitories, Police Stations & Schools**: **35%** chance of basement generation.
- **Warehouses, Gun Stores & Auto Repair Shops**: **50%** chance of basement generation.
- **Other Structures**: **0%** chance.

Basement Features:
- Pitch-black unlit illumination (0% natural sunlight).
- Vertical connections to Ground Floor ($Z=0$) via stairs (`TileType.STAIRS`), ladder hatches (`TileType.LADDER`), or floor trapdoors (`TileType.TRAPDOOR`).
- High-tier rare basement loot: ammo crates, firearms, swords, fuel canisters, tools, and MREs.

## Upper Floors ($Z > 0$)
Large civic, commercial, and residential structures feature multi-story upper floors extending vertically up to $Z=5$ topped with roofs (`TileType.ROOF`).
- Navigation across vertical Z-levels uses 3D A* pathfinding (`AStar3D`) supporting staircases and ladder shafts.
