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
            "noise_level": 18.0,
            "physics": {"mass": 1200.0, "max_speed": 0.45, "acceleration": 0.02, "brake_force": 0.04, "friction": 0.05, "steer_rate": 0.1, "collision_factor": 1.0}
        },
        VehicleType.SUV_OFFROAD: {
            "name": "Offroad SUV",
            "speed": 0.40,
            "max_fuel": 120.0,
            "trunk_capacity": 30,
            "durability": 150.0,
            "noise_level": 22.0,
            "physics": {"mass": 1800.0, "max_speed": 0.40, "acceleration": 0.025, "brake_force": 0.05, "friction": 0.04, "steer_rate": 0.08, "collision_factor": 1.3}
        },
        VehicleType.PICKUP_TRUCK: {
            "name": "Pickup Truck",
            "speed": 0.32,
            "max_fuel": 110.0,
            "trunk_capacity": 40,
            "durability": 140.0,
            "noise_level": 20.0,
            "physics": {"mass": 1600.0, "max_speed": 0.38, "acceleration": 0.018, "brake_force": 0.04, "friction": 0.05, "steer_rate": 0.09, "collision_factor": 1.2}
        },
        VehicleType.VAN: {
            "name": "Delivery Van",
            "speed": 0.28,
            "max_fuel": 130.0,
            "trunk_capacity": 60,
            "durability": 120.0,
            "noise_level": 16.0,
            "physics": {"mass": 2100.0, "max_speed": 0.32, "acceleration": 0.015, "brake_force": 0.035, "friction": 0.06, "steer_rate": 0.07, "collision_factor": 1.5}
        },
    }


class VehiclePhysicsUtility:
    """Utility allowing developers and modders to inspect, configure, and fine-tune vehicle physics parameters on the fly."""
    @staticmethod
    def customize_physics(vehicle: Vehicle, mass: float = None, max_speed: float = None, acceleration: float = None,
                          brake_force: float = None, friction: float = None, steer_rate: float = None, collision_factor: float = None):
        p = vehicle.physics
        if mass is not None:
            p.mass = mass
        if max_speed is not None:
            p.max_speed = max_speed
        if acceleration is not None:
            p.acceleration = acceleration
        if brake_force is not None:
            p.brake_force = brake_force
        if friction is not None:
            p.friction = friction
        if steer_rate is not None:
            p.steer_rate = steer_rate
        if collision_factor is not None:
            p.collision_factor = collision_factor


class VehicleRegistry:
    """Registry tool allowing modders and developers to easily register and instantiate custom vehicle models with custom physics."""
    _custom_vehicles = {}

    @classmethod
    def register_vehicle_type(cls, model_id: str, name: str, speed: float, max_fuel: float, trunk_capacity: int, durability: float, noise_level: float = 18.0, physics_cfg: dict = None):
        cls._custom_vehicles[model_id] = {
            "name": name,
            "speed": speed,
            "max_fuel": max_fuel,
            "trunk_capacity": trunk_capacity,
            "durability": durability,
            "noise_level": noise_level,
            "physics": physics_cfg or {"mass": 1200.0, "max_speed": speed, "acceleration": 0.02, "brake_force": 0.04, "friction": 0.05, "steer_rate": 0.1, "collision_factor": 1.0}
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
        v.trunk_capacity = info["trunk_capacity"]
        v.noise_level = info["noise_level"]

        phys_cfg = info.get("physics", {})
        VehiclePhysicsUtility.customize_physics(v, **phys_cfg)

        return v
