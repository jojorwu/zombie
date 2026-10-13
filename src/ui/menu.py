import sys
import os
import subprocess
import pygame


class MainMenuUI:
    """
    Main Menu UI with interactive world settings controls (map size, entity counts, power grid)
    and integrated Automated Test Suite & Max-Load Stress Benchmark runner.
    """
    def __init__(self, config, screen_width=800, screen_height=650):
        self.config = config.copy()
        if "simulation" not in self.config:
            self.config["simulation"] = {}
        self.sim_cfg = self.config["simulation"]

        self.screen_width = screen_width
        self.screen_height = screen_height

        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Zombie AI Simulation - Main Menu & Test Suite Runner")
        self.title_font = pygame.font.SysFont("Arial", 22, bold=True)
        self.font = pygame.font.SysFont("Arial", 15)
        self.bold_font = pygame.font.SysFont("Arial", 15, bold=True)

        self.start_requested = False
        self.resume_requested = False
        self.run_tests_requested = False
        self.quit_requested = False
        self.has_active_sim = False

        self.test_status_msg = "Not Executed"
        self.test_passed = None
        self.test_running = False

    def toggle_map_size(self):
        sizes = [(200, 200), (500, 500), (1000, 1000)]
        curr_w = self.sim_cfg.get("map_width", 1000)
        curr_h = self.sim_cfg.get("map_height", 1000)

        next_idx = 0
        for i, (w, h) in enumerate(sizes):
            if w == curr_w and h == curr_h:
                next_idx = (i + 1) % len(sizes)
                break

        nw, nh = sizes[next_idx]
        self.sim_cfg["map_width"] = nw
        self.sim_cfg["map_height"] = nh

    def run_automated_tests(self):
        self.test_running = True
        self.render_test_running_screen()

        try:
            cmd = [sys.executable, os.path.join("tests", "run_tests.py")]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            output = res.stdout + res.stderr

            if res.returncode == 0 and "Passed: True" in output:
                self.test_passed = True
                tps_str = ""
                for line in output.splitlines():
                    if "Executed 100 Ticks in" in line or "TPS" in line:
                        tps_str = line.strip()
                        break
                self.test_status_msg = f"ALL TESTS PASSED! {tps_str}"
            else:
                self.test_passed = False
                self.test_status_msg = "TEST SUITE FAILED! Check test report logs."
        except Exception as e:
            self.test_passed = False
            self.test_status_msg = f"Test Execution Error: {e}"

        self.test_running = False

    def render_test_running_screen(self):
        self.screen.fill((20, 20, 25))
        txt = self.bold_font.render("[RUNNING AUTOMATED TESTS & STRESS BENCHMARK... PLEASE WAIT]", True, (255, 215, 0))
        rect = txt.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(txt, rect)
        pygame.display.flip()

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
                elif event.key == pygame.K_t:
                    self.run_automated_tests()
                elif event.key == pygame.K_m:
                    self.toggle_map_size()
                elif event.key == pygame.K_UP:
                    self.sim_cfg["num_zombies"] = min(500, self.sim_cfg.get("num_zombies", 30) + 5)
                elif event.key == pygame.K_DOWN:
                    self.sim_cfg["num_zombies"] = max(1, self.sim_cfg.get("num_zombies", 30) - 5)
                elif event.key == pygame.K_RIGHT:
                    self.sim_cfg["num_survivors"] = min(200, self.sim_cfg.get("num_survivors", 20) + 2)
                elif event.key == pygame.K_LEFT:
                    self.sim_cfg["num_survivors"] = max(1, self.sim_cfg.get("num_survivors", 20) - 2)
                elif event.key == pygame.K_a:
                    self.sim_cfg["num_animals"] = min(100, self.sim_cfg.get("num_animals", 10) + 2)
                elif event.key == pygame.K_s:
                    self.sim_cfg["num_animals"] = max(0, self.sim_cfg.get("num_animals", 10) - 2)
                elif event.key == pygame.K_v:
                    self.sim_cfg["num_vehicles"] = min(50, self.sim_cfg.get("num_vehicles", 4) + 1)
                elif event.key == pygame.K_c:
                    self.sim_cfg["num_vehicles"] = max(0, self.sim_cfg.get("num_vehicles", 4) - 1)
                elif event.key == pygame.K_p:
                    self.sim_cfg["electricity_enabled"] = not self.sim_cfg.get("electricity_enabled", True)
                elif event.key == pygame.K_w:
                    self.sim_cfg["water_enabled"] = not self.sim_cfg.get("water_enabled", True)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if 220 <= mx <= 580 and 470 <= my <= 510:
                    self.start_requested = True
                elif 220 <= mx <= 580 and 520 <= my <= 560:
                    self.run_automated_tests()
                elif 220 <= mx <= 580 and 570 <= my <= 605 and self.has_active_sim:
                    self.resume_requested = True

    def render(self):
        self.screen.fill((22, 22, 28))

        y_offset = 25
        def draw_text(text, font_obj=self.font, color=(220, 220, 220), center_x=True):
            nonlocal y_offset
            img = font_obj.render(text, True, color)
            rect = img.get_rect()
            if center_x:
                rect.centerx = self.screen_width // 2
            else:
                rect.x = 70
            rect.y = y_offset
            self.screen.blit(img, rect)
            y_offset += 26

        draw_text("ZOMBIE AI SIMULATION - ENGINE MENU", self.title_font, (255, 215, 0))
        draw_text("WORLD CONFIGURATION & AUTOMATED TEST RUNNER", self.bold_font, (0, 255, 200))

        y_offset += 10
        draw_text("World & Simulation Settings:", self.bold_font, (255, 255, 255), center_x=False)
        draw_text(f"  Map Dimensions: {self.sim_cfg.get('map_width', 1000)} x {self.sim_cfg.get('map_height', 1000)} tiles  [M to Cycle Size]", color=(200, 220, 255), center_x=False)
        draw_text(f"  Power Grid: Cutoff Day {self.sim_cfg.get('electricity_cutoff_day', 7)}  ({'ENABLED' if self.sim_cfg.get('electricity_enabled', True) else 'DISABLED'})  [P to Toggle]", color=(255, 215, 0), center_x=False)
        draw_text(f"  Water Supply: Cutoff Day {self.sim_cfg.get('water_cutoff_day', 14)}  ({'ENABLED' if self.sim_cfg.get('water_enabled', True) else 'DISABLED'})  [W to Toggle]", color=(0, 200, 255), center_x=False)
        draw_text(f"  Survivors Count: {self.sim_cfg.get('num_survivors', 20)}  [LEFT / RIGHT Arrows]", color=(0, 255, 127), center_x=False)
        draw_text(f"  Zombies Count: {self.sim_cfg.get('num_zombies', 30)}  [UP / DOWN Arrows]", color=(255, 99, 71), center_x=False)
        draw_text(f"  Animals Count: {self.sim_cfg.get('num_animals', 10)}  [A / S Keys]", color=(255, 192, 203), center_x=False)
        draw_text(f"  Vehicles Count: {self.sim_cfg.get('num_vehicles', 4)}  [V / C Keys]", color=(100, 149, 237), center_x=False)

        # Test Suite Banner
        y_offset += 10
        banner_color = (100, 100, 100) if self.test_passed is None else ((0, 200, 100) if self.test_passed else (220, 50, 50))
        pygame.draw.rect(self.screen, (35, 35, 45), (60, y_offset, 680, 35), border_radius=6)
        pygame.draw.rect(self.screen, banner_color, (60, y_offset, 680, 35), 2, border_radius=6)
        test_txt = self.bold_font.render(f"Test Status: {self.test_status_msg}", True, banner_color)
        t_rect = test_txt.get_rect(center=(self.screen_width // 2, y_offset + 17))
        self.screen.blit(test_txt, t_rect)

        # Action Buttons
        y_offset = 470
        # Button 1: Start Simulation
        pygame.draw.rect(self.screen, (0, 140, 70), (220, 470, 360, 40), border_radius=6)
        pygame.draw.rect(self.screen, (0, 230, 110), (220, 470, 360, 40), 2, border_radius=6)
        st_txt = self.bold_font.render("[ ENTER / CLICK ] START SIMULATION", True, (255, 255, 255))
        st_rect = st_txt.get_rect(center=(self.screen_width // 2, 490))
        self.screen.blit(st_txt, st_rect)

        # Button 2: Run Automated Tests
        pygame.draw.rect(self.screen, (130, 80, 0), (220, 520, 360, 40), border_radius=6)
        pygame.draw.rect(self.screen, (255, 170, 0), (220, 520, 360, 40), 2, border_radius=6)
        tst_txt = self.bold_font.render("[ T / CLICK ] RUN TESTS & STRESS BENCHMARK", True, (255, 255, 255))
        tst_rect = tst_txt.get_rect(center=(self.screen_width // 2, 540))
        self.screen.blit(tst_txt, tst_rect)

        # Button 3: Resume Active Simulation if open
        if self.has_active_sim:
            pygame.draw.rect(self.screen, (60, 90, 140), (220, 570, 360, 35), border_radius=6)
            res_txt = self.font.render("[ ESC ] RESUME ACTIVE SIMULATION", True, (255, 255, 255))
            res_rect = res_txt.get_rect(center=(self.screen_width // 2, 587))
            self.screen.blit(res_txt, res_rect)

        pygame.display.flip()
