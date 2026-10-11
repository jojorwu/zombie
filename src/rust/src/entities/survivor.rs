use pyo3::prelude::*;

#[pyclass]
#[derive(Clone, Debug)]
pub struct RustSurvivorEntity {
    #[pyo3(get, set)]
    pub id: usize,
    #[pyo3(get, set)]
    pub x: f32,
    #[pyo3(get, set)]
    pub y: f32,
    #[pyo3(get, set)]
    pub z: i32,
    #[pyo3(get, set)]
    pub hp: f32,
    #[pyo3(get, set)]
    pub hunger: f32,
    #[pyo3(get, set)]
    pub thirst: f32,
    #[pyo3(get, set)]
    pub is_alive: bool,
}

#[pymethods]
impl RustSurvivorEntity {
    #[new]
    pub fn new(id: usize, x: f32, y: f32, z: i32) -> Self {
        RustSurvivorEntity {
            id,
            x,
            y,
            z,
            hp: 100.0,
            hunger: 100.0,
            thirst: 100.0,
            is_alive: true,
        }
    }

    pub fn update_vitals(&mut self, dt_ticks: u64) {
        if !self.is_alive {
            return;
        }
        let ticks_f = dt_ticks as f32;
        self.hunger = (self.hunger - 0.025 * ticks_f).max(0.0);
        self.thirst = (self.thirst - 0.035 * ticks_f).max(0.0);

        if self.hunger <= 0.0 || self.thirst <= 0.0 {
            self.hp = (self.hp - 0.1 * ticks_f).max(0.0);
            if self.hp <= 0.0 {
                self.is_alive = false;
            }
        }
    }
}
