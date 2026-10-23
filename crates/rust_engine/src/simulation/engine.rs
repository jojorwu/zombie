use crate::entities::{RustSurvivorEntity, RustZombieEngine};
use crate::systems::RustAcousticSystem;
use crate::world::RustWorldGrid;
use numpy::{IntoPyArray, PyArray1, PyArray2, PyArray3, PyReadonlyArray1, PyReadonlyArray2};
use pyo3::prelude::*;
use rayon::prelude::*;
use std::collections::HashMap;

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

    pub fn sync_survivor_state(
        &mut self,
        x: f32,
        y: f32,
        z: i32,
        health: f32,
        hunger: f32,
        thirst: f32,
        current_tick: u64,
    ) {
        self.sim
            .sync_survivor_at(0, x, y, z, health, hunger, thirst);
        self.sim.current_tick = current_tick;
    }

    pub fn step(&mut self, dx: f32, dy: f32, action: i32) {
        self.sim.step_simulation(vec![action], vec![(dx, dy)]);
    }

    pub fn get_observation_flat<'py>(&self, py: Python<'py>) -> &'py PyArray1<f32> {
        let obs_matrix = self.sim.get_observations_matrix(py);
        let slice = unsafe { obs_matrix.as_slice().unwrap() };
        let first_57 = if slice.len() >= 57 {
            slice[0..57].to_vec()
        } else {
            vec![0.0f32; 57]
        };
        first_57.into_pyarray(py)
    }

    pub fn get_current_tick(&self) -> u64 {
        self.sim.current_tick
    }

    pub fn get_survivor_pos(&self) -> (f32, f32, i32) {
        self.sim.get_survivor_pos(0)
    }
}

/// World Ground Item Entity in Rust.
#[derive(Clone, Debug)]
#[pyclass]
pub struct RustWorldItem {
    #[pyo3(get, set)]
    pub x: f32,
    #[pyo3(get, set)]
    pub y: f32,
    #[pyo3(get, set)]
    pub z: i32,
    #[pyo3(get, set)]
    pub item_type: u32, // 1: Food, 2: Water, 3: Medkit, 4: Ammo, 5: Material, 6: Weapon
    #[pyo3(get, set)]
    pub amount: u32,
    #[pyo3(get, set)]
    pub active: bool,
}

#[pymethods]
impl RustWorldItem {
    #[new]
    pub fn new(x: f32, y: f32, z: i32, item_type: u32, amount: u32) -> Self {
        RustWorldItem {
            x,
            y,
            z,
            item_type,
            amount,
            active: true,
        }
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
    /// Subset of `zombies` (indices) that Python currently simulates actively.
    /// Zombies outside this window are frozen in inactive chunks and are not
    /// stepped, observed, or harvested until rehydrated by the chunk manager.
    pub active_zombie_indices: Vec<usize>,
    pub items: Vec<RustWorldItem>,
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
            zombies.push(RustZombieEngine::new(
                zx,
                zy,
                0,
                50.0,
                0.08,
                -(i as i64) - 1,
            ));
        }

        let active_zombie_indices: Vec<usize> = (0..zombies.len()).collect();

        RustFullSimulationCore {
            width,
            height,
            current_tick: 0,
            world_grid,
            survivors,
            zombies,
            active_zombie_indices,
            items: Vec::new(),
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
        self.zombies
            .push(RustZombieEngine::new(x, y, z, hp, speed, -(id as i64) - 1));
        self.active_zombie_indices.push(id);
        id
    }

