use pyo3::prelude::*;
use pyo3::types::PyBytes;
use numpy::{PyArray1, PyReadonlyArray1, PyReadonlyArray3, IntoPyArray};
use std::collections::{BinaryHeap, HashMap, HashSet};
use std::cmp::Ordering;

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

/// High-performance Rust zombie flocking steering calculation using zero-copy NumPy inputs.
#[pyfunction]
pub fn compute_zombie_flock_steering<'py>(
    py: Python<'py>,
    zombie_coords: PyReadonlyArray1<'py, f32>,
    separation_dist: f32,
) -> &'py PyArray1<f32> {
    let coords_slice = zombie_coords.as_slice().unwrap_or(&[]);
    let num_zombies = coords_slice.len() / 3;
    let mut steering_vectors = vec![0.0f32; num_zombies * 2];

    if num_zombies >= 2 {
        let sq_sep = separation_dist * separation_dist;

        for i in 0..num_zombies {
            let z1_x = coords_slice[i * 3];
            let z1_y = coords_slice[i * 3 + 1];
            let z1_z = coords_slice[i * 3 + 2];

            let mut sep_x = 0.0f32;
            let mut sep_y = 0.0f32;

            for j in 0..num_zombies {
                if i == j {
                    continue;
                }

                let z2_x = coords_slice[j * 3];
                let z2_y = coords_slice[j * 3 + 1];
                let z2_z = coords_slice[j * 3 + 2];

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
    }

    steering_vectors.into_pyarray(py)
}

fn is_opaque_tile(t: i64) -> bool {
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

#[derive(Copy, Clone, Eq, PartialEq)]
struct PathNode {
    f: u32,
    g: u32,
    x: i32,
    y: i32,
    z: i32,
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

fn is_walkable_tile(t: i64) -> bool {
    matches!(
        t,
        0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 16 | 18 | 19
    )
}

fn is_breakable_tile(t: i64) -> bool {
    matches!(t, 14 | 15 | 17 | 20)
}

fn is_stairs_or_ladder(t: i64) -> bool {
    matches!(t, 10 | 11 | 13)
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

#[pyclass]
pub struct RustEngineCore {
    width: usize,
    height: usize,
    current_tick: u64,
    survivor_x: f32,
    survivor_y: f32,
    survivor_z: i32,
    survivor_health: f32,
    survivor_hunger: f32,
    survivor_thirst: f32,
}

#[pymethods]
impl RustEngineCore {
    #[new]
    fn new(width: usize, height: usize) -> Self {
        RustEngineCore {
            width,
            height,
            current_tick: 0,
            survivor_x: (width / 2) as f32,
            survivor_y: (height / 2) as f32,
            survivor_z: 0,
            survivor_health: 100.0,
            survivor_hunger: 100.0,
            survivor_thirst: 100.0,
        }
    }

    fn sync_survivor_state(&mut self, x: f32, y: f32, z: i32, health: f32, hunger: f32, thirst: f32, current_tick: u64) {
        self.survivor_x = x;
        self.survivor_y = y;
        self.survivor_z = z;
        self.survivor_health = health;
        self.survivor_hunger = hunger;
        self.survivor_thirst = thirst;
        self.current_tick = current_tick;
    }

    fn step(&mut self, dx: f32, dy: f32, _action: i32) {
        self.current_tick += 1;
        self.survivor_x = (self.survivor_x + dx * 0.15).max(0.0).min((self.width - 1) as f32);
        self.survivor_y = (self.survivor_y + dy * 0.15).max(0.0).min((self.height - 1) as f32);
        self.survivor_hunger = (self.survivor_hunger - 0.025).max(0.0);
        self.survivor_thirst = (self.survivor_thirst - 0.035).max(0.0);
    }

    fn get_observation_flat<'py>(&self, py: Python<'py>) -> &'py PyArray1<f32> {
        let mut obs = vec![0.0f32; 57];
        obs[0] = self.survivor_health / 100.0;
        obs[1] = self.survivor_hunger / 100.0;
        obs[2] = self.survivor_thirst / 100.0;
        obs[3] = 1.0;
        obs[4] = 1.0;
        obs[22] = self.survivor_z as f32 / 20.0;
        obs.into_pyarray(py)
    }

    fn get_current_tick(&self) -> u64 {
        self.current_tick
    }

    fn get_survivor_pos(&self) -> (f32, f32, i32) {
        (self.survivor_x, self.survivor_y, self.survivor_z)
    }
}

#[pymodule]
fn rust_vulkan_render(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<VulkanTileRenderer>()?;
    m.add_class::<RustEngineCore>()?;
    m.add_function(wrap_pyfunction!(compute_zombie_flock_steering, m)?)?;
    m.add_function(wrap_pyfunction!(compute_a_star_3d_path, m)?)?;
    m.add_function(wrap_pyfunction!(check_line_of_sight_rust, m)?)?;
    m.add_function(wrap_pyfunction!(compute_fog_of_war_rust, m)?)?;
    Ok(())
}
