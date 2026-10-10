use pyo3::prelude::*;
use numpy::{PyArray3, IntoPyArray, ndarray::Array3};
use crate::world::grid::{RustWorldGrid, TILE_ROAD, TILE_BUILDING_WALL, TILE_FLOOR, TILE_DOOR, TILE_WINDOW};

#[pyclass]
pub struct RustWorldGenerator;

#[pymethods]
impl RustWorldGenerator {
    #[new]
    pub fn new() -> Self {
        RustWorldGenerator
    }

    pub fn generate_map_grid(
        &self,
        py: Python,
        width: usize,
        height: usize,
        z_min: i32,
        z_max: i32,
    ) -> PyResult<Py<PyArray3<i64>>> {
        let grid = Self::generate_map(width, height, z_min, z_max);
        let z_layers = (z_max - z_min + 1) as usize;
        let mut arr = vec![0i64; z_layers * height * width];

        for z in z_min..=z_max {
            let z_idx = (z - z_min) as usize;
            for y in 0..height {
                for x in 0..width {
                    let tile = grid.get_tile(x as i32, y as i32, z);
                    let idx = z_idx * (height * width) + y * width + x;
                    arr[idx] = tile;
                }
            }
        }

        let py_array = Array3::from_shape_vec((z_layers, height, width), arr)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        Ok(py_array.into_pyarray(py).to_owned())
    }
}

impl RustWorldGenerator {
    pub fn generate_map(width: usize, height: usize, z_min: i32, z_max: i32) -> RustWorldGrid {
        let mut grid = RustWorldGrid::new(width, height, z_min, z_max);

        let mid_x = width / 2;
        let mid_y = height / 2;

        for x in 0..width {
            for rw in 0..3 {
                if mid_y + rw < height {
                    grid.set_tile(x as i32, (mid_y + rw) as i32, 0, TILE_ROAD);
                }
            }
        }

        for y in 0..height {
            for rw in 0..3 {
                if mid_x + rw < width {
                    grid.set_tile((mid_x + rw) as i32, y as i32, 0, TILE_ROAD);
                }
            }
        }

        for b_idx in 0..4 {
            let bx = match b_idx {
                0 => mid_x / 2,
                1 => mid_x + mid_x / 2,
                2 => mid_x / 2,
                _ => mid_x + mid_x / 2,
            };
            let by = match b_idx {
                0 => mid_y / 2,
                1 => mid_y / 2,
                2 => mid_y + mid_y / 2,
                _ => mid_y + mid_y / 2,
            };

            let bw = 12;
            let bh = 10;

            for x in bx..(bx + bw) {
                for y in by..(by + bh) {
                    let is_wall = x == bx || x == bx + bw - 1 || y == by || y == by + bh - 1;
                    if is_wall {
                        if x == bx + bw / 2 && y == by + bh - 1 {
                            grid.set_tile(x as i32, y as i32, 0, TILE_DOOR);
                        } else if x == bx + 3 && y == by {
                            grid.set_tile(x as i32, y as i32, 0, TILE_WINDOW);
                        } else {
                            grid.set_tile(x as i32, y as i32, 0, TILE_BUILDING_WALL);
                        }
                    } else {
                        grid.set_tile(x as i32, y as i32, 0, TILE_FLOOR);
                    }
                }
            }
        }

        grid
    }
}
