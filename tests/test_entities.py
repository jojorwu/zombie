import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.world import World, TileType
from src.entities import Survivor, Zombie, Vehicle, Animal, ItemEntity, ResourceItem, CraftingSystem, NoiseEvent, ZombieState

class TestEntities(unittest.TestCase):
    def test_zombie_vision_and_hearing_ai(self):
        world = World(width=30, height=30, z_min=-20, z_max=20)
        world.current_tick = 1800  # Daylight (noon peak)
        # Clear obstacle at ground level for test
        g_idx = world.z_to_idx(0)
        world.grid[g_idx, 5, 5:20] = TileType.GRASS

        zombie = Zombie(5.0, 5.0, z=0)
        survivor = Survivor(10.0, 5.0, z=0)
        noise_events = [NoiseEvent(18.0, 5.0, 0, volume=20.0)]

        # Test line of sight vision
        self.assertTrue(zombie.has_line_of_sight(survivor.x, survivor.y, survivor.z, world))
        seen = zombie.check_vision(world, [survivor])
        self.assertIsNotNone(seen)

        # Test hearing
        heard = zombie.check_hearing(noise_events)
        self.assertIsNotNone(heard)

        # Update zombie AI
        zombie.update(world, [survivor], [], noise_events)
        self.assertEqual(zombie.state, ZombieState.CHASE)
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
        world = World(width=20, height=20, z_min=-20, z_max=20)
        survivor = Survivor(10.0, 10.0, z=0)
        self.assertEqual(survivor.z, 0)

        # Make tiles on level 0 and level 1 walkable stairs
        idx_0 = world.z_to_idx(0)
        idx_1 = world.z_to_idx(1)
        world.grid[idx_0, 10, 10] = TileType.STAIRS
        world.grid[idx_1, 10, 10] = TileType.STAIRS
        survivor.perform_action(7, world, [], [], [], [], [survivor])  # Action 7 = Stairs Up
        self.assertEqual(survivor.z, 1)

        survivor.perform_action(8, world, [], [], [], [], [survivor])  # Action 8 = Stairs Down
        self.assertEqual(survivor.z, 0)

    def test_firearms_ammo_and_scent_flocking(self):
        world = World(width=30, height=30)
        world.grid[:, 5, 4:20] = TileType.GRASS

        survivor = Survivor(5.0, 5.0, z=0)
        survivor.inventory[ResourceItem.PISTOL] = 1
        survivor.inventory[ResourceItem.PISTOL_AMMO] = 10

        zombie1 = Zombie(10.0, 5.0, z=0)
        zombie2 = Zombie(11.0, 5.0, z=0)
        noise_events = []

        # Survivor shoots pistol
        survivor.perform_action(6, world, [], [], [zombie1, zombie2], [], [survivor], noise_events=noise_events)

        # Verify ammo consumed and noise generated
        self.assertEqual(survivor.inventory[ResourceItem.PISTOL_AMMO], 9)
        self.assertGreater(len(noise_events), 0)
        self.assertLess(zombie1.hp, zombie1.max_hp)

        # Test flocking vector calculation
        flock_vec = zombie1.compute_flocking_vector([zombie1, zombie2])
        self.assertIsNotNone(flock_vec)

if __name__ == "__main__":
    unittest.main()
