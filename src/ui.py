import sys
import pygame
import numpy as np
from src.world import TileType, TILE_COLORS, BUILDING_COLORS, BuildingType
from src.entities import ResourceItem

class MainMenuUI:
    def __init__(self, config, screen_width=800, screen_height=600):
        self.config = config.copy()
        self.sim_cfg = self.config.get("simulation", {})
        self.screen_width = screen_width
        self.screen_height = screen_height

        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Zombie AI Simulation - Main Menu & Settings")
        self.title_font = pygame.font.SysFont("Arial", 22, bold=True)
        self.font = pygame.font.SysFont("Arial", 16)
        self.bold_font = pygame.font.SysFont("Arial", 16, bold=True)

        self.start_requested = False
        self.resume_requested = False
        self.quit_requested = False
        self.has_active_sim = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_requested = True
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.has_active_sim:
                        self.resume_requested = True
                elif event.key == pygame.K_RETURN:
                    self.start_requested = True
                elif event.key == pygame.K_UP:
                    self.sim_cfg["num_zombies"] = min(200, self.sim_cfg.get("num_zombies", 30) + 5)
                elif event.key == pygame.K_DOWN:
                    self.sim_cfg["num_zombies"] = max(1, self.sim_cfg.get("num_zombies", 30) - 5)
                elif event.key == pygame.K_RIGHT:
                    self.sim_cfg["num_survivors"] = min(100, self.sim_cfg.get("num_survivors", 20) + 2)
                elif event.key == pygame.K_LEFT:
                    self.sim_cfg["num_survivors"] = max(1, self.sim_cfg.get("num_survivors", 20) - 2)
                elif event.key == pygame.K_p:
                    self.sim_cfg["electricity_enabled"] = not self.sim_cfg.get("electricity_enabled", True)
                elif event.key == pygame.K_w:
                    self.sim_cfg["water_enabled"] = not self.sim_cfg.get("water_enabled", True)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Check start button click (x: 250..550, y: 460..500)
                if 250 <= mx <= 550 and 460 <= my <= 500:
                    self.start_requested = True
                elif 250 <= mx <= 550 and 510 <= my <= 550 and self.has_active_sim:
                    self.resume_requested = True

    def render(self):
        self.screen.fill((25, 25, 30))

        y_offset = 30
        def draw_text(text, font_obj=self.font, color=(220, 220, 220), center_x=True):
            nonlocal y_offset
            img = font_obj.render(text, True, color)
            rect = img.get_rect()
            if center_x:
                rect.centerx = self.screen_width // 2
            else:
                rect.x = 80
            rect.y = y_offset
            self.screen.blit(img, rect)
            y_offset += 28

        draw_text("ZOMBIE AI NEUROEVOLUTION", self.title_font, (255, 215, 0))
        draw_text("MAIN MENU & WORLD CREATION SETTINGS", self.bold_font, (0, 255, 200))

        y_offset += 20
        draw_text("World & Simulation Settings:", self.bold_font, (255, 255, 255), center_x=False)
        draw_text(f"  Map Width: {self.sim_cfg.get('map_width', 1000)} x {self.sim_cfg.get('map_height', 1000)} tiles", color=(200, 220, 255), center_x=False)
        draw_text(f"  Power Cutoff: Day {self.sim_cfg.get('electricity_cutoff_day', 7)}  ({'ON' if self.sim_cfg.get('electricity_enabled', True) else 'OFF'})  [P to Toggle]", color=(255, 215, 0), center_x=False)
        draw_text(f"  Water Cutoff: Day {self.sim_cfg.get('water_cutoff_day', 14)}  ({'ON' if self.sim_cfg.get('water_enabled', True) else 'OFF'})  [W to Toggle]", color=(0, 200, 255), center_x=False)
        draw_text(f"  Survivors Count: {self.sim_cfg.get('num_survivors', 20)}  [LEFT / RIGHT Arrows]", color=(0, 255, 127), center_x=False)
        draw_text(f"  Zombies Count: {self.sim_cfg.get('num_zombies', 30)}  [UP / DOWN Arrows]", color=(255, 99, 71), center_x=False)
        draw_text(f"  Animals Count: {self.sim_cfg.get('num_animals', 10)}", color=(255, 192, 203), center_x=False)
        draw_text(f"  Vehicles Count: {self.sim_cfg.get('num_vehicles', 4)}", color=(100, 149, 237), center_x=False)
        draw_text(f"  Time Scale: 1 real hour = 1 month (24h/day = {self.sim_cfg.get('day_length_ticks', 3600)} ticks)", color=(220, 220, 220), center_x=False)

        # Draw Start Button
        y_offset = 460
        pygame.draw.rect(self.screen, (0, 150, 70), (250, 460, 300, 40), border_radius=6)
        pygame.draw.rect(self.screen, (0, 230, 100), (250, 460, 300, 40), 2, border_radius=6)
        start_txt = self.bold_font.render("[ ENTER / CLICK ] START SIMULATION", True, (255, 255, 255))
        st_rect = start_txt.get_rect(center=(self.screen_width // 2, 480))
        self.screen.blit(start_txt, st_rect)

        if self.has_active_sim:
            pygame.draw.rect(self.screen, (70, 100, 150), (250, 510, 300, 35), border_radius=6)
            res_txt = self.font.render("[ ESC ] RESUME SIMULATION", True, (255, 255, 255))
            res_rect = res_txt.get_rect(center=(self.screen_width // 2, 527))
            self.screen.blit(res_txt, res_rect)

        pygame.display.flip()

class RendererUI:
    def __init__(self, simulation, tile_size=16):
        self.sim = simulation
        self.tile_size = tile_size
        self.width = simulation.world.width * tile_size + 300
        self.height = simulation.world.height * tile_size

        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Zombie Neuroevolution Simulation (GRU Memory)")
        self.font = pygame.font.SysFont("Arial", 14)
        self.bold_font = pygame.font.SysFont("Arial", 16, bold=True)

        self.fog_of_war_enabled = False
        self.speed_multiplier = 1
        self.paused = False
        self.view_z = 0  # Active height level (0, 1, 2)
        self.open_menu_requested = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_m, pygame.K_ESCAPE):
                    self.open_menu_requested = True
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_f:
                    self.fog_of_war_enabled = not self.fog_of_war_enabled
                elif event.key in (pygame.K_z, pygame.K_PAGEUP, pygame.K_UP):
                    self.view_z = min(self.sim.world.z_max, self.view_z + 1)
                elif event.key in (pygame.K_x, pygame.K_PAGEDOWN, pygame.K_DOWN):
                    self.view_z = max(self.sim.world.z_min, self.view_z - 1)
                elif event.key == pygame.K_1:
                    self.speed_multiplier = 1
                elif event.key == pygame.K_2:
                    self.speed_multiplier = 2
                elif event.key == pygame.K_5:
                    self.speed_multiplier = 5
                elif event.key == pygame.K_0:
                    self.speed_multiplier = 20
                elif event.key == pygame.K_TAB:
                    self.sim.selected_survivor_idx = (self.sim.selected_survivor_idx + 1) % len(self.sim.survivors)
                    self.view_z = self.sim.survivors[self.sim.selected_survivor_idx].z
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                tx, ty = mx // self.tile_size, my // self.tile_size
                if tx < self.sim.world.width and ty < self.sim.world.height:
                    best_idx = 0
                    min_d = 999.0
                    for idx, s in enumerate(self.sim.survivors):
                        d = (s.x - tx)**2 + (s.y - ty)**2 + (s.z - self.view_z)**2 * 10
                        if d < min_d:
                            min_d = d
                            best_idx = idx
                    self.sim.selected_survivor_idx = best_idx
                    self.view_z = self.sim.survivors[best_idx].z

    def render(self):
        self.screen.fill((20, 20, 20))

        visible_tiles = None
        sel_survivor = self.sim.survivors[self.sim.selected_survivor_idx]
        if self.fog_of_war_enabled and sel_survivor.is_alive:
            visible_tiles = self.sim.world.compute_fog_of_war(sel_survivor.x, sel_survivor.y, radius=8, z=sel_survivor.z)

        light = self.sim.world.get_light_level()
        cur_z = self.view_z
        z_idx = self.sim.world.z_to_idx(cur_z)

        # Viewport Camera Culling for 1000x1000 Large Map Performance
        map_draw_width = (self.width - 300) // self.tile_size
        map_draw_height = self.height // self.tile_size

        cam_x = sel_survivor.x if sel_survivor.is_alive else self.sim.world.width / 2.0
        cam_y = sel_survivor.y if sel_survivor.is_alive else self.sim.world.height / 2.0

        min_x = max(0, int(cam_x - map_draw_width // 2))
        max_x = min(self.sim.world.width, min_x + map_draw_width)
        min_x = max(0, max_x - map_draw_width)

        min_y = max(0, int(cam_y - map_draw_height // 2))
        max_y = min(self.sim.world.height, min_y + map_draw_height)
        min_y = max(0, max_y - map_draw_height)

        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                screen_px = (x - min_x) * self.tile_size
                screen_py = (y - min_y) * self.tile_size

                if visible_tiles is not None and (x, y) not in visible_tiles:
                    color = (10, 10, 10)
                else:
                    ttype = self.sim.world.grid[z_idx, y, x]
                    if ttype == TileType.BUILDING_FLOOR and (x, y, cur_z) in self.sim.world.building_grid:
                        btype = self.sim.world.building_grid[(x, y, cur_z)]
                        base_color = BUILDING_COLORS.get(btype, TILE_COLORS[ttype])
                    else:
                        base_color = TILE_COLORS[ttype]

                    color = (
                        int(base_color[0] * (light if cur_z >= 0 else 0.8)),
                        int(base_color[1] * (light if cur_z >= 0 else 0.8)),
                        int(base_color[2] * (light if cur_z >= 0 else 0.8))
                    )
                rect = (screen_px, screen_py, self.tile_size, self.tile_size)
                pygame.draw.rect(self.screen, color, rect)

        def to_screen(wx, wy):
            return int((wx - min_x) * self.tile_size), int((wy - min_y) * self.tile_size)

        # Draw acoustic Noise Events on current level
        for ne in getattr(self.sim, 'noise_events', []):
            if ne.z == cur_z and min_x <= ne.x <= max_x and min_y <= ne.y <= max_y:
                nx_p, ny_p = to_screen(ne.x, ne.y)
                r_p = int(ne.volume * self.tile_size)
                pygame.draw.circle(self.screen, (255, 100, 0), (nx_p, ny_p), max(3, r_p), 1)

        for item in self.sim.items:
            if not item.collected and item.z == cur_z and min_x <= item.x <= max_x and min_y <= item.y <= max_y:
                ix, iy = int(item.x), int(item.y)
                if visible_tiles is None or (ix, iy) in visible_tiles:
                    px, py = to_screen(item.x, item.y)
                    color = (255, 215, 0) if item.item_type == ResourceItem.FOOD else (0, 255, 255)
                    pygame.draw.circle(self.screen, color, (px, py), 3)

        for v in self.sim.vehicles:
            if v.z == cur_z and min_x <= v.x <= max_x and min_y <= v.y <= max_y:
                vx, vy = int(v.x), int(v.y)
                if visible_tiles is None or (vx, vy) in visible_tiles:
                    px, py = to_screen(v.x, v.y)
                    pygame.draw.rect(self.screen, (70, 130, 180), (px - 6, py - 6, 12, 12))

        for a in self.sim.animals:
            if a.is_alive and a.z == cur_z and min_x <= a.x <= max_x and min_y <= a.y <= max_y:
                ax, ay = int(a.x), int(a.y)
                if visible_tiles is None or (ax, ay) in visible_tiles:
                    px, py = to_screen(a.x, a.y)
                    pygame.draw.circle(self.screen, (255, 192, 203), (px, py), 4)

        for z in self.sim.zombies:
            if z.is_alive and z.z == cur_z and min_x <= z.x <= max_x and min_y <= z.y <= max_y:
                zx, zy = int(z.x), int(z.y)
                if visible_tiles is None or (zx, zy) in visible_tiles:
                    px, py = to_screen(z.x, z.y)
                    pygame.draw.circle(self.screen, (178, 34, 34), (px, py), 5)

        for idx, s in enumerate(self.sim.survivors):
            if s.is_alive and s.z == cur_z and min_x <= s.x <= max_x and min_y <= s.y <= max_y:
                sx, sy = int(s.x), int(s.y)
                if visible_tiles is None or (sx, sy) in visible_tiles:
                    px, py = to_screen(s.x, s.y)
                    color = (255, 255, 255) if idx == self.sim.selected_survivor_idx else (50, 205, 50)
                    pygame.draw.circle(self.screen, color, (px, py), 6)

        sidebar_x = self.sim.world.width * self.tile_size
        pygame.draw.rect(self.screen, (30, 30, 30), (sidebar_x, 0, 300, self.height))
        pygame.draw.line(self.screen, (100, 100, 100), (sidebar_x, 0), (sidebar_x, self.height), 2)

        y_offset = 10
        def draw_text(text, font_obj=self.font, color=(220, 220, 220)):
            nonlocal y_offset
            img = font_obj.render(text, True, color)
            self.screen.blit(img, (sidebar_x + 10, y_offset))
            y_offset += 20

        chase_cnt = sum(1 for z in self.sim.zombies if z.is_alive and getattr(z, 'state', None) == 'chase')
        invest_cnt = sum(1 for z in self.sim.zombies if z.is_alive and getattr(z, 'state', None) == 'investigate')

        draw_text("Zombie AI Neuroevolution", self.bold_font, (255, 215, 0))
        draw_text(f"Date: {self.sim.world.get_time_string()}")
        draw_text(f"Gen: {self.sim.evolution_manager.generation}  Tick: {self.sim.world.current_tick}")
        draw_text(f"View Level Z: {self.view_z}  Light: {light:.2f}")
        draw_text(f"Power: {'BLACKOUT' if self.sim.world.is_power_out() else 'ONLINE'} | Water: {'CUT OFF' if self.sim.world.is_water_out() else 'ONLINE'}")
        draw_text(f"Active Noises: {len(getattr(self.sim, 'noise_events', []))}")
        draw_text(f"Zombies: Chase={chase_cnt} Hear/Invest={invest_cnt}")
        draw_text(f"Speed: {self.speed_multiplier}x  Status: {'PAUSED' if self.paused else 'RUNNING'}")
        draw_text(f"Best Score: {self.sim.best_historical_score:.1f}")

        y_offset += 10
        draw_text("Selected Survivor Stats", self.bold_font, (0, 255, 127))
        draw_text(f"Index: {self.sim.selected_survivor_idx} / {len(self.sim.survivors)}")

        s = sel_survivor
        if s.is_alive:
            draw_text(f"Floor/Level: {s.z + 1} / {self.sim.world.num_levels}")
            draw_text(f"Health: {s.health:.1f} / 100")
            draw_text(f"Hunger: {s.hunger:.1f} / 100")
            draw_text(f"Thirst: {s.thirst:.1f} / 100")
            draw_text(f"Sleep: {s.sleep:.1f} / 100")
            draw_text(f"Kills: {s.kills}  Score: {s.score:.1f}")
            draw_text(f"In Vehicle: {'Yes' if s.in_vehicle else 'No'}")

            # Show GRU hidden memory state mean activation
            cur_hidden = self.sim.hidden_states[self.sim.selected_survivor_idx]
            hidden_norm = float(cur_hidden.norm().item())
            draw_text(f"GRU Memory Activation: {hidden_norm:.2f}")

            y_offset += 5
            draw_text("Inventory:", self.bold_font)
            for item_k, item_v in s.inventory.items():
                draw_text(f"  {item_k}: {item_v}")
        else:
            draw_text("SURVIVOR DEAD", color=(255, 69, 0))

        y_offset += 15
        draw_text("Hotkeys:", self.bold_font)
        draw_text(" [M / ESC] Main Menu & Settings")
        draw_text(" [SPACE] Pause / Resume")
        draw_text(" [F] Toggle Fog of War")
        draw_text(" [Z/X] Change View Height Level")
        draw_text(" [1/2/5/0] Speed Multipliers")
        draw_text(" [TAB] Switch Survivor")
        draw_text(" [Mouse Click] Select Survivor")

        pygame.display.flip()
