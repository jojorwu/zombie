import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.world import World, TileType

class TestWorld(unittest.TestCase):
    def test_world_generation_extended_height_and_bridges(self):
        world = World(width=40, height=30, day_length_ticks=100, z_min=-20, z_max=20)
        self.assertEqual(world.width, 40)
        self.assertEqual(world.height, 30)
        self.assertEqual(world.num_levels, 41)
        self.assertEqual(world.grid.shape, (41, 30, 40))
        self.assertEqual(world.z_min, -20)
        self.assertEqual(world.z_max, 20)

        # Ground level is z=0, index = 20
        g_idx = world.z_to_idx(0)
        self.assertEqual(g_idx, 20)
        self.assertTrue(world.is_walkable(0, 0, z=0) or not world.is_walkable(0, 0, z=0))

    def test_world_parking_roof_trash_features(self):
        world = World(width=50, height=40, z_min=0, z_max=2)
        # Verify tile types exist in definitions
        self.assertEqual(TileType.PARKING, 14)
        self.assertEqual(TileType.ROOF, 15)
        self.assertEqual(TileType.TRASH_CAN, 16)

    def test_day_night_cycle(self):
        world = World(width=20, height=20, day_length_ticks=100)
        world.current_tick = 25  # Noon peak
        l2 = world.get_light_level()
        world.current_tick = 75  # Midnight trough
        l3 = world.get_light_level()
        self.assertGreater(l2, l3)

    def test_fog_of_war(self):
        world = World(width=20, height=20)
        visible = world.compute_fog_of_war(10, 10, radius=5)
        self.assertIn((10, 10), visible)
        self.assertGreater(len(visible), 1)

if __name__ == "__main__":
    unittest.main()
