use pyo3::prelude::*;

#[pyclass]
pub struct RustItemStateUtility;

#[pymethods]
impl RustItemStateUtility {
    #[new]
    pub fn new() -> Self {
        RustItemStateUtility
    }

    #[staticmethod]
    pub fn calculate_durability_loss(base_durability: f32, metal_quality_tier: u32, hits_count: u32) -> f32 {
        let quality_multiplier = match metal_quality_tier {
            0 => 2.0, // Scrap
            1 => 1.0, // Iron
            2 => 0.6, // Steel
            3 => 0.3, // Hardened Steel
            _ => 0.1, // Titanium
        };

        let loss = (hits_count as f32 * 0.5) * quality_multiplier;
        (base_durability - loss).max(0.0)
    }

    #[staticmethod]
    pub fn calculate_metal_purity(scrap_iron: f32, steel_ingots: f32) -> f32 {
        let total = scrap_iron + steel_ingots;
        if total <= 0.0 {
            return 0.0;
        }
        ((steel_ingots * 1.0 + scrap_iron * 0.4) / total) * 100.0
    }
}
