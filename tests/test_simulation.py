import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import json
from src.simulation import SimulationEngine, EventBus, GameEvent, NoiseEmittedEvent, DamageDealtEvent, DoubleBufferedStateExchanger
from src.entities.state_manager import LazyChunkStatePersistence
from src.ai.pathfinding import AStar3D
from src.world import World


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

    def test_async_fixed_timestep_loop(self):
        with open("config.json", "r") as f:
            config = json.load(f).copy()
        config["simulation"]["map_width"] = 30
        config["simulation"]["map_height"] = 30

        sim = SimulationEngine(config)
        sim.run_fixed_timestep_loop(target_tps=120, max_ticks=10)
        self.assertEqual(sim.world.current_tick, 10)

    def test_astar_3d_pathfinding(self):
        world = World(width=30, height=30)
        pathfinder = AStar3D(world)

        path = pathfinder.find_path((5.0, 5.0, 0), (10.0, 5.0, 0))
        self.assertIsInstance(path, list)

    def test_chunk_entity_freezing(self):
        with open("config.json", "r") as f:
            config = json.load(f).copy()
        config["simulation"]["map_width"] = 100
        config["simulation"]["map_height"] = 100

        sim = SimulationEngine(config)
        for s in sim.survivors:
            s.x, s.y = 10.0, 10.0
        sim.zombies[0].x, sim.zombies[0].y = 12.0, 10.0
        sim.zombies[1].x, sim.zombies[1].y = 90.0, 90.0

        z2_initial_pos = (sim.zombies[1].x, sim.zombies[1].y)

        for _ in range(10):
            sim.tick()

        self.assertEqual((sim.zombies[1].x, sim.zombies[1].y), z2_initial_pos)

    def test_street_corpse_spawning_and_ballistics(self):
        with open("config.json", "r") as f:
            config = json.load(f).copy()
        sim = SimulationEngine(config)

        corpses = [i for i in sim.items if i.contents]
        self.assertGreater(len(corpses), 0)

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

    def test_event_bus_publishing_and_handling(self):
        bus = EventBus()
        received_events = []

        def noise_handler(event):
            received_events.append(event)

        bus.subscribe(NoiseEmittedEvent, noise_handler)
        event = NoiseEmittedEvent(x=10.0, y=10.0, z=0, volume=20.0, source_type="gunshot")
        bus.publish(event)
        self.assertEqual(len(received_events), 0)

        bus.process_events()
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].volume, 20.0)

    def test_double_buffered_snapshot(self):
        with open("config.json", "r") as f:
            config = json.load(f).copy()
        config["simulation"]["map_width"] = 30
        config["simulation"]["map_height"] = 30
        sim = SimulationEngine(config)

        exchanger = DoubleBufferedStateExchanger()
        exchanger.capture_snapshot(sim.world, sim.survivors, sim.zombies, sim.vehicles, sim.items)

        snapshot = exchanger.get_render_snapshot()
        self.assertEqual(len(snapshot.survivors), len(sim.survivors))

    def test_lazy_chunk_state_persistence(self):
        persistence = LazyChunkStatePersistence()
        self.assertFalse(persistence.is_inflated(0, 0))

        persistence.log_delta_change(0, 0, "furniture_damage", {"x": 5, "y": 5, "durability": 50.0})
        deltas = persistence.inflate_chunk_states(0, 0)

        self.assertTrue(persistence.is_inflated(0, 0))
        self.assertEqual(len(deltas), 1)
        self.assertEqual(deltas[0]["data"]["durability"], 50.0)


if __name__ == "__main__":
    unittest.main()
