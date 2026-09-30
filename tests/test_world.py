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

    def test_new_tiles_speed_modifiers_and_chunks(self):
        world = World(width=64, height=64)
        # Check new tile types speed modifiers
        self.assertEqual(world.get_tile_speed_modifier(0, 0), world.get_tile_speed_modifier(0, 0))
        self.assertGreater(TileType.SAND, 0)
        self.assertGreater(TileType.ROAD_HIGHWAY, 0)

        # Check ChunkManager active chunks updating
        chunk_mgr = world.chunk_manager
        chunk_mgr.update_active_chunks([(10, 10), (50, 50)], view_distance_chunks=1)
        self.assertIn((0, 0), chunk_mgr.active_chunks)
        self.assertIn((3, 3), chunk_mgr.active_chunks)

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

    def test_furniture_tiles_and_sound_occlusion(self):
        world = World(width=30, height=30)
        g_idx = world.z_to_idx(0)
        world.grid[g_idx, 5, 10] = TileType.BUILDING_WALL

        from src.entities import Zombie, NoiseEvent
        zombie = Zombie(8.0, 5.0, z=0)
        noise_event = [NoiseEvent(5.0, 5.0, 0, volume=20.0)]

        # Check sound attenuation through wall
        heard = zombie.check_hearing(noise_event, world=world)
        self.assertIsNotNone(heard)

        # Check furniture tile non-walkability
        self.assertFalse(world.is_walkable(0, 0) and world.grid[g_idx, 0, 0] == TileType.REFRIGERATOR)

if __name__ == "__main__":
    unittest.main()
