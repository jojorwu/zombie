import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.world import World, TileType
from src.entities import Survivor, Zombie, Vehicle, Animal, ItemEntity, ResourceItem, CraftingSystem

class TestEntities(unittest.TestCase):
    def test_entities_and_actions(self):
        world = World(width=30, height=30)
        # Ensure tiles around (5, 5) are walkable grass for tests
        world.grid[:, 5, 4:10] = TileType.GRASS
        survivor = Survivor(5.0, 5.0, z=0)
        zombie = Zombie(5.5, 5.0, z=0)
        vehicle = Vehicle(6.0, 5.0, z=0)
        animal = Animal(7.0, 5.0, z=0)
        food = ItemEntity(5.2, 5.2, ResourceItem.FOOD, 2, z=0)

        # Move survivor
        survivor.move(1, 0, world)
        self.assertGreater(survivor.x, 5.0)

        # Gather item
        survivor.perform_action(1, world, [food], [vehicle], [zombie], [animal], [survivor])
        self.assertTrue(food.collected)
        self.assertEqual(survivor.inventory[ResourceItem.FOOD], 4)

        # Zombie attacks survivor
        zombie.update(world, [survivor], [vehicle])
        self.assertLess(survivor.health, 100.0)

        # Crafting test
        survivor.inventory[ResourceItem.WOOD] = 2
        survivor.inventory[ResourceItem.METAL] = 2
        self.assertTrue(CraftingSystem.can_craft(survivor.inventory, ResourceItem.WEAPON))
        survivor.perform_action(3, world, [], [], [], [], [survivor])  # Craft weapon action
        self.assertEqual(survivor.inventory[ResourceItem.WEAPON], 1)

    def test_3d_height_levels_and_stairs(self):
        world = World(width=20, height=20, num_levels=3)
        survivor = Survivor(10.0, 10.0, z=0)
        self.assertEqual(survivor.z, 0)

        # Make tiles on level 0 and level 1 walkable stairs
        world.grid[0, 10, 10] = TileType.STAIRS
        world.grid[1, 10, 10] = TileType.STAIRS
        survivor.perform_action(7, world, [], [], [], [], [survivor])  # Action 7 = Stairs Up
        self.assertEqual(survivor.z, 1)

        survivor.perform_action(8, world, [], [], [], [], [survivor])  # Action 8 = Stairs Down
        self.assertEqual(survivor.z, 0)

if __name__ == "__main__":
    unittest.main()
