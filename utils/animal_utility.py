import random
from src.entities.animal import Animal, Rat
from src.world import TileType


class AnimalUtility:
    """Utility module for creating, spawning, and managing wild animals and rats."""
    @staticmethod
    def spawn_rats(world, count=15):
        """Spawns rats near trash cans and inside building interiors."""
        rats = []
        trash_coords = []
        building_coords = []

        g_idx = world.z_to_idx(0)
        for y in range(world.height):
            for x in range(world.width):
                tile = world.grid[g_idx, y, x]
                if tile == TileType.TRASH_CAN:
                    trash_coords.append((x, y))
                elif tile == TileType.BUILDING_FLOOR:
                    building_coords.append((x, y))

        spawn_pool = trash_coords + building_coords
        if not spawn_pool:
            return rats

        for _ in range(min(count, len(spawn_pool))):
            x, y = random.choice(spawn_pool)
            rats.append(Rat(x + 0.5, y + 0.5, z=0))

        return rats

    @staticmethod
    def spawn_wildlife(world, count=10):
        """Spawns wild generic animals on walkable grass and forest tiles."""
        animals = []
        g_idx = world.z_to_idx(0)
        walkable = []

        for y in range(world.height):
            for x in range(world.width):
                if world.grid[g_idx, y, x] in (TileType.GRASS, TileType.FOREST_SPARSE):
                    walkable.append((x, y))

        if not walkable:
            return animals

        for _ in range(min(count, len(walkable))):
            x, y = random.choice(walkable)
            animals.append(Animal(x + 0.5, y + 0.5, z=0))

        return animals
