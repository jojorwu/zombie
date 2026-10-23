"""Leaf module for transient environmental events (noise, scent).

Canonical home of ``NoiseEvent`` and ``ScentTrail`` (formerly in the
misnamed ``src.entities.sensory``). This module only imports stdlib at
module level; ``src.systems.sound`` is resolved lazily on first use so it
can be imported from entities, world, systems and simulation layers
without creating circular-import chains.
"""
import math

from src.entities.identifiers import next_uid

_PROFILE_CACHE = None


def _sound_profiles():
    """Lazily resolve SoundUtility.SOUND_PROFILES (avoids import-time cycles)."""
    global _PROFILE_CACHE
    if _PROFILE_CACHE is None:
        from src.systems.sound import SoundUtility
        _PROFILE_CACHE = SoundUtility.SOUND_PROFILES
    return _PROFILE_CACHE


class NoiseEvent:
    """
    Acoustic noise event with decibel sound pressure level (dB) and realistic propagation decay.
    """
    __slots__ = ("lifetime", "source_type", "uid", "volume", "x", "y", "z")

    def __init__(self, x, y, z, volume=10.0, lifetime=5, source_type="general"):
        self.uid = next_uid()
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.volume = float(volume)
        self.lifetime = lifetime
        self.source_type = source_type

        profile = _sound_profiles().get(source_type, None)
        if profile and volume == 10.0:
            self.volume = profile["db_spl"] / 5.0  # Scale dB to simulation spatial radius

    def update(self):
        self.lifetime -= 1
        self.volume = max(0.0, self.volume - 0.5)


class ScentTrail:
    """Represents a survivor's olfactory trail left behind in the environment."""
    __slots__ = ("intensity", "uid", "x", "y", "z")

    def __init__(self, x, y, z, intensity=100.0):
        self.uid = next_uid()
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
