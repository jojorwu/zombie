use pyo3::prelude::*;
use std::collections::HashMap;

/// Native Spatial Hash Cell Grid in Rust.
#[pyclass]
pub struct RustSpatialGrid {
    cell_size: f32,
    grid: HashMap<(i32, i32, i32), Vec<usize>>,
}

#[pymethods]
impl RustSpatialGrid {
    #[new]
    pub fn new(cell_size: f32) -> Self {
        RustSpatialGrid {
            cell_size,
            grid: HashMap::new(),
        }
    }

    pub fn clear(&mut self) {
        self.grid.clear();
    }

    pub fn insert_entity(&mut self, entity_id: usize, x: f32, y: f32, z: i32) {
        let cx = (x / self.cell_size).floor() as i32;
        let cy = (y / self.cell_size).floor() as i32;
        self.grid.entry((cx, cy, z)).or_insert_with(Vec::new).push(entity_id);
    }

    pub fn get_nearby_entities(&self, x: f32, y: f32, z: i32) -> Vec<usize> {
        let cx = (x / self.cell_size).floor() as i32;
        let cy = (y / self.cell_size).floor() as i32;
        let mut nearby = Vec::new();

        for dx in -1..=1 {
            for dy in -1..=1 {
                if let Some(list) = self.grid.get(&(cx + dx, cy + dy, z)) {
                    nearby.extend_from_slice(list);
                }
            }
        }
        nearby
    }
}
