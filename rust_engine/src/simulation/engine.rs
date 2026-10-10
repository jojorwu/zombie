use pyo3::prelude::*;
use numpy::{PyArray1, PyArray2, PyArray3, IntoPyArray, PyReadonlyArray1};
use rayon::prelude::*;
use crate::world::RustWorldGrid;
use crate::entities::{RustSurvivorEntity, RustZombieEngine};
use crate::systems::RustAcousticSystem;

#[pyclass]
pub struct RustEngineCore {
    sim: RustFullSimulationCore,
}

#[pymethods]
impl RustEngineCore {
    #[new]
    pub fn new(width: usize, height: usize) -> Self {
        RustEngineCore {
            sim: RustFullSimulationCore::new(width, height, 1, 20),
        }
    }

    pub fn sync_survivor_state(&mut self, x: f32, y: f32, z: i32, health: f32, hunger: f32, thirst: f32, current_tick: u64) {
        self.sim.sync_survivor_at(0, x, y, z, health, hunger, thirst);
        self.sim.current_tick = current_tick;
    }

    pub fn step(&mut self, dx: f32, dy: f32, action: i32) {
        self.sim.step_simulation(vec![action], vec![(dx, dy)]);
    }

    pub fn get_observation_flat<'py>(&self, py: Python<'py>) -> &'py PyArray1<f32> {
        if let Some(surv) = self.sim.survivors.first() {
            let mut obs = vec![0.0f32; 57];
            obs[0] = surv.hp / 100.0;
            obs[1] = surv.hunger / 100.0;
            obs[2] = surv.thirst / 100.0;
            obs[3] = if surv.is_alive { 1.0 } else { 0.0 };
            obs[4] = self.sim.ambient_light;
            obs[20] = (surv.x / self.sim.width as f32).clamp(0.0, 1.0);
            obs[21] = (surv.y / self.sim.height as f32).clamp(0.0, 1.0);
            obs[22] = (surv.z as f32 / 20.0).clamp(-1.0, 1.0);
            obs[23] = (self.sim.current_tick % 3600) as f32 / 3600.0;

            let sx = surv.x as i32;
            let sy = surv.y as i32;
            let sz = surv.z;
            let mut sensor_idx = 32;

            for dy in -2..=2 {
                for dx in -2..=2 {
                    if sensor_idx < 57 {
                        let tx = sx + dx;
                        let ty = sy + dy;
                        obs[sensor_idx] = if self.sim.world_grid.is_walkable(tx as f32, ty as f32, sz) { 1.0 } else { 0.0 };
                        sensor_idx += 1;
                    }
                }
            }
            obs.into_pyarray(py)
        } else {
            vec![0.0f32; 57].into_pyarray(py)
        }
    }

    pub fn get_current_tick(&self) -> u64 {
        self.sim.current_tick
    }

    pub fn get_survivor_pos(&self) -> (f32, f32, i32) {
        self.sim.get_survivor_pos(0)
    }
}

/// Native Full Simulation Core in Rust.
#[derive(Clone)]
#[pyclass]
pub struct RustFullSimulationCore {
    pub width: usize,
    pub height: usize,
    pub current_tick: u64,
    pub world_grid: RustWorldGrid,
    pub survivors: Vec<RustSurvivorEntity>,
    pub zombies: Vec<RustZombieEngine>,
    pub ambient_light: f32,
    pub noise_events: Vec<(f32, f32, i32, f32)>, // (x, y, z, volume_db)
}

#[pymethods]
impl RustFullSimulationCore {
    #[new]
    pub fn new(width: usize, height: usize, num_survivors: usize, num_zombies: usize) -> Self {
        let world_grid = RustWorldGrid::new(width, height, -2, 5);
        let mut survivors = Vec::with_capacity(num_survivors);
        for i in 0..num_survivors {
            survivors.push(RustSurvivorEntity::new(
                i,
                (width / 2) as f32 + (i as f32 * 2.0),
                (height / 2) as f32,
                0,
            ));
        }

        let mut zombies = Vec::with_capacity(num_zombies);
        for i in 0..num_zombies {
            let zx = (width / 4) as f32 + ((i % 10) as f32 * 3.0);
            let zy = (height / 4) as f32 + ((i / 10) as f32 * 3.0);
            zombies.push(RustZombieEngine::new(zx, zy, 0, 50.0, 0.08));
        }

        RustFullSimulationCore {
            width,
            height,
            current_tick: 0,
            world_grid,
            survivors,
            zombies,
            ambient_light: 1.0,
            noise_events: Vec::new(),
        }
    }

