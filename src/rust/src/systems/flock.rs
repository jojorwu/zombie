use pyo3::prelude::*;
use numpy::{PyArray1, PyReadonlyArray1, IntoPyArray};

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
