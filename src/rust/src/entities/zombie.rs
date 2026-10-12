use pyo3::prelude::*;

/// Behavior Mode for Standard Zombie
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum ZombieBehaviorMode {
    Solitary = 0, // Individual idle wandering / patrolling
    Group = 1,    // Small group cohesion (3-8 zombies nearby)
    Horde = 2,    // Large horde swarming / chasing target
}

/// Native Standard Zombie Entity Engine in Rust.
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
    #[pyo3(get, set)]
    pub is_crawler: bool,
    #[pyo3(get, set)]
    pub behavior_mode: u8, // 0 = Solitary, 1 = Group, 2 = Horde
    #[pyo3(get, set)]
    pub wander_angle: f32,
}

#[pymethods]
impl RustZombieEngine {
    #[new]
    pub fn new(x: f32, y: f32, z: i32, hp: f32, speed: f32) -> Self {
        RustZombieEngine {
            x,
            y,
            z,
            hp: if hp > 0.0 { hp } else { 50.0 },
            speed: if speed > 0.0 { speed } else { 0.08 },
            is_alive: true,
            is_crawler: false,
            behavior_mode: 0,
            wander_angle: (x * 12.3 + y * 45.6) % std::f32::consts::TAU,
        }
    }

    pub fn dismember_legs(&mut self) {
        self.is_crawler = true;
        self.speed *= 0.4; // 60% speed penalty for crawling
    }

    pub fn update_zombie_movement(&mut self, target_x: f32, target_y: f32, is_walkable: bool) -> (f32, f32) {
        if !self.is_alive {
            return (self.x, self.y);
        }

        let dx = target_x - self.x;
        let dy = target_y - self.y;
        let dist = (dx * dx + dy * dy).sqrt();

        if dist > 0.1 && is_walkable {
            let eff_speed = if self.is_crawler { self.speed * 0.4 } else { self.speed };
            self.x += (dx / dist) * eff_speed;
            self.y += (dy / dist) * eff_speed;
        }

        (self.x, self.y)
    }

    pub fn check_bite_attack(&self, survivor_x: f32, survivor_y: f32) -> (bool, f32, f32) {
        let dx = self.x - survivor_x;
        let dy = self.y - survivor_y;
        let dist_sq = dx * dx + dy * dy;

        if self.is_alive && dist_sq < 1.0 {
            (true, 25.0, 0.25) // Standard bite attack
        } else {
            (false, 0.0, 0.0)
        }
    }
}
