use pyo3::prelude::*;

/// Physical Projectile entity flying through 3D space with velocity, drag, and gravity.
#[derive(Clone, Debug)]
#[pyclass]
pub struct PhysicalProjectile {
    #[pyo3(get, set)]
    pub x: f32,
    #[pyo3(get, set)]
    pub y: f32,
    #[pyo3(get, set)]
    pub z: i32,
    #[pyo3(get, set)]
    pub vx: f32,
    #[pyo3(get, set)]
    pub vy: f32,
    #[pyo3(get, set)]
    pub damage: f32,
    #[pyo3(get, set)]
    pub lifetime_ticks: u32,
    #[pyo3(get, set)]
    pub caliber: String,
}

#[pymethods]
impl PhysicalProjectile {
    #[new]
    pub fn new(x: f32, y: f32, z: i32, vx: f32, vy: f32, damage: f32, caliber: String) -> Self {
        PhysicalProjectile {
            x,
            y,
            z,
            vx,
            vy,
            damage,
            lifetime_ticks: 60, // 60 ticks flight max
            caliber,
        }
    }

    pub fn update(&mut self) -> bool {
        if self.lifetime_ticks == 0 {
            return false;
        }
        self.x += self.vx;
        self.y += self.vy;
        // Apply slight air drag coefficient
        self.vx *= 0.98;
        self.vy *= 0.98;
        self.lifetime_ticks -= 1;
        self.lifetime_ticks > 0
    }
}

/// Native Ballistics Projectile Flight Utility in Rust.
#[pyclass]
pub struct RustBallisticsUtility;

#[pymethods]
impl RustBallisticsUtility {
    #[new]
    pub fn new() -> Self {
        RustBallisticsUtility
    }

    #[staticmethod]
    pub fn calculate_trajectory(v0_ms: f32, distance_m: f32, wind_ms: f32) -> (f32, f32, f32) {
        let time_s = distance_m / v0_ms.max(1.0);
        let bullet_drop = 0.5 * 9.81 * time_s * time_s;
        let wind_drift = 0.5 * wind_ms * time_s * time_s;
        let final_v = (v0_ms - 0.5 * time_s * 100.0).max(10.0);
        (bullet_drop, wind_drift, final_v)
    }
}

impl Default for RustBallisticsUtility {
    fn default() -> Self {
        Self::new()
    }
}

/// Native Particle System in Rust.
#[pyclass]
pub struct RustParticleSystem {
    particles: Vec<(f32, f32, i32, u32)>,
}

#[pymethods]
impl RustParticleSystem {
    #[new]
    pub fn new() -> Self {
        RustParticleSystem {
            particles: Vec::new(),
        }
    }

    pub fn spawn_particles(&mut self, x: f32, y: f32, z: i32, count: u32, lifetime: u32) {
        for _ in 0..count {
            self.particles.push((x, y, z, lifetime));
        }
    }

    pub fn tick(&mut self) -> usize {
        self.particles.retain_mut(|p| {
            if p.3 > 0 {
                p.3 -= 1;
                true
            } else {
                false
            }
        });
        self.particles.len()
    }
}

impl Default for RustParticleSystem {
    fn default() -> Self {
        Self::new()
    }
}
