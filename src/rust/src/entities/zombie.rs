use pyo3::prelude::*;

/// Zombie Variant Types
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum RustZombieType {
    Standard = 0,
    Runner = 1,
    Brute = 2,
    Screamer = 3,
}

/// Native Zombie Entity Life Cycle Engine in Rust with Special Variants & Dismemberment.
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
    pub zombie_type: u8, // 0 = Standard, 1 = Runner, 2 = Brute, 3 = Screamer
    #[pyo3(get, set)]
    pub is_crawler: bool,
    #[pyo3(get, set)]
    pub shriek_cooldown: u32,
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
            zombie_type: 0,
            is_crawler: false,
            shriek_cooldown: 0,
        }
    }

    pub fn set_variant(&mut self, variant_id: u8) {
        self.zombie_type = variant_id;
        match variant_id {
            1 => {
                // Runner
                self.speed = 0.15;
                self.hp = 35.0;
            }
            2 => {
                // Brute
                self.speed = 0.05;
                self.hp = 180.0;
            }
            3 => {
                // Screamer
                self.speed = 0.09;
                self.hp = 45.0;
            }
            _ => {
                // Standard
                self.speed = 0.08;
                self.hp = 50.0;
            }
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
            let dmg = if self.zombie_type == 2 { 45.0 } else { 25.0 }; // Brute deals extra bite damage
            (true, dmg, 0.25)
        } else {
            (false, 0.0, 0.0)
        }
    }

    pub fn trigger_screamer_shriek(&mut self) -> (bool, f32) {
        if self.zombie_type == 3 && self.shriek_cooldown == 0 {
            self.shriek_cooldown = 150; // Cooldown of 150 ticks
            (true, 85.0) // Screamer shriek generates 85 dB noise
        } else {
            if self.shriek_cooldown > 0 {
                self.shriek_cooldown -= 1;
            }
            (false, 0.0)
        }
    }
}
