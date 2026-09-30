import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.world import World
from src.entities import Survivor
from src.brain import BrainNet, extract_survivor_inputs, GeneticEvolutionManager

class TestBrain(unittest.TestCase):
    def test_brain_forward(self):
        brain = BrainNet()
        survivor = Survivor(5, 5)
        world = World(20, 20)
        inputs = extract_survivor_inputs(survivor, world, [], [], [], [])
        self.assertEqual(len(inputs), 18)

        dx, dy, action = brain.get_action_and_movement(inputs)
        self.assertTrue(-1.0 <= dx <= 1.0)
        self.assertTrue(-1.0 <= dy <= 1.0)
        self.assertTrue(0 <= action <= 6)

    def test_genetic_evolution(self):
        evo = GeneticEvolutionManager(population_size=10)
        brains = evo.create_initial_brains()
        self.assertEqual(len(brains), 10)

        brains_and_fitness = [(b, i * 10.0) for i, b in enumerate(brains)]
        new_brains, best_fit = evo.evolve_population(brains_and_fitness)
        self.assertEqual(len(new_brains), 10)
        self.assertEqual(evo.generation, 2)
        self.assertEqual(best_fit, 90.0)

        evo.save_best_brain(brains[0], "test_brain.pth")
        self.assertTrue(os.path.exists("test_brain.pth"))
        evo.load_best_brain(brains[1], "test_brain.pth")
        os.remove("test_brain.pth")

if __name__ == "__main__":
    unittest.main()
