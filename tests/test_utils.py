import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.utils.p_np_math import PolynomialVerifier, PNPComplexityEngine
from src.utils.mod_utility import ModUtility
from src.utils.dev_utility import DevUtility
from src.utils.pathfinding_utility import PathfindingUtility
from src.utils.vehicle_utility import VehicleRegistry, VehicleType, VehiclePhysicsUtility
from src.utils.tile_interaction_utility import TileInteractionUtility
from src.ai.pathfinding import AStar3D
from src.world import World, TileType, ChunkManager

class TestUtilitiesAndMath(unittest.TestCase):
    def test_3d_astar_pathfinding(self):
        world = World(width=30, height=30, z_min=0, z_max=2)
        # Ensure path is clear
        world.grid[:, 5, 5:15] = TileType.GRASS
        astar = AStar3D(world)
        path = astar.find_path((5.0, 5.0, 0), (14.0, 5.0, 0))
        self.assertGreater(len(path), 0)

    def test_pathfinding_utility(self):
        util = PathfindingUtility(width=30, height=30)
        res = util.benchmark_pathfinding(num_runs=10)
        self.assertIn("avg_time_ms", res)

    def test_chunk_manager(self):
        cm = ChunkManager(world_width=60, world_height=40, chunk_size=16)
        chunk = cm.get_chunk_at(20, 20)
        self.assertIsNotNone(chunk)
        self.assertEqual(chunk.chunk_x, 1)
        self.assertEqual(chunk.chunk_y, 1)
    def test_p_np_verifier(self):
        clauses = [(1, 2, -3), (-1, 2, 3)]
        assignment = {1: True, 2: True, 3: False}
        self.assertTrue(PolynomialVerifier.verify_3sat(clauses, assignment))

        numbers = [3, 10, 4, 21, 7]
        target = 14
        certificate = [0, 4]  # 3 + 7 = 10 != 14
        self.assertFalse(PolynomialVerifier.verify_subset_sum(numbers, target, certificate))

        certificate_correct = [1, 2]  # 10 + 4 = 14
        self.assertTrue(PolynomialVerifier.verify_subset_sum(numbers, target, certificate_correct))

    def test_pnp_complexity_engine(self):
        engine = PNPComplexityEngine(degree=3)
        p_bound = engine.polynomial_bound(10)
        np_bound = engine.exponential_bound(10)
        self.assertEqual(p_bound, 1000.0)
        self.assertEqual(np_bound, 1024.0)

        analysis = engine.analyze_p_vs_np([5, 10])
        self.assertEqual(len(analysis), 2)

    def test_mod_utility(self):
        util = ModUtility(mods_dir="mods")
        valid_cnt = util.validate_all_mods()
        self.assertGreaterEqual(valid_cnt, 1)

    def test_dev_utility(self):
        dev = DevUtility()
        bench_res = dev.run_math_benchmarks()
        self.assertIn("matrix_time_ms", bench_res)
        self.assertIn("pnp_time_ms", bench_res)

    def test_vehicle_utility_and_gas_pumps(self):
        # Test custom vehicle model registration
        VehicleRegistry.register_vehicle_type(
            model_id="armored_truck",
            name="Armored SWAT Truck",
            speed=0.25,
            max_fuel=180.0,
            trunk_capacity=80,
            durability=300.0,
            noise_level=25.0
        )
        truck = VehicleRegistry.create_vehicle("armored_truck", 10.0, 10.0, z=0)
        self.assertEqual(truck.trunk_capacity, 80)
        self.assertEqual(truck.physics.mass, 1200.0)

        # Test trunk storage
        self.assertTrue(truck.store_in_trunk("food", 5))
        self.assertEqual(truck.trunk_inventory.get("food", 0), 5)
        taken = truck.take_from_trunk("food", 2)
        self.assertEqual(taken, 2)
        self.assertEqual(truck.trunk_inventory.get("food", 0), 3)

        # Test gas pump fuel siphoning
        world = World(width=20, height=20)
        z_idx = world.z_to_idx(0)
        world.grid[z_idx, 5, 5] = TileType.GAS_PUMP
        inventory = {}
        success, amount = TileInteractionUtility.siphon_fuel_from_pump(world, 5, 5, 0, inventory)
        self.assertTrue(success)
        self.assertEqual(inventory.get("fuel", 0), 2)

    def test_cdda_vehicle_parts_and_physics(self):
        v = VehicleRegistry.create_vehicle("sedan", 5.0, 5.0, z=0)
        self.assertIn("engine", v.parts)
        self.assertIn("bumper", v.parts)

        # Test engine operation check
        self.assertTrue(v.can_start_engine())

        # Test physics customization
        VehiclePhysicsUtility.customize_physics(v, mass=1500.0, max_speed=0.6)
        self.assertEqual(v.physics.mass, 1500.0)
        self.assertEqual(v.physics.max_speed, 0.6)

        # Test physics throttle acceleration
        v.update_physics(throttle=1.0, steer=0.0)
        self.assertGreater(v.physics.speed, 0.0)

        # Test high speed braking momentum
        v.physics.velocity_x = 0.4
        v.update_physics(brake=True)
        self.assertGreater(v.physics.speed, 0.0)  # Vehicle does not stop instantly at high speed

if __name__ == "__main__":
    unittest.main()
