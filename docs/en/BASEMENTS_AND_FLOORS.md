# Multi-Floor & Basement Generation

## Underground Basements ($Z < 0$)
Building generators evaluate exact basement spawning probabilities:
- **Residential Buildings & Police Stations**: **20%** chance of basement.
- **Warehouses & Gun Stores**: **40%** chance of basement.
- **Other Structures**: **0%** chance.

Basements feature:
- Pitch-black illumination (0% natural sunlight).
- Stair/ladder hatch connections to Ground Floor ($Z=0$).
- Specialized rare basement loot (ammo crates, rifles, fuel canisters, canned food).

## Upper Floors ($Z > 0$)
Large civic and commercial buildings (hospitals, schools, dormitories) feature multi-story upper floors up to $Z=2..5$ topped with roofs (`TileType.ROOF`).
