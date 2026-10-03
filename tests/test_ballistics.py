import unittest
from src.world import World, TileType
from utils.ballistics_utility import BallisticsUtility, MaterialResistance


class DummyTarget:
    def __init__(self, x, y, z=0, hp=100.0):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.hp = float(hp)
        self.is_alive = True

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.is_alive = False


class TestBallisticsUtility(unittest.TestCase):
    def setUp(self):
        self.world = World(width=30, height=30, z_min=0, z_max=2)
        # Clear test corridor to GRASS
        z_idx = self.world.z_to_idx(0)
        for x in range(30):
            self.world.grid[z_idx, 5, x] = TileType.GRASS

    def test_trajectory_calculation(self):
        traj = BallisticsUtility.calculate_trajectory("5.56mm", distance_m=50.0, wind_speed_kmh=10.0, wind_angle_rad=1.57)
        self.assertIn("terminal_velocity_ms", traj)
        self.assertIn("kinetic_energy_j", traj)
        self.assertGreater(traj["kinetic_energy_j"], 500.0)

    def test_window_shattering(self):
        # Place window at (10, 5, 0)
        z_idx = self.world.z_to_idx(0)
        self.world.grid[z_idx, 5, 10] = TileType.WINDOW

        # Shoot bullet from (5.0, 5.0, 0) towards (10, 5) at angle 0.0 (east)
        sim_res = BallisticsUtility.simulate_bullet_flight(
            self.world,
            start_x=5.0,
            start_y=5.0,
            start_z=0,
            angle_rad=0.0,
            caliber="5.56mm"
        )

        self.assertIn((10, 5, 0), sim_res["shattered_windows"])
        self.assertEqual(self.world.grid[z_idx, 5, 10], TileType.WINDOW_BROKEN)

    def test_wall_penetration(self):
        z_idx = self.world.z_to_idx(0)
        # Wooden door at (8, 5) -> 160 J resistance
        self.world.grid[z_idx, 5, 8] = TileType.DOOR

        # 5.56mm (~1700 J) should overpenetrate wooden door
        sim_res = BallisticsUtility.simulate_bullet_flight(
            self.world,
            start_x=5.0,
            start_y=5.0,
            start_z=0,
            angle_rad=0.0,
            caliber="5.56mm"
        )

        self.assertGreater(sim_res["traversed_distance_m"], 4.0)

    def test_multi_target_hits(self):
        t1 = DummyTarget(x=7.0, y=5.0, z=0)
        t2 = DummyTarget(x=9.0, y=5.0, z=0)

        sim_res = BallisticsUtility.simulate_bullet_flight(
            self.world,
            start_x=5.0,
            start_y=5.0,
            start_z=0,
            angle_rad=0.0,
            caliber="5.56mm",
            targets=[t1, t2]
        )

        self.assertEqual(len(sim_res["hits"]), 2)
        self.assertLess(t1.hp, 100.0)
        self.assertLess(t2.hp, 100.0)


if __name__ == "__main__":
    unittest.main()
