import random
from src.entities.animal import Animal, Rat
from src.world.tiles import TileType


class AnimalUtility:
    """Utility module for creating, spawning, and managing wild animals and rats."""
    @staticmethod
    def spawn_rats(world, count=15):
        """Spawns rats near trash cans and inside building interiors without duplicate coordinate overlaps."""
        rats = []
        trash_coords = []
        building_coords = []

        g_idx = world.z_to_idx(0)
        for y in range(world.height):
            for x in range(world.width):
                tile = world.grid[g_idx, y, x]
                if tile == TileType.TRASH_CAN:
                    trash_coords.append((x, y))
                elif tile in (TileType.BUILDING_FLOOR, TileType.FLOOR_WOOD, TileType.FLOOR_TILE, TileType.FLOOR_CONCRETE, TileType.FLOOR_CARPET):
                    building_coords.append((x, y))

        spawn_pool = trash_coords + building_coords
        if not spawn_pool:
            return rats

        chosen_coords = random.sample(spawn_pool, min(count, len(spawn_pool)))
        for x, y in chosen_coords:
            rats.append(Rat(x + 0.5, y + 0.5, z=0))

        return rats

    @staticmethod
    def spawn_wildlife(world, count=10):
        """Spawns wild generic animals on walkable grass and forest tiles without duplicate coordinate overlaps."""
        animals = []
        g_idx = world.z_to_idx(0)
        walkable = []

        for y in range(world.height):
            for x in range(world.width):
                if world.grid[g_idx, y, x] in (TileType.GRASS, TileType.GRASS_DENSE, TileType.GRASS_DRY, TileType.FOREST_SPARSE, TileType.FOREST):
                    walkable.append((x, y))

        if not walkable:
            return animals

        chosen_coords = random.sample(walkable, min(count, len(walkable)))
        for x, y in chosen_coords:
            animals.append(Animal(x + 0.5, y + 0.5, z=0))

        return animals