    pub fn set_tile(&mut self, x: i32, y: i32, z: i32, tile_type: i64) {
        self.world_grid.set_tile(x, y, z, tile_type);
    }

    pub fn get_tile(&self, x: i32, y: i32, z: i32) -> i64 {
        self.world_grid.get_tile(x, y, z)
    }

    pub fn set_ground_layer(&mut self, ground_data: PyReadonlyArray1<i64>) {
        let slice = ground_data.as_slice().unwrap_or(&[]);
        if slice.len() == self.world_grid.ground_layer.len() {
            self.world_grid.ground_layer.copy_from_slice(slice);
        }
    }

    pub fn add_survivor(&mut self, x: f32, y: f32, z: i32) -> usize {
        let id = self.survivors.len();
        self.survivors.push(RustSurvivorEntity::new(id, x, y, z));
        id
    }

    pub fn add_zombie(&mut self, x: f32, y: f32, z: i32, hp: f32, speed: f32) -> usize {
        let id = self.zombies.len();
        self.zombies.push(RustZombieEngine::new(x, y, z, hp, speed));
        id
    }

    pub fn sync_survivor_at(&mut self, index: usize, x: f32, y: f32, z: i32, hp: f32, hunger: f32, thirst: f32) {
        if index < self.survivors.len() {
            let surv = &mut self.survivors[index];
            surv.x = x;
            surv.y = y;
            surv.z = z;
            surv.hp = hp;
            surv.hunger = hunger;
            surv.thirst = thirst;
            surv.is_alive = hp > 0.0;
        }
    }

    pub fn sync_zombie_at(&mut self, index: usize, x: f32, y: f32, z: i32, hp: f32) {
        if index < self.zombies.len() {
            let zomb = &mut self.zombies[index];
            zomb.x = x;
            zomb.y = y;
            zomb.z = z;
            zomb.hp = hp;
            zomb.is_alive = hp > 0.0;
        }
    }

    pub fn get_survivor_pos(&self, index: usize) -> (f32, f32, i32) {
        if index < self.survivors.len() {
            let s = &self.survivors[index];
            (s.x, s.y, s.z)
        } else {
            (0.0, 0.0, 0)
        }
    }

    pub fn get_survivors_count(&self) -> usize {
        self.survivors.len()
    }

    pub fn get_zombies_count(&self) -> usize {
        self.zombies.len()
    }

    pub fn get_zombie_pos(&self, index: usize) -> (f32, f32, i32, f32, bool) {
        if index < self.zombies.len() {
            let z = &self.zombies[index];
            (z.x, z.y, z.z, z.hp, z.is_alive)
        } else {
            (0.0, 0.0, 0, 0.0, false)
        }
    }

    pub fn emit_noise(&mut self, x: f32, y: f32, z: i32, volume_db: f32) {
        self.noise_events.push((x, y, z, volume_db));
    }

