import math
from src.utils.sound_utility import SoundUtility


class NoiseEvent:
    """
    Acoustic noise event with decibel sound pressure level (dB) and realistic propagation decay.
    """
    def __init__(self, x, y, z, volume=10.0, lifetime=5, source_type="general"):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.volume = float(volume)
        self.lifetime = lifetime
        self.source_type = source_type

        profile = SoundUtility.SOUND_PROFILES.get(source_type, None)
        if profile and volume == 10.0:
            self.volume = profile["db_spl"] / 5.0  # Scale dB to simulation spatial radius

    def update(self):
        self.lifetime -= 1
        self.volume = max(0.0, self.volume - 0.5)


class ScentTrail:
    """Represents a survivor's olfactory trail left behind in the environment."""
    def __init__(self, x, y, z, intensity=100.0):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.intensity = intensity

    def update(self, world=None):
        decay = 1.0
        if world and world.weather.is_in_rain(self.x, self.y):
            decay = 4.0  # Rain rapidly washes away scent trails
        self.intensity -= decay

        if world and world.weather.wind_speed > 5.0:
            drift_speed = (world.weather.wind_speed / 100.0) * 0.05
            self.x += math.cos(world.weather.wind_angle) * drift_speed
            self.y += math.sin(world.weather.wind_angle) * drift_speed
