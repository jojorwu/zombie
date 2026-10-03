# Tile & Furniture Interaction Engine (`utils/tile_interaction_utility.py`)

## Overview
The tile interaction utility enables intelligent survivors and neural network brains to manipulate environmental furniture, lockpick barricaded doors or safes, siphon vehicle fuel, and harvest natural resources.

## Actions & Interactions
1. **Push / Move Furniture (`push_furniture`)**:
   - Pushes adjacent furniture (cabinets, tables, sofas, beds, refrigerators, safes) 1 tile in the facing direction if the target tile is walkable floor/ground.
   - Allows survivors to block open doorways or clear choked hallways.
2. **Dismantle Furniture (`dismantle_furniture`)**:
   - Dismantles furniture into reusable raw materials (wood and metal) using tools like axes or crowbars into inventory.
3. **Lockpick Doors & Weapon Safes (`lockpick_door_or_safe`)**:
   - Allows survivors with a lockpick or crowbar to open locked doors (`TileType.DOOR_LOCKED` -> `DOOR_OPEN`) or crack weapon safes (`TileType.WEAPON_SAFE`) to extract money and jewelry.
4. **Harvest Bush Sticks (`harvest_bush_sticks`)**:
   - Harvests sticks/branches from forest bushes (`TileType.BUSH`), placing sticks into inventory and leaving grass tiles.
5. **Siphon Gas Station Fuel (`siphon_fuel_from_pump`)**:
   - Siphons fuel canisters directly from gas station pumps (`TileType.GAS_PUMP`) into survivor inventory.

## Utility API Reference
- `TileInteractionUtility.is_movable_furniture(tile_type)`
- `TileInteractionUtility.get_adjacent_furniture(world, x, y, z)`
- `TileInteractionUtility.push_furniture(world, x, y, z, push_dx, push_dy)`
- `TileInteractionUtility.dismantle_furniture(world, x, y, z, inventory)`
- `TileInteractionUtility.lockpick_door_or_safe(world, x, y, z, inventory)`
- `TileInteractionUtility.harvest_bush_sticks(world, x, y, z, inventory)`
- `TileInteractionUtility.siphon_fuel_from_pump(world, x, y, z, inventory)`
