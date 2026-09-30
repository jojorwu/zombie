import sys
import os
import json
import argparse

from src.simulation import SimulationEngine


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def main():
    parser = argparse.ArgumentParser(description="Zombie AI Simulation")
    parser.add_argument("--headless", action="store_true", help="Run simulation in headless mode (no GUI)")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config JSON file")
    parser.add_argument("--ticks", type=int, default=1000, help="Number of ticks to run in headless mode")
    args = parser.parse_args()

    config_path = get_resource_path(args.config)
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        config = {
            "simulation": {
                "map_width": 1000,
                "map_height": 1000,
                "num_survivors": 20,
                "num_zombies": 30,
                "num_animals": 10,
                "num_vehicles": 4,
                "electricity_cutoff_day": 7,
                "water_cutoff_day": 14,
                "electricity_enabled": True,
                "water_enabled": True,
                "day_length_ticks": 3600
            }
        }

    sim_engine = SimulationEngine(config)

    if args.headless:
        print("[Simulation Engine] Running in HEADLESS mode...")
        for tick in range(1, args.ticks + 1):
            sim_engine.tick()
            if tick % 500 == 0 or tick == args.ticks:
                alive = sum(1 for s in sim_engine.survivors if s.is_alive)
                print(f"Tick {tick}/{args.ticks} | Alive Survivors: {alive}/{len(sim_engine.survivors)} | Date: {sim_engine.world.get_time_string()}")
        print("[Simulation Engine] Headless simulation completed successfully.")
    else:
        from src.ui import MainMenuUI, RendererUI
        menu_ui = MainMenuUI(config)
        renderer_ui = None
        in_menu = True

        import pygame
        clock = pygame.time.Clock()

        while True:
            if in_menu:
                menu_ui.handle_events()
                if menu_ui.start_requested:
                    sim_engine = SimulationEngine(menu_ui.config)
                    renderer_ui = RendererUI(sim_engine)
                    menu_ui.has_active_sim = True
                    menu_ui.start_requested = False
                    in_menu = False
                elif menu_ui.resume_requested:
                    menu_ui.resume_requested = False
                    in_menu = False
                else:
                    menu_ui.render()
            else:
                renderer_ui.handle_events()
                if renderer_ui.open_menu_requested:
                    renderer_ui.open_menu_requested = False
                    in_menu = True
                else:
                    if not renderer_ui.paused:
                        for _ in range(renderer_ui.speed_multiplier):
                            sim_engine.tick()
                    renderer_ui.render()

            clock.tick(60)


if __name__ == "__main__":
    main()
