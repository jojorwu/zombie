import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.world import World
from src.entities import Survivor, Zombie, Vehicle, Animal, ItemEntity, ResourceItem, CraftingSystem

class TestEntities(unittest.TestCase):
    def test_entities_and_actions(self):
        world = World(width=30, height=30)
        survivor = Survivor(5.0, 5.0)
        zombie = Zombie(5.5, 5.0)
        vehicle = Vehicle(6.0, 5.0)
        animal = Animal(7.0, 5.0)
        food = ItemEntity(5.2, 5.2, ResourceItem.FOOD, 2)

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

if __name__ == "__main__":
    unittest.main()
