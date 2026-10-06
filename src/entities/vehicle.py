import math
from utils.container_utility import ContainerUtility

try:
    from rust_vulkan_render import RustVehiclePhysics
    RUST_VEHICLE_AVAILABLE = True
except ImportError:
    RUST_VEHICLE_AVAILABLE = False


class VehiclePart:
    """CDDA-style modular vehicle part (engine, battery, wheels, bumper, fuel tank, cargo trunk, armor)."""
    def __init__(self, name: str, part_type: str, hp: float = 100.0, max_hp: float = 100.0):
        self.name = name
        self.part_type = part_type
        self.hp = float(hp)
        self.max_hp = float(max_hp)

    @property
    def condition_percent(self) -> float:
        return max(0.0, (self.hp / self.max_hp) * 100.0) if self.max_hp > 0 else 0.0

    def repair(self, amount: float):
        self.hp = min(self.max_hp, self.hp + amount)

    def damage(self, amount: float):
        self.hp = max(0.0, self.hp - amount)


class VehiclePhysics:
    """Configurable vehicle physics engine handling mass, velocity, acceleration, braking, friction, steering, and momentum."""
    def __init__(self, mass: float = 1200.0, max_speed: float = 0.45, acceleration: float = 0.02,
                 brake_force: float = 0.04, friction: float = 0.05, steer_rate: float = 0.1, collision_factor: float = 1.0):
        self.mass = mass
        self.max_speed = max_speed
        self.acceleration = acceleration
        self.brake_force = brake_force
        self.friction = friction
        self.steer_rate = steer_rate
        self.collision_factor = collision_factor

        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.heading_angle = 0.0

        if RUST_VEHICLE_AVAILABLE:
            self.rust_physics = RustVehiclePhysics(0.0, 0.0, mass, acceleration * 1000.0, 100.0)
        else:
            self.rust_physics = None

    @property
    def speed(self) -> float:
        return math.hypot(self.velocity_x, self.velocity_y)


class Vehicle:
    """CDDA-style modular vehicle entity with parts, customizable physics, and momentum collisions."""
    def __init__(self, x, y, fuel=100.0, max_fuel=100.0, z=0, model_type="sedan"):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.fuel = fuel
        self.max_fuel = max_fuel
        self.model_type = model_type
        self.driver = None
        self.trunk_inventory = {}
        self.trunk_capacity = 80.0
        self.noise_level = 18.0

        self.physics = VehiclePhysics()

        self.parts = {
            "engine": VehiclePart("V6 Engine", "engine", hp=100.0),
            "battery": VehiclePart("12V Battery", "battery", hp=100.0),
            "fuel_tank": VehiclePart("Gas Tank", "fuel_tank", hp=100.0),
            "wheel_fl": VehiclePart("Front Left Wheel", "wheel", hp=100.0),
            "wheel_fr": VehiclePart("Front Right Wheel", "wheel", hp=100.0),
            "wheel_rl": VehiclePart("Rear Left Wheel", "wheel", hp=100.0),
            "wheel_rr": VehiclePart("Rear Right Wheel", "wheel", hp=100.0),
            "bumper": VehiclePart("Steel Bumper", "bumper", hp=100.0),
            "seat": VehiclePart("Driver Seat", "seat", hp=100.0),
            "cargo": VehiclePart("Trunk Cargo", "cargo", hp=100.0),
        }

    @property
    def durability(self) -> float:
        if not self.parts:
            return 0.0
        return sum(p.hp for p in self.parts.values()) / len(self.parts)

    @property
    def max_durability(self) -> float:
        if not self.parts:
            return 100.0
        return sum(p.max_hp for p in self.parts.values()) / len(self.parts)

    @property
    def speed(self) -> float:
        return self.physics.speed

    @speed.setter
    def speed(self, val: float):
        pass

    def is_occupied(self):
        return self.driver is not None

    def can_start_engine(self) -> bool:
        engine = self.parts.get("engine")
        battery = self.parts.get("battery")
        if self.fuel <= 0.0:
            return False
        if engine and engine.hp <= 0.0:
            return False
        if battery and battery.hp <= 0.0:
            return False
        return True

    def update_physics(self, throttle: float = 0.0, steer: float = 0.0, brake: bool = False, world=None, noise_events=None):
        """Updates CDDA-style vehicle physics, engine operation, wheel condition, acoustic noise, and driver Z synchronization."""
        p = self.physics
        cur_sp = p.speed

        if p.rust_physics:
            p.rust_physics.x = self.x
            p.rust_physics.y = self.y
            p.rust_physics.fuel = self.fuel
            nx, ny, sp = p.rust_physics.update_physics(throttle, p.heading_angle + steer * p.steer_rate, 1.0 - p.friction)
            self.fuel = p.rust_physics.fuel

        if self.can_start_engine() and throttle != 0.0:
            engine_mult = (self.parts["engine"].condition_percent / 100.0) if "engine" in self.parts else 1.0
            wheel_cond = sum(self.parts[w].condition_percent for w in ["wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"] if w in self.parts) / 400.0

            acc = p.acceleration * throttle * engine_mult * max(0.2, wheel_cond)
            p.heading_angle += steer * p.steer_rate * (1.0 if cur_sp > 0.01 else 0.0)

            p.velocity_x += math.cos(p.heading_angle) * acc
            p.velocity_y += math.sin(p.heading_angle) * acc

            self.fuel = max(0.0, self.fuel - 0.03 * abs(throttle))

            if noise_events is not None:
                from src.entities.sensory import NoiseEvent
                noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=self.noise_level, source_type="vehicle_engine"))

        wheel_avg = sum(self.parts[w].condition_percent for w in ["wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"] if w in self.parts) / 400.0 if self.parts else 1.0

        if brake:
            effective_brake = p.brake_force * max(0.15, (1.0 / (1.0 + cur_sp * 3.0))) * max(0.3, wheel_avg)
            p.velocity_x *= max(0.0, 1.0 - effective_brake)
            p.velocity_y *= max(0.0, 1.0 - effective_brake)
        else:
            p.velocity_x *= (1.0 - p.friction * (2.0 - wheel_avg))
            p.velocity_y *= (1.0 - p.friction * (2.0 - wheel_avg))

        cur_sp = p.speed
        if cur_sp > p.max_speed:
            p.velocity_x = (p.velocity_x / cur_sp) * p.max_speed
            p.velocity_y = (p.velocity_y / cur_sp) * p.max_speed

        nx = self.x + p.velocity_x
        ny = self.y + p.velocity_y

        if world and world.is_walkable(nx, ny, self.z):
            self.x, self.y = nx, ny
            if self.driver:
                self.driver.x, self.driver.y, self.driver.z = self.x, self.y, self.z
        elif world:
            impact_damage = cur_sp * 150.0 * p.collision_factor
            if "bumper" in self.parts:
                self.parts["bumper"].damage(impact_damage)
            if "engine" in self.parts:
                self.parts["engine"].damage(impact_damage * 0.5)
            p.velocity_x = -p.velocity_x * 0.3
            p.velocity_y = -p.velocity_y * 0.3

            if self.driver:
                self.driver.x, self.driver.y, self.driver.z = self.x, self.y, self.z

    def store_in_trunk(self, item_type: str, amount: int = 1) -> bool:
        """Stores items in vehicle trunk using Project Zomboid ContainerUtility weight rules."""
        success, added = ContainerUtility.add_item_to_container(self, item_type, amount)
        return success

    def take_from_trunk(self, item_type: str, amount: int = 1) -> int:
        """Takes items from vehicle trunk using ContainerUtility."""
        return ContainerUtility.remove_item_from_container(self, item_type, amount)
