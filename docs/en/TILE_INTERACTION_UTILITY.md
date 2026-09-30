# Tile & Furniture Interaction Engine (`utils/tile_interaction_utility.py`)

## Overview
The tile interaction utility enables intelligent survivors and neural network brains to manipulate environmental furniture and barricade doorways.

## Actions & Interactions
1. **Push / Move Furniture (`Action 9`)**:
   - Pushes adjacent furniture (cabinets, tables, sofas, beds, refrigerators) 1 tile in the facing direction if the target tile is walkable.
   - Allows survivors to block open doorways or clear choked hallways.
2. **Dismantle Furniture (`Action 10`)**:
   - Dismantles furniture into reusable raw materials (wood and metal) using tools like axes or crowbars.
3. **Container Search (`Action 1`)**:
   - Searches adjacent refrigerators, cabinets, and kitchen counters for contextual loot.

## Utility API
- `TileInteractionUtility.push_furniture(world, x, y, z, push_dx, push_dy)`
- `TileInteractionUtility.dismantle_furniture(world, x, y, z, inventory)`
