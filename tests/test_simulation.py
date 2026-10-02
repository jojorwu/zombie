import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import json
from src.simulation import SimulationEngine

class TestSimulation(unittest.TestCase):
    def test_simulation_integration(self):
        with open("config.json", "r") as f:
            config = json.load(f).copy()
        config["simulation"]["map_width"] = 30
        config["simulation"]["map_height"] = 30

        sim = SimulationEngine(config)
        self.assertEqual(len(sim.survivors), config["simulation"]["num_survivors"])
        self.assertEqual(len(sim.zombies), config["simulation"]["num_zombies"])
        self.assertEqual(len(sim.vehicles), config["simulation"]["num_vehicles"])
        self.assertEqual(len(sim.animals), config["simulation"]["num_animals"])
        self.assertGreater(len(sim.items), 0)

        # Run 50 ticks
        for _ in range(50):
            sim.tick()

        self.assertEqual(sim.world.current_tick, 50)

    def test_chunk_entity_freezing(self):
        with open("config.json", "r") as f:
            config = json.load(f).copy()
        config["simulation"]["map_width"] = 100
        config["simulation"]["map_height"] = 100

        sim = SimulationEngine(config)
        # Place all survivors at (10, 10) so only nearby chunks are active
        for s in sim.survivors:
            s.x, s.y = 10.0, 10.0
        # Place zombie 1 in active chunk (near survivor) and zombie 2 far away in inactive chunk (90, 90)
        sim.zombies[0].x, sim.zombies[0].y = 12.0, 10.0
        sim.zombies[1].x, sim.zombies[1].y = 90.0, 90.0

        z1_initial_pos = (sim.zombies[0].x, sim.zombies[0].y)
        z2_initial_pos = (sim.zombies[1].x, sim.zombies[1].y)

        # Run 10 ticks
        for _ in range(10):
            sim.tick()

        # Far zombie position remains unchanged (frozen in inactive chunk)
        self.assertEqual((sim.zombies[1].x, sim.zombies[1].y), z2_initial_pos)

    def test_street_corpse_spawning_and_ballistics(self):
        with open("config.json", "r") as f:
            config = json.load(f).copy()
        sim = SimulationEngine(config)

        # Verify street corpses are spawned in items
        corpses = [i for i in sim.items if i.contents]
        self.assertGreater(len(corpses), 0)

        # Test Ballistics Utility Bullet Drop
        from utils.ballistics_utility import BallisticsUtility
        traj = BallisticsUtility.calculate_trajectory("5.56mm", distance_m=100.0)
        self.assertIn("bullet_drop_m", traj)
        self.assertGreater(traj["bullet_drop_m"], 0.0)

    def test_generation_reset_and_evolution(self):
        with open("config.json", "r") as f:
            config = json.load(f)

        sim = SimulationEngine(config)
        initial_gen = sim.evolution_manager.generation
        sim.end_generation()
        self.assertEqual(sim.evolution_manager.generation, initial_gen + 1)
        self.assertEqual(len(sim.survivors), config["simulation"]["num_survivors"])

if __name__ == "__main__":
    unittest.main()
