import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.world import World, TileType

class TestWorld(unittest.TestCase):
    def test_world_generation(self):
        world = World(width=40, height=30, day_length_ticks=100)
        self.assertEqual(world.width, 40)
        self.assertEqual(world.height, 30)
        self.assertEqual(world.grid.shape, (30, 40))

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
