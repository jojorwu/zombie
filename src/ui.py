import sys
import pygame
import numpy as np
from src.world import TileType, TILE_COLORS, BUILDING_COLORS, BuildingType
from src.entities import ResourceItem

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

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_f:
                    self.fog_of_war_enabled = not self.fog_of_war_enabled
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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                tx, ty = mx // self.tile_size, my // self.tile_size
                if tx < self.sim.world.width and ty < self.sim.world.height:
                    best_idx = 0
                    min_d = 999.0
                    for idx, s in enumerate(self.sim.survivors):
                        d = (s.x - tx)**2 + (s.y - ty)**2
                        if d < min_d:
                            min_d = d
                            best_idx = idx
                    self.sim.selected_survivor_idx = best_idx

    def render(self):
        self.screen.fill((20, 20, 20))

        visible_tiles = None
        sel_survivor = self.sim.survivors[self.sim.selected_survivor_idx]
        if self.fog_of_war_enabled and sel_survivor.is_alive:
            visible_tiles = self.sim.world.compute_fog_of_war(sel_survivor.x, sel_survivor.y, radius=8)

        light = self.sim.world.get_light_level()
        for y in range(self.sim.world.height):
            for x in range(self.sim.world.width):
                if visible_tiles is not None and (x, y) not in visible_tiles:
                    color = (10, 10, 10)
                else:
                    ttype = self.sim.world.grid[y, x]
                    if ttype == TileType.BUILDING_FLOOR and (x, y) in self.sim.world.building_grid:
                        btype = self.sim.world.building_grid[(x, y)]
                        base_color = BUILDING_COLORS.get(btype, TILE_COLORS[ttype])
                    else:
                        base_color = TILE_COLORS[ttype]

                    color = (
                        int(base_color[0] * light),
                        int(base_color[1] * light),
                        int(base_color[2] * light)
                    )
                rect = (x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                pygame.draw.rect(self.screen, color, rect)

        for item in self.sim.items:
            if not item.collected:
                ix, iy = int(item.x), int(item.y)
                if visible_tiles is None or (ix, iy) in visible_tiles:
                    px = int(item.x * self.tile_size)
                    py = int(item.y * self.tile_size)
                    color = (255, 215, 0) if item.item_type == ResourceItem.FOOD else (0, 255, 255)
                    pygame.draw.circle(self.screen, color, (px, py), 3)

        for v in self.sim.vehicles:
            vx, vy = int(v.x), int(v.y)
            if visible_tiles is None or (vx, vy) in visible_tiles:
                px = int(v.x * self.tile_size) - 6
                py = int(v.y * self.tile_size) - 6
                pygame.draw.rect(self.screen, (70, 130, 180), (px, py, 12, 12))

        for a in self.sim.animals:
            if a.is_alive:
                ax, ay = int(a.x), int(a.y)
                if visible_tiles is None or (ax, ay) in visible_tiles:
                    px = int(a.x * self.tile_size)
                    py = int(a.y * self.tile_size)
                    pygame.draw.circle(self.screen, (255, 192, 203), (px, py), 4)

        for z in self.sim.zombies:
            if z.is_alive:
                zx, zy = int(z.x), int(z.y)
                if visible_tiles is None or (zx, zy) in visible_tiles:
                    px = int(z.x * self.tile_size)
                    py = int(z.y * self.tile_size)
                    pygame.draw.circle(self.screen, (178, 34, 34), (px, py), 5)

        for idx, s in enumerate(self.sim.survivors):
            if s.is_alive:
                sx, sy = int(s.x), int(s.y)
                if visible_tiles is None or (sx, sy) in visible_tiles:
                    px = int(s.x * self.tile_size)
                    py = int(s.y * self.tile_size)
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

        draw_text("Zombie Neuroevolution (GRU)", self.bold_font, (255, 215, 0))
        draw_text(f"Gen: {self.sim.evolution_manager.generation}  Tick: {self.sim.world.current_tick}")
        draw_text(f"Light level: {light:.2f}")
        draw_text(f"Speed: {self.speed_multiplier}x  (0=Fast Train)")
        draw_text(f"Fog of War [F]: {'ON' if self.fog_of_war_enabled else 'OFF'}")
        draw_text(f"Status: {'PAUSED' if self.paused else 'RUNNING'}")
        draw_text(f"Best Score: {self.sim.best_historical_score:.1f}")

        y_offset += 10
        draw_text("Selected Survivor Stats", self.bold_font, (0, 255, 127))
        draw_text(f"Index: {self.sim.selected_survivor_idx} / {len(self.sim.survivors)}")

        s = sel_survivor
        if s.is_alive:
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
        draw_text(" [SPACE] Pause / Resume")
        draw_text(" [F] Toggle Fog of War")
        draw_text(" [1/2/5/0] Speed Multipliers")
        draw_text(" [TAB] Switch Survivor")
        draw_text(" [Mouse Click] Select Survivor")

        pygame.display.flip()