    pub fn step_simulation(&mut self, actions: Vec<i32>, movements: Vec<(f32, f32)>) {
        self.current_tick += 1;

        // Calculate ambient light based on 24-hour cycle (3,600 ticks = 1 day)
        let day_tick = (self.current_tick % 3600) as f32;
        let day_phase = (day_tick / 3600.0) * std::f32::consts::TAU;
        self.ambient_light = (0.2 + 0.8 * ((day_phase - std::f32::consts::FRAC_PI_2).sin() * 0.5 + 0.5)).clamp(0.1, 1.0);

        // 1. Update Survivors
        for (i, surv) in self.survivors.iter_mut().enumerate() {
            if !surv.is_alive {
                continue;
            }

            if i < movements.len() {
                let (dx, dy) = movements[i];
                let speed_mult = 0.20;
                let new_x = surv.x + dx * speed_mult;
                let new_y = surv.y + dy * speed_mult;

                if self.world_grid.is_walkable(new_x, new_y, surv.z) {
                    surv.x = new_x.max(0.0).min((self.width - 1) as f32);
                    surv.y = new_y.max(0.0).min((self.height - 1) as f32);
                } else if self.world_grid.is_walkable(new_x, surv.y, surv.z) {
                    surv.x = new_x.max(0.0).min((self.width - 1) as f32);
                } else if self.world_grid.is_walkable(surv.x, new_y, surv.z) {
                    surv.y = new_y.max(0.0).min((self.height - 1) as f32);
                }
            }

            // Update vitals
            surv.update_vitals(1);

            // Process action if attack (action == 1)
            if i < actions.len() && actions[i] == 1 {
                let surv_x = surv.x;
                let surv_y = surv.y;
                let surv_z = surv.z;
                // Attack closest zombie within 1.8 units
                for z in self.zombies.iter_mut() {
                    if z.is_alive && z.z == surv_z {
                        let dz_x = z.x - surv_x;
                        let dz_y = z.y - surv_y;
                        if dz_x * dz_x + dz_y * dz_y <= 3.24 {
                            z.hp -= 35.0;
                            if z.hp <= 0.0 {
                                z.is_alive = false;
                            }
                            break;
                        }
                    }
                }
            }
        }

        // 2. Update Zombies (with flocking + perception)
        let active_survivors: Vec<(f32, f32, i32)> = self.survivors.iter()
            .filter(|s| s.is_alive)
            .map(|s| (s.x, s.y, s.z))
            .collect();

        let num_zombies = self.zombies.len();
        let mut steerings = vec![(0.0f32, 0.0f32); num_zombies];

        // Flocking separation between zombies
        for i in 0..num_zombies {
            if !self.zombies[i].is_alive {
                continue;
            }
            let z1 = &self.zombies[i];
            let mut sep_x = 0.0f32;
            let mut sep_y = 0.0f32;
            for j in 0..num_zombies {
                if i == j || !self.zombies[j].is_alive {
                    continue;
                }
                let z2 = &self.zombies[j];
                if z1.z != z2.z {
                    continue;
                }
                let dx = z1.x - z2.x;
                let dy = z1.y - z2.y;
                let d2 = dx * dx + dy * dy;
                if d2 > 0.0001 && d2 < 2.25 {
                    let d = d2.sqrt();
                    sep_x += (dx / d) * (1.5 - d);
                    sep_y += (dy / d) * (1.5 - d);
                }
            }
            steerings[i] = (sep_x, sep_y);
        }

        // Move zombies and check bite attacks
        for (i, zombie) in self.zombies.iter_mut().enumerate() {
            if !zombie.is_alive {
                continue;
            }

            // Find target (closest alive survivor within active distance <= 35.0)
            let mut closest_target: Option<(f32, f32)> = None;
            let mut min_dist = f32::MAX;

            for &(sx, sy, sz) in &active_survivors {
                if sz == zombie.z {
                    let dx = sx - zombie.x;
                    let dy = sy - zombie.y;
                    let dist = (dx * dx + dy * dy).sqrt();
                    if dist < min_dist && dist <= 35.0 {
                        min_dist = dist;
                        closest_target = Some((sx, sy));
                    }
                }
            }

            // Also check noise events if no close survivor visible
            if min_dist > 15.0 {
                for &(nx, ny, nz, vol) in &self.noise_events {
                    if nz == zombie.z {
                        let heard = RustAcousticSystem::propagate_noise_decibels(
                            nx, ny, nz, vol, zombie.x, zombie.y, zombie.z
                        );
                        if heard > 20.0 {
                            closest_target = Some((nx, ny));
                            break;
                        }
                    }
                }
            }

            if let Some((tx, ty)) = closest_target {
                let dx = tx - zombie.x;
                let dy = ty - zombie.y;
                let dist = (dx * dx + dy * dy).sqrt();
                if dist > 0.2 {
                    let (sep_x, sep_y) = steerings[i];
                    let move_x = (dx / dist) * zombie.speed + sep_x * 0.05;
                    let move_y = (dy / dist) * zombie.speed + sep_y * 0.05;

                    let new_zx = (zombie.x + move_x).max(0.0).min((self.width - 1) as f32);
                    let new_zy = (zombie.y + move_y).max(0.0).min((self.height - 1) as f32);

                    if self.world_grid.is_walkable(new_zx, new_zy, zombie.z) {
                        zombie.x = new_zx;
                        zombie.y = new_zy;
                    }
                }
            }

            // Bite attack check on alive survivors
            for surv in self.survivors.iter_mut() {
                if surv.is_alive && surv.z == zombie.z {
                    let (has_bitten, damage, _slowdown) = zombie.check_bite_attack(surv.x, surv.y);
                    if has_bitten {
                        surv.hp = (surv.hp - damage * 0.1).max(0.0);
                        if surv.hp <= 0.0 {
                            surv.is_alive = false;
                        }
                    }
                }
            }
        }

        // Clear processed noise events
        self.noise_events.clear();
    }

