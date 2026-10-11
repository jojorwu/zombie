use pyo3::prelude::*;

pub mod ai;
pub mod entities;
pub mod modding;
pub mod renderer;
pub mod simulation;
pub mod systems;
pub mod world;

use ai::RustBrainInference;

use entities::{
    RustAnatomicalHealth, RustContainerUtility, RustEntityManager, RustFoodSpoilageUtility, RustSurvivorEntity,
    RustVehiclePhysics, RustZombieEngine,
};
use modding::RustLuaModManager;
use renderer::VulkanTileRenderer;
use simulation::{RustEngineCore, RustFullSimulationCore, RustParallelEnvManager, RustSpatialGrid};
use systems::{
    compute_a_star_3d_path, compute_zombie_flock_steering, RustAcousticSystem, RustAnimalUtility,
    RustBallisticsUtility, RustElectricityUtility, RustEnvironmentManager, RustItemStateUtility,
    RustPNPComplexityEngine, RustParticleSystem, RustPlantUtility, RustTileInteractionUtility,
};
use world::{check_line_of_sight_rust, compute_fog_of_war_rust, RustWorldGenerator, RustWorldGrid, RustChunkManager};

#[pymodule]
fn rust_engine(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<VulkanTileRenderer>()?;
    m.add_class::<RustBrainInference>()?;
    m.add_class::<RustWorldGenerator>()?;
    m.add_class::<RustWorldGrid>()?;
    m.add_class::<RustChunkManager>()?;
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
    m.add_class::<RustParallelEnvManager>()?;
    m.add_class::<RustSurvivorEntity>()?;
    m.add_class::<RustEntityManager>()?;
    m.add_class::<RustPNPComplexityEngine>()?;
    m.add_class::<RustElectricityUtility>()?;
    m.add_class::<RustTileInteractionUtility>()?;
    m.add_class::<RustItemStateUtility>()?;
    m.add_class::<RustPlantUtility>()?;
    m.add_class::<RustAnimalUtility>()?;
    m.add_function(wrap_pyfunction!(compute_zombie_flock_steering, m)?)?;
    m.add_function(wrap_pyfunction!(compute_a_star_3d_path, m)?)?;
    m.add_function(wrap_pyfunction!(check_line_of_sight_rust, m)?)?;
    m.add_function(wrap_pyfunction!(compute_fog_of_war_rust, m)?)?;
    Ok(())
}
