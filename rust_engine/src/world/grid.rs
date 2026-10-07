use std::collections::HashMap;

pub const TILE_GRASS: i64 = 0;
pub const TILE_ROAD: i64 = 1;
pub const TILE_BUILDING_WALL: i64 = 2;
pub const TILE_FLOOR: i64 = 3;
pub const TILE_DOOR: i64 = 7;
pub const TILE_STAIRS: i64 = 8;
pub const TILE_WINDOW: i64 = 49;
pub const TILE_WINDOW_BROKEN: i64 = 55;

#[derive(Clone)]
pub struct RustWorldGrid {
    pub width: usize,
    pub height: usize,
    pub z_min: i32,
    pub z_max: i32,
    pub ground_layer: Vec<i64>, // Z = 0
    pub sparse_z_grid: HashMap<(i32, usize, usize), i64>,
}

impl RustWorldGrid {
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