    pub fn get_observations_matrix<'py>(&self, py: Python<'py>) -> &'py PyArray2<f32> {
        let num_survivors = self.survivors.len();
        let mut obs_matrix = vec![0.0f32; num_survivors * 57];

        for (i, surv) in self.survivors.iter().enumerate() {
            let row_offset = i * 57;

            // Status features (0..4)
            obs_matrix[row_offset] = surv.hp / 100.0;
            obs_matrix[row_offset + 1] = surv.hunger / 100.0;
            obs_matrix[row_offset + 2] = surv.thirst / 100.0;
            obs_matrix[row_offset + 3] = if surv.is_alive { 1.0 } else { 0.0 };
            obs_matrix[row_offset + 4] = self.ambient_light;

            // Closest zombie features (5..21) - Up to 3 closest zombies
            let mut zombie_dists: Vec<(f32, f32, f32, f32, f32)> = Vec::new();
            for z in &self.zombies {
                if z.is_alive && z.z == surv.z {
                    let dx = z.x - surv.x;
                    let dy = z.y - surv.y;
                    let dist = (dx * dx + dy * dy).sqrt();
                    zombie_dists.push((dist, dx, dy, z.hp, z.speed));
                }
            }
            zombie_dists.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));

            for z_idx in 0..3 {
                let base = row_offset + 5 + (z_idx * 5);
                if z_idx < zombie_dists.len() {
                    let (dist, dx, dy, hp, speed) = zombie_dists[z_idx];
                    obs_matrix[base] = (dx / 50.0).clamp(-1.0, 1.0);
                    obs_matrix[base + 1] = (dy / 50.0).clamp(-1.0, 1.0);
                    obs_matrix[base + 2] = (dist / 50.0).clamp(0.0, 1.0);
                    obs_matrix[base + 3] = hp / 100.0;
                    obs_matrix[base + 4] = speed;
                }
            }

            // Position & Status metrics (20..31)
            obs_matrix[row_offset + 20] = (surv.x / self.width as f32).clamp(0.0, 1.0);
            obs_matrix[row_offset + 21] = (surv.y / self.height as f32).clamp(0.0, 1.0);
            obs_matrix[row_offset + 22] = (surv.z as f32 / 20.0).clamp(-1.0, 1.0);
            obs_matrix[row_offset + 23] = (self.current_tick % 3600) as f32 / 3600.0;

            // 5x5 Spatial Sensor Grid around survivor (32..57)
            let sx = surv.x as i32;
            let sy = surv.y as i32;
            let sz = surv.z;
            let mut sensor_idx = 32;

            for dy in -2..=2 {
                for dx in -2..=2 {
                    if sensor_idx < 57 {
                        let tx = sx + dx;
                        let ty = sy + dy;
                        let is_walk = if self.world_grid.is_walkable(tx as f32, ty as f32, sz) {
                            1.0f32
                        } else {
                            0.0f32
                        };
                        obs_matrix[row_offset + sensor_idx] = is_walk;
                        sensor_idx += 1;
                    }
                }
            }
        }

        let array2d = numpy::ndarray::Array2::from_shape_vec((num_survivors, 57), obs_matrix).unwrap();
        array2d.into_pyarray(py)
    }

    pub fn get_current_tick(&self) -> u64 {
        self.current_tick
    }
}

