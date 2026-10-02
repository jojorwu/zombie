import sys
import os
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import torch
import numpy as np
from src.ai.brain_net import BrainNet, GeneticEvolutionManager, save_zbrain, load_zbrain, DEVICE
from src.ai.brain_actions import batch_get_action_and_movement, extract_survivor_inputs
from src.entities import Survivor
from src.world import World


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


if __name__ == "__main__":
    unittest.main()
