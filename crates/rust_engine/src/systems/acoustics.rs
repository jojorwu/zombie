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
