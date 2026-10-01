import math

class SoundUtility:
    """
    Realistic Acoustic Sound Physics Utility Engine:
    - Decibel sound pressure level (dB SPL) modeling
    - Geometric inverse-square law distance loss (6 dB loss per doubling of distance)
    - Obstacle materials decibel absorption (Solid wall = -25 dB, Wooden door = -12 dB)
    - Distinct decibel profiles for firearms, footsteps, vehicles, furniture movements, and thunder
    """
    SOUND_PROFILES = {
        "rifle_shot": {"db_spl": 155.0, "frequency_hz": 1200},
        "shotgun_shot": {"db_spl": 160.0, "frequency_hz": 800},
        "pistol_shot": {"db_spl": 140.0, "frequency_hz": 1500},
        "vehicle_engine": {"db_spl": 85.0, "frequency_hz": 300},
        "furniture_push": {"db_spl": 70.0, "frequency_hz": 250},
        "dismantling": {"db_spl": 75.0, "frequency_hz": 500},
        "footsteps": {"db_spl": 40.0, "frequency_hz": 800},
        "crafting": {"db_spl": 55.0, "frequency_hz": 1000},
        "thunder": {"db_spl": 120.0, "frequency_hz": 100},
    }

    # Threshold of hearing for zombie / human ear
    HEARING_THRESHOLD_DB = 20.0

    @classmethod
    def calculate_perceived_decibels(cls, sound_type, distance_m, wall_count=0, door_count=0):
        """
        Calculates the perceived sound pressure in dB at a given distance through obstacles.
        SPL(d) = SPL_0 - 20 * log10(d) - (walls * 25) - (doors * 12)
        """
        profile = cls.SOUND_PROFILES.get(sound_type, {"db_spl": 60.0})
        base_db = profile["db_spl"]

        if distance_m <= 1.0:
            distance_loss = 0.0
        else:
            distance_loss = 20.0 * math.log10(distance_m)

        obstacle_loss = (wall_count * 25.0) + (door_count * 12.0)
        perceived_db = base_db - distance_loss - obstacle_loss

        is_audible = perceived_db >= cls.HEARING_THRESHOLD_DB
        effective_volume = max(0.0, perceived_db - cls.HEARING_THRESHOLD_DB)

        return {
            "source_db": base_db,
            "perceived_db": round(perceived_db, 1),
            "is_audible": is_audible,
            "effective_volume": round(effective_volume, 1)
        }
