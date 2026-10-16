try:
    from rust_engine import RustElectricityUtility
    RUST_ELEC_AVAILABLE = True
except ImportError:
    RUST_ELEC_AVAILABLE = False


class ElectricityUtility:
    def __init__(self, cutoff_day: int = 7, grid_enabled: bool = True):
        self.cutoff_day = cutoff_day
        self.grid_enabled = grid_enabled
        # Gasoline power generators tracking: (x, y, z) -> fuel_units (float)
        self.active_generators = {}

    def add_generator(self, x: int, y: int, z: int, fuel_amount: float = 100.0) -> None:
        self.active_generators[(int(x), int(y), int(z))] = float(fuel_amount)

    def refuel_generator(self, x: int, y: int, z: int, fuel_amount: float) -> bool:
        pos = (int(x), int(y), int(z))
        if pos in self.active_generators:
            self.active_generators[pos] += float(fuel_amount)
            return True
        return False

    def is_power_active(self, current_day: int, x: int = 0, y: int = 0, z: int = 0) -> bool:
        if self.grid_enabled and current_day < self.cutoff_day:
            return True
        # Check local generator coverage within 12 tile radius
        pos_target = (int(x), int(y), int(z))
        for (gx, gy, gz), fuel in self.active_generators.items():
            if gz == pos_target[2] and fuel > 0.0:
                if abs(gx - pos_target[0]) <= 12 and abs(gy - pos_target[1]) <= 12:
                    return True
        return False

    def update_generators(self, decay_rate: float = 0.05) -> None:
        """Consumes generator fuel on each tick."""
        depleted = []
        for pos, fuel in self.active_generators.items():
            new_fuel = fuel - decay_rate
            if new_fuel <= 0.0:
                depleted.append(pos)
            else:
                self.active_generators[pos] = new_fuel
        for pos in depleted:
            self.active_generators[pos] = 0.0

    def is_electricity_active(self, current_day: float) -> bool:
        """Backwards-compatible alias used by EngineUtilityFacade.

        Returns True while the city power grid is still online (before the
        configured cutoff day) or when at least one generator has fuel left.
        """
        if self.grid_enabled and current_day < self.cutoff_day:
            return True
        return any(fuel > 0.0 for fuel in self.active_generators.values())
