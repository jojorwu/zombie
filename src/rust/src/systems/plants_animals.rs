use pyo3::prelude::*;

#[pyclass]
pub struct RustPlantUtility;

#[pymethods]
impl RustPlantUtility {
    #[new]
    pub fn new() -> Self {
        RustPlantUtility
    }

    #[staticmethod]
    pub fn calculate_growth_progress(current_stage: u32, temperature_c: f32, rained_today: bool) -> (u32, f32) {
        if temperature_c < 2.0 {
            return (current_stage, 0.0);
        }

        let temp_mult = ((temperature_c - 10.0) / 15.0).max(0.2).min(1.5);
        let rain_bonus = if rained_today { 1.3 } else { 1.0 };

        let progress = 0.05 * temp_mult * rain_bonus;
        let mut new_stage = current_stage;

        if progress >= 0.08 && current_stage < 4 {
            new_stage += 1;
        }

        (new_stage, progress)
    }
}

#[pyclass]
pub struct RustAnimalUtility;

#[pymethods]
impl RustAnimalUtility {
    #[new]
    pub fn new() -> Self {
        RustAnimalUtility
    }

    #[staticmethod]
    pub fn calculate_flee_vector(animal_x: f32, animal_y: f32, threat_x: f32, threat_y: f32, speed: f32) -> (f32, f32) {
        let dx = animal_x - threat_x;
        let dy = animal_y - threat_y;
        let dist = (dx * dx + dy * dy).sqrt();

        if dist < 0.001 {
            return (animal_x + speed, animal_y);
        }

        (
            animal_x + (dx / dist) * speed,
            animal_y + (dy / dist) * speed,
        )
    }
}
