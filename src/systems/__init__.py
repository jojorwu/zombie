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

# NOTE: all re-exports are resolved lazily via __getattr__ below.  Eager
# imports here created circular-import chains such as:
#   src.systems.__init__ -> src.systems.container -> src.entities.item ->
#   src.entities.__init__ -> src.entities.survivor.looting ->
#   src.systems.container (partially initialized)  => ImportError
# Keeping the barrel lazy means importing any leaf module never drags the
# whole graph in, regardless of entry point.
_lazy = {
    # Light systems (no src.world dependency)
    "SoundUtility": "src.systems.sound",
    "BallisticsUtility": "src.systems.ballistics",
    "MaterialResistance": "src.systems.ballistics",
    "ElectricityUtility": "src.systems.electricity",
    "VehicleType": "src.systems.vehicle",
    "VehicleData": "src.systems.vehicle",
    "VehiclePhysicsUtility": "src.systems.vehicle",
    "VehicleRegistry": "src.systems.vehicle",
    "FoodSpoilageUtility": "src.systems.food_spoilage",
    "ItemCategory": "src.systems.container",
    "ITEM_WEIGHTS": "src.systems.container",
    "ContainerUtility": "src.systems.container",
    "ItemConditionState": "src.systems.item_state",
    "ItemStateUtility": "src.systems.item_state",
    # Heavy imports (depend on src.world)
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
