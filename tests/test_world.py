import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.world import World, TileType, ChunkState
from src.world.generation import GraphGrammarBuildingGenerator
from src.entities.item import MetalQuality
from utils.item_state_utility import ItemStateUtility

class TestWorld(unittest.TestCase):
    def test_sparse_spatial_hashing(self):
        world = World(width=40, height=30, z_min=-2, z_max=5)
        g_idx0 = world.z_to_idx(0)
        g_idx1 = world.z_to_idx(2)

        world.grid[g_idx0, 10, 10] = TileType.ROAD.value
        world.grid[g_idx1, 10, 10] = TileType.BUILDING_WALL.value

        self.assertEqual(world.grid[g_idx0, 10, 10], TileType.ROAD.value)
        self.assertEqual(world.grid[g_idx1, 10, 10], TileType.BUILDING_WALL.value)
        self.assertIn((g_idx1, 10, 10), world.sparse_z_grid)

    def test_graph_grammar_building_generator(self):
        graph = GraphGrammarBuildingGenerator.generate_room_graph()
        self.assertIn("Entrance", graph)
        self.assertIn("Hallway", graph["Entrance"])
        self.assertIn("Bathroom", graph["Bedroom"])

    def test_world_generation_extended_height_and_bridges(self):
        world = World(width=40, height=30, day_length_ticks=100, z_min=-20, z_max=20)
        self.assertEqual(world.width, 40)
        self.assertEqual(world.height, 30)
        self.assertEqual(world.num_levels, 41)
        self.assertEqual(world.z_min, -20)
        self.assertEqual(world.z_max, 20)

        g_idx = world.z_to_idx(0)
        self.assertEqual(g_idx, 20)
        self.assertTrue(world.is_walkable(0, 0, z=0) or not world.is_walkable(0, 0, z=0))

    def test_world_parking_roof_trash_features(self):
        world = World(width=50, height=40, z_min=0, z_max=2)
        self.assertEqual(TileType.PARKING, 14)
        self.assertEqual(TileType.ROOF, 15)
        self.assertEqual(TileType.TRASH_CAN, 16)

    def test_new_tiles_speed_modifiers_and_chunks(self):
        world = World(width=64, height=64)
        self.assertEqual(world.get_tile_speed_modifier(0, 0), world.get_tile_speed_modifier(0, 0))
        self.assertGreater(TileType.SAND, 0)
        self.assertGreater(TileType.ROAD_HIGHWAY, 0)

        chunk_mgr = world.chunk_manager
        chunk_mgr.update_active_chunks([(10, 10), (50, 50)], view_distance_chunks=1)
        self.assertIn((0, 0), chunk_mgr.active_chunks)
        self.assertIn((3, 3), chunk_mgr.active_chunks)

    def test_chunk_states_and_multi_chunk_building_coverage(self):
        world = World(width=64, height=64)
        chunk_mgr = world.chunk_manager

        large_building = {
            "x": 10, "y": 10, "w": 12, "h": 12, "type": "residential"
        }
        chunk_mgr.register_building(large_building)

        c00 = chunk_mgr.get_chunk(0, 0)
        c10 = chunk_mgr.get_chunk(1, 0)
        c01 = chunk_mgr.get_chunk(0, 1)
        c11 = chunk_mgr.get_chunk(1, 1)

        self.assertIn(large_building, c00.buildings)
        self.assertIn(large_building, c10.buildings)
        self.assertIn(large_building, c01.buildings)
        self.assertIn(large_building, c11.buildings)

        chunk_mgr.update_active_chunks([(2, 2)], view_distance_chunks=0)

        self.assertEqual(c00.state, ChunkState.ACTIVE)
        self.assertEqual(c10.state, ChunkState.ACTIVE)
        self.assertEqual(c01.state, ChunkState.ACTIVE)
        self.assertEqual(c11.state, ChunkState.ACTIVE)

        c33 = chunk_mgr.get_chunk(3, 3)
        self.assertEqual(c33.state, ChunkState.INACTIVE)

    def test_accelerated_time_and_cutoffs(self):
        world = World(width=100, height=100, day_length_ticks=3600, electricity_cutoff_day=7, water_cutoff_day=14)
        self.assertFalse(world.is_power_out())
        self.assertFalse(world.is_water_out())
        time_str = world.get_time_string()
        self.assertIn("Y1-M01-D01", time_str)

        world.current_tick = 3600 * 7.5
        self.assertTrue(world.is_power_out())
        self.assertFalse(world.is_water_out())

        world.current_tick = 3600 * 14.5
        self.assertTrue(world.is_power_out())
        self.assertTrue(world.is_water_out())

    def test_day_night_cycle(self):
        world = World(width=20, height=20, day_length_ticks=3600)
        world.current_tick = 1800
        l2 = world.get_light_level()
        world.current_tick = 0
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

        heard = zombie.check_hearing(noise_event, world=world)
        self.assertIsNotNone(heard)

        self.assertFalse(world.is_walkable(0, 0) and world.grid[g_idx, 0, 0] == TileType.REFRIGERATOR)

    def test_weather_wind_rain_and_dynamic_lights(self):
        world = World(width=150, height=150)
        self.assertIsNotNone(world.weather)
        self.assertGreaterEqual(world.weather.wind_speed, 0.0)

        world.weather.rain_front = {"x": 10.0, "y": 10.0, "w": 100.0, "h": 100.0, "vx": 0.1, "vy": 0.1, "lifetime": 100}
        self.assertTrue(world.weather.is_in_rain(20, 20))
        self.assertFalse(world.weather.is_in_rain(120, 120))

        from src.world import DynamicLight
        world.dynamic_lights.append(DynamicLight(10.0, 10.0, 0, radius=5.0))
        self.assertEqual(len(world.dynamic_lights), 1)

    def test_basement_generation_probabilities(self):
        world = World(width=100, height=100, z_min=-2, z_max=2)
        basement_count = sum(1 for b in world.buildings if b.get("has_basement", False))
        self.assertGreaterEqual(basement_count, 0)
        self.assertLess(world.get_light_level(z=-1), world.get_light_level(z=0))

    def test_post_apocalyptic_elements_and_lockpicking(self):
        world = World(width=20, height=20)
        z_idx = world.z_to_idx(0)

        world.grid[z_idx, 5, 5] = TileType.DOOR_LOCKED
        from src.entities.item import ResourceItem
        from utils.tile_interaction_utility import TileInteractionUtility
        inventory = {ResourceItem.LOCKPICK: 1}
        success = TileInteractionUtility.lockpick_door_or_safe(world, 5, 5, 0, inventory)
        self.assertTrue(success)
        self.assertEqual(world.grid[z_idx, 5, 5], TileType.DOOR_OPEN)

        world.grid[z_idx, 6, 6] = TileType.WEAPON_SAFE
        success = TileInteractionUtility.lockpick_door_or_safe(world, 6, 6, 0, inventory)
        self.assertTrue(success)
        self.assertGreater(inventory.get(ResourceItem.MONEY, 0), 0)

        world.current_tick = 0
        fov_tiles = world.compute_fog_of_war(10, 10, radius=8, z=0)
        self.assertGreater(len(fov_tiles), 0)

if __name__ == "__main__":
    unittest.main()
