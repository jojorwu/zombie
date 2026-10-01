from src.entities.vehicle import Vehicle


class VehicleType:
    SEDAN = "sedan"
    SUV_OFFROAD = "offroad_suv"
    PICKUP_TRUCK = "pickup_truck"
    VAN = "van"


class VehicleData:
    PRESETS = {
        VehicleType.SEDAN: {
            "name": "Sedan",
            "speed": 0.35,
            "max_fuel": 100.0,
            "trunk_capacity": 20,
            "durability": 100.0,
            "noise_level": 18.0
        },
        VehicleType.SUV_OFFROAD: {
            "name": "Offroad SUV",
            "speed": 0.40,
            "max_fuel": 120.0,
            "trunk_capacity": 30,
            "durability": 150.0,
            "noise_level": 22.0
        },
        VehicleType.PICKUP_TRUCK: {
            "name": "Pickup Truck",
            "speed": 0.32,
            "max_fuel": 110.0,
            "trunk_capacity": 40,
            "durability": 140.0,
            "noise_level": 20.0
        },
        VehicleType.VAN: {
            "name": "Delivery Van",
            "speed": 0.28,
            "max_fuel": 130.0,
            "trunk_capacity": 60,
            "durability": 120.0,
            "noise_level": 16.0
        },
    }


class VehicleRegistry:
    """Registry tool allowing modders and developers to easily register and instantiate custom vehicle models."""
    _custom_vehicles = {}

    @classmethod
    def register_vehicle_type(cls, model_id: str, name: str, speed: float, max_fuel: float, trunk_capacity: int, durability: float, noise_level: float = 18.0):
        cls._custom_vehicles[model_id] = {
            "name": name,
            "speed": speed,
            "max_fuel": max_fuel,
            "trunk_capacity": trunk_capacity,
            "durability": durability,
            "noise_level": noise_level
        }

    @classmethod
    def get_vehicle_info(cls, model_id: str) -> dict:
        if model_id in cls._custom_vehicles:
            return cls._custom_vehicles[model_id]
        return VehicleData.PRESETS.get(model_id, VehicleData.PRESETS[VehicleType.SEDAN])

    @classmethod
    def create_vehicle(cls, model_id: str, x: float, y: float, z: int = 0, fuel: float = None) -> Vehicle:
        info = cls.get_vehicle_info(model_id)
        if fuel is None:
            fuel = info["max_fuel"] * 0.5
        v = Vehicle(x, y, fuel=fuel, max_fuel=info["max_fuel"], z=z, model_type=model_id)
        v.speed = info["speed"]
        v.trunk_capacity = info["trunk_capacity"]
        v.durability = info["durability"]
        v.max_durability = info["durability"]
        v.noise_level = info["noise_level"]
        return v
