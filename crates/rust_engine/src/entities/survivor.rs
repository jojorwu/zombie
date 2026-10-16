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
    pub stamina: f32,
    #[pyo3(get, set)]
    pub sleep: f32,
    #[pyo3(get, set)]
    pub food_items: u32,
    #[pyo3(get, set)]
    pub water_items: u32,
    #[pyo3(get, set)]
    pub medkits: u32,
    #[pyo3(get, set)]
    pub ammo: u32,
    #[pyo3(get, set)]
    pub weapon_tier: u32,
    #[pyo3(get, set)]
    pub materials: u32,
    #[pyo3(get, set)]
    pub in_vehicle: bool,
    #[pyo3(get, set)]
    pub vehicle_fuel: f32,
    #[pyo3(get, set)]
    pub score: f32,
    #[pyo3(get, set)]
    pub kills: u32,
    #[pyo3(get, set)]
    pub ticks_survived: u64,
    #[pyo3(get, set)]
    pub facing_angle: f32,
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
            stamina: 100.0,
            sleep: 100.0,
            food_items: 2,
            water_items: 2,
            medkits: 1,
            ammo: 15,
            weapon_tier: 1, // knife/bat by default
            materials: 0,
            in_vehicle: false,
            vehicle_fuel: 0.0,
            score: 0.0,
            kills: 0,
            ticks_survived: 0,
            facing_angle: 0.0,
            is_alive: true,
        }
    }

    pub fn update_vitals(&mut self, dt_ticks: u64) {
        if !self.is_alive {
            return;
        }
        let ticks_f = dt_ticks as f32;
        self.ticks_survived += dt_ticks;
        self.score += 0.05 * ticks_f;

        self.hunger = (self.hunger - 0.025 * ticks_f).max(0.0);
        self.thirst = (self.thirst - 0.035 * ticks_f).max(0.0);
        self.sleep = (self.sleep - 0.015 * ticks_f).max(0.0);

        // Auto-consume food when low
        if self.hunger < 40.0 && self.food_items > 0 {
            self.food_items -= 1;
            self.hunger = (self.hunger + 55.0).min(100.0);
            self.score += 2.0;
        }

        // Auto-consume water when low
        if self.thirst < 40.0 && self.water_items > 0 {
            self.water_items -= 1;
            self.thirst = (self.thirst + 50.0).min(100.0);
            self.score += 2.0;
        }

        // Auto-use medkit when damaged
        if self.hp < 50.0 && self.medkits > 0 {
            self.medkits -= 1;
            self.hp = (self.hp + 45.0).min(100.0);
            self.score += 3.0;
        }

        if self.hunger <= 0.0 || self.thirst <= 0.0 {
            self.hp = (self.hp - 0.15 * ticks_f).max(0.0);
            if self.hp <= 0.0 {
                self.is_alive = false;
            }
        }
    }

    pub fn calculate_fitness(&self) -> f32 {
        self.score + (self.kills as f32 * 25.0) + (self.ticks_survived as f32 * 0.1)
    }
}
