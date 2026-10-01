import random
from src.world import TileType
from src.entities.item import ResourceItem


class PlantStage:
    SEED = "seed"
    SPROUT = "sprout"
    MATURE = "mature"


class PlantEntity:
    """Represents a growing or wild plant entity (mushrooms, berries, herbs)."""
    def __init__(self, x: float, y: float, plant_type: str = ResourceItem.BERRIES, z: int = 0):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.plant_type = plant_type
        self.growth_stage = PlantStage.MATURE if random.random() < 0.6 else PlantStage.SPROUT
        self.growth_ticks = 0
        self.harvested = False

    def update(self):
        if self.harvested or self.growth_stage == PlantStage.MATURE:
            return
        self.growth_ticks += 1
        if self.growth_ticks > 150 and self.growth_stage == PlantStage.SEED:
            self.growth_stage = PlantStage.SPROUT
        elif self.growth_ticks > 300 and self.growth_stage == PlantStage.SPROUT:
            self.growth_stage = PlantStage.MATURE

    def harvest(self):
        if not self.harvested and self.growth_stage == PlantStage.MATURE:
            self.harvested = True
            return self.plant_type, random.randint(1, 3)
        return None, 0


class PlantUtility:
    """Utility module for configuring, spawning, and managing wild forest plants and herbs."""
    @staticmethod
    def spawn_wild_plants(world, plant_density: float = 0.05):
        """Spawns wild mushrooms and berries across dense/sparse forest tiles."""
        plants = []
        g_idx = world.z_to_idx(0)
        forest_tiles = (TileType.FOREST, TileType.FOREST_DENSE, TileType.FOREST_SPARSE)

        for y in range(world.height):
            for x in range(world.width):
                if world.grid[g_idx, y, x] in forest_tiles:
                    if random.random() < plant_density:
                        ptype = ResourceItem.MUSHROOM if random.random() < 0.5 else ResourceItem.BERRIES
                        plants.append(PlantEntity(x + 0.5, y + 0.5, plant_type=ptype, z=0))
        return plants

    @staticmethod
    def harvest_adjacent_plants(survivor, plants):
        """Allows survivor to harvest nearby mature plants into inventory."""
        for plant in plants:
            if not plant.harvested and plant.z == survivor.z:
                dist = abs(plant.x - survivor.x) + abs(plant.y - survivor.y)
                if dist < 1.2:
                    ptype, amt = plant.harvest()
                    if ptype:
                        survivor.inventory[ptype] = survivor.inventory.get(ptype, 0) + amt
                        survivor.score += 3.0
