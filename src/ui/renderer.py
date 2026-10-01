import sys
import math
import pygame
from src.world import TileType, TILE_COLORS, BUILDING_COLORS
from src.entities import ResourceItem
from src.ui.themes import UITheme, THEME_COLORS
from src.ui.camera import Camera
from src.ui.vulkan_bridge import VulkanBridge
from src.ui.hud_renderer import HUDRenderer


class RendererUI:
    def __init__(self, simulation, tile_size=16):
        self.sim = simulation
        self.tile_size = tile_size
        self.width = simulation.world.width * tile_size + 300
        self.height = simulation.world.height * tile_size

        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Zombie Neuroevolution Simulation (Native Rust Vulkan Render)")
        self.font = pygame.font.SysFont("Arial", 14)
        self.bold_font = pygame.font.SysFont("Arial", 16, bold=True)

        self.camera = Camera(tile_size=tile_size)
        self.hud_renderer = HUDRenderer(self.screen, self.font, self.bold_font, simulation.world.width * tile_size, self.height)

        max_tile = max(TILE_COLORS.keys())
        self.palette = [TILE_COLORS.get(i, (50, 50, 50)) for i in range(max_tile + 1)]
        self.vulkan_bridge = VulkanBridge(tile_size, self.palette)

        self.fog_of_war_enabled = False
        self.speed_multiplier = 1
        self.paused = False
        self.view_z = 0
        self.open_menu_requested = False
        self.active_theme = UITheme.DARK
        self.theme_list = [UITheme.DARK, UITheme.NEON, UITheme.TACTICAL, UITheme.RETRO]
        self.theme_idx = 0

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
                elif event.key == pygame.K_t:
                    self.theme_idx = (self.theme_idx + 1) % len(self.theme_list)
                    self.active_theme = self.theme_list[self.theme_idx]
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
        theme = THEME_COLORS[self.active_theme]
        self.screen.fill(theme["bg"])

        visible_tiles = None
        sel_survivor = self.sim.survivors[self.sim.selected_survivor_idx]
        if self.fog_of_war_enabled and sel_survivor.is_alive:
            visible_tiles = self.sim.world.compute_fog_of_war(sel_survivor.x, sel_survivor.y, radius=8, z=sel_survivor.z)

        light = self.sim.world.get_light_level()
        cur_z = self.view_z
        z_idx = self.sim.world.z_to_idx(cur_z)

        cam_x = sel_survivor.x if sel_survivor.is_alive else self.sim.world.width / 2.0
        cam_y = sel_survivor.y if sel_survivor.is_alive else self.sim.world.height / 2.0

        min_x, max_x, min_y, max_y, map_draw_w, map_draw_h = self.camera.get_viewport_bounds(
            cam_x, cam_y, self.width, self.height, self.sim.world.width, self.sim.world.height
        )

        if self.vulkan_bridge.is_available:
            viewport_surf = self.vulkan_bridge.render_viewport(
                self.sim.world, cur_z, z_idx, min_x, max_x, min_y, max_y, map_draw_w, map_draw_h, light, visible_tiles
            )
            if viewport_surf:
                self.screen.blit(viewport_surf, (0, 0))
        else:
            for y in range(min_y, max_y):
                for x in range(min_x, max_x):
                    screen_px, screen_py = self.camera.world_to_screen(x, y, min_x, min_y)

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
            return self.camera.world_to_screen(wx, wy, min_x, min_y)

        for dl in getattr(self.sim.world, 'dynamic_lights', []):
            if dl.z == cur_z and min_x <= dl.x <= max_x and min_y <= dl.y <= max_y:
                lx_p, ly_p = to_screen(dl.x, dl.y)
                lr_p = int(dl.radius * self.tile_size)
                pygame.draw.circle(self.screen, dl.color, (lx_p, ly_p), max(4, lr_p), 2)

        rf = self.sim.world.weather.rain_front
        if rf and cur_z >= 0:
            rx_start = max(min_x, int(rf["x"]))
            rx_end = min(max_x, int(rf["x"] + rf["w"]))
            ry_start = max(min_y, int(rf["y"]))
            ry_end = min(max_y, int(rf["y"] + rf["h"]))

            slant_x = int(math.cos(self.sim.world.weather.wind_angle) * 8)
            for ry in range(ry_start, ry_end, 2):
                for rx in range(rx_start, rx_end, 2):
                    if (rx + ry + self.sim.world.current_tick) % 7 == 0:
                        px, py = to_screen(rx, ry)
                        pygame.draw.line(self.screen, (150, 200, 255), (px, py), (px + slant_x, py + 8), 1)

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
                    if "ammo" in item.item_type or item.item_type in (ResourceItem.PISTOL, ResourceItem.SHOTGUN, ResourceItem.RIFLE):
                        color = (255, 69, 0)
                    elif item.item_type in (ResourceItem.KNIFE, ResourceItem.AXE, ResourceItem.CROWBAR, ResourceItem.BASEBALL_BAT, ResourceItem.CHEF_KNIFE, ResourceItem.FRYING_PAN):
                        color = (192, 192, 192)
                    elif item.item_type in (ResourceItem.CANNED_FOOD, ResourceItem.BREAD, ResourceItem.APPLE, ResourceItem.MEAT, ResourceItem.MRE, ResourceItem.FOOD):
                        color = (255, 215, 0)
                    elif item.item_type in (ResourceItem.WATER_BOTTLE, ResourceItem.WATER):
                        color = (0, 255, 255)
                    else:
                        color = (180, 180, 200)
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

        self.hud_renderer.render_sidebar(
            self.sim, self.active_theme, self.speed_multiplier, self.paused, self.view_z, light, self.vulkan_bridge.is_available
        )

        pygame.display.flip()
