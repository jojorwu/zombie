class Vehicle:
    def __init__(self, x, y, fuel=100.0, max_fuel=100.0, z=0, model_type="sedan"):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.fuel = fuel
        self.max_fuel = max_fuel
        self.speed = 0.35
        self.model_type = model_type
        self.driver = None  # Reference to Survivor if inside
        self.trunk_inventory = {}
        self.trunk_capacity = 25
        self.durability = 100.0
        self.max_durability = 100.0
        self.noise_level = 18.0

    def is_occupied(self):
        return self.driver is not None

    def store_in_trunk(self, item_type: str, amount: int = 1) -> bool:
        current_items = sum(self.trunk_inventory.values())
        if current_items + amount <= self.trunk_capacity:
            self.trunk_inventory[item_type] = self.trunk_inventory.get(item_type, 0) + amount
            return True
        return False

    def take_from_trunk(self, item_type: str, amount: int = 1) -> int:
        available = self.trunk_inventory.get(item_type, 0)
        taken = min(available, amount)
        if taken > 0:
            self.trunk_inventory[item_type] -= taken
            if self.trunk_inventory[item_type] <= 0:
                del self.trunk_inventory[item_type]
        return taken
