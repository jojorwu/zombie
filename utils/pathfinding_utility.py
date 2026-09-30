#!/usr/bin/env python3
"""
Utility 4: Pathfinding & Navigation Utility for 3D A* Shortest Paths.
Benchmarking, route validation, and navigation testing tool.
Usage: python -m utils.pathfinding_utility
"""

import sys
import os
import time
from src.world import World, TileType
from src.pathfinding import AStar3D

class PathfindingUtility:
    def __init__(self, width=60, height=40):
        self.world = World(width=width, height=height, z_min=0, z_max=2)
        self.astar = AStar3D(self.world)

    def benchmark_pathfinding(self, num_runs=50):
        print("==================================================")
        print("  UTILITY 4: 3D A* Pathfinding Benchmark")
        print("==================================================")
        walkable = []
        for z in range(self.world.z_min, self.world.z_max + 1):
            for y in range(self.world.height):
                for x in range(self.world.width):
                    if self.world.is_walkable(x, y, z):
                        walkable.append((x, y, z))

        if len(walkable) < 2:
            print("[PathfindingUtility] Not enough walkable tiles to test.")
            return {}

        start_time = time.time()
        successful_paths = 0
        total_length = 0

        for i in range(min(num_runs, len(walkable) - 1)):
            s = walkable[i]
            g = walkable[-(i + 1)]
            path = self.astar.find_path(s, g)
            if path:
                successful_paths += 1
                total_length += len(path)

        elapsed = time.time() - start_time
        avg_time_ms = (elapsed / num_runs) * 1000.0 if num_runs > 0 else 0.0
        print(f"Executed {num_runs} path searches in {elapsed:.3f} s ({avg_time_ms:.2f} ms/path)")
        print(f"Successful paths found: {successful_paths}/{num_runs}")
        print(f"Average path node steps: {total_length / max(1, successful_paths):.1f}")

        return {
            "num_runs": num_runs,
            "elapsed_seconds": elapsed,
            "avg_time_ms": avg_time_ms,
            "success_rate": successful_paths / num_runs
        }

def main():
    util = PathfindingUtility()
    util.benchmark_pathfinding(num_runs=30)

if __name__ == "__main__":
    main()
