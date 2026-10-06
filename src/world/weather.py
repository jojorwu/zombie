import math
import random

try:
    from rust_vulkan_render import RustEnvironmentManager
    RUST_ENV_AVAILABLE = True
except ImportError:
    RUST_ENV_AVAILABLE = False


class Season:
    SPRING = "Spring"
    SUMMER = "Summer"
    AUTUMN = "Autumn"
    WINTER = "Winter"


class WeatherManager:
    """
    Simulates dynamic 4-season calendar, wind directions/speeds, temperature, and localized moving rain/snowstorms.
    - Spring: Heavy rainstorms, mild temperatures (15°C)
    - Summer: High heat (32°C), clear skies, rapid dehydration
    - Autumn: Strong wind gusts, cold rain, falling foliage (8°C)
    - Winter: Freezing temperatures (-12°C), snowstorms, hypothermia risk, slowed movement
    """
    SEASONS_BY_MONTH = {
        12: Season.WINTER, 1: Season.WINTER, 2: Season.WINTER,
        3: Season.SPRING, 4: Season.SPRING, 5: Season.SPRING,
        6: Season.SUMMER, 7: Season.SUMMER, 8: Season.SUMMER,
        9: Season.AUTUMN, 10: Season.AUTUMN, 11: Season.AUTUMN,
    }

    def __init__(self, world_width, world_height):
        self.world_width = world_width
        self.world_height = world_height
        self.wind_angle = random.uniform(0, 2 * math.pi)
        self.wind_speed = random.uniform(10.0, 50.0)
        self.rain_front = None
        self.next_rain_tick = 3600 * 3
        self.season = Season.SPRING
        self.temperature = 15.0
        self.rust_env = RustEnvironmentManager() if RUST_ENV_AVAILABLE else None

    def update_season(self, current_tick):
        total_mins = current_tick / 2.5
        total_days = total_mins / 1440.0
        month = int((total_days / 30.0) % 12) + 1
        self.season = self.SEASONS_BY_MONTH.get(month, Season.SPRING)

        if self.season == Season.SPRING:
            self.temperature = 15.0 + random.uniform(-2.0, 2.0)
        elif self.season == Season.SUMMER:
            self.temperature = 32.0 + random.uniform(-3.0, 3.0)
        elif self.season == Season.AUTUMN:
            self.temperature = 8.0 + random.uniform(-2.0, 2.0)
        elif self.season == Season.WINTER:
            self.temperature = -12.0 + random.uniform(-4.0, 2.0)

    def update(self, current_tick):
        self.update_season(current_tick)

        if self.rust_env:
            light_lvl, rust_temp, wind_sp = self.rust_env.update_weather(current_tick, False)
            self.temperature = rust_temp
            self.wind_speed = wind_sp
        else:
            self.wind_angle += random.uniform(-0.02, 0.02)
            base_wind = 40.0 if self.season == Season.AUTUMN else 20.0
            self.wind_speed = max(0.0, min(100.0, base_wind + random.uniform(-5.0, 5.0)))

        # Trigger rain/snow storm front based on season
        storm_freq = 3600 * 2 if self.season in (Season.SPRING, Season.WINTER) else 3600 * 4
        if current_tick >= self.next_rain_tick and self.rain_front is None:
            self.rain_front = {
                "x": float(random.randint(0, max(1, self.world_width - 100))),
                "y": float(random.randint(0, max(1, self.world_height - 100))),
                "w": 100,
                "h": 100,
                "vx": math.cos(self.wind_angle) * 0.2,
                "vy": math.sin(self.wind_angle) * 0.2,
                "lifetime": 1200,
                "type": "snow" if self.season == Season.WINTER else "rain"
            }
            self.next_rain_tick = current_tick + storm_freq

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