/// Multi-Environment Parallel Simulation Manager for High-Speed PPO Reinforcement Learning.
/// Runs N independent simulation environments in parallel threads via Rayon without Python GIL overhead.
#[pyclass]
pub struct RustParallelEnvManager {
    num_envs: usize,
    num_survivors_per_env: usize,
    envs: Vec<RustFullSimulationCore>,
}

#[pymethods]
impl RustParallelEnvManager {
    #[new]
    pub fn new(num_envs: usize, width: usize, height: usize, num_survivors: usize, num_zombies: usize) -> Self {
        let mut envs = Vec::with_capacity(num_envs);
        for _ in 0..num_envs {
            envs.push(RustFullSimulationCore::new(width, height, num_survivors, num_zombies));
        }
        RustParallelEnvManager {
            num_envs,
            num_survivors_per_env: num_survivors,
            envs,
        }
    }

    pub fn get_num_envs(&self) -> usize {
        self.num_envs
    }

    /// Steps all parallel environments concurrently using Rayon parallel threads while GIL is released.
    pub fn step_all_parallel<'py>(
        &mut self,
        py: Python<'py>,
        all_actions: Vec<Vec<i32>>,
        all_movements: Vec<Vec<(f32, f32)>>,
    ) -> &'py PyArray3<f32> {
        let num_envs = self.num_envs;
        let num_survivors = self.num_survivors_per_env;

        let envs = &mut self.envs;

        // Release Python GIL and execute Rayon parallel simulation step
        py.allow_threads(|| {
            envs.par_iter_mut().enumerate().for_each(|(i, env)| {
                let actions = if i < all_actions.len() { all_actions[i].clone() } else { vec![] };
                let movements = if i < all_movements.len() { all_movements[i].clone() } else { vec![] };
                env.step_simulation(actions, movements);
            });
        });

        // Collect 3D observation tensor (num_envs, num_survivors, 57)
        let mut total_obs = vec![0.0f32; num_envs * num_survivors * 57];

        for (e_idx, env) in self.envs.iter().enumerate() {
            let env_offset = e_idx * num_survivors * 57;
            for (s_idx, surv) in env.survivors.iter().enumerate() {
                let s_offset = env_offset + s_idx * 57;

                total_obs[s_offset] = surv.hp / 100.0;
                total_obs[s_offset + 1] = surv.hunger / 100.0;
                total_obs[s_offset + 2] = surv.thirst / 100.0;
                total_obs[s_offset + 3] = if surv.is_alive { 1.0 } else { 0.0 };
                total_obs[s_offset + 4] = env.ambient_light;

                total_obs[s_offset + 20] = (surv.x / env.width as f32).clamp(0.0, 1.0);
                total_obs[s_offset + 21] = (surv.y / env.height as f32).clamp(0.0, 1.0);
                total_obs[s_offset + 22] = (surv.z as f32 / 20.0).clamp(-1.0, 1.0);
                total_obs[s_offset + 23] = (env.current_tick % 3600) as f32 / 3600.0;

                let sx = surv.x as i32;
                let sy = surv.y as i32;
                let sz = surv.z;
                let mut sensor_idx = 32;

                for dy in -2..=2 {
                    for dx in -2..=2 {
                        if sensor_idx < 57 {
                            let tx = sx + dx;
                            let ty = sy + dy;
                            let is_walk = if env.world_grid.is_walkable(tx as f32, ty as f32, sz) { 1.0f32 } else { 0.0f32 };
                            total_obs[s_offset + sensor_idx] = is_walk;
                            sensor_idx += 1;
                        }
                    }
                }
            }
        }

        let array3d = numpy::ndarray::Array3::from_shape_vec((num_envs, num_survivors, 57), total_obs).unwrap();
        array3d.into_pyarray(py)
    }
}
