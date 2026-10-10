use pyo3::prelude::*;

/// Native Zombie Entity Life Cycle Engine in Rust.
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustZombieEngine {
    #[pyo3(get, set)]
    pub x: f32,
    #[pyo3(get, set)]
    pub y: f32,
    #[pyo3(get, set)]
    pub z: i32,
    #[pyo3(get, set)]
    pub hp: f32,
    #[pyo3(get, set)]
    pub speed: f32,
    #[pyo3(get, set)]
    pub is_alive: bool,
}

#[pymethods]
impl RustZombieEngine {
    #[new]
    pub fn new(x: f32, y: f32, z: i32, hp: f32, speed: f32) -> Self {
        RustZombieEngine {
            x,
            y,
            z,
            hp,
            speed,
            is_alive: true,
        }
    }

    pub fn update_zombie_movement(&mut self, target_x: f32, target_y: f32, is_walkable: bool) -> (f32, f32) {
        if !self.is_alive {
            return (self.x, self.y);
        }

        let dx = target_x - self.x;
        let dy = target_y - self.y;
        let dist = (dx * dx + dy * dy).sqrt();

        if dist > 0.1 && is_walkable {
            self.x += (dx / dist) * self.speed;
            self.y += (dy / dist) * self.speed;
        }

        (self.x, self.y)
    }

    pub fn check_bite_attack(&self, survivor_x: f32, survivor_y: f32) -> (bool, f32, f32) {
        let dx = self.x - survivor_x;
        let dy = self.y - survivor_y;
        let dist_sq = dx * dx + dy * dy;

        if self.is_alive && dist_sq < 1.0 {
            (true, 25.0, 0.25)
        } else {
            (false, 0.0, 0.0)
        }
    }
}
