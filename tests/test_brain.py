import sys
import os
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import torch
import numpy as np
from src.ai.brain_net import BrainNet, GeneticEvolutionManager, save_zbrain, load_zbrain, DEVICE
from src.ai.brain_actions import batch_get_action_and_movement, extract_survivor_inputs, check_line_of_sight
from src.ai.hierarchical_ai import HierarchicalDecisionPlanner, HighLevelGoal
from src.entities import Survivor
from src.entities.zombie import Zombie
from src.world import World, TileType


class TestBrain(unittest.TestCase):
    def test_brain_net_forward_and_action(self):
        brain = BrainNet(input_size=57, hidden_size=64, output_size=13)
        inputs = np.random.randn(57).astype(np.float32)
        hidden = brain.init_hidden()

        dx, dy, action_idx, new_hidden = brain.get_action_and_movement(inputs, hidden)

        self.assertIsInstance(dx, float)
        self.assertIsInstance(dy, float)
        self.assertIsInstance(action_idx, int)
        self.assertGreaterEqual(action_idx, 0)
        self.assertLess(action_idx, 11)
        self.assertEqual(new_hidden.shape, (1, 64))

    def test_zbrain_compression_save_load(self):
        brain1 = BrainNet(input_size=57, hidden_size=64, output_size=13)
        brain2 = BrainNet(input_size=57, hidden_size=64, output_size=13)

        with tempfile.NamedTemporaryFile(suffix=".zbrain", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            save_zbrain(brain1, tmp_path)
            self.assertTrue(os.path.exists(tmp_path))
            self.assertGreater(os.path.getsize(tmp_path), 0)

            load_zbrain(brain2, tmp_path)

            for p1, p2 in zip(brain1.parameters(), brain2.parameters()):
                self.assertTrue(torch.allclose(p1.cpu(), p2.cpu(), atol=1e-2))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_batch_get_action_and_movement(self):
        brains = [BrainNet(input_size=57, hidden_size=64, output_size=13) for _ in range(4)]
        inputs_list = [np.random.randn(57).astype(np.float32) for _ in range(4)]
        hiddens = [b.init_hidden() for b in brains]

        outputs = batch_get_action_and_movement(brains, inputs_list, hiddens)
        self.assertEqual(len(outputs), 4)
        for dx, dy, act, h in outputs:
            self.assertIsInstance(dx, float)
            self.assertIsInstance(dy, float)
            self.assertIsInstance(act, int)
            self.assertEqual(h.shape, (1, 64))

    def test_survivor_extract_inputs_57(self):
        world = World(width=30, height=30)
        survivor = Survivor(10.0, 10.0)
        inputs = extract_survivor_inputs(survivor, world, items=[], vehicles=[], zombies=[], animals=[])
        self.assertEqual(inputs.shape, (57,))

    def test_hierarchical_decision_planner(self):
        planner = HierarchicalDecisionPlanner(goal_eval_interval=10)
        world = World(width=30, height=30)
        survivor = Survivor(10.0, 10.0)

        goal = planner.evaluate_goal(survivor, world, items=[], vehicles=[], zombies=[], animals=[])
        self.assertIsInstance(goal, HighLevelGoal)

        dx, dy, action = planner.execute_low_level_behaviour(
            survivor, world, items=[], vehicles=[], zombies=[], animals=[], raw_dx=0.5, raw_dy=0.0, raw_action=0
        )
        self.assertIsInstance(dx, float)
        self.assertIsInstance(dy, float)
        self.assertIsInstance(action, int)

    def test_check_line_of_sight_and_spatial_memory(self):
        world = World(width=30, height=30)
        survivor = Survivor(10.0, 10.0)
        zombie = Zombie(15.0, 10.0)

        # Direct LOS clear path
        self.assertTrue(check_line_of_sight(world, survivor.x, survivor.y, zombie.x, zombie.y, 0))

        # Place wall between survivor and zombie
        z_idx = world.z_to_idx(0)
        world.grid[z_idx, 10, 12] = TileType.WALL_BRICK.value
        self.assertFalse(check_line_of_sight(world, survivor.x, survivor.y, zombie.x, zombie.y, 0))

        # Verify extract_survivor_inputs uses spatial memory when blocked
        survivor.spatial_memory["zombie"] = (15.0, 10.0, 0, world.current_tick)
        inputs = extract_survivor_inputs(survivor, world, items=[], vehicles=[], zombies=[zombie], animals=[])
        self.assertNotEqual(inputs[8], 0.0)  # Should use remembered dx


if __name__ == "__main__":
    unittest.main()
