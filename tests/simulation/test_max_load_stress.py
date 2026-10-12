import sys
import os
import time
import unittest
import json
import gc
import psutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.simulation import SimulationEngine, EventBus, NoiseEmittedEvent, DamageDealtEvent
from src.entities.state_manager import FurnitureStateManager, ItemStateManager, LazyChunkStatePersistence
from src.world import World, ChunkManager, TileType


class TestMaxLoadStress(unittest.TestCase):
    """
    High-Stress Benchmark Test for CPU and RAM utilization.
    Evaluates simulation performance under extreme load conditions (large map, 1000+ zombies, 50 survivors,
    vehicles, items, chunk transitions, and event bus flooding).
    """

    def setUp(self):
        gc.collect()
        self.process = psutil.Process(os.getpid())

    def get_mem_mb(self) -> float:
        return self.process.memory_info().rss / (1024 * 1024)

    def test_max_load_stress_simulation(self):
        print("\n" + "=" * 60)
        print("     STARTING MAX-LOAD CPU & RAM STRESS BENCHMARK TEST")
        print("=" * 60)

        initial_mem = self.get_mem_mb()
        print(f"[Benchmark] Initial RAM Usage: {initial_mem:.2f} MB")

        with open("config.json", "r") as f:
            config = json.load(f).copy()

        config["simulation"]["map_width"] = 200
        config["simulation"]["map_height"] = 200
        config["simulation"]["num_survivors"] = 50
        config["simulation"]["num_zombies"] = 1000
        config["simulation"]["num_vehicles"] = 15
        config["simulation"]["num_animals"] = 30

        start_time = time.time()
        sim = SimulationEngine(config)
        init_time = time.time() - start_time

        post_init_mem = self.get_mem_mb()
        print(f"[Benchmark] Engine Initialization Time: {init_time:.3f} s")
        print(f"[Benchmark] RAM After Initialization: {post_init_mem:.2f} MB (+{post_init_mem - initial_mem:.2f} MB)")

        # Verify entity counts
        self.assertEqual(len(sim.survivors), 50)
        self.assertEqual(len(sim.zombies), 1000)
        self.assertEqual(len(sim.vehicles), 15)

        # Flood event bus with events to test throughput
        for i in range(500):
            sim.event_bus.publish(NoiseEmittedEvent(x=float(i % 200), y=float(i % 200), z=0, volume=50.0, source_type="gunshot"))
            sim.event_bus.publish(DamageDealtEvent(damage=25.0))

        # Run 100 high-stress simulation ticks
        tick_start = time.time()
        num_ticks = 100

        peak_mem = post_init_mem

        for t in range(num_ticks):
            sim.tick()
            curr_mem = self.get_mem_mb()
            if curr_mem > peak_mem:
                peak_mem = curr_mem

            # Periodically move survivors around to force active chunk recalculations
            if t % 10 == 0:
                for survivor in sim.survivors:
                    survivor.x = (survivor.x + 15.0) % 200
                    survivor.y = (survivor.y + 15.0) % 200

        tick_duration = time.time() - tick_start
        tps = num_ticks / tick_duration

        print(f"[Benchmark] Executed {num_ticks} Ticks in {tick_duration:.3f} s ({tps:.2f} TPS)")
        print(f"[Benchmark] Peak RAM Usage: {peak_mem:.2f} MB (+{peak_mem - initial_mem:.2f} MB)")

        # Perform cleanup and garbage collection
        del sim
        gc.collect()

        final_mem = self.get_mem_mb()
        print(f"[Benchmark] RAM After Cleanup: {final_mem:.2f} MB (Retained Delta: {final_mem - initial_mem:+.2f} MB)")
        print("=" * 60 + "\n")

        # Assertions for reasonable performance thresholds
        self.assertGreater(tps, 5.0, f"TPS too low: {tps:.2f}")


if __name__ == "__main__":
    unittest.main()
