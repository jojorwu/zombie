import json
import argparse
import time
import os
import sys
from src.simulation import SimulationEngine

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

def main():
    parser = argparse.ArgumentParser(description="Zombie AI Neuroevolution Simulation")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config file")
    parser.add_argument("--headless", action="store_true", help="Run simulation in headless mode (no GUI)")
    parser.add_argument("--ticks", type=int, default=1000, help="Number of ticks to run in headless mode")
    args = parser.parse_args()

    config_path = get_resource_path(args.config) if not os.path.isabs(args.config) and not os.path.exists(args.config) else args.config
    if not os.path.exists(config_path):
        config_path = get_resource_path("config.json")

    with open(config_path, "r") as f:
        config = json.load(f)

    if args.headless or os.environ.get("SDL_VIDEODRIVER") == "dummy":
        sim = SimulationEngine(config)
        print(f"Running headless simulation for {args.ticks} ticks...")
        start_time = time.time()
        for i in range(args.ticks):
            sim.tick()
            if i % 200 == 0:
                alive = sum(1 for s in sim.survivors if s.is_alive)
                print(f"Tick {i}/{args.ticks} | Gen {sim.evolution_manager.generation} | Alive: {alive} | Best score: {sim.best_historical_score:.1f}")
        print(f"Completed {args.ticks} ticks in {time.time() - start_time:.2f} seconds.")
    else:
        from src.ui import MainMenuUI, RendererUI
        import pygame
        clock = pygame.time.Clock()

        menu = MainMenuUI(config)
        sim = None
        renderer = None

        running = True
        in_menu = True

        while running:
            if in_menu:
                menu.handle_events()
                menu.render()

                if menu.start_requested:
                    menu.start_requested = False
                    sim = SimulationEngine(menu.config)
                    renderer = RendererUI(sim, tile_size=menu.config["simulation"].get("tile_size", 16))
                    menu.has_active_sim = True
                    in_menu = False
                elif menu.resume_requested:
                    menu.resume_requested = False
                    if sim is not None:
                        in_menu = False
                clock.tick(30)
            else:
                renderer.handle_events()
                if renderer.open_menu_requested:
                    renderer.open_menu_requested = False
                    in_menu = True
                else:
                    if not renderer.paused:
                        for _ in range(renderer.speed_multiplier):
                            sim.tick()
                    renderer.render()
                    clock.tick(menu.config["simulation"].get("fps", 30))

if __name__ == "__main__":
    main()
