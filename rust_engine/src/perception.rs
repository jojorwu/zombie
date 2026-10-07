use pyo3::prelude::*;
use numpy::PyReadonlyArray3;
use std::collections::HashSet;

pub fn is_opaque_tile(t: i64) -> bool {
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
