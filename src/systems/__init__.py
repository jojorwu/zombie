"""
Simulation Systems Module.
Exposes high-performance native Rust systems and Python interfaces.
"""
try:
    from rust_engine import (
        PhysicalProjectile,
        RustAcousticSystem,
        RustBallisticsUtility,
        RustElectricityUtility,
        RustTileInteractionUtility,
        compute_a_star_3d_path,
        compute_zombie_flock_steering,
    )
    RUST_SYSTEMS_AVAILABLE = True
except ImportError:
    RUST_SYSTEMS_AVAILABLE = False
    PhysicalProjectile = None
    RustAcousticSystem = None
    RustBallisticsUtility = None
    RustElectricityUtility = None
    RustTileInteractionUtility = None
    compute_a_star_3d_path = None
    compute_zombie_flock_steering = None

# Light imports (no src.world dependency)
from src.systems.sound import SoundUtility
from src.systems.ballistics import BallisticsUtility, MaterialResistance
from src.systems.electricity import ElectricityUtility
from src.systems.vehicle import VehicleType, VehicleData, VehiclePhysicsUtility, VehicleRegistry
from src.systems.food_spoilage import FoodSpoilageUtility
from src.systems.container import ItemCategory, ITEM_WEIGHTS, ContainerUtility
from src.systems.item_state import ItemConditionState, ItemStateUtility

# Heavy imports (depend on src.world) — imported lazily via __getattr__
_lazy = {
    "PathfindingUtility": "src.systems.pathfinding",
    "TileInteractionUtility": "src.systems.tile_interaction",
}


def __getattr__(name):
    if name in _lazy:
        import importlib
        mod = importlib.import_module(_lazy[name])
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "PhysicalProjectile",
    "RustAcousticSystem",
    "RustBallisticsUtility",
    "RustElectricityUtility",
    "RustTileInteractionUtility",
    "compute_a_star_3d_path",
    "compute_zombie_flock_steering",
    "BallisticsUtility",
    "MaterialResistance",
    "SoundUtility",
    "ElectricityUtility",
    "VehicleType",
    "VehicleData",
    "VehiclePhysicsUtility",
    "VehicleRegistry",
    "FoodSpoilageUtility",
    "ItemCategory",
    "ITEM_WEIGHTS",
    "ContainerUtility",
    "ItemConditionState",
    "ItemStateUtility",
    "PathfindingUtility",
    "TileInteractionUtility",
    "RUST_SYSTEMS_AVAILABLE",
]
