class Vehicle:
    def __init__(self, x, y, fuel=100.0, max_fuel=100.0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.fuel = fuel
        self.max_fuel = max_fuel
        self.speed = 0.3
        self.driver = None  # Reference to Survivor if inside

    def is_occupied(self):
        return self.driver is not None
