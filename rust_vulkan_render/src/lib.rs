use pyo3::prelude::*;
use pyo3::types::PyBytes;
use numpy::{PyArray1, PyReadonlyArray1, PyReadonlyArray3, IntoPyArray};
use mlua::{Lua, Result as LuaResult};
use std::collections::{BinaryHeap, HashMap, HashSet};
use std::cmp::Ordering;

#[pyclass]
pub struct VulkanTileRenderer {
    map_draw_width: u32,
    map_draw_height: u32,
    tile_size: u32,
    pixel_width: usize,
    pixel_height: usize,
}

#[pymethods]
impl VulkanTileRenderer {
    #[new]
    fn new(map_draw_width: u32, map_draw_height: u32, tile_size: u32) -> Self {
        let pixel_width = (map_draw_width * tile_size) as usize;
        let pixel_height = (map_draw_height * tile_size) as usize;
        VulkanTileRenderer {
            map_draw_width,
            map_draw_height,
            tile_size,
            pixel_width,
            pixel_height,
        }
    }

    fn render_viewport_bytes<'py>(
        &self,
        py: Python<'py>,
        grid_slice: &[u8],
        building_override: &[u8],
        tile_palette: Vec<(u8, u8, u8)>,
        light: f32,
        fog_mask: Option<&[u8]>,
    ) -> &'py PyBytes {
        let buffer_size = self.pixel_width * self.pixel_height * 4;
        let mut buffer = vec![255u8; buffer_size];

        let ts = self.tile_size as usize;
        let mw = self.map_draw_width as usize;
        let mh = self.map_draw_height as usize;
        let stride = self.pixel_width * 4;

        let has_building = !building_override.is_empty();
        let has_fog = fog_mask.is_some();
        let fog_buf = fog_mask.unwrap_or(&[]);

        for ty in 0..mh {
            let row_offset_tiles = ty * mw;
            let py_start = ty * ts;

            for tx in 0..mw {
                let tile_idx = row_offset_tiles + tx;
                let px_start = tx * ts;

                let is_visible = if has_fog {
                    fog_buf.get(tile_idx).copied().unwrap_or(1) > 0
                } else {
                    true
                };

                let (r_base, g_base, b_base) = if !is_visible {
                    (10u8, 10u8, 10u8)
                } else {
                    let mut r = 0u8;
                    let mut g = 0u8;
                    let mut b = 0u8;
                    let mut override_found = false;

                    if has_building {
                        let b_idx = tile_idx * 3;
                        if b_idx + 2 < building_override.len() {
                            let br = building_override[b_idx];
                            let bg = building_override[b_idx + 1];
                            let bb = building_override[b_idx + 2];
                            if br > 0 || bg > 0 || bb > 0 {
                                r = br;
                                g = bg;
                                b = bb;
                                override_found = true;
                            }
                        }
                    }

                    if !override_found {
                        let t_type = grid_slice.get(tile_idx).copied().unwrap_or(0) as usize;
                        if t_type < tile_palette.len() {
                            let p = tile_palette[t_type];
                            r = p.0;
                            g = p.1;
                            b = p.2;
                        } else {
                            r = 50;
                            g = 50;
                            b = 50;
                        }
                    }

                    (
                        (r as f32 * light) as u8,
                        (g as f32 * light) as u8,
                        (b as f32 * light) as u8,
                    )
                };

                for dy in 0..ts {
                    let line_start = (py_start + dy) * stride + px_start * 4;
                    for dx in 0..ts {
                        let px_idx = line_start + dx * 4;
                        if px_idx + 3 < buffer.len() {
                            buffer[px_idx] = r_base;
                            buffer[px_idx + 1] = g_base;
                            buffer[px_idx + 2] = b_base;
                            buffer[px_idx + 3] = 255;
                        }
                    }
                }
            }
        }

        PyBytes::new(py, &buffer)
    }

    fn render_grid_buffer(&self, grid: Vec<i32>, light: f32) -> Vec<u8> {
        let num_pixels = (self.pixel_width * self.pixel_height * 4) as usize;
        let mut buffer = vec![20u8; num_pixels];

        for (idx, &tile) in grid.iter().enumerate() {
            let x = (idx % self.map_draw_width as usize) as u32;
            let y = (idx / self.map_draw_width as usize) as u32;

            let (r, g, b) = match tile {
                0 => (34u8, 139u8, 34u8),
                1 => (105u8, 105u8, 105u8),
                2 => (100u8, 50u8, 20u8),
                3 => (210u8, 180u8, 140u8),
                _ => (50u8, 50u8, 50u8),
            };

            let px = (y as usize * self.map_draw_width as usize + x as usize) * 4;
            if px + 3 < buffer.len() {
                buffer[px] = (r as f32 * light) as u8;
                buffer[px + 1] = (g as f32 * light) as u8;
                buffer[px + 2] = (b as f32 * light) as u8;
                buffer[px + 3] = 255;
            }
        }

        buffer
    }
}

