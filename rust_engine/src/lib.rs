use pyo3::prelude::*;

pub mod acoustics;
pub mod ballistics;
pub mod container;
pub mod core;
pub mod environment;
pub mod flock;
pub mod health;
pub mod modding;
pub mod pathfinding;
pub mod perception;
pub mod physics;
pub mod renderer;

use acoustics::RustAcousticSystem;
use ballistics::{RustBallisticsUtility, RustParticleSystem};
use container::{RustContainerUtility, RustFoodSpoilageUtility};
use core::{RustEngineCore, RustFullSimulationCore, RustSpatialGrid, RustZombieEngine};
use environment::RustEnvironmentManager;
use flock::compute_zombie_flock_steering;
use health::RustAnatomicalHealth;
use modding::RustLuaModManager;
use pathfinding::compute_a_star_3d_path;
use perception::{check_line_of_sight_rust, compute_fog_of_war_rust};
use physics::RustVehiclePhysics;
use renderer::VulkanTileRenderer;

#[pymodule]
fn rust_engine(_py: Python, m: &PyModule) -> PyResult<()> {
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
    m.add_class::<RustFullSimulationCore>()?;
    m.add_function(wrap_pyfunction!(compute_zombie_flock_steering, m)?)?;
    m.add_function(wrap_pyfunction!(compute_a_star_3d_path, m)?)?;
    m.add_function(wrap_pyfunction!(check_line_of_sight_rust, m)?)?;
    m.add_function(wrap_pyfunction!(compute_fog_of_war_rust, m)?)?;
    Ok(())
}
