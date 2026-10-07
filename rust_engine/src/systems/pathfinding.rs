use pyo3::prelude::*;
use numpy::PyReadonlyArray3;
use std::collections::{BinaryHeap, HashMap};
use std::cmp::Ordering;

#[derive(Copy, Clone, Eq, PartialEq)]
pub struct PathNode {
    pub f: u32,
    pub g: u32,
    pub x: i32,
    pub y: i32,
    pub z: i32,
}

impl Ord for PathNode {
    fn cmp(&self, other: &Self) -> Ordering {
        other.f.cmp(&self.f)
    }
}

impl PartialOrd for PathNode {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

pub fn is_walkable_tile(t: i64) -> bool {
    matches!(
        t,
        0 | 1 | 3 | 5 | 7 | 8 | 10 | 12 | 13 | 14 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 26 | 27 | 28 | 30 | 50 | 51 | 52 | 54 | 57 | 62 | 63 | 64 | 65 | 75 | 76 | 78 | 79
    )
}

pub fn is_breakable_tile(t: i64) -> bool {
    matches!(t, 7 | 49 | 53 | 55)
}

pub fn is_stairs_or_ladder(t: i64) -> bool {
    matches!(t, 8 | 13 | 79)
}

/// High-performance full 3D A* Pathfinding in Rust over 3D NumPy grid `grid_3d` [num_levels, height, width] with z_min support.
#[pyfunction]
pub fn compute_a_star_3d_path<'py>(
    start: (i32, i32, i32),
    goal: (i32, i32, i32),
    grid_3d: PyReadonlyArray3<'py, i64>,
    z_min: i32,
    max_nodes: usize,
) -> Vec<(i32, i32, i32)> {
    let (sx, sy, sz) = start;
    let (gx, gy, gz) = goal;

    if sx == gx && sy == gy && sz == gz {
        return vec![start];
    }

    let shape = grid_3d.shape();
    let num_levels = shape[0] as i32;
    let height = shape[1] as i32;
    let width = shape[2] as i32;

    let sz_idx = sz - z_min;
    let gz_idx = gz - z_min;

    if sz_idx < 0 || sz_idx >= num_levels || gz_idx < 0 || gz_idx >= num_levels {
        return vec![];
    }

    let view = grid_3d.as_array();

    let get_tile = |x: i32, y: i32, z: i32| -> i64 {
        let zi = z - z_min;
        if zi >= 0 && zi < num_levels && y >= 0 && y < height && x >= 0 && x < width {
            view[[zi as usize, y as usize, x as usize]]
        } else {
            -1
        }
    };

    let start_tile = get_tile(sx, sy, sz);
    let goal_tile = get_tile(gx, gy, gz);

    if start_tile < 0 || (!is_walkable_tile(start_tile) && !is_breakable_tile(start_tile)) {
        return vec![];
    }
    if goal_tile < 0 || (!is_walkable_tile(goal_tile) && !is_breakable_tile(goal_tile)) {
        return vec![];
    }

    let mut open_set = BinaryHeap::new();
    let mut g_score = HashMap::new();
    let mut came_from = HashMap::new();

    let h_start = (((sx - gx).abs() + (sy - gy).abs()) * 10 + (sz - gz).abs() * 30) as u32;
    open_set.push(PathNode { f: h_start, g: 0, x: sx, y: sy, z: sz });
    g_score.insert((sx, sy, sz), 0u32);

    let mut nodes_expanded = 0;

    let neighbors_2d = [
        (-1, 0, 10), (1, 0, 10), (0, -1, 10), (0, 1, 10),
        (-1, -1, 14), (1, -1, 14), (-1, 1, 14), (1, 1, 14),
    ];

    while let Some(current) = open_set.pop() {
        if current.x == gx && current.y == gy && current.z == gz {
            let mut path = vec![(current.x, current.y, current.z)];
            let mut curr_pos = (current.x, current.y, current.z);
            while let Some(&parent) = came_from.get(&curr_pos) {
                path.push(parent);
                curr_pos = parent;
            }
            path.reverse();
            return path;
        }

        nodes_expanded += 1;
        if nodes_expanded > max_nodes {
            break;
        }

        let curr_tile = get_tile(current.x, current.y, current.z);

        // 1. Horizontal 2D neighbors
        for &(dx, dy, base_cost) in &neighbors_2d {
            let nx = current.x + dx;
            let ny = current.y + dy;
            let nz = current.z;

            if dx.abs() == 1 && dy.abs() == 1 {
                let t1 = get_tile(current.x + dx, current.y, nz);
                let t2 = get_tile(current.x, current.y + dy, nz);
                if !is_walkable_tile(t1) && !is_walkable_tile(t2) {
                    continue;
                }
            }

            let tile = get_tile(nx, ny, nz);
            if tile < 0 {
                continue;
            }

            let is_walk = is_walkable_tile(tile);
            let is_break = is_breakable_tile(tile);

            if is_walk || is_break {
                let cost_penalty = if is_break { 30u32 } else { 0u32 };
                let tentative_g = current.g + base_cost + cost_penalty;
                let existing_g = g_score.get(&(nx, ny, nz)).copied().unwrap_or(u32::MAX);

                if tentative_g < existing_g {
                    came_from.insert((nx, ny, nz), (current.x, current.y, current.z));
                    g_score.insert((nx, ny, nz), tentative_g);
                    let h = (((nx - gx).abs() + (ny - gy).abs()) * 10 + (nz - gz).abs() * 30) as u32;
                    open_set.push(PathNode { f: tentative_g + h, g: tentative_g, x: nx, y: ny, z: nz });
                }
            }
        }

        // 2. Vertical Z neighbors (stairs / ladders / trapdoors)
        if is_stairs_or_ladder(curr_tile) {
            for dz in &[-1, 1] {
                let nz = current.z + dz;
                let tile = get_tile(current.x, current.y, nz);
                if tile >= 0 && (is_walkable_tile(tile) || is_breakable_tile(tile)) {
                    let tentative_g = current.g + 20;
                    let existing_g = g_score.get(&(current.x, current.y, nz)).copied().unwrap_or(u32::MAX);

                    if tentative_g < existing_g {
                        came_from.insert((current.x, current.y, nz), (current.x, current.y, current.z));
                        g_score.insert((current.x, current.y, nz), tentative_g);
                        let h = (((current.x - gx).abs() + (current.y - gy).abs()) * 10 + (nz - gz).abs() * 30) as u32;
                        open_set.push(PathNode { f: tentative_g + h, g: tentative_g, x: current.x, y: current.y, z: nz });
                    }
                }
            }
        }
    }

    vec![]
}
