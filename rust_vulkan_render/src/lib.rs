use pyo3::prelude::*;

#[pyclass]
pub struct VulkanTileRenderer {
    width: u32,
    height: u32,
    tile_size: u32,
}

#[pymethods]
impl VulkanTileRenderer {
    #[new]
    fn new(width: u32, height: u32, tile_size: u32) -> Self {
        VulkanTileRenderer {
            width,
            height,
            tile_size,
        }
    }

    fn render_grid_buffer(&self, grid: Vec<i32>, light: f32) -> Vec<u8> {
        let num_pixels = (self.width * self.height * 4) as usize;
        let mut buffer = vec![20u8; num_pixels];

        for (idx, &tile) in grid.iter().enumerate() {
            let x = (idx % self.width as usize) as u32;
            let y = (idx / self.width as usize) as u32;

            let (r, g, b) = match tile {
                0 => (34u8, 139u8, 34u8),
                1 => (105u8, 105u8, 105u8),
                2 => (100u8, 50u8, 20u8),
                3 => (210u8, 180u8, 140u8),
                _ => (50u8, 50u8, 50u8),
            };

            let px = (y * self.width + x) as usize * 4;
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

#[pymodule]
fn rust_vulkan_render(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<VulkanTileRenderer>()?;
    Ok(())
}
