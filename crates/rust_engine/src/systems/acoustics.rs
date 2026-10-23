use pyo3::prelude::*;

/// Native Acoustic Decibel Noise Propagation Engine in Rust.
#[pyclass]
pub struct RustAcousticSystem;

#[pymethods]
impl RustAcousticSystem {
    #[new]
    pub fn new() -> Self {
        RustAcousticSystem
    }

    /// Source sound pressure level (dB SPL) per noise profile.
    /// Mirrors `SoundUtility.SOUND_PROFILES` in the Python fallback layer.
    #[staticmethod]
    pub fn get_source_db_spl(source_type: &str) -> f32 {
        match source_type {
            "rifle_shot" | "assault_rifle_shot" => 155.0,
            "sniper_shot" => 165.0,
            "shotgun_shot" => 160.0,
            "pistol_shot" => 140.0,
            "magnum_shot" => 150.0,
            "smg_shot" => 142.0,
            "crossbow_shot" => 25.0,
            "sledgehammer" | "vehicle_engine" => 85.0,
            "furniture_push" => 70.0,
            "dismantling" => 75.0,
            "footsteps" => 40.0,
            "crafting" => 55.0,
            "thunder" => 120.0,
            _ => 50.0,
        }
    }

    #[staticmethod]
    pub fn propagate_noise_decibels(
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

impl Default for RustAcousticSystem {
    fn default() -> Self {
        Self::new()
    }
}
