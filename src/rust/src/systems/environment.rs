use pyo3::prelude::*;

/// Native Dynamic Weather & Lighting Environment Manager in Rust.
#[pyclass]
pub struct RustEnvironmentManager {
    #[pyo3(get, set)]
    pub wind_speed: f32,
    #[pyo3(get, set)]
    pub wind_direction: f32,
    #[pyo3(get, set)]
    pub temperature: f32,
    #[pyo3(get, set)]
    pub rain_intensity: f32,
}

#[pymethods]
impl RustEnvironmentManager {
    #[new]
    pub fn new() -> Self {
        RustEnvironmentManager {
            wind_speed: 5.0,
            wind_direction: 0.0,
            temperature: 20.0,
            rain_intensity: 0.0,
        }
    }

    pub fn update_weather(&mut self, current_tick: u64, is_power_out: bool) -> (f32, f32, f32) {
        let hour = ((current_tick / 150) % 24) as f32;

        let solar_elevation = ((hour - 6.0) / 24.0 * 2.0 * std::f32::consts::PI).sin();
        let mut light_level = if solar_elevation > 0.0 {
            (solar_elevation * (std::f32::consts::PI / 2.0)).sin() * 0.85 + 0.15
        } else {
            (0.15 + solar_elevation * 0.3).max(0.08)
        };

        if is_power_out {
            light_level *= 0.75;
        }

        self.temperature = 15.0 + solar_elevation * 10.0 - self.rain_intensity * 3.0;

        (light_level, self.temperature, self.wind_speed)
    }
}
