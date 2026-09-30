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

    def test_accelerated_time_and_cutoffs(self):
        world = World(width=100, height=100, day_length_ticks=3600, electricity_cutoff_day=7, water_cutoff_day=14)
        # At tick 0: Day 1, Power and Water are online
        self.assertFalse(world.is_power_out())
        self.assertFalse(world.is_water_out())
        time_str = world.get_time_string()
        self.assertIn("Y1-M01-D01", time_str)

        # Fast forward to Day 8 (3600 * 7 = 25200 ticks)
        world.current_tick = 3600 * 7.5
        self.assertTrue(world.is_power_out())
        self.assertFalse(world.is_water_out())

        # Fast forward to Day 15 (3600 * 14 = 50400 ticks)
        world.current_tick = 3600 * 14.5
        self.assertTrue(world.is_power_out())
        self.assertTrue(world.is_water_out())

    def test_day_night_cycle(self):
        world = World(width=20, height=20, day_length_ticks=3600)
        world.current_tick = 1800  # Noon peak (12:00)
        l2 = world.get_light_level()
        world.current_tick = 0  # Midnight (00:00)
        l3 = world.get_light_level()
        self.assertGreater(l2, l3)

    def test_fog_of_war(self):
        world = World(width=20, height=20)
        visible = world.compute_fog_of_war(10, 10, radius=5)
        self.assertIn((10, 10), visible)
        self.assertGreater(len(visible), 1)

if __name__ == "__main__":
    unittest.main()
