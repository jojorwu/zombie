import math
from dataclasses import dataclass


@dataclass
class MetabolicState:
    body_temperature: float = 37.0  # Celsius
    clothing_wetness: float = 0.0   # 0.0 (dry) to 100.0 (soaked)
    physical_activity: float = 0.0  # 0.0 (resting) to 100.0 (sprinting)
    hypothermia_stage: int = 0      # 0 (normal), 1 (mild), 2 (severe)
    hyperthermia_stage: int = 0     # 0 (normal), 1 (mild), 2 (severe)
    sepsis_risk: float = 0.0        # 0.0 to 100.0 percent
    sepsis_active: bool = False


class MetabolicBalanceSimulator:
    """
    Unified Metabolic Balance Simulator for Survivors.
    Models core body temperature, clothing insulation, rain wetness, wind chill,
    metabolic heat generation, hypothermia/hyperthermia, wound sterility, and sepsis.
    """
    __slots__ = ("state",)

    def __init__(self):
        self.state = MetabolicState()

    def update(self, survivor, world, is_moving: bool = False, is_running: bool = False) -> None:
        state = self.state
        weather = getattr(world, 'weather', None)

        ambient_temp = 20.0
        wind_speed = 0.0
        is_raining = False

        if weather is not None:
            ambient_temp = getattr(weather, 'temperature', 20.0)
            wind_speed = getattr(weather, 'wind_speed', 0.0)
            is_raining = weather.is_in_rain(survivor.x, survivor.y) if hasattr(weather, 'is_in_rain') else False

        building_grid = getattr(world, 'building_grid', {})
        in_shelter = building_grid.get((int(survivor.x), int(survivor.y))) is not None or getattr(survivor, 'in_vehicle', None) is not None

        # Shelter insulation bonus
        if in_shelter:
            ambient_temp += 5.0
            wind_speed = 0.0

        # Rain wetness accumulation & drying
        if is_raining and not in_shelter:
            state.clothing_wetness = min(100.0, state.clothing_wetness + 1.5)
        else:
            state.clothing_wetness = max(0.0, state.clothing_wetness - 0.5)

        # Wind chill effect
        wind_chill = (wind_speed * 0.15) if not in_shelter else 0.0
        effective_temp = ambient_temp - wind_chill - (state.clothing_wetness * 0.1)

        # Physical activity heat generation
        if is_running:
            state.physical_activity = min(100.0, state.physical_activity + 5.0)
        elif is_moving:
            state.physical_activity = min(50.0, state.physical_activity + 2.0)
        else:
            state.physical_activity = max(0.0, state.physical_activity - 3.0)

        metabolic_heat = state.physical_activity * 0.01

        # Temperature thermal equilibrium adjustment
        temp_delta = (effective_temp - state.body_temperature) * 0.002 + metabolic_heat * 0.05
        state.body_temperature = max(30.0, min(43.0, state.body_temperature + temp_delta))

        # Hypothermia & Hyperthermia Stages
        if state.body_temperature < 35.0:
            state.hypothermia_stage = 2 if state.body_temperature < 33.0 else 1
            if hasattr(survivor, 'take_damage'):
                survivor.take_damage(0.15 * state.hypothermia_stage)
        else:
            state.hypothermia_stage = 0

        if state.body_temperature > 39.0:
            state.hyperthermia_stage = 2 if state.body_temperature > 41.0 else 1
            if hasattr(survivor, 'take_damage'):
                survivor.take_damage(0.15 * state.hyperthermia_stage)
        else:
            state.hyperthermia_stage = 0

        # Wound Sterility & Sepsis Risk
        body = getattr(survivor, 'body', None)
        if body and getattr(body, 'total_bleeding', 0) > 0:
            state.sepsis_risk = min(100.0, state.sepsis_risk + 0.2)
            if state.sepsis_risk >= 70.0:
                state.sepsis_active = True
                if hasattr(survivor, 'take_damage'):
                    survivor.take_damage(0.2)
        else:
            state.sepsis_risk = max(0.0, state.sepsis_risk - 0.1)
