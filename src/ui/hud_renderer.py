import math
import pygame
from src.ui.themes import THEME_COLORS


class HUDRenderer:
    """Renders sidebar HUD, survivor stats, system performance, time/weather indicators, and hotkeys."""
    def __init__(self, screen, font, bold_font, sidebar_x, height):
        self.screen = screen
        self.font = font
        self.bold_font = bold_font
        self.sidebar_x = sidebar_x
        self.height = height

    def render_sidebar(self, sim, active_theme, speed_multiplier, paused, view_z, light, has_rust_vulkan):
        theme = THEME_COLORS[active_theme]
        pygame.draw.rect(self.screen, theme["sidebar_bg"], (self.sidebar_x, 0, 300, self.height))
        pygame.draw.line(self.screen, theme["sidebar_line"], (self.sidebar_x, 0), (self.sidebar_x, self.height), 2)

        y_offset = 10

        def draw_text(text, font_obj=self.font, color=theme["text"]):
            nonlocal y_offset
            img = font_obj.render(text, True, color)
            self.screen.blit(img, (self.sidebar_x + 10, y_offset))
            y_offset += 20

        def draw_stat_bar(label, val, max_val, color):
            nonlocal y_offset
            img = self.font.render(f"{label}: {val:.1f}/{max_val:.0f}", True, theme["text"])
            self.screen.blit(img, (self.sidebar_x + 10, y_offset))
            bar_x = self.sidebar_x + 150
            bar_w = 130
            pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, y_offset + 3, bar_w, 12), border_radius=3)
            fill_w = int((max(0.0, min(max_val, val)) / max_val) * bar_w)
            if fill_w > 0:
                pygame.draw.rect(self.screen, color, (bar_x, y_offset + 3, fill_w, 12), border_radius=3)
            y_offset += 20

        chase_cnt = sum(1 for z in sim.zombies if z.is_alive and getattr(z, 'state', None) == 'chase')
        invest_cnt = sum(1 for z in sim.zombies if z.is_alive and getattr(z, 'state', None) == 'investigate')

        wind_deg = int(math.degrees(sim.world.weather.wind_angle) % 360)
        wind_spd = sim.world.weather.wind_speed
        has_rain = sim.world.weather.rain_front is not None

        sim.memory_monitor.update_fps()
        mem_stats = sim.memory_monitor.get_memory_stats(sim.factory)

        draw_text("Zombie AI Neuroevolution", self.bold_font, theme["title"])
        draw_text(f"Render Engine: {'Native Rust Vulkan' if has_rust_vulkan else 'OpenGL/SDL2'}", color=(0, 255, 200))
        draw_text(f"RAM Usage: {mem_stats['ram_rss_mb']} MB | CPU: {mem_stats['cpu_percent']}%", color=(255, 215, 0))
        draw_text(f"Theme: {active_theme} [T to Switch]", color=theme["accent"])
        draw_text(f"Date: {sim.world.get_time_string()}")
        draw_text(f"Gen: {sim.evolution_manager.generation}  Tick: {sim.world.current_tick}")
        draw_text(f"View Level Z: {view_z}  Light: {light:.2f}")
        draw_text(f"Power: {'BLACKOUT' if sim.world.is_power_out() else 'ONLINE'} | Water: {'CUT OFF' if sim.world.is_water_out() else 'ONLINE'}")
        draw_text(f"Wind: {wind_spd:.1f} km/h ({wind_deg}°)", color=(180, 220, 255))
        draw_text(f"Weather: {'LOCAL RAINSTORM' if has_rain else 'CLEAR SKIES'}", color=(0, 255, 255) if has_rain else (255, 215, 0))
        draw_text(f"Active Noises: {len(getattr(sim, 'noise_events', []))}")
        draw_text(f"Zombies: Chase={chase_cnt} Hear/Invest={invest_cnt}")
        draw_text(f"Speed: {speed_multiplier}x  Status: {'PAUSED' if paused else 'RUNNING'}")
        draw_text(f"Best Score: {sim.best_historical_score:.1f}")

        y_offset += 10
        draw_text("Selected Survivor Stats", self.bold_font, theme["header"])
        draw_text(f"Index: {sim.selected_survivor_idx} / {len(sim.survivors)}")

        sel_survivor = sim.survivors[sim.selected_survivor_idx]
        s = sel_survivor
        if s.is_alive:
            floor_name = f"Basement B{abs(view_z)}" if view_z < 0 else (f"Ground Floor" if view_z == 0 else f"Floor {view_z + 1}")
            draw_text(f"View Floor: {floor_name} (Z={view_z})")
            draw_stat_bar("Health", s.health, 100.0, (220, 50, 50))
            draw_stat_bar("Hunger", s.hunger, 100.0, (220, 160, 40))
            draw_stat_bar("Thirst", s.thirst, 100.0, (40, 180, 220))
            draw_stat_bar("Sleep", s.sleep, 100.0, (160, 100, 220))

            draw_text(f"Kills: {s.kills}  Score: {s.score:.1f}")
            draw_text(f"In Vehicle: {'Yes' if s.in_vehicle else 'No'}")

            cur_hidden = sim.hidden_states[sim.selected_survivor_idx]
            hidden_norm = float(cur_hidden.norm().item())
            draw_text(f"GRU Memory Activation: {hidden_norm:.2f}")

            y_offset += 5
            draw_text("Inventory & Weapons:", self.bold_font, theme["header"])
            for item_k, item_v in s.inventory.items():
                if item_v > 0:
                    draw_text(f"  {item_k}: {item_v}")
        else:
            draw_text("SURVIVOR DEAD", color=(255, 69, 0))

        y_offset += 15
        draw_text("Hotkeys & Actions:", self.bold_font, theme["header"])
        draw_text(" [M / ESC] Main Menu & Settings")
        draw_text(" [T] Switch UI Theme")
        draw_text(" [SPACE] Pause / Resume")
        draw_text(" [F] Toggle Fog of War")
        draw_text(" [Z/X] Change Height Level")
        draw_text(" [1/2/5/0] Speed Multipliers")
        draw_text(" [TAB] Switch Survivor")
        draw_text(" [Action 9] Move Furniture")
        draw_text(" [Action 10] Dismantle Furniture")
