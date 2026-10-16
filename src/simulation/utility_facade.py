from typing import Any

from src.systems.ballistics import BallisticsUtility
from src.systems.container import ContainerUtility
from src.entities.sensory import NoiseEvent
from src.systems.sound import SoundUtility
from src.systems.vehicle import VehiclePhysicsUtility
from src.systems.tile_interaction import TileInteractionUtility

try:
    from rust_engine import (
        RustAcousticSystem,
        RustBallisticsUtility,
        RustContainerUtility,
        RustElectricityUtility,
        RustTileInteractionUtility,
        RustVehiclePhysics,
    )
    RUST_UTILITIES_AVAILABLE = True
except ImportError:
    RUST_UTILITIES_AVAILABLE = False


class EngineUtilityFacade:
    """
    Unified Engine Utility Facade providing a clean, single-point API
    for container operations, tile interactions, acoustics, ballistics,
    vehicle physics, and power grid status.
    """

    # --- Container & Inventory Operations ---
    @staticmethod
    def get_item_weight(item_type: str) -> float:
        return ContainerUtility.get_item_weight(item_type)

    @staticmethod
    def get_container_capacity(container: Any) -> float:
        return ContainerUtility.get_container_capacity(container)

    @staticmethod
    def get_container_weight(container: Any) -> float:
        return ContainerUtility.get_container_weight(container)

    @staticmethod
    def transfer_item(source: Any, target: Any, item_type: str, amount: int = 1) -> int:
        """Transfers items between any source and target containers atomically."""
        return ContainerUtility.transfer_item(source, target, item_type, amount)

    @staticmethod
    def batch_transfer_items(transfers: list[tuple[Any, Any, str, int]]) -> list[int]:
        """Executes a list of (source, target, item_type, amount) transfers in batch."""
        results = []
        for src, tgt, itype, amt in transfers:
            results.append(ContainerUtility.transfer_item(src, tgt, itype, amt))
        return results

    @staticmethod
    def add_item_to_container(container: Any, item_type: str, amount: int = 1) -> tuple[bool, int]:
        return ContainerUtility.add_item_to_container(container, item_type, amount)

    @staticmethod
    def remove_item_from_container(container: Any, item_type: str, amount: int = 1) -> int:
        return ContainerUtility.remove_item_from_container(container, item_type, amount)

    # --- World & Tile Interactions ---
    @staticmethod
    def siphon_fuel_from_pump(world: Any, x: int, y: int, z: int, target_inventory: dict[str, int]) -> tuple[bool, int]:
        """Siphons fuel from gas pump tile into target inventory."""
        return TileInteractionUtility.siphon_fuel_from_pump(world, x, y, z, target_inventory)

    @staticmethod
    def interact_with_door(world: Any, x: int, y: int, z: int) -> bool:
        """Toggles door open/closed state on specified grid tile."""
        return TileInteractionUtility.interact_with_door(world, x, y, z)

    @staticmethod
    def barricade_tile(world: Any, x: int, y: int, z: int, inventory: dict[str, int]) -> bool:
        """Barricades door or window tile using wood/planks from inventory."""
        return TileInteractionUtility.barricade_window_or_door(world, x, y, z, inventory)

    @staticmethod
    def lockpick_door(world: Any, x: int, y: int, z: int, inventory: dict[str, int]) -> bool:
        """Attempts to lockpick locked door tile using lockpicks from inventory."""
        return TileInteractionUtility.lockpick_door(world, x, y, z, inventory)

    # --- Acoustics & Ballistics ---
    @staticmethod
    def create_noise_event(x: float, y: float, z: int, source_type: str = "general", volume: float | None = None) -> NoiseEvent:
        """Creates a NoiseEvent using SoundUtility / RustAcousticSystem sound profile SPL scaling."""
        if volume is None:
            if RUST_UTILITIES_AVAILABLE:
                db_spl = RustAcousticSystem.get_source_db_spl(source_type)
            else:
                profile = SoundUtility.SOUND_PROFILES.get(source_type, {})
                db_spl = profile.get("db_spl", 50.0)
            volume = db_spl / 5.0
        return NoiseEvent(x, y, z, volume=volume, source_type=source_type)

    @staticmethod
    def batch_create_noises(noises_data: list[tuple[float, float, int, str, float | None]]) -> list[NoiseEvent]:
        """Batched creation of noise events."""
        return [
            EngineUtilityFacade.create_noise_event(x, y, z, source_type=stype, volume=vol)
            for x, y, z, stype, vol in noises_data
        ]

    @staticmethod
    def calculate_ballistics(caliber: str, distance_m: float = 100.0) -> dict[str, float]:
        """Calculates ballistics trajectory drop, kinetic energy, and penetration via Rust Ballistics Utility."""
        if RUST_UTILITIES_AVAILABLE:
            v0 = BallisticsUtility.AMMO_PROFILES.get(caliber, {}).get("muzzle_velocity", 380.0)
            drop, drift, final_v = RustBallisticsUtility.calculate_trajectory(v0, distance_m, 0.0)
            return {
                "drop_m": drop,
                "wind_drift_m": drift,
                "velocity_m_s": final_v,
                "kinetic_energy_j": 0.5 * 0.008 * (final_v ** 2),
            }
        return BallisticsUtility.calculate_trajectory(caliber, distance_m=distance_m)

    # --- Vehicle Physics & Power Grid ---
    @staticmethod
    def customize_vehicle_physics(vehicle: Any, mass: float = 1200.0, max_speed: float = 0.45) -> None:
        """Configures vehicle physics parameters via VehiclePhysicsUtility."""
        VehiclePhysicsUtility.customize_physics(vehicle, mass=mass, max_speed=max_speed)

    @staticmethod
    def is_electricity_active(electricity_utility: Any, current_day: float) -> bool:
        """Checks power grid active status for given simulation day."""
        if electricity_utility:
            return electricity_utility.is_electricity_active(current_day)
        return True
