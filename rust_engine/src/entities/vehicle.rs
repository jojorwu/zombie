use pyo3::prelude::*;
use crate::world::RustWorldGrid;

/// Native Vehicle Physics & High-Momentum Wall Breaching in Rust.
#[pyclass]
pub struct RustVehiclePhysics {
    #[pyo3(get, set)]
    pub x: f32,
    #[pyo3(get, set)]
    pub y: f32,
    #[pyo3(get, set)]
    pub vx: f32,
    #[pyo3(get, set)]
    pub vy: f32,
    #[pyo3(get, set)]
    pub mass: f32,
    #[pyo3(get, set)]
    pub fuel: f32,
    #[pyo3(get, set)]
    pub engine_power: f32,
}

#[pymethods]
impl RustVehiclePhysics {
    #[new]
    pub fn new(x: f32, y: f32, mass: f32, engine_power: f32, fuel: f32) -> Self {
        RustVehiclePhysics {
            x,
            y,
            vx: 0.0,
            vy: 0.0,
            mass,
            fuel,
            engine_power,
        }
    }

    pub fn update_physics(&mut self, throttle: f32, steering_angle: f32, friction: f32) -> (f32, f32, f32) {
        if self.fuel > 0.0 && throttle.abs() > 0.01 {
            let force = throttle * self.engine_power / self.mass.max(100.0);
            self.vx += steering_angle.cos() * force;
            self.vy += steering_angle.sin() * force;
            self.fuel = (self.fuel - throttle.abs() * 0.005).max(0.0);
        }

        self.vx *= friction;
        self.vy *= friction;

        self.x += self.vx;
        self.y += self.vy;

        let speed = (self.vx * self.vx + self.vy * self.vy).sqrt();
        (self.x, self.y, speed)
    }

    pub fn check_zombie_collision(&mut self, zombie_x: f32, zombie_y: f32) -> (bool, f32) {
        let dx = self.x - zombie_x;
        let dy = self.y - zombie_y;
        let dist_sq = dx * dx + dy * dy;
        let speed = (self.vx * self.vx + self.vy * self.vy).sqrt();

        if dist_sq < 1.44 && speed > 0.05 {
            let damage = speed * 250.0 * (self.mass / 1000.0);
            self.vx *= 0.85;
            self.vy *= 0.85;
            (true, damage)
        } else {
            (false, 0.0)
        }
    }

    /// Checks high-momentum vehicle wall/door breaching on world grid.
    /// If vehicle momentum >= 120.0, breaches walls and locked doors, replacing them with floor tiles.
    pub fn check_wall_breach(&mut self, grid: &mut RustWorldGrid, z: i32) -> (bool, i32, i32) {
        let speed = (self.vx * self.vx + self.vy * self.vy).sqrt();
        let momentum = self.mass * speed;

        let tx = (self.x + self.vx) as i32;
        let ty = (self.y + self.vy) as i32;

        let tile = grid.get_tile(tx, ty, z);
        // Breachable tiles: BUILDING_WALL (2), DOOR (7), WINDOW (49), SANDBAG (62)
        if matches!(tile, 2 | 7 | 49 | 62) {
            if momentum >= 120.0 {
                // Breach wall/obstacle, turn into floor (3)
                grid.set_tile(tx, ty, z, 3);
                // Apply momentum dampening on impact
                self.vx *= 0.4;
                self.vy *= 0.4;
                return (true, tx, ty);
            } else {
                // Insufficient momentum: bounce back
                self.vx = -self.vx * 0.3;
                self.vy = -self.vy * 0.3;
            }
        }
        (false, 0, 0)
    }
}
