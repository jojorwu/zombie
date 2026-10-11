use pyo3::prelude::*;

#[pyclass]
pub struct RustElectricityUtility {
    #[pyo3(get, set)]
    pub grid_online: bool,
    #[pyo3(get, set)]
    pub cutoff_day: u32,
}

#[pymethods]
impl RustElectricityUtility {
    #[new]
    pub fn new(cutoff_day: u32) -> Self {
        RustElectricityUtility {
            grid_online: true,
            cutoff_day,
        }
    }

    pub fn check_power_status(&mut self, current_day: u32, generator_fuel: f32) -> bool {
        if current_day >= self.cutoff_day {
            self.grid_online = false;
        }

        self.grid_online || (generator_fuel > 0.0)
    }

    pub fn tick_generator(&self, mut fuel: f32, load_kw: f32) -> (f32, bool) {
        if fuel <= 0.0 {
            return (0.0, false);
        }

        let consumption = 0.001 * load_kw.max(0.5);
        fuel = (fuel - consumption).max(0.0);
        (fuel, fuel > 0.0)
    }
}
