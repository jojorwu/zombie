#!/usr/bin/env python3
import sys
import os
import time
import argparse

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.simulation.engine import SimulationEngine
from src.ai.brain_net import DEVICE


def parse_args():
    parser = argparse.ArgumentParser(description="Autonomous High-Speed AI Brain Training Engine")
    parser.add_argument("--generations", type=int, default=50, help="Number of evolutionary generations to run")
    parser.add_argument("--survivors", type=int, default=25, help="Population size of survivors per generation")
    parser.add_argument("--zombies", type=int, default=100, help="Number of zombies spawned")
    parser.add_argument("--map-size", type=int, default=200, help="Width and height of the simulation world")
    parser.add_argument("--max-ticks", type=int, default=108000, help="Max ticks per generation (1 month = 108,000 ticks)")
    parser.add_argument("--output", type=str, default="best_brain.zbrain", help="Output compressed model filename")
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 65)
    print("      AUTONOMOUS HIGH-SPEED SURVIVOR AI TRAINING ENGINE")
    print("=" * 65)
    print(f"Device Acceleration : {DEVICE}")
    print(f"Generations Target  : {args.generations}")
    print(f"Survivor Population : {args.survivors}")
    print(f"Zombie Count        : {args.zombies}")
    print(f"Map Size            : {args.map_size}x{args.map_size}")
    print(f"Max Gen Ticks       : {args.max_ticks} (1 Month)")
    print(f"Output Model File   : {args.output}")
    print("-" * 65)

    sim_config = {
        "simulation": {
            "map_width": args.map_size,
            "map_height": args.map_size,
            "num_survivors": args.survivors,
            "num_zombies": args.zombies,
            "num_animals": 10,
            "num_vehicles": 5,
            "day_length_ticks": 3600,
            "electricity_cutoff_day": 7,
            "water_cutoff_day": 14,
            "electricity_enabled": True,
            "water_enabled": True,
            "max_ticks_per_gen": args.max_ticks,
        },
        "evolution": {
            "mutation_rate": 0.15,
            "mutation_scale": 0.25,
            "elite_fraction": 0.2,
        }
    }

    engine = SimulationEngine(sim_config)
    start_time = time.time()

    for gen in range(1, args.generations + 1):
        gen_start = time.time()
        print(f"\n[Generation {gen}/{args.generations}] Simulating survivor population...")

        while engine.world.current_tick < args.max_ticks and any(s.is_alive for s in engine.survivors):
            engine.tick()

        duration = time.time() - gen_start
        ticks_processed = engine.world.current_tick
        tps = ticks_processed / max(0.001, duration)

        alive_survivors = sum(1 for s in engine.survivors if s.is_alive)
        best_idx = max(range(len(engine.survivors)), key=lambda i: engine.survivors[i].calculate_fitness())
        best_survivor = engine.survivors[best_idx]
        best_brain = engine.brains[best_idx]
        best_fit = best_survivor.calculate_fitness()

        print(f"  - Ticks Processed   : {ticks_processed} / {args.max_ticks}")
        print(f"  - Ticks Per Second  : {tps:.1f} TPS")
        print(f"  - Survivors Alive   : {alive_survivors}/{args.survivors}")
        print(f"  - Best Gen Fitness  : {best_fit:.2f}")
        print(f"  - Max Kills By Best : {best_survivor.kills}")
        print(f"  - Tiles Explored    : {len(best_survivor.visited_tiles)}")
        print(f"  - Best All-Time Fit : {engine.best_historical_score:.2f}")

        if best_fit >= engine.best_historical_score:
            engine.best_historical_score = best_fit
            engine.evolution_manager.save_best_brain(best_brain, args.output)
            print(f"  [SAVED CHECKPOINT] Model compressed and saved to '{args.output}'")

        if gen < args.generations:
            engine.end_generation()

    total_time = time.time() - start_time
    print("\n" + "=" * 65)
    print("              TRAINING COMPLETED SUCCESSFULLY!")
    print("=" * 65)
    print(f"Total Time Elapsed : {total_time:.2f} seconds")
    print(f"Best Model Saved   : {args.output}")
    print("=" * 65)


if __name__ == "__main__":
    main()
