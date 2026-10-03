# City & World Generation

## World Grid & District Zoning
The map generator creates 1000x1000 procedural worlds divided into distinct urban districts:
1. **Commercial / City Center**: Multi-story commercial complexes, supermarkets, gun stores, hospitals, and police stations surrounded by asphalt roads, crosswalks, and sidewalks.
2. **Residential District**: Single-family houses, apartments, dormitories, and schools with yards, mailboxes, trash cans, and residential streets.
3. **Industrial & Storage District**: Warehouses, garages, parking lots, gas stations, and auto repair shops (`BuildingType.AUTO_REPAIR_SHOP`).
4. **Parks & Forest District**: Dense/sparse forests, bushes, dead trees, grass, sand, and winding rivers crossed by bridges.

## Building Generation, BSP Partitions & Municipal Cutoffs
- **BSP Interior Partitions**: Buildings are procedurally partitioned into rooms using Binary Space Partitioning (BSP) with internal wooden doors (`TileType.DOOR_CLOSED`), furniture layouts, and light switches.
- **Security & Lockpicking**: Key commercial structures contain locked doors (`TileType.DOOR_LOCKED`) and weapon safes (`TileType.WEAPON_SAFE`).
- **Post-Apocalyptic Road Barricades**: Roadways feature sandbags (`TileType.SANDBAG`), barbed wire (`TileType.BARBED_WIRE`), and abandoned vehicles.
- **Municipal Service Cutoffs**: Municipal electricity and water supplies shut down after configurable cutoff days (default day 7 in `config.json`).

## Tile Movement Speed Modifiers (`TILE_SPEED_MODIFIERS`)
- **Highways & Asphalt Roads**: 1.2x movement speed multiplier.
- **Dirt Roads & Sidewalks**: 1.0x standard speed multiplier.
- **Dense Grass & Sand**: 0.75x - 0.85x reduced speed multiplier.
- **Dense Forest & Bushes**: 0.5x reduced speed multiplier and vision obstruction.
