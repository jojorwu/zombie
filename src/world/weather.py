import math
import random

class WeatherManager:
    """Simulates dynamic wind directions/speeds and localized 100x100 moving rainstorms."""
    def __init__(self, world_width, world_height):
        self.world_width = world_width
        self.world_height = world_height
        self.wind_angle = random.uniform(0, 2 * math.pi)  # Radians
        self.wind_speed = random.uniform(10.0, 50.0)      # km/h
        self.rain_front = None                            # dict: {x, y, w: 100, h: 100, vx, vy, lifetime}
        self.next_rain_tick = 3600 * 3                    # 3-day interval

    def update(self, current_tick):
        # Gradually shift wind direction & speed
        self.wind_angle += random.uniform(-0.02, 0.02)
        self.wind_speed = max(0.0, min(100.0, self.wind_speed + random.uniform(-0.5, 0.5)))

        # Trigger rain front every ~3 in-game days (10,800 ticks)
        if current_tick >= self.next_rain_tick and self.rain_front is None:
            self.rain_front = {
                "x": float(random.randint(0, max(1, self.world_width - 100))),
                "y": float(random.randint(0, max(1, self.world_height - 100))),
                "w": 100,
                "h": 100,
                "vx": math.cos(self.wind_angle) * 0.2,
                "vy": math.sin(self.wind_angle) * 0.2,
                "lifetime": 1200  # ~8 in-game hours
            }
            self.next_rain_tick = current_tick + 3600 * 3

        if self.rain_front:
            self.rain_front["x"] = max(0.0, min(self.world_width - 100, self.rain_front["x"] + self.rain_front["vx"]))
            self.rain_front["y"] = max(0.0, min(self.world_height - 100, self.rain_front["y"] + self.rain_front["vy"]))
            self.rain_front["lifetime"] -= 1
            if self.rain_front["lifetime"] <= 0:
                self.rain_front = None

    def is_in_rain(self, x, y):
        if not self.rain_front:
            return False
        rf = self.rain_front
        return (rf["x"] <= x <= rf["x"] + rf["w"]) and (rf["y"] <= y <= rf["y"] + rf["h"])