    pub fn sync_survivor_at(
        &mut self,
        index: usize,
        x: f32,
        y: f32,
        z: i32,
        hp: f32,
        hunger: f32,
        thirst: f32,
    ) {
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
            if !self.active_zombie_indices.contains(&index) {
                self.active_zombie_indices.push(index);
            }
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

    /// Idempotent, identity-keyed zombie roster sync (stable mapping table).
    /// `uids` is an int64 vector of each entity's stable monotonic uid
    /// (`py_zombie.uid`) — exact for any uid, no float32 precision loss.
    /// `data` rows are `[x, y, z_level, hp, speed]`, aligned row-for-row with
    /// `uids`. Rust matches incoming entities by uid instead of row index, so
    /// chunk freeze/rehydrate and death cleanup can reorder or resize the
    /// Python active list without ever mapping wrong slots onto entities.
    /// Rows absent from `data` become frozen (kept in the roster, excluded
    /// from the active window); uids not seen before are appended as new
    /// zombies.
    #[pyo3(signature = (uids, data, full_roster = false))]
    pub fn sync_zombies_batch(
        &mut self,
        uids: PyReadonlyArray1<i64>,
        data: PyReadonlyArray2<f32>,
        full_roster: bool,
    ) {
        let uid_vec = uids.as_array();
        let array = data.as_array();
        let rows = array.nrows().min(uid_vec.len());

        if full_roster {
            // Full-world snapshot (e.g. generation reset): rebuild the roster
            // from scratch with every entity inside the active window.
            self.zombies.clear();
            self.active_zombie_indices.clear();
            for i in 0..rows {
                let eid = uid_vec[i];
                let x = array[[i, 0]];
                let y = array[[i, 1]];
                let z = array[[i, 2]] as i32;
                let hp = array[[i, 3]];
                let speed = array[[i, 4]];
                let idx = self.zombies.len();
                self.zombies
                    .push(RustZombieEngine::new(x, y, z, hp, speed, eid));
                self.active_zombie_indices.push(idx);
            }
            return;
        }

        // Incremental active-window sync: update-by-id, append-new, freeze-missing.
        let mut touched: Vec<bool> = vec![false; self.zombies.len()];
        for i in 0..rows {
            let eid = uid_vec[i];
            let x = array[[i, 0]];
            let y = array[[i, 1]];
            let z = array[[i, 2]] as i32;
            let hp = array[[i, 3]];
            let speed = array[[i, 4]];

            match self.zombies.iter().position(|zb| zb.entity_id == eid) {
                Some(idx) => {
                    let zomb = &mut self.zombies[idx];
                    zomb.x = x;
                    zomb.y = y;
                    zomb.z = z;
                    zomb.hp = hp;
                    zomb.is_alive = hp > 0.0;
                    if speed > 0.0 {
                        zomb.speed = speed;
                    }
                    touched[idx] = true;
                }
                None => {
                    let idx = self.zombies.len();
                    self.zombies
                        .push(RustZombieEngine::new(x, y, z, hp, speed, eid));
                    touched.push(true);
                }
            }
        }

        self.active_zombie_indices = touched
            .iter()
            .enumerate()
            .filter(|(_, t)| **t)
            .map(|(i, _)| i)
            .collect();
    }

    /// Harvests only the ACTIVE-window zombies. Returns `(uids, data)` where
    /// `uids` is int64[N] (exact monotonic uids) and `data` is float32[N, 5]
    /// with columns `[x, y, z_level, hp, is_alive]`. Row order matches the
    /// last `sync_zombies_batch(...)` call, so Python can zip it with its own
    /// list; rows are keyed by uid for safe reordering on either side.
    pub fn get_zombies_batch<'py>(
        &self,
        py: Python<'py>,
    ) -> (&'py PyArray1<i64>, &'py PyArray2<f32>) {
        let active = &self.active_zombie_indices;
        let n = active.len();
        let uid_array = PyArray1::<i64>::zeros(py, [n], false);
        let py_array = PyArray2::<f32>::zeros(py, [n, 5], false);
        let uids = unsafe { uid_array.as_slice_mut().unwrap() };
        let slice = unsafe { py_array.as_slice_mut().unwrap() };

        let zombies_ref = &self.zombies;
        for (row, &zi) in active.iter().enumerate() {
            if zi >= zombies_ref.len() {
                continue;
            }
            let z = &zombies_ref[zi];
            let r = &mut slice[row * 5..row * 5 + 5];
            uids[row] = z.entity_id;
            r[0] = z.x;
            r[1] = z.y;
            r[2] = z.z as f32;
            r[3] = z.hp;
            r[4] = if z.is_alive { 1.0 } else { 0.0 };
        }

        (uid_array, py_array)
    }

