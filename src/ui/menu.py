import sys
import pygame

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
