use pyo3::prelude::*;
use numpy::{PyArray1, PyArray2, IntoPyArray};

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
    pub fn new(width: usize, height: usize) -> Self {
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

    pub fn sync_survivor_state(&mut self, x: f32, y: f32, z: i32, health: f32, hunger: f32, thirst: f32, current_tick: u64) {
        self.survivor_x = x;
        self.survivor_y = y;
        self.survivor_z = z;
        self.survivor_health = health;
        self.survivor_hunger = hunger;
        self.survivor_thirst = thirst;
        self.current_tick = current_tick;
    }

    pub fn step(&mut self, dx: f32, dy: f32, _action: i32) {
        self.current_tick += 1;
        self.survivor_x = (self.survivor_x + dx * 0.15).max(0.0).min((self.width - 1) as f32);
        self.survivor_y = (self.survivor_y + dy * 0.15).max(0.0).min((self.height - 1) as f32);
        self.survivor_hunger = (self.survivor_hunger - 0.025).max(0.0);
        self.survivor_thirst = (self.survivor_thirst - 0.035).max(0.0);
    }

    pub fn get_observation_flat<'py>(&self, py: Python<'py>) -> &'py PyArray1<f32> {
        let mut obs = vec![0.0f32; 57];
        obs[0] = self.survivor_health / 100.0;
        obs[1] = self.survivor_hunger / 100.0;
        obs[2] = self.survivor_thirst / 100.0;
        obs[3] = 1.0;
        obs[4] = 1.0;
        obs[22] = self.survivor_z as f32 / 20.0;
        obs.into_pyarray(py)
    }

    pub fn get_current_tick(&self) -> u64 {
        self.current_tick
    }

    pub fn get_survivor_pos(&self) -> (f32, f32, i32) {
        (self.survivor_x, self.survivor_y, self.survivor_z)
    }
}

/// Native Full Simulation Core in Rust.
#[pyclass]
pub struct RustFullSimulationCore {
    pub width: usize,
    pub height: usize,
    pub current_tick: u64,
    pub survivors: Vec<(f32, f32, i32, f32, f32, f32)>, // (x, y, z, hp, hunger, thirst)
    pub zombies: Vec<(f32, f32, i32, f32, f32)>,        // (x, y, z, hp, speed)
}

#[pymethods]
impl RustFullSimulationCore {
    #[new]
    pub fn new(width: usize, height: usize, num_survivors: usize, num_zombies: usize) -> Self {
        let mut survivors = Vec::with_capacity(num_survivors);
        for _ in 0..num_survivors {
            survivors.push(((width / 2) as f32, (height / 2) as f32, 0, 100.0, 100.0, 100.0));
        }

        let mut zombies = Vec::with_capacity(num_zombies);
        for _ in 0..num_zombies {
            zombies.push(((width / 4) as f32, (height / 4) as f32, 0, 50.0, 0.07));
        }

        RustFullSimulationCore {
            width,
            height,
            current_tick: 0,
            survivors,
            zombies,
        }
    }

    pub fn sync_survivor_at(&mut self, index: usize, x: f32, y: f32, z: i32, hp: f32, hunger: f32, thirst: f32) {
        if index < self.survivors.len() {
            self.survivors[index] = (x, y, z, hp, hunger, thirst);
        }
    }

    pub fn step_simulation(&mut self, _actions: Vec<i32>, movements: Vec<(f32, f32)>) {
        self.current_tick += 1;

        for (i, surv) in self.survivors.iter_mut().enumerate() {
            if i < movements.len() {
                let (dx, dy) = movements[i];
                surv.0 = (surv.0 + dx * 0.15).max(0.0).min((self.width - 1) as f32);
                surv.1 = (surv.1 + dy * 0.15).max(0.0).min((self.height - 1) as f32);
            }
            surv.4 = (surv.4 - 0.025).max(0.0);
            surv.5 = (surv.5 - 0.035).max(0.0);
        }

        for zombie in self.zombies.iter_mut() {
            if let Some(closest) = self.survivors.first() {
                let dx = closest.0 - zombie.0;
                let dy = closest.1 - zombie.1;
                let dist = (dx * dx + dy * dy).sqrt();
                if dist > 0.5 {
                    zombie.0 += (dx / dist) * zombie.4;
                    zombie.1 += (dy / dist) * zombie.4;
                }
            }
        }
    }

    pub fn get_observations_matrix<'py>(&self, py: Python<'py>) -> &'py PyArray2<f32> {
        let num_survivors = self.survivors.len();
        let mut obs_matrix = vec![0.0f32; num_survivors * 57];

        for (i, surv) in self.survivors.iter().enumerate() {
            let row_offset = i * 57;
            obs_matrix[row_offset] = surv.3 / 100.0;
            obs_matrix[row_offset + 1] = surv.4 / 100.0;
            obs_matrix[row_offset + 2] = surv.5 / 100.0;
            obs_matrix[row_offset + 3] = 1.0;
            obs_matrix[row_offset + 4] = 1.0;
            obs_matrix[row_offset + 22] = surv.2 as f32 / 20.0;
        }

        let array2d = numpy::ndarray::Array2::from_shape_vec((num_survivors, 57), obs_matrix).unwrap();
        array2d.into_pyarray(py)
    }

    pub fn get_current_tick(&self) -> u64 {
        self.current_tick
    }
}