/// 1. Native Vehicle Physics in Rust.
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
    fn new(x: f32, y: f32, mass: f32, engine_power: f32, fuel: f32) -> Self {
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

    fn update_physics(&mut self, throttle: f32, steering_angle: f32, friction: f32) -> (f32, f32, f32) {
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

    fn check_zombie_collision(&mut self, zombie_x: f32, zombie_y: f32) -> (bool, f32) {
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
}

/// 2. Native Acoustic Decibel Noise Propagation Engine in Rust.
#[pyclass]
pub struct RustAcousticSystem;

#[pymethods]
impl RustAcousticSystem {
    #[new]
    fn new() -> Self {
        RustAcousticSystem
    }

    #[staticmethod]
    fn propagate_noise_decibels(
        source_x: f32,
        source_y: f32,
        source_z: i32,
        volume_db: f32,
        target_x: f32,
        target_y: f32,
        target_z: i32,
    ) -> f32 {
        if (source_z - target_z).abs() > 1 {
            return 0.0;
        }

        let dx = target_x - source_x;
        let dy = target_y - source_y;
        let dist = (dx * dx + dy * dy).sqrt() + (source_z - target_z).abs() as f32 * 2.0;

        if dist <= 0.001 {
            return volume_db;
        }

        let attenuated = volume_db - 20.0 * dist.log10().max(0.0);
        attenuated.max(0.0)
    }
}

/// 3. Native Anatomical Health & Damage System in Rust.
#[pyclass]
pub struct RustAnatomicalHealth {
    #[pyo3(get, set)]
    pub head: f32,
    #[pyo3(get, set)]
    pub torso: f32,
    #[pyo3(get, set)]
    pub left_arm: f32,
    #[pyo3(get, set)]
    pub right_arm: f32,
    #[pyo3(get, set)]
    pub left_leg: f32,
    #[pyo3(get, set)]
    pub right_leg: f32,
    #[pyo3(get, set)]
    pub bleeding_rate: f32,
}

#[pymethods]
impl RustAnatomicalHealth {
    #[new]
    #[pyo3(signature = (head=35.0, torso=100.0, left_arm=40.0, right_arm=40.0, left_leg=45.0, right_leg=45.0))]
    fn new(head: f32, torso: f32, left_arm: f32, right_arm: f32, left_leg: f32, right_leg: f32) -> Self {
        RustAnatomicalHealth {
            head,
            torso,
            left_arm,
            right_arm,
            left_leg,
            right_leg,
            bleeding_rate: 0.0,
        }
    }

    fn apply_targeted_damage(&mut self, part: &str, raw_damage: f32, armor_reduction: f32) -> f32 {
        let actual_damage = (raw_damage * (1.0 - armor_reduction)).max(0.0);

        match part {
            "head" => {
                self.head = (self.head - actual_damage).max(0.0);
                self.bleeding_rate += actual_damage * 0.05;
            }
            "torso" => {
                self.torso = (self.torso - actual_damage).max(0.0);
                self.bleeding_rate += actual_damage * 0.03;
            }
            "left_arm" => self.left_arm = (self.left_arm - actual_damage).max(0.0),
            "right_arm" => self.right_arm = (self.right_arm - actual_damage).max(0.0),
            "left_leg" => {
                self.left_leg = (self.left_leg - actual_damage).max(0.0);
                self.bleeding_rate += actual_damage * 0.02;
            }
            "right_leg" => {
                self.right_leg = (self.right_leg - actual_damage).max(0.0);
                self.bleeding_rate += actual_damage * 0.02;
            }
            _ => {
                self.torso = (self.torso - actual_damage).max(0.0);
            }
        }

        actual_damage
    }

    fn tick_bleeding(&mut self) -> f32 {
        if self.bleeding_rate > 0.0 {
            let bleed_damage = self.bleeding_rate * 0.1;
            self.torso = (self.torso - bleed_damage).max(0.0);
            bleed_damage
        } else {
            0.0
        }
    }

    fn get_total_health(&self) -> f32 {
        let max_total = 35.0 * 0.3 + 100.0 * 0.4 + (40.0 + 40.0 + 45.0 + 45.0) * 0.075;
        let cur_total = self.head * 0.3 + self.torso * 0.4 + (self.left_arm + self.right_arm + self.left_leg + self.right_leg) * 0.075;
        ((cur_total / max_total) * 100.0).max(0.0).min(100.0)
    }

    fn get_speed_multiplier(&self) -> f32 {
        let min_leg = self.left_leg.min(self.right_leg);
        if min_leg < 30.0 {
            0.4
        } else if min_leg < 60.0 {
            0.7
        } else {
            1.0
        }
    }
}

/// 4. Native Dynamic Weather & Lighting Environment Manager in Rust.
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
    fn new() -> Self {
        RustEnvironmentManager {
            wind_speed: 5.0,
            wind_direction: 0.0,
            temperature: 20.0,
            rain_intensity: 0.0,
        }
    }

    fn update_weather(&mut self, current_tick: u64, is_power_out: bool) -> (f32, f32, f32) {
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

/// 5. Native Zombie Entity Life Cycle Engine in Rust.
#[pyclass]
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
    fn new(x: f32, y: f32, z: i32, hp: f32, speed: f32) -> Self {
        RustZombieEngine {
            x,
            y,
            z,
            hp,
            speed,
            is_alive: true,
        }
    }

    fn update_zombie_movement(&mut self, target_x: f32, target_y: f32, is_walkable: bool) -> (f32, f32) {
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

    fn check_bite_attack(&self, survivor_x: f32, survivor_y: f32) -> (bool, f32, f32) {
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

/// 6. Native Spatial Hash Cell Grid in Rust.
#[pyclass]
pub struct RustSpatialGrid {
    cell_size: f32,
    grid: HashMap<(i32, i32, i32), Vec<usize>>,
}

#[pymethods]
impl RustSpatialGrid {
    #[new]
    fn new(cell_size: f32) -> Self {
        RustSpatialGrid {
            cell_size,
            grid: HashMap::new(),
        }
    }

    fn clear(&mut self) {
        self.grid.clear();
    }

    fn insert_entity(&mut self, entity_id: usize, x: f32, y: f32, z: i32) {
        let cx = (x / self.cell_size).floor() as i32;
        let cy = (y / self.cell_size).floor() as i32;
        self.grid.entry((cx, cy, z)).or_insert_with(Vec::new).push(entity_id);
    }

    fn get_nearby_entities(&self, x: f32, y: f32, z: i32) -> Vec<usize> {
        let cx = (x / self.cell_size).floor() as i32;
        let cy = (y / self.cell_size).floor() as i32;
        let mut nearby = Vec::new();

        for dx in -1..=1 {
            for dy in -1..=1 {
                if let Some(list) = self.grid.get(&(cx + dx, cy + dy, z)) {
                    nearby.extend_from_slice(list);
                }
            }
        }
        nearby
    }
}

/// 7. Native Container Utility in Rust.
#[pyclass]
pub struct RustContainerUtility;

#[pymethods]
impl RustContainerUtility {
    #[new]
    fn new() -> Self {
        RustContainerUtility
    }

    #[staticmethod]
    fn calculate_container_weight(items: Vec<(f32, u32)>, bag_reduction: f32) -> f32 {
        let total_raw: f32 = items.iter().map(|(w, qty)| w * (*qty as f32)).sum();
        total_raw * (1.0 - bag_reduction.max(0.0).min(0.9))
    }

    #[staticmethod]
    fn can_fit_item(current_weight: f32, capacity: f32, item_weight: f32, amount: u32) -> bool {
        current_weight + (item_weight * (amount as f32)) <= capacity
    }
}

/// 8. Native Ballistics Projectile Flight Utility in Rust.
#[pyclass]
pub struct RustBallisticsUtility;

#[pymethods]
impl RustBallisticsUtility {
    #[new]
    fn new() -> Self {
        RustBallisticsUtility
    }

    #[staticmethod]
    fn calculate_trajectory(v0_ms: f32, distance_m: f32, wind_ms: f32) -> (f32, f32, f32) {
        let time_s = distance_m / v0_ms.max(1.0);
        let bullet_drop = 0.5 * 9.81 * time_s * time_s;
        let wind_drift = 0.5 * wind_ms * time_s * time_s;
        let final_v = (v0_ms - 0.5 * time_s * 100.0).max(10.0);
        (bullet_drop, wind_drift, final_v)
    }
}

/// 9. Native Food Spoilage Decay Utility in Rust.
#[pyclass]
pub struct RustFoodSpoilageUtility;

#[pymethods]
impl RustFoodSpoilageUtility {
    #[new]
    fn new() -> Self {
        RustFoodSpoilageUtility
    }

    #[staticmethod]
    fn calculate_freshness_decay(
        base_freshness: f32,
        ambient_temp_c: f32,
        is_refrigerated: bool,
        is_freezer: bool,
        power_online: bool,
    ) -> f32 {
        let mut decay_mult = 1.0f32;

        if power_online {
            if is_freezer {
                decay_mult = 0.01;
            } else if is_refrigerated {
                decay_mult = 0.10;
            }
        }

        let temp_factor = ((ambient_temp_c - 10.0) / 10.0).max(0.1);
        let total_decay = 0.001 * decay_mult * temp_factor;
        (base_freshness - total_decay).max(0.0)
    }
}

/// 10. Native Particle System in Rust.
#[pyclass]
pub struct RustParticleSystem {
    particles: Vec<(f32, f32, i32, u32)>,
}

#[pymethods]
impl RustParticleSystem {
    #[new]
    fn new() -> Self {
        RustParticleSystem {
            particles: Vec::new(),
        }
    }

    fn spawn_particles(&mut self, x: f32, y: f32, z: i32, count: u32, lifetime: u32) {
        for _ in 0..count {
            self.particles.push((x, y, z, lifetime));
        }
    }

    fn tick(&mut self) -> usize {
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

/// High-performance Rust zombie flocking steering calculation using zero-copy NumPy inputs.
#[pyfunction]
pub fn compute_zombie_flock_steering<'py>(
    py: Python<'py>,
    zombie_coords: PyReadonlyArray1<'py, f32>,
    separation_dist: f32,
) -> &'py PyArray1<f32> {
    let coords_slice = zombie_coords.as_slice().unwrap_or(&[]);
    let num_zombies = coords_slice.len() / 3;
    let mut steering_vectors = vec![0.0f32; num_zombies * 2];

    if num_zombies >= 2 {
        let sq_sep = separation_dist * separation_dist;

        for i in 0..num_zombies {
            let z1_x = coords_slice[i * 3];
            let z1_y = coords_slice[i * 3 + 1];
            let z1_z = coords_slice[i * 3 + 2];

            let mut sep_x = 0.0f32;
            let mut sep_y = 0.0f32;

            for j in 0..num_zombies {
                if i == j {
                    continue;
                }

                let z2_x = coords_slice[j * 3];
                let z2_y = coords_slice[j * 3 + 1];
                let z2_z = coords_slice[j * 3 + 2];

                if (z1_z - z2_z).abs() > 0.1 {
                    continue;
                }

                let dx = z1_x - z2_x;
                let dy = z1_y - z2_y;
                let dist_sq = dx * dx + dy * dy;

                if dist_sq > 0.0001 && dist_sq < sq_sep {
                    let dist = dist_sq.sqrt();
                    sep_x += (dx / dist) * (separation_dist - dist);
                    sep_y += (dy / dist) * (separation_dist - dist);
                }
            }

            steering_vectors[i * 2] = sep_x;
            steering_vectors[i * 2 + 1] = sep_y;
        }
    }

    steering_vectors.into_pyarray(py)
}

fn is_opaque_tile(t: i64) -> bool {
    matches!(
        t,
        2 | 6 | 11 | 29 | 33 | 34 | 35 | 36 | 37 | 38 | 39 | 40 | 41 | 42 | 43 | 44 | 45 | 46 | 47 | 48 | 58 | 59 | 60 | 61
    )
}

/// Fast Rust raycasting line-of-sight check.
#[pyfunction]
pub fn check_line_of_sight_rust<'py>(
    x1: f32,
    y1: f32,
    z1: i32,
    x2: f32,
    y2: f32,
    z2: i32,
    grid_3d: PyReadonlyArray3<'py, i64>,
    z_min: i32,
) -> bool {
    if (z1 - z2).abs() > 1 {
        return false;
    }

    let dx = x2 - x1;
    let dy = y2 - y1;
    let dist = (dx * dx + dy * dy).sqrt();
    if dist < 0.1 {
        return true;
    }

    let steps = (dist * 2.0).ceil() as usize;
    if steps == 0 {
        return true;
    }

    let step_x = dx / (steps as f32);
    let step_y = dy / (steps as f32);

    let shape = grid_3d.shape();
    let num_levels = shape[0] as i32;
    let height = shape[1] as i32;
    let width = shape[2] as i32;

    let z_idx = z1 - z_min;
    if z_idx < 0 || z_idx >= num_levels {
        return false;
    }

    let view = grid_3d.as_array();
    let mut cx = x1;
    let mut cy = y1;

    for _ in 0..steps {
        cx += step_x;
        cy += step_y;
        let ix = cx as i32;
        let iy = cy as i32;

        if ix >= 0 && ix < width && iy >= 0 && iy < height {
            let tile = view[[z_idx as usize, iy as usize, ix as usize]];
            if is_opaque_tile(tile) {
                return false;
            }
        }
    }

    true
}

/// Fast Rust raycasted Fog-of-War tile visibilities.
#[pyfunction]
#[pyo3(signature = (x, y, radius, z, grid_3d, z_min, facing_angle=None, fov_degrees=180.0))]
pub fn compute_fog_of_war_rust<'py>(
    x: f32,
    y: f32,
    radius: usize,
    z: i32,
    grid_3d: PyReadonlyArray3<'py, i64>,
    z_min: i32,
    facing_angle: Option<f32>,
    fov_degrees: f32,
) -> Vec<(i32, i32)> {
    let ix = x as i32;
    let iy = y as i32;

    let shape = grid_3d.shape();
    let num_levels = shape[0] as i32;
    let height = shape[1] as i32;
    let width = shape[2] as i32;

    let z_idx = z - z_min;
    if z_idx < 0 || z_idx >= num_levels {
        return vec![(ix, iy)];
    }

    let view = grid_3d.as_array();
    let mut visible = HashSet::new();
    visible.insert((ix, iy));

    let num_rays = 36usize;
    let half_fov = facing_angle.map(|_| (fov_degrees / 2.0).to_radians());

    for i in 0..num_rays {
        let angle = (i as f32) * (2.0 * std::f32::consts::PI / (num_rays as f32));
        let r_dx = angle.cos();
        let r_dy = angle.sin();

        if let (Some(f_angle), Some(h_fov)) = (facing_angle, half_fov) {
            let ray_angle = r_dy.atan2(r_dx);
            let mut diff = (ray_angle - f_angle + std::f32::consts::PI) % (2.0 * std::f32::consts::PI) - std::f32::consts::PI;
            if diff < -std::f32::consts::PI {
                diff += 2.0 * std::f32::consts::PI;
            }
            if diff.abs() > h_fov {
                continue;
            }
        }

        let mut cx = x;
        let mut cy = y;

        for _step in 0..radius {
            cx += r_dx;
            cy += r_dy;
            let tx = cx as i32;
            let ty = cy as i32;

            if tx >= 0 && tx < width && ty >= 0 && ty < height {
                visible.insert((tx, ty));
                let tile = view[[z_idx as usize, ty as usize, tx as usize]];
                if is_opaque_tile(tile) {
                    break;
                }
            } else {
                break;
            }
        }
    }

    visible.into_iter().collect()
}

#[derive(Copy, Clone, Eq, PartialEq)]
struct PathNode {
    f: u32,
    g: u32,
    x: i32,
    y: i32,
    z: i32,
}

impl Ord for PathNode {
    fn cmp(&self, other: &Self) -> Ordering {
        other.f.cmp(&self.f)
    }
}

impl PartialOrd for PathNode {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn is_walkable_tile(t: i64) -> bool {
    matches!(
        t,
        0 | 1 | 3 | 5 | 7 | 8 | 10 | 12 | 13 | 14 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 26 | 27 | 28 | 30 | 50 | 51 | 52 | 54 | 57 | 62 | 63 | 64 | 65 | 75 | 76 | 78 | 79
    )
}

fn is_breakable_tile(t: i64) -> bool {
    matches!(t, 7 | 49 | 53 | 55)
}

fn is_stairs_or_ladder(t: i64) -> bool {
    matches!(t, 8 | 13 | 79)
}

/// High-performance full 3D A* Pathfinding in Rust over 3D NumPy grid `grid_3d` [num_levels, height, width] with z_min support.
#[pyfunction]
pub fn compute_a_star_3d_path<'py>(
    start: (i32, i32, i32),
    goal: (i32, i32, i32),
    grid_3d: PyReadonlyArray3<'py, i64>,
    z_min: i32,
    max_nodes: usize,
) -> Vec<(i32, i32, i32)> {
    let (sx, sy, sz) = start;
    let (gx, gy, gz) = goal;

    if sx == gx && sy == gy && sz == gz {
        return vec![start];
    }

    let shape = grid_3d.shape();
    let num_levels = shape[0] as i32;
    let height = shape[1] as i32;
    let width = shape[2] as i32;

    let sz_idx = sz - z_min;
    let gz_idx = gz - z_min;

    if sz_idx < 0 || sz_idx >= num_levels || gz_idx < 0 || gz_idx >= num_levels {
        return vec![];
    }

    let view = grid_3d.as_array();

    let get_tile = |x: i32, y: i32, z: i32| -> i64 {
        let zi = z - z_min;
        if zi >= 0 && zi < num_levels && y >= 0 && y < height && x >= 0 && x < width {
            view[[zi as usize, y as usize, x as usize]]
        } else {
            -1
        }
    };

    let start_tile = get_tile(sx, sy, sz);
    let goal_tile = get_tile(gx, gy, gz);

    if start_tile < 0 || (!is_walkable_tile(start_tile) && !is_breakable_tile(start_tile)) {
        return vec![];
    }
    if goal_tile < 0 || (!is_walkable_tile(goal_tile) && !is_breakable_tile(goal_tile)) {
        return vec![];
    }

    let mut open_set = BinaryHeap::new();
    let mut g_score = HashMap::new();
    let mut came_from = HashMap::new();

    let h_start = (((sx - gx).abs() + (sy - gy).abs()) * 10 + (sz - gz).abs() * 30) as u32;
    open_set.push(PathNode { f: h_start, g: 0, x: sx, y: sy, z: sz });
    g_score.insert((sx, sy, sz), 0u32);

    let mut nodes_expanded = 0;

    let neighbors_2d = [
        (-1, 0, 10), (1, 0, 10), (0, -1, 10), (0, 1, 10),
        (-1, -1, 14), (1, -1, 14), (-1, 1, 14), (1, 1, 14),
    ];

    while let Some(current) = open_set.pop() {
        if current.x == gx && current.y == gy && current.z == gz {
            let mut path = vec![(current.x, current.y, current.z)];
            let mut curr_pos = (current.x, current.y, current.z);
            while let Some(&parent) = came_from.get(&curr_pos) {
                path.push(parent);
                curr_pos = parent;
            }
            path.reverse();
            return path;
        }

        nodes_expanded += 1;
        if nodes_expanded > max_nodes {
            break;
        }

        let curr_tile = get_tile(current.x, current.y, current.z);

        // 1. Horizontal 2D neighbors
        for &(dx, dy, base_cost) in &neighbors_2d {
            let nx = current.x + dx;
            let ny = current.y + dy;
            let nz = current.z;

            if dx.abs() == 1 && dy.abs() == 1 {
                let t1 = get_tile(current.x + dx, current.y, nz);
                let t2 = get_tile(current.x, current.y + dy, nz);
                if !is_walkable_tile(t1) && !is_walkable_tile(t2) {
                    continue;
                }
            }

            let tile = get_tile(nx, ny, nz);
            if tile < 0 {
                continue;
            }

            let is_walk = is_walkable_tile(tile);
            let is_break = is_breakable_tile(tile);

            if is_walk || is_break {
                let cost_penalty = if is_break { 30u32 } else { 0u32 };
                let tentative_g = current.g + base_cost + cost_penalty;
                let existing_g = g_score.get(&(nx, ny, nz)).copied().unwrap_or(u32::MAX);

                if tentative_g < existing_g {
                    came_from.insert((nx, ny, nz), (current.x, current.y, current.z));
                    g_score.insert((nx, ny, nz), tentative_g);
                    let h = (((nx - gx).abs() + (ny - gy).abs()) * 10 + (nz - gz).abs() * 30) as u32;
                    open_set.push(PathNode { f: tentative_g + h, g: tentative_g, x: nx, y: ny, z: nz });
                }
            }
        }

        // 2. Vertical Z neighbors (stairs / ladders / trapdoors)
        if is_stairs_or_ladder(curr_tile) {
            for dz in &[-1, 1] {
                let nz = current.z + dz;
                let tile = get_tile(current.x, current.y, nz);
                if tile >= 0 && (is_walkable_tile(tile) || is_breakable_tile(tile)) {
                    let tentative_g = current.g + 20;
                    let existing_g = g_score.get(&(current.x, current.y, nz)).copied().unwrap_or(u32::MAX);

                    if tentative_g < existing_g {
                        came_from.insert((current.x, current.y, nz), (current.x, current.y, current.z));
                        g_score.insert((current.x, current.y, nz), tentative_g);
                        let h = (((current.x - gx).abs() + (current.y - gy).abs()) * 10 + (nz - gz).abs() * 30) as u32;
                        open_set.push(PathNode { f: tentative_g + h, g: tentative_g, x: current.x, y: current.y, z: nz });
                    }
                }
            }
        }
    }

    vec![]
}

/// Native Lua Mod Manager in Rust powered by `mlua`.
#[pyclass(unsendable)]
pub struct RustLuaModManager {
    lua: Lua,
}

#[pymethods]
impl RustLuaModManager {
    #[new]
    fn new() -> Self {
        let lua = Lua::new();
        RustLuaModManager { lua }
    }

    fn load_mod_script(&self, script: &str) -> PyResult<bool> {
        let res: LuaResult<()> = self.lua.load(script).exec();
        Ok(res.is_ok())
    }

    fn trigger_event(&self, event_name: &str, arg: u64) -> PyResult<bool> {
        let globals = self.lua.globals();
        if let Ok(func) = globals.get::<_, mlua::Function>(event_name) {
            let _: LuaResult<()> = func.call(arg);
            Ok(true)
        } else {
            Ok(false)
        }
    }
}

#[pyclass]
pub struct RustEngineCore {
    width: usize,
    height: usize,
    current_tick: u64,
    survivor_x: f32,
    survivor_y: f32,
    survivor_z: i32,
    survivor_health: f32,
    survivor_hunger: f32,
    survivor_thirst: f32,
}

#[pymethods]
impl RustEngineCore {
    #[new]
    fn new(width: usize, height: usize) -> Self {
        RustEngineCore {
            width,
            height,
            current_tick: 0,
            survivor_x: (width / 2) as f32,
            survivor_y: (height / 2) as f32,
            survivor_z: 0,
            survivor_health: 100.0,
            survivor_hunger: 100.0,
            survivor_thirst: 100.0,
        }
    }

    fn sync_survivor_state(&mut self, x: f32, y: f32, z: i32, health: f32, hunger: f32, thirst: f32, current_tick: u64) {
        self.survivor_x = x;
        self.survivor_y = y;
        self.survivor_z = z;
        self.survivor_health = health;
        self.survivor_hunger = hunger;
        self.survivor_thirst = thirst;
        self.current_tick = current_tick;
    }

    fn step(&mut self, dx: f32, dy: f32, _action: i32) {
        self.current_tick += 1;
        self.survivor_x = (self.survivor_x + dx * 0.15).max(0.0).min((self.width - 1) as f32);
        self.survivor_y = (self.survivor_y + dy * 0.15).max(0.0).min((self.height - 1) as f32);
        self.survivor_hunger = (self.survivor_hunger - 0.025).max(0.0);
        self.survivor_thirst = (self.survivor_thirst - 0.035).max(0.0);
    }

    fn get_observation_flat<'py>(&self, py: Python<'py>) -> &'py PyArray1<f32> {
        let mut obs = vec![0.0f32; 57];
        obs[0] = self.survivor_health / 100.0;
        obs[1] = self.survivor_hunger / 100.0;
        obs[2] = self.survivor_thirst / 100.0;
        obs[3] = 1.0;
        obs[4] = 1.0;
        obs[22] = self.survivor_z as f32 / 20.0;
        obs.into_pyarray(py)
    }

    fn get_current_tick(&self) -> u64 {
        self.current_tick
    }

    fn get_survivor_pos(&self) -> (f32, f32, i32) {
        (self.survivor_x, self.survivor_y, self.survivor_z)
    }
}

#[pymodule]
fn rust_vulkan_render(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<VulkanTileRenderer>()?;
    m.add_class::<RustEngineCore>()?;
    m.add_class::<RustLuaModManager>()?;
    m.add_class::<RustVehiclePhysics>()?;
    m.add_class::<RustAcousticSystem>()?;
    m.add_class::<RustAnatomicalHealth>()?;
    m.add_class::<RustEnvironmentManager>()?;
    m.add_class::<RustZombieEngine>()?;
    m.add_class::<RustSpatialGrid>()?;
    m.add_class::<RustContainerUtility>()?;
    m.add_class::<RustBallisticsUtility>()?;
    m.add_class::<RustFoodSpoilageUtility>()?;
    m.add_class::<RustParticleSystem>()?;
    m.add_function(wrap_pyfunction!(compute_zombie_flock_steering, m)?)?;
    m.add_function(wrap_pyfunction!(compute_a_star_3d_path, m)?)?;
    m.add_function(wrap_pyfunction!(check_line_of_sight_rust, m)?)?;
    m.add_function(wrap_pyfunction!(compute_fog_of_war_rust, m)?)?;
    Ok(())
}
