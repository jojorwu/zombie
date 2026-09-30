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
