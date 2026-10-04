use pyo3::prelude::*;
use pyo3::types::PyBytes;

#[pyclass]
pub struct VulkanTileRenderer {
    map_draw_width: u32,
    map_draw_height: u32,
    tile_size: u32,
    pixel_width: usize,
    pixel_height: usize,
}

#[pymethods]
impl VulkanTileRenderer {
    #[new]
    fn new(map_draw_width: u32, map_draw_height: u32, tile_size: u32) -> Self {
        let pixel_width = (map_draw_width * tile_size) as usize;
        let pixel_height = (map_draw_height * tile_size) as usize;
        VulkanTileRenderer {
            map_draw_width,
            map_draw_height,
            tile_size,
            pixel_width,
            pixel_height,
        }
    }

    /// Fast viewport tile grid renderer into RGBA pixel buffer PyBytes.
    fn render_viewport_bytes<'py>(
        &self,
        py: Python<'py>,
        grid_slice: &[u8],
        building_override: &[u8],
        tile_palette: Vec<(u8, u8, u8)>,
        light: f32,
        fog_mask: Option<&[u8]>,
    ) -> &'py PyBytes {
        let buffer_size = self.pixel_width * self.pixel_height * 4;
        let mut buffer = vec![255u8; buffer_size];

        let ts = self.tile_size as usize;
        let mw = self.map_draw_width as usize;
        let mh = self.map_draw_height as usize;
        let stride = self.pixel_width * 4;

        let has_building = !building_override.is_empty();
        let has_fog = fog_mask.is_some();
        let fog_buf = fog_mask.unwrap_or(&[]);

        for ty in 0..mh {
            let row_offset_tiles = ty * mw;
            let py_start = ty * ts;

            for tx in 0..mw {
                let tile_idx = row_offset_tiles + tx;
                let px_start = tx * ts;

                let is_visible = if has_fog {
                    fog_buf.get(tile_idx).copied().unwrap_or(1) > 0
                } else {
                    true
                };

                let (r_base, g_base, b_base) = if !is_visible {
                    (10u8, 10u8, 10u8)
                } else {
                    let mut r = 0u8;
                    let mut g = 0u8;
                    let mut b = 0u8;
                    let mut override_found = false;

                    if has_building {
                        let b_idx = tile_idx * 3;
                        if b_idx + 2 < building_override.len() {
                            let br = building_override[b_idx];
                            let bg = building_override[b_idx + 1];
                            let bb = building_override[b_idx + 2];
                            if br > 0 || bg > 0 || bb > 0 {
                                r = br;
                                g = bg;
                                b = bb;
                                override_found = true;
                            }
                        }
                    }

                    if !override_found {
                        let t_type = grid_slice.get(tile_idx).copied().unwrap_or(0) as usize;
                        if t_type < tile_palette.len() {
                            let p = tile_palette[t_type];
                            r = p.0;
                            g = p.1;
                            b = p.2;
                        } else {
                            r = 50;
                            g = 50;
                            b = 50;
                        }
                    }

                    (
                        (r as f32 * light) as u8,
                        (g as f32 * light) as u8,
                        (b as f32 * light) as u8,
                    )
                };

                for dy in 0..ts {
                    let line_start = (py_start + dy) * stride + px_start * 4;
                    for dx in 0..ts {
                        let px_idx = line_start + dx * 4;
                        if px_idx + 3 < buffer.len() {
                            buffer[px_idx] = r_base;
                            buffer[px_idx + 1] = g_base;
                            buffer[px_idx + 2] = b_base;
                            buffer[px_idx + 3] = 255;
                        }
                    }
                }
            }
        }

        PyBytes::new(py, &buffer)
    }

    fn render_grid_buffer(&self, grid: Vec<i32>, light: f32) -> Vec<u8> {
        let num_pixels = (self.pixel_width * self.pixel_height * 4) as usize;
        let mut buffer = vec![20u8; num_pixels];

        for (idx, &tile) in grid.iter().enumerate() {
            let x = (idx % self.map_draw_width as usize) as u32;
            let y = (idx / self.map_draw_width as usize) as u32;

            let (r, g, b) = match tile {
                0 => (34u8, 139u8, 34u8),
                1 => (105u8, 105u8, 105u8),
                2 => (100u8, 50u8, 20u8),
                3 => (210u8, 180u8, 140u8),
                _ => (50u8, 50u8, 50u8),
            };

            let px = (y as usize * self.map_draw_width as usize + x as usize) * 4;
            if px + 3 < buffer.len() {
                buffer[px] = (r as f32 * light) as u8;
                buffer[px + 1] = (g as f32 * light) as u8;
                buffer[px + 2] = (b as f32 * light) as u8;
                buffer[px + 3] = 255;
            }
        }

        buffer
    }
}

/// High-performance Rust zombie flocking steering calculation.
/// Inputs:
/// - `zombie_coords`: flattened array of [x, y, z] floats for active zombies
/// - `separation_dist`: distance threshold for horde separation force
/// Returns:
/// - flattened array of [steering_dx, steering_dy] vectors for each zombie
#[pyfunction]
pub fn compute_zombie_flock_steering(
    zombie_coords: Vec<f32>,
    separation_dist: f32,
) -> Vec<f32> {
    let num_zombies = zombie_coords.len() / 3;
    let mut steering_vectors = vec![0.0f32; num_zombies * 2];

    if num_zombies < 2 {
        return steering_vectors;
    }

    let sq_sep = separation_dist * separation_dist;

    for i in 0..num_zombies {
        let z1_x = zombie_coords[i * 3];
        let z1_y = zombie_coords[i * 3 + 1];
        let z1_z = zombie_coords[i * 3 + 2];

        let mut sep_x = 0.0f32;
        let mut sep_y = 0.0f32;

        for j in 0..num_zombies {
            if i == j {
                continue;
            }

            let z2_x = zombie_coords[j * 3];
            let z2_y = zombie_coords[j * 3 + 1];
            let z2_z = zombie_coords[j * 3 + 2];

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

    steering_vectors
}

#[pymodule]
fn rust_vulkan_render(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<VulkanTileRenderer>()?;
    m.add_function(wrap_pyfunction!(compute_zombie_flock_steering, m)?)?;
    Ok(())
}
