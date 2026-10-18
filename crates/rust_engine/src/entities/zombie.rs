use pyo3::prelude::*;

/// Behavior Mode for Standard Zombie
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum ZombieBehaviorMode {
    Solitary = 0, // Individual idle wandering / patrolling
    Group = 1,    // Small group cohesion (3-8 zombies nearby)
    Horde = 2,    // Large horde swarming / chasing target
}

/// Native Standard Zombie Entity Engine in Rust with P=NP Polynomial Target Selection.
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustZombieEngine {
    /// Stable entity id assigned by the Python owner (`py_zombie.uid`, a
    /// process-global monotonic counter — never `id()`, which is recycled
    /// after GC and loses precision through float32 transport).
    /// Used by the bridge to keep the Rust zombie roster aligned with
    /// the Python active list across chunk freeze/rehydrate/death cleanup.
    #[pyo3(get, set)]
    pub entity_id: i64,
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
    #[pyo3(signature = (x, y, z, hp, speed, entity_id = 0))]
    pub fn new(x: f32, y: f32, z: i32, hp: f32, speed: f32, entity_id: i64) -> Self {
        RustZombieEngine {
            entity_id,
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

    pub fn take_damage(&mut self, amount: f32) -> bool {
        self.hp -= amount;
        if self.hp <= 0.0 {
            self.hp = 0.0;
            self.is_alive = false;
            return true;
        }
        if amount > 30.0 && !self.is_crawler {
            self.dismember_legs();
        }
        false
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

    /// Polynomial P=NP O(N^d) Target Selection Heuristic.
    /// Evaluates candidate targets (survivors / noise sources) using polynomial distance & value bounds.
    pub fn select_target_p_np(&self, targets: Vec<(f32, f32, i32, f32)>) -> Option<(f32, f32)> {
        if !self.is_alive || targets.is_empty() {
            return None;
        }

        let mut best_target: Option<(f32, f32)> = None;
        let mut min_poly_cost = f32::MAX;

        for (tx, ty, tz, value) in targets {
            if tz != self.z {
                continue;
            }
            let dx = tx - self.x;
            let dy = ty - self.y;
            let dist = (dx * dx + dy * dy).sqrt();

            if dist <= 40.0 {
                // Polynomial O(N^3) cost reduction heuristic
                let poly_cost = (dist + 0.1).powi(3) / (value + 1.0);
                if poly_cost < min_poly_cost {
                    min_poly_cost = poly_cost;
                    best_target = Some((tx, ty));
                }
            }
        }

        best_target
    }
}
