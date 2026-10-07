use pyo3::prelude::*;

pub mod entities;
pub mod modding;
pub mod renderer;
pub mod simulation;
pub mod systems;
pub mod world;

use entities::{
    RustAnatomicalHealth, RustContainerUtility, RustFoodSpoilageUtility, RustSurvivorEntity,
    RustVehiclePhysics, RustZombieEngine,
};
use modding::RustLuaModManager;
use renderer::VulkanTileRenderer;
use simulation::{RustEngineCore, RustFullSimulationCore, RustSpatialGrid};
use systems::{
    compute_a_star_3d_path, compute_zombie_flock_steering, RustAcousticSystem,
    RustBallisticsUtility, RustEnvironmentManager, RustParticleSystem,
};
use world::{check_line_of_sight_rust, compute_fog_of_war_rust};

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
    m.add_class::<RustSurvivorEntity>()?;
    m.add_function(wrap_pyfunction!(compute_zombie_flock_steering, m)?)?;
    m.add_function(wrap_pyfunction!(compute_a_star_3d_path, m)?)?;
    m.add_function(wrap_pyfunction!(check_line_of_sight_rust, m)?)?;
    m.add_function(wrap_pyfunction!(compute_fog_of_war_rust, m)?)?;
    Ok(())
}
