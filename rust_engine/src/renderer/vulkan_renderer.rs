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
    pub fn new(map_draw_width: u32, map_draw_height: u32, tile_size: u32) -> Self {
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

    pub fn render_viewport_bytes<'py>(
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

    #[pyo3(signature = (grid_slice, building_override, tile_palette, light, survivors, zombies, vehicles, items, fog_mask=None))]
    pub fn render_composite_viewport<'py>(
        &self,
        py: Python<'py>,
        grid_slice: &[u8],
        building_override: &[u8],
        tile_palette: Vec<(u8, u8, u8)>,
        light: f32,
        survivors: Vec<(f32, f32, bool)>, // (x, y, is_selected)
        zombies: Vec<(f32, f32)>,         // (x, y)
        vehicles: Vec<(f32, f32)>,        // (x, y)
        items: Vec<(f32, f32)>,           // (x, y)
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

        // Draw items
        for (ix, iy) in items {
            let px = (ix * ts as f32) as i32;
            let py = (iy * ts as f32) as i32;
            Self::draw_filled_circle(&mut buffer, self.pixel_width, self.pixel_height, px, py, 3, (255, 215, 0));
        }

        // Draw vehicles
        for (vx, vy) in vehicles {
            let px = (vx * ts as f32) as i32;
            let py = (vy * ts as f32) as i32;
            Self::draw_filled_rect(&mut buffer, self.pixel_width, self.pixel_height, px - 6, py - 6, 12, 12, (70, 130, 180));
        }

        // Draw zombies
        for (zx, zy) in zombies {
            let px = (zx * ts as f32) as i32;
            let py = (zy * ts as f32) as i32;
            Self::draw_filled_circle(&mut buffer, self.pixel_width, self.pixel_height, px, py, 5, (178, 34, 34));
        }

        // Draw survivors
        for (sx, sy, is_sel) in survivors {
            let px = (sx * ts as f32) as i32;
            let py = (sy * ts as f32) as i32;
            let col = if is_sel { (255, 255, 255) } else { (50, 205, 50) };
            Self::draw_filled_circle(&mut buffer, self.pixel_width, self.pixel_height, px, py, 6, col);
        }

        PyBytes::new(py, &buffer)
    }

    /// Renders headless PPM image bytes directly for offscreen video/GIF recording without Pygame.
    pub fn render_offscreen_ppm<'py>(
        &self,
        py: Python<'py>,
        rgba_buffer: &[u8],
    ) -> &'py PyBytes {
        let header = format!("P6\n{} {}\n255\n", self.pixel_width, self.pixel_height);
        let mut ppm_data = header.into_bytes();
        ppm_data.reserve((self.pixel_width * self.pixel_height * 3) as usize);

        for chunk in rgba_buffer.chunks(4) {
            if chunk.len() >= 3 {
                ppm_data.push(chunk[0]);
                ppm_data.push(chunk[1]);
                ppm_data.push(chunk[2]);
            }
        }

        PyBytes::new(py, &ppm_data)
    }

    pub fn render_grid_buffer(&self, grid: Vec<i32>, light: f32) -> Vec<u8> {
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

impl VulkanTileRenderer {
    fn draw_filled_circle(
        buffer: &mut [u8],
        width: usize,
        height: usize,
        cx: i32,
        cy: i32,
        radius: i32,
        color: (u8, u8, u8),
    ) {
        let r_sq = radius * radius;
        for dy in -radius..=radius {
            for dx in -radius..=radius {
                if dx * dx + dy * dy <= r_sq {
                    let px = cx + dx;
                    let py = cy + dy;
                    if px >= 0 && px < width as i32 && py >= 0 && py < height as i32 {
                        let idx = (py as usize * width + px as usize) * 4;
                        if idx + 3 < buffer.len() {
                            buffer[idx] = color.0;
                            buffer[idx + 1] = color.1;
                            buffer[idx + 2] = color.2;
                            buffer[idx + 3] = 255;
                        }
                    }
                }
            }
        }
    }

    fn draw_filled_rect(
        buffer: &mut [u8],
        width: usize,
        height: usize,
        rx: i32,
        ry: i32,
        rw: i32,
        rh: i32,
        color: (u8, u8, u8),
    ) {
        for dy in 0..rh {
            for dx in 0..rw {
                let px = rx + dx;
                let py = ry + dy;
                if px >= 0 && px < width as i32 && py >= 0 && py < height as i32 {
                    let idx = (py as usize * width + px as usize) * 4;
                    if idx + 3 < buffer.len() {
                        buffer[idx] = color.0;
                        buffer[idx + 1] = color.1;
                        buffer[idx + 2] = color.2;
                        buffer[idx + 3] = 255;
                    }
                }
            }
        }
    }
}
