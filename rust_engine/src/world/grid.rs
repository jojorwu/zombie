use pyo3::prelude::*;
use std::collections::{HashMap, HashSet};

pub const TILE_GRASS: i64 = 0;
pub const TILE_ROAD: i64 = 1;
pub const TILE_BUILDING_WALL: i64 = 2;
pub const TILE_FLOOR: i64 = 3;
pub const TILE_DOOR: i64 = 7;
pub const TILE_STAIRS: i64 = 8;
pub const TILE_WINDOW: i64 = 49;
pub const TILE_WINDOW_BROKEN: i64 = 55;

#[derive(Clone)]
#[pyclass]
pub struct RustWorldGrid {
    pub width: usize,
    pub height: usize,
    pub z_min: i32,
    pub z_max: i32,
    pub ground_layer: Vec<i64>, // Z = 0
    pub sparse_z_grid: HashMap<(i32, usize, usize), i64>,
}

#[pymethods]
impl RustWorldGrid {
    #[new]
    pub fn new(width: usize, height: usize, z_min: i32, z_max: i32) -> Self {
        let size = width * height;
        RustWorldGrid {
            width,
            height,
            z_min,
            z_max,
            ground_layer: vec![TILE_GRASS; size],
            sparse_z_grid: HashMap::new(),
        }
    }

    pub fn get_tile(&self, x: i32, y: i32, z: i32) -> i64 {
        if x < 0 || x >= self.width as i32 || y < 0 || y >= self.height as i32 {
            return -1;
        }
        let ux = x as usize;
        let uy = y as usize;

        if z == 0 {
            self.ground_layer[uy * self.width + ux]
        } else {
            *self.sparse_z_grid.get(&(z, uy, ux)).unwrap_or(&0)
        }
    }

    pub fn set_tile(&mut self, x: i32, y: i32, z: i32, tile_type: i64) {
        if x < 0 || x >= self.width as i32 || y < 0 || y >= self.height as i32 {
            return;
        }
        let ux = x as usize;
        let uy = y as usize;

        if z == 0 {
            self.ground_layer[uy * self.width + ux] = tile_type;
        } else {
            self.sparse_z_grid.insert((z, uy, ux), tile_type);
        }
    }

    pub fn is_walkable(&self, x: f32, y: f32, z: i32) -> bool {
        let tile = self.get_tile(x as i32, y as i32, z);
        matches!(tile, 0 | 1 | 3 | 5 | 7 | 8 | 10 | 12 | 13 | 14 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 26 | 27 | 28 | 30 | 50 | 51 | 52 | 54 | 57 | 62 | 63 | 64 | 65 | 75 | 76 | 78 | 79)
    }
}

/// Native Chunk & Active Simulation Zone Manager in Rust.
#[pyclass]
pub struct RustChunkManager {
    chunk_size: usize,
    num_chunks_x: usize,
    num_chunks_y: usize,
    active_chunks: HashSet<(usize, usize)>,
}

#[pymethods]
impl RustChunkManager {
    #[new]
    pub fn new(world_width: usize, world_height: usize, chunk_size: usize) -> Self {
        let num_chunks_x = (world_width + chunk_size - 1) / chunk_size;
        let num_chunks_y = (world_height + chunk_size - 1) / chunk_size;
        RustChunkManager {
            chunk_size,
            num_chunks_x,
            num_chunks_y,
            active_chunks: HashSet::new(),
        }
    }

    pub fn get_chunk_coords(&self, x: f32, y: f32) -> (usize, usize) {
        let cx = (x as usize / self.chunk_size).min(self.num_chunks_x.saturating_sub(1));
        let cy = (y as usize / self.chunk_size).min(self.num_chunks_y.saturating_sub(1));
        (cx, cy)
    }

    pub fn update_active_chunks(&mut self, survivor_positions: Vec<(f32, f32)>, active_radius: usize) -> Vec<(usize, usize)> {
        let mut new_active = HashSet::new();
        for (sx, sy) in survivor_positions {
            let (cx, cy) = self.get_chunk_coords(sx, sy);
            let min_cx = cx.saturating_sub(active_radius);
            let max_cx = (cx + active_radius).min(self.num_chunks_x.saturating_sub(1));
            let min_cy = cy.saturating_sub(active_radius);
            let max_cy = (cy + active_radius).min(self.num_chunks_y.saturating_sub(1));

            for y in min_cy..=max_cy {
                for x in min_cx..=max_cx {
                    new_active.insert((x, y));
                }
            }
        }
        self.active_chunks = new_active;
        self.active_chunks.iter().cloned().collect()
    }

    pub fn is_chunk_active(&self, cx: usize, cy: usize) -> bool {
        self.active_chunks.contains(&(cx, cy))
    }

    pub fn is_position_active(&self, x: f32, y: f32) -> bool {
        let coords = self.get_chunk_coords(x, y);
        self.active_chunks.contains(&coords)
    }
}
