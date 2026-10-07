class ElectricityUtility:
    """
    Utility module for managing municipal power grid cutoffs, fuel generators,
    light switches, and building appliance electrification.
    """
    def __init__(self, cutoff_day=7, grid_enabled=True):
        self.cutoff_day = cutoff_day
        self.grid_enabled = grid_enabled
        self.generators = []  # dicts: {x, y, z, fuel, active}
        self.switches = {}  # (x, y, z) -> active: bool

    def register_switch(self, x: int, y: int, z: int, active: bool = False):
        self.switches[(int(x), int(y), int(z))] = active

    def toggle_switch(self, x: int, y: int, z: int) -> bool:
        pos = (int(x), int(y), int(z))
        if pos in self.switches:
            self.switches[pos] = not self.switches[pos]
            return self.switches[pos]
        self.switches[pos] = True
        return True

    def is_switch_active(self, x: int, y: int, z: int) -> bool:
        return self.switches.get((int(x), int(y), int(z)), False)

    def is_power_active(self, world, x=None, y=None, z=None):
        """Checks if power grid is online or if localized generator is powered."""
        if not world.is_power_out():
            return True

        if x is not None and y is not None and z is not None:
            for gen in self.generators:
                if gen["active"] and gen["z"] == z and gen["fuel"] > 0:
                    dist_sq = (gen["x"] - x)**2 + (gen["y"] - y)**2
                    if dist_sq <= 400.0:  # 20 tile generator radius
                        return True
        return False

    def add_generator(self, x, y, z, fuel=50.0):
        gen = {"x": x, "y": y, "z": z, "fuel": fuel, "active": fuel > 0}
        self.generators.append(gen)
        return gen

    def update_generators(self):
        for gen in self.generators:
            if gen["active"]:
                gen["fuel"] = max(0.0, gen["fuel"] - 0.05)
                if gen["fuel"] <= 0:
                    gen["active"] = False
