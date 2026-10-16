use pyo3::prelude::*;

/// Native Container Utility in Rust.
#[pyclass]
pub struct RustContainerUtility;

#[pymethods]
impl RustContainerUtility {
    #[new]
    pub fn new() -> Self {
        RustContainerUtility
    }

    #[staticmethod]
    pub fn calculate_container_weight(items: Vec<(f32, u32)>, bag_reduction: f32) -> f32 {
        let total_raw: f32 = items.iter().map(|(w, qty)| w * (*qty as f32)).sum();
        total_raw * (1.0 - bag_reduction.max(0.0).min(0.9))
    }

    #[staticmethod]
    pub fn can_fit_item(current_weight: f32, capacity: f32, item_weight: f32, amount: u32) -> bool {
        current_weight + (item_weight * (amount as f32)) <= capacity
    }
}

/// Native Food Spoilage Decay Utility in Rust.
#[pyclass]
pub struct RustFoodSpoilageUtility;

#[pymethods]
impl RustFoodSpoilageUtility {
    #[new]
    pub fn new() -> Self {
        RustFoodSpoilageUtility
    }

    #[staticmethod]
    pub fn calculate_freshness_decay(
        base_freshness: f32,
        ambient_temp_c: f32,
        is_refrigerated: bool,
        is_freezer: bool,
        power_online: bool,
    ) -> f32 {
        let mut decay_mult = 1.0f32;

        if power_online {
            if is_freezer {
                decay_mult = 0.01;
            } else if is_refrigerated {
                decay_mult = 0.10;
            }
        }

        let temp_factor = ((ambient_temp_c - 10.0) / 10.0).max(0.1);
        let total_decay = 0.001 * decay_mult * temp_factor;
        (base_freshness - total_decay).max(0.0)
    }
}
