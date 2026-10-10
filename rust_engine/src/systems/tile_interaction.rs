use pyo3::prelude::*;

#[pyclass]
pub struct RustTileInteractionUtility;

#[pymethods]
impl RustTileInteractionUtility {
    #[new]
    pub fn new() -> Self {
        RustTileInteractionUtility
    }

    #[staticmethod]
    pub fn calculate_barricade_hp(wood_planks: u32, nails: u32) -> f32 {
        let planks = wood_planks.min(4);
        let max_nails = planks * 4;
        let actual_nails = nails.min(max_nails);

        (planks as f32 * 100.0) + (actual_nails as f32 * 25.0)
    }

    #[staticmethod]
    pub fn attempt_lockpick(lock_difficulty: u32, lockpick_skill: u32, has_bobby_pin: bool) -> (bool, bool) {
        if !has_bobby_pin {
            return (false, false);
        }

        let base_success = 0.3 + (lockpick_skill as f32 * 0.15) - (lock_difficulty as f32 * 0.1);
        let success_chance = base_success.max(0.05).min(0.95);

        let roll: f32 = rand::random();
        let success = roll < success_chance;

        let pin_break_roll: f32 = rand::random();
        let pin_broken = !success && (pin_break_roll < 0.40);

        (success, pin_broken)
    }

    #[staticmethod]
    pub fn siphon_gasoline(vehicle_fuel: f32, canister_capacity: f32, canister_current: f32) -> (f32, f32) {
        let canister_space = (canister_capacity - canister_current).max(0.0);
        let siphoned = vehicle_fuel.min(canister_space);

        let new_vehicle_fuel = vehicle_fuel - siphoned;
        let new_canister_fuel = canister_current + siphoned;

        (new_vehicle_fuel, new_canister_fuel)
    }
}
