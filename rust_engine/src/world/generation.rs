use crate::world::grid::{RustWorldGrid, TILE_ROAD, TILE_BUILDING_WALL, TILE_FLOOR, TILE_DOOR, TILE_WINDOW};

pub struct RustWorldGenerator;

impl RustWorldGenerator {
    pub fn generate_map(width: usize, height: usize, z_min: i32, z_max: i32) -> RustWorldGrid {
        let mut grid = RustWorldGrid::new(width, height, z_min, z_max);

        // 1. Generate Main Roads (Cross Grid)
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

        // 2. Generate Buildings
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
