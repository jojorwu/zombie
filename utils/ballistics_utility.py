import math


class BallisticsUtility:
    """
    Utility module for realistic firearm ballistics simulation:
    - Bullet velocity decay and aerodynamic air drag
    - Wind deflection and crosswind drift
    - Gravitational bullet drop
    - Terminal kinetic energy calculation (Joules) and damage scaling
    """
    CALIBERS = {
        "9mm": {
            "mass_kg": 0.008,          # 8 grams (124 grain)
            "muzzle_velocity": 360.0,   # m/s
            "drag_coeff": 0.15,
            "max_range": 50.0,
            "base_damage": 35.0,
        },
        "5.56mm": {
            "mass_kg": 0.004,          # 4 grams (62 grain)
            "muzzle_velocity": 940.0,   # m/s
            "drag_coeff": 0.25,
            "max_range": 150.0,
            "base_damage": 75.0,
        },
        "12gauge": {
            "mass_kg": 0.028,          # 28 grams (1 oz slug/buck)
            "muzzle_velocity": 475.0,   # m/s
            "drag_coeff": 0.35,
            "max_range": 35.0,
            "base_damage": 110.0,
        },
        ".357magnum": {
            "mass_kg": 0.010,
            "muzzle_velocity": 440.0,
            "drag_coeff": 0.18,
            "max_range": 65.0,
            "base_damage": 85.0,
        },
        ".308sniper": {
            "mass_kg": 0.011,
            "muzzle_velocity": 850.0,
            "drag_coeff": 0.30,
            "max_range": 300.0,
            "base_damage": 160.0,
        },
        "arrow": {
            "mass_kg": 0.025,
            "muzzle_velocity": 90.0,
            "drag_coeff": 0.40,
            "max_range": 40.0,
            "base_damage": 75.0,
        },
    }

    @classmethod
    def calculate_trajectory(cls, caliber, distance_m, wind_speed_kmh=0.0, wind_angle_rad=0.0):
        data = cls.CALIBERS.get(caliber, cls.CALIBERS["9mm"])
        v0 = data["muzzle_velocity"]
        m = data["mass_kg"]
        cd = data["drag_coeff"]

        dist = max(0.1, float(distance_m))
        decay_factor = math.exp(-cd * (dist / 100.0))
        terminal_velocity = v0 * decay_factor
        flight_time = dist / max(50.0, (v0 + terminal_velocity) / 2.0)

        kinetic_energy = 0.5 * m * (terminal_velocity ** 2)

        crosswind_m_s = (wind_speed_kmh / 3.6) * math.sin(wind_angle_rad)
        wind_drift_m = 0.1 * crosswind_m_s * (flight_time ** 1.5)
        bullet_drop_m = 0.5 * 9.81 * (flight_time ** 2)

        damage_scale = max(0.2, terminal_velocity / v0)
        final_damage = data["base_damage"] * damage_scale

        return {
            "terminal_velocity_ms": round(terminal_velocity, 1),
            "flight_time_s": round(flight_time, 3),
            "kinetic_energy_j": round(kinetic_energy, 1),
            "wind_drift_m": round(wind_drift_m, 2),
            "bullet_drop_m": round(bullet_drop_m, 2),
            "damage": round(final_damage, 1),
        }