    pub fn sync_survivors_batch(&mut self, data: PyReadonlyArray2<f32>) {
        let array = data.as_array();
        let rows = array.nrows();
        for i in 0..rows {
            let x = array[[i, 0]];
            let y = array[[i, 1]];
            let z = array[[i, 2]] as i32;
            let hp = array[[i, 3]];
            let hunger = array[[i, 4]];
            let thirst = array[[i, 5]];
            if i < self.survivors.len() {
                let surv = &mut self.survivors[i];
                surv.x = x;
                surv.y = y;
                surv.z = z;
                surv.hp = hp;
                surv.hunger = hunger;
                surv.thirst = thirst;
                surv.is_alive = hp > 0.0;
            } else {
                let mut s = RustSurvivorEntity::new(i, x, y, z);
                s.hp = hp;
                s.hunger = hunger;
                s.thirst = thirst;
                self.survivors.push(s);
            }
        }
        self.survivors.truncate(rows);
    }

    pub fn get_survivors_batch<'py>(&self, py: Python<'py>) -> &'py PyArray2<f32> {
        let n = self.survivors.len();
        let py_array = PyArray2::<f32>::zeros(py, [n, 4], false);
        let slice = unsafe { py_array.as_slice_mut().unwrap() };

        let survivors_ref = &self.survivors;
        slice
            .par_chunks_mut(4)
            .enumerate()
            .for_each(|(i, s_slice)| {
                if i < survivors_ref.len() {
                    let s = &survivors_ref[i];
                    s_slice[0] = s.x;
                    s_slice[1] = s.y;
                    s_slice[2] = s.z as f32;
                    s_slice[3] = if s.is_alive { 1.0 } else { 0.0 };
                }
            });

        py_array
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

    pub fn add_item(&mut self, x: f32, y: f32, z: i32, item_type: u32, amount: u32) {
        self.items.push(RustWorldItem {
            x,
            y,
            z,
            item_type,
            amount,
            active: true,
        });
    }

    pub fn clear_items(&mut self) {
        self.items.clear();
    }

    pub fn get_fitness_scores<'py>(&self, py: Python<'py>) -> &'py PyArray1<f32> {
        let n = self.survivors.len();
        let py_array = PyArray1::<f32>::zeros(py, [n], false);
        let slice = unsafe { py_array.as_slice_mut().unwrap() };
        for (i, surv) in self.survivors.iter().enumerate() {
            slice[i] = surv.calculate_fitness();
        }
        py_array
    }

    pub fn get_survivors_detailed_batch<'py>(&self, py: Python<'py>) -> &'py PyArray2<f32> {
        let n = self.survivors.len();
        let py_array = PyArray2::<f32>::zeros(py, [n, 12], false);
        let slice = unsafe { py_array.as_slice_mut().unwrap() };
        for (i, surv) in self.survivors.iter().enumerate() {
            let offset = i * 12;
            slice[offset] = surv.x;
            slice[offset + 1] = surv.y;
            slice[offset + 2] = surv.z as f32;
            slice[offset + 3] = surv.hp;
            slice[offset + 4] = surv.hunger;
            slice[offset + 5] = surv.thirst;
            slice[offset + 6] = if surv.is_alive { 1.0 } else { 0.0 };
            slice[offset + 7] = surv.score;
            slice[offset + 8] = surv.kills as f32;
            slice[offset + 9] = surv.ammo as f32;
            slice[offset + 10] = surv.food_items as f32;
            slice[offset + 11] = surv.medkits as f32;
        }
        py_array
    }

    pub fn get_items_batch<'py>(&self, py: Python<'py>) -> &'py PyArray2<f32> {
        let active_items: Vec<&RustWorldItem> = self.items.iter().filter(|it| it.active).collect();
        let n = active_items.len();
        let py_array = PyArray2::<f32>::zeros(py, [n, 5], false);
        let slice = unsafe { py_array.as_slice_mut().unwrap() };
        for (i, item) in active_items.iter().enumerate() {
            let offset = i * 5;
            slice[offset] = item.x;
            slice[offset + 1] = item.y;
            slice[offset + 2] = item.z as f32;
            slice[offset + 3] = item.item_type as f32;
            slice[offset + 4] = item.amount as f32;
        }
        py_array
    }

    pub fn step_simulation(&mut self, actions: Vec<i32>, movements: Vec<(f32, f32)>) {
        self.current_tick += 1;

        // Calculate ambient light based on 24-hour cycle (3,600 ticks = 1 day)
        let day_tick = (self.current_tick % 3600) as f32;
        let day_phase = (day_tick / 3600.0) * std::f32::consts::TAU;
        self.ambient_light = (0.2
            + 0.8 * ((day_phase - std::f32::consts::FRAC_PI_2).sin() * 0.5 + 0.5))
            .clamp(0.1, 1.0);

        let mut dropped_loot: Vec<(f32, f32, i32, u32)> = Vec::new();

        // 1. Update Survivors
        for (i, surv) in self.survivors.iter_mut().enumerate() {
            if !surv.is_alive {
                continue;
            }

            if i < movements.len() {
                let (dx, dy) = movements[i];
                if dx.abs() > 0.001 || dy.abs() > 0.001 {
                    surv.facing_angle = dy.atan2(dx);
                }
                let speed_mult = if surv.in_vehicle { 0.40 } else { 0.20 };
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

            // Update vitals (auto-eat, auto-drink, auto-heal if needed)
            surv.update_vitals(1);

            // Execute Actions 0..10
            let action = if i < actions.len() { actions[i] } else { 0 };
            match action {
                1 => {
                    // Action 1: Gather / Loot items nearby (within 1.8 units)
                    let sx = surv.x;
                    let sy = surv.y;
                    let sz = surv.z;
                    for item in self.items.iter_mut() {
                        if item.active && item.z == sz {
                            let d2 = (item.x - sx) * (item.x - sx) + (item.y - sy) * (item.y - sy);
                            if d2 <= 3.24 {
                                item.active = false;
                                match item.item_type {
                                    1 => surv.food_items += item.amount,
                                    2 => surv.water_items += item.amount,
                                    3 => surv.medkits += item.amount,
                                    4 => surv.ammo += item.amount,
                                    5 => surv.materials += item.amount,
                                    _ => surv.weapon_tier = surv.weapon_tier.max(item.amount),
                                }
                                surv.score += 5.0;
                                break;
                            }
                        }
                    }
                }
                2 => {
                    // Action 2: Craft / Use Medkit
                    if surv.hp < 80.0 && surv.medkits > 0 {
                        surv.medkits -= 1;
                        surv.hp = (surv.hp + 45.0).min(100.0);
                        surv.score += 5.0;
                    } else if surv.materials >= 2 {
                        surv.materials -= 2;
                        surv.medkits += 1;
                        surv.score += 10.0;
                    }
                }
                3 => {
                    // Action 3: Craft / Upgrade Weapon
                    if surv.materials >= 3 {
                        surv.materials -= 3;
                        surv.weapon_tier = (surv.weapon_tier + 1).min(3);
                        surv.score += 15.0;
                    }
                }
                4 => {
                    // Action 4: Vehicle Interaction (toggle vehicle)
                    surv.in_vehicle = !surv.in_vehicle;
                    surv.score += 2.0;
                }
                5 => {
                    // Action 5: Rest / Sleep
                    surv.sleep = (surv.sleep + 1.5).min(100.0);
                    surv.stamina = (surv.stamina + 1.5).min(100.0);
                    surv.score += 0.2;
                }
                6 => {
                    // Action 6: Attack (Melee or Ranged Firearm)
                    let surv_x = surv.x;
                    let surv_y = surv.y;
                    let surv_z = surv.z;

                    if surv.weapon_tier >= 2 && surv.ammo > 0 {
                        // Ranged firearm attack
                        surv.ammo -= 1;
                        self.noise_events.push((surv_x, surv_y, surv_z, 80.0));
                        let mut target_idx: Option<usize> = None;
                        let mut min_d2 = 625.0f32; // 25^2
                        for &zi in &self.active_zombie_indices {
                            if zi >= self.zombies.len() {
                                continue;
                            }
                            let z = &self.zombies[zi];
                            if z.is_alive && z.z == surv_z {
                                let d2 = (z.x - surv_x) * (z.x - surv_x)
                                    + (z.y - surv_y) * (z.y - surv_y);
                                if d2 < min_d2 {
                                    min_d2 = d2;
                                    target_idx = Some(zi);
                                }
                            }
                        }
                        if let Some(zi) = target_idx {
                            let z = &mut self.zombies[zi];
                            z.hp -= 80.0;
                            if z.hp <= 0.0 {
                                z.is_alive = false;
                                surv.kills += 1;
                                surv.score += 25.0;
                                dropped_loot.push((
                                    z.x,
                                    z.y,
                                    z.z,
                                    ((self.current_tick % 5) + 1) as u32,
                                ));
                            }
                        }
                    } else {
                        // Melee attack
                        self.noise_events.push((surv_x, surv_y, surv_z, 15.0));
                        let dmg = if surv.weapon_tier == 1 { 45.0 } else { 25.0 };
                        let active_melee: Vec<usize> = self.active_zombie_indices.clone();
                        for zi in active_melee {
                            if zi >= self.zombies.len() {
                                continue;
                            }
                            let z = &mut self.zombies[zi];
                            if z.is_alive && z.z == surv_z {
                                let dz_x = z.x - surv_x;
                                let dz_y = z.y - surv_y;
                                if dz_x * dz_x + dz_y * dz_y <= 3.24 {
                                    z.hp -= dmg;
                                    if z.hp <= 0.0 {
                                        z.is_alive = false;
                                        surv.kills += 1;
                                        surv.score += 20.0;
                                        dropped_loot.push((
                                            z.x,
                                            z.y,
                                            z.z,
                                            ((self.current_tick % 5) + 1) as u32,
                                        ));
                                    }
                                    break;
                                }
                            }
                        }
                    }
                }
                7 => {
                    // Action 7: Climb up
                    if surv.z < 5 && self.world_grid.is_walkable(surv.x, surv.y, surv.z + 1) {
                        surv.z += 1;
                    }
                }
                8 => {
                    // Action 8: Climb down
                    if surv.z > -2 && self.world_grid.is_walkable(surv.x, surv.y, surv.z - 1) {
                        surv.z -= 1;
                    }
                }
                9 => {
                    // Action 9: Push / Reinforce furniture or barricade
                    let tx = surv.x as i32;
                    let ty = surv.y as i32;
                    let tz = surv.z;
                    for (dx, dy) in [(-1, 0), (1, 0), (0, -1), (0, 1)] {
                        let tile = self.world_grid.get_tile(tx + dx, ty + dy, tz);
                        if matches!(tile, 2 | 7 | 49 | 62) {
                            self.noise_events.push((surv.x, surv.y, surv.z, 20.0));
                            surv.score += 5.0;
                            break;
                        }
                    }
                }
                10 => {
                    // Action 10: Dismantle obstacle tile
                    let tx = surv.x as i32;
                    let ty = surv.y as i32;
                    let tz = surv.z;
                    for (dx, dy) in [(-1, 0), (1, 0), (0, -1), (0, 1)] {
                        let tile = self.world_grid.get_tile(tx + dx, ty + dy, tz);
                        if matches!(tile, 7 | 49 | 62 | 63) {
                            self.world_grid.set_tile(tx + dx, ty + dy, tz, 3); // clear to floor
                            surv.materials += 2;
                            surv.score += 10.0;
                            self.noise_events.push((surv.x, surv.y, surv.z, 25.0));
                            break;
                        }
                    }
                }
                _ => {} // Action 0: Idle
            }
        }

        // Spawn dropped loot from killed zombies
        for (lx, ly, lz, itype) in dropped_loot {
            self.items.push(RustWorldItem {
                x: lx,
                y: ly,
                z: lz,
                item_type: itype,
                amount: 1,
                active: true,
            });
        }

        // 2. Update Zombies (with flocking + perception)
        let active_survivors: Vec<(f32, f32, i32)> = self
            .survivors
            .iter()
            .filter(|s| s.is_alive)
            .map(|s| (s.x, s.y, s.z))
            .collect();

        let num_zombies = self.zombies.len();
        let mut steerings = vec![(0.0f32, 0.0f32); num_zombies];
        let mut behavior_modes = vec![0u8; num_zombies];

        // Active-window membership lookup: zombies frozen in inactive chunks
        // keep their state but are not stepped by flocking/movement this tick.
        let mut is_active = vec![false; num_zombies];
        for &zi in &self.active_zombie_indices {
            if zi < num_zombies {
                is_active[zi] = true;
            }
        }

        // Parallelized Flocking separation and mode assessment using Rayon
        let zombies_ref = &self.zombies;
        steerings
            .par_iter_mut()
            .zip(behavior_modes.par_iter_mut())
            .enumerate()
            .for_each(|(i, (steer, mode))| {
                let z1 = &zombies_ref[i];
                if !z1.is_alive || !is_active[i] {
                    return;
                }
                let mut sep_x = 0.0f32;
                let mut sep_y = 0.0f32;
                let mut nearby_count = 0usize;

                for (j, z2) in zombies_ref.iter().enumerate() {
                    if i == j || !z2.is_alive || z1.z != z2.z {
                        continue;
                    }
                    let dx = z1.x - z2.x;
                    let dy = z1.y - z2.y;
                    let d2 = dx * dx + dy * dy;
                    if d2 < 36.0 {
                        nearby_count += 1;
                    }
                    if d2 > 0.0001 && d2 < 2.25 {
                        let d = d2.sqrt();
                        sep_x += (dx / d) * (1.5 - d);
                        sep_y += (dy / d) * (1.5 - d);
                    }
                }
                *steer = (sep_x, sep_y);
                *mode = if nearby_count >= 9 {
                    2
                } else if nearby_count >= 3 {
                    1
                } else {
                    0
                };
            });

        // Track zombie pressure against door/barricade tiles
        let mut tile_pressure: HashMap<(i32, i32, i32), usize> = HashMap::new();

        // Move zombies and check bite attacks (active window only)
        for (i, zombie) in self.zombies.iter_mut().enumerate() {
            if !zombie.is_alive || !is_active[i] {
                continue;
            }

            zombie.behavior_mode = behavior_modes[i];

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
                            nx, ny, nz, vol, zombie.x, zombie.y, zombie.z,
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
                    let mode_speed_mult = if zombie.behavior_mode == 2 {
                        1.25
                    } else if zombie.behavior_mode == 1 {
                        1.0
                    } else {
                        0.85
                    };
                    let cur_speed = zombie.speed * mode_speed_mult;

                    let move_x = (dx / dist) * cur_speed + sep_x * 0.05;
                    let move_y = (dy / dist) * cur_speed + sep_y * 0.05;

                    let new_zx = (zombie.x + move_x).max(0.0).min((self.width - 1) as f32);
                    let new_zy = (zombie.y + move_y).max(0.0).min((self.height - 1) as f32);

                    if self.world_grid.is_walkable(new_zx, new_zy, zombie.z) {
                        zombie.x = new_zx;
                        zombie.y = new_zy;
                    } else {
                        let obstacle_x = new_zx as i32;
                        let obstacle_y = new_zy as i32;
                        *tile_pressure
                            .entry((obstacle_x, obstacle_y, zombie.z))
                            .or_insert(0) += 1;
                    }
                }
            } else {
                let (sep_x, sep_y) = steerings[i];
                zombie.wander_angle += ((self.current_tick + i as u64) % 7) as f32 * 0.1 - 0.3;
                let wander_speed = zombie.speed * 0.35;
                let move_x = zombie.wander_angle.cos() * wander_speed + sep_x * 0.03;
                let move_y = zombie.wander_angle.sin() * wander_speed + sep_y * 0.03;

                let new_zx = (zombie.x + move_x).max(0.0).min((self.width - 1) as f32);
                let new_zy = (zombie.y + move_y).max(0.0).min((self.height - 1) as f32);

                if self.world_grid.is_walkable(new_zx, new_zy, zombie.z) {
                    zombie.x = new_zx;
                    zombie.y = new_zy;
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

        // Apply horde pressure: breach obstacles pushed by >= 3 zombies
        for ((ox, oy, oz), pressure) in tile_pressure {
            if pressure >= 3 {
                let tile = self.world_grid.get_tile(ox, oy, oz);
                if matches!(tile, 7 | 49 | 62 | 63) {
                    self.world_grid.set_tile(ox, oy, oz, 3);
                }
            }
        }

        // Retain only active items if items buffer grows too large
        if self.items.len() > 2500 {
            self.items.retain(|it| it.active);
        }

        // Clear processed noise events
        self.noise_events.clear();
    }

    pub fn get_observations_matrix<'py>(&self, py: Python<'py>) -> &'py PyArray2<f32> {
        let num_survivors = self.survivors.len();
        let py_array = PyArray2::<f32>::zeros(py, [num_survivors, 57], false);
        let slice = unsafe { py_array.as_slice_mut().unwrap() };

        let survivors_ref = &self.survivors;
        let zombies_ref = &self.zombies;
        let active_zombie_indices_ref = &self.active_zombie_indices;
        let items_ref = &self.items;
        let ambient = self.ambient_light;
        let width_f = self.width as f32;
        let height_f = self.height as f32;
        let cur_tick = self.current_tick;
        let grid_ref = &self.world_grid;

        slice
            .par_chunks_mut(57)
            .enumerate()
            .for_each(|(i, chunk_slice)| {
                if i >= survivors_ref.len() {
                    return;
                }
                let surv = &survivors_ref[i];

                // 0..4: Vitals & Light
                chunk_slice[0] = surv.hp / 100.0;
                chunk_slice[1] = surv.hunger / 100.0;
                chunk_slice[2] = surv.thirst / 100.0;
                chunk_slice[3] = surv.sleep / 100.0;
                chunk_slice[4] = ambient;

                // 5..7: Equipment & Vehicle
                chunk_slice[5] = if surv.in_vehicle { 1.0 } else { 0.0 };
                chunk_slice[6] = if surv.weapon_tier > 0 { 1.0 } else { 0.0 };
                chunk_slice[7] = if surv.medkits > 0 { 1.0 } else { 0.0 };

                // 8..10: Closest Zombie dx, dy, dz
                let mut min_z_dist2 = 625.0f32; // 25^2
                let mut z_dx = 0.0f32;
                let mut z_dy = 0.0f32;
                let mut z_dz = 0.0f32;
                for &zi in active_zombie_indices_ref {
                    if zi >= zombies_ref.len() {
                        continue;
                    }
                    let z = &zombies_ref[zi];
                    if z.is_alive && z.z == surv.z {
                        let dx = z.x - surv.x;
                        let dy = z.y - surv.y;
                        let d2 = dx * dx + dy * dy;
                        if d2 < min_z_dist2 {
                            min_z_dist2 = d2;
                            z_dx = (dx / 25.0).clamp(-1.0, 1.0);
                            z_dy = (dy / 25.0).clamp(-1.0, 1.0);
                            z_dz = (z.z - surv.z) as f32 / 20.0;
                        }
                    }
                }
                chunk_slice[8] = z_dx;
                chunk_slice[9] = z_dy;
                chunk_slice[10] = z_dz;

                // 11..13: Closest Item dx, dy, dz
                let mut min_i_dist2 = 625.0f32;
                let mut i_dx = 0.0f32;
                let mut i_dy = 0.0f32;
                let mut i_dz = 0.0f32;
                for it in items_ref {
                    if it.active && it.z == surv.z {
                        let dx = it.x - surv.x;
                        let dy = it.y - surv.y;
                        let d2 = dx * dx + dy * dy;
                        if d2 < min_i_dist2 {
                            min_i_dist2 = d2;
                            i_dx = (dx / 25.0).clamp(-1.0, 1.0);
                            i_dy = (dy / 25.0).clamp(-1.0, 1.0);
                            i_dz = (it.z - surv.z) as f32 / 20.0;
                        }
                    }
                }
                chunk_slice[11] = i_dx;
                chunk_slice[12] = i_dy;
                chunk_slice[13] = i_dz;

                // 14..16: Resource indicators
                chunk_slice[14] = (surv.ammo as f32 / 50.0).clamp(0.0, 1.0);
                chunk_slice[15] = (surv.food_items as f32 / 10.0).clamp(0.0, 1.0);
                chunk_slice[16] = (surv.water_items as f32 / 10.0).clamp(0.0, 1.0);

                // 17..19: Materials & Stats
                chunk_slice[17] = (surv.materials as f32 / 10.0).clamp(0.0, 1.0);
                chunk_slice[18] = (surv.weapon_tier as f32 / 3.0).clamp(0.0, 1.0);
                chunk_slice[19] = (surv.stamina / 100.0).clamp(0.0, 1.0);

                // 20..23: Position & Time
                chunk_slice[20] = (surv.x / width_f).clamp(0.0, 1.0);
                chunk_slice[21] = (surv.y / height_f).clamp(0.0, 1.0);
                chunk_slice[22] = (surv.z as f32 / 20.0).clamp(-1.0, 1.0);
                chunk_slice[23] = (cur_tick % 3600) as f32 / 3600.0;

                // 24..31: Morale, Score, Kills
                chunk_slice[24] = 0.0;
                chunk_slice[25] = 0.0;
                chunk_slice[26] = 0.8;
                chunk_slice[27] = surv.hp / 100.0;
                chunk_slice[28] = surv.hp / 100.0;
                chunk_slice[29] = surv.hp / 100.0;
                chunk_slice[30] = 0.0;
                chunk_slice[31] = (surv.kills as f32 / 20.0).clamp(0.0, 1.0);

                // 32..56: 5x5 Local Spatial Grid Vision
                let sx = surv.x as i32;
                let sy = surv.y as i32;
                let sz = surv.z;
                let mut sensor_idx = 32;

                for dy in -2..=2 {
                    for dx in -2..=2 {
                        if sensor_idx < 57 {
                            let tx = sx + dx;
                            let ty = sy + dy;
                            chunk_slice[sensor_idx] =
                                if grid_ref.is_walkable(tx as f32, ty as f32, sz) {
                                    1.0
                                } else {
                                    -1.0
                                };
                            sensor_idx += 1;
                        }
                    }
                }
            });

        py_array
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
    pub fn new(
        num_envs: usize,
        width: usize,
        height: usize,
        num_survivors: usize,
        num_zombies: usize,
    ) -> Self {
        let mut envs = Vec::with_capacity(num_envs);
        for _ in 0..num_envs {
            envs.push(RustFullSimulationCore::new(
                width,
                height,
                num_survivors,
                num_zombies,
            ));
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
                let actions = if i < all_actions.len() {
                    all_actions[i].clone()
                } else {
                    vec![]
                };
                let movements = if i < all_movements.len() {
                    all_movements[i].clone()
                } else {
                    vec![]
                };
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
                            let is_walk = if env.world_grid.is_walkable(tx as f32, ty as f32, sz) {
                                1.0f32
                            } else {
                                0.0f32
                            };
                            total_obs[s_offset + sensor_idx] = is_walk;
                            sensor_idx += 1;
                        }
                    }
                }
            }
        }

        let array3d =
            numpy::ndarray::Array3::from_shape_vec((num_envs, num_survivors, 57), total_obs)
                .unwrap();
        array3d.into_pyarray(py)
    }
}
