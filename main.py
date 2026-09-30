import json
import argparse
import time
import os
from src.simulation import SimulationEngine

def main():
    parser = argparse.ArgumentParser(description="Zombie AI Neuroevolution Simulation")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    parser.add_argument("--headless", action="store_true", help="Run simulation in headless mode (no GUI)")
    parser.add_argument("--ticks", type=int, default=1000, help="Number of ticks to run in headless mode")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    sim = SimulationEngine(config)

    if args.headless or os.environ.get("SDL_VIDEODRIVER") == "dummy":
        print(f"Running headless simulation for {args.ticks} ticks...")
        start_time = time.time()
        for i in range(args.ticks):
            sim.tick()
            if i % 200 == 0:
                alive = sum(1 for s in sim.survivors if s.is_alive)
                print(f"Tick {i}/{args.ticks} | Gen {sim.evolution_manager.generation} | Alive: {alive} | Best score: {sim.best_historical_score:.1f}")
        print(f"Completed {args.ticks} ticks in {time.time() - start_time:.2f} seconds.")
    else:
        from src.ui import RendererUI
        renderer = RendererUI(sim, tile_size=config["simulation"]["tile_size"])
        import pygame
        clock = pygame.time.Clock()

        running = True
        while running:
            renderer.handle_events()
            if not renderer.paused:
                for _ in range(renderer.speed_multiplier):
                    sim.tick()
            renderer.render()
            clock.tick(config["simulation"]["fps"])

if __name__ == "__main__":
    main()
