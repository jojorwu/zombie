import math
import torch
import numpy as np
from src.ai.brain_net import DEVICE

try:
    from rust_engine import check_line_of_sight_rust
    RUST_LOS_AVAILABLE = True
except ImportError:
    RUST_LOS_AVAILABLE = False


def batch_get_action_and_movement(brains: list, inputs_list: list, prev_hiddens: list) -> list:
    """
    High-performance batched PyTorch inference over active survivors.
    Executes batched tensor matrix multiplication (BMM) for max speed and zero memory allocation churn.
    """
    if not brains or not inputs_list:
        return []

    num_survivors = len(brains)

    if num_survivors == 1:
        return [brains[0].get_action_and_movement(inputs_list[0], prev_hiddens[0])]

    w_fc1 = torch.stack([b.fc1.weight for b in brains])
    b_fc1 = torch.stack([b.fc1.bias for b in brains])
    w_ih = torch.stack([b.gru.weight_ih for b in brains])
    w_hh = torch.stack([b.gru.weight_hh for b in brains])
    b_ih = torch.stack([b.gru.bias_ih for b in brains])
    b_hh = torch.stack([b.gru.bias_hh for b in brains])
    w_out = torch.stack([b.fc_out.weight for b in brains])
    b_out = torch.stack([b.fc_out.bias for b in brains])

    inp_np = np.ascontiguousarray(np.array(inputs_list, dtype=np.float32))
    x = torch.from_numpy(inp_np).to(DEVICE).unsqueeze(1)

    valid_hiddens = []
    for h in prev_hiddens:
        if h is None:
            h = brains[0].init_hidden()
        if h.dim() == 3:
            h = h.squeeze(1)
        elif h.dim() == 1:
            h = h.unsqueeze(0)
        if h.device != DEVICE:
            h = h.to(DEVICE)
        valid_hiddens.append(h)

    h_cat = torch.cat(valid_hiddens, dim=0).to(DEVICE)

    with torch.inference_mode():
        out = torch.bmm(x, w_fc1.transpose(1, 2)).squeeze(1) + b_fc1
        out = torch.relu(out)

        gi = torch.bmm(out.unsqueeze(1), w_ih.transpose(1, 2)).squeeze(1) + b_ih
        gh = torch.bmm(h_cat.unsqueeze(1), w_hh.transpose(1, 2)).squeeze(1) + b_hh

        i_r, i_i, i_n = gi.chunk(3, 1)
        h_r, h_i, h_n = gh.chunk(3, 1)

        resetgate = torch.sigmoid(i_r + h_r)
        inputgate = torch.sigmoid(i_i + h_i)
        newgate = torch.tanh(i_n + resetgate * h_n)
        h_next = newgate + inputgate * (h_cat - newgate)

        out_final = torch.bmm(h_next.unsqueeze(1), w_out.transpose(1, 2)).squeeze(1) + b_out
        out_arr = out_final.cpu().numpy()

        dxs = np.tanh(out_arr[:, 0])
        dys = np.tanh(out_arr[:, 1])
        actions = np.argmax(out_arr[:, 2:], axis=1)

        results = []
        for i in range(num_survivors):
            results.append((
                float(dxs[i]),
                float(dys[i]),
                int(actions[i]),
                h_next[i:i + 1]
            ))
        return results


def check_line_of_sight(world, x0: float, y0: float, x1: float, y1: float, z: int) -> bool:
    """Raycast check between two points on the same Z level to verify Line-of-Sight using fast Rust C-API."""
    if RUST_LOS_AVAILABLE:
        if hasattr(world, 'get_3d_grid_array'):
            grid_3d = world.get_3d_grid_array()
        else:
            grid_3d = world.grid.astype(np.int64)
        return check_line_of_sight_rust(float(x0), float(y0), int(z), float(x1), float(y1), int(z), grid_3d, world.z_min)

    ix0, iy0 = int(x0), int(y0)
    ix1, iy1 = int(x1), int(y1)

    dx = abs(ix1 - ix0)
    dy = abs(iy1 - iy0)
    sx = 1 if ix0 < ix1 else -1
    sy = 1 if iy0 < iy1 else -1
    err = dx - dy

    curr_x, curr_y = ix0, iy0

    while True:
        if not world.is_walkable(curr_x + 0.5, curr_y + 0.5, z):
            if (curr_x, curr_y) != (ix0, iy0) and (curr_x, curr_y) != (ix1, iy1):
                return False
        if curr_x == ix1 and curr_y == iy1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            curr_x += sx
        if e2 < dx:
            err += dx
            curr_y += sy

    return True


def extract_survivor_inputs(survivor, world, items, vehicles, zombies, animals) -> np.ndarray:
    """Extracts 57 numerical input features with Raycast Line-of-Sight perception masking and spatial memory."""
    inputs = np.zeros(57, dtype=np.float32)
    inputs[0] = survivor.health / 100.0
    inputs[1] = survivor.hunger / 100.0
    inputs[2] = survivor.thirst / 100.0
    inputs[3] = survivor.sleep / 100.0
    inputs[4] = world.get_light_level()
    inputs[5] = 1.0 if survivor.in_vehicle else 0.0
    inputs[6] = 1.0 if survivor.inventory.get("weapon", 0) > 0 or survivor.inventory.get("pistol", 0) > 0 else 0.0
    inputs[7] = 1.0 if survivor.inventory.get("medkit", 0) > 0 else 0.0

    current_tick = getattr(world, 'current_tick', 0)

    def find_closest_visible_or_remembered(entities, category_key: str, max_dist: float = 15.0):
        min_dist = max_dist
        best_dx, best_dy, best_dz = 0.0, 0.0, 0.0
        sx, sy, sz = survivor.x, survivor.y, survivor.z

        for e in entities:
            if getattr(e, 'is_alive', True) and not getattr(e, 'collected', False):
                ez = getattr(e, 'z', 0)
                dx = e.x - sx
                dy = e.y - sy
                dz = ez - sz
                d = math.hypot(dx, dy) + abs(dz) * 2.0

                if d < max_dist and ez == sz:
                    if check_line_of_sight(world, sx, sy, e.x, e.y, int(sz)):
                        # Store in survivor's spatial memory
                        if hasattr(survivor, 'spatial_memory'):
                            survivor.spatial_memory[category_key] = (e.x, e.y, ez, current_tick)
                        if d < min_dist:
                            min_dist = d
                            best_dx = dx / max_dist
                            best_dy = dy / max_dist
                            best_dz = dz / 20.0

        # Memory Fallback if no directly visible entity found
        if min_dist == max_dist and hasattr(survivor, 'spatial_memory') and category_key in survivor.spatial_memory:
            mx, my, mz, mtick = survivor.spatial_memory[category_key]
            # Retain memory for 300 ticks (~10 seconds)
            if current_tick - mtick <= 300 and int(mz) == int(sz):
                dx = mx - sx
                dy = my - sy
                d = math.hypot(dx, dy)
                if d < max_dist:
                    best_dx = dx / max_dist
                    best_dy = dy / max_dist

        return best_dx, best_dy, best_dz

    inputs[8], inputs[9], inputs[10] = find_closest_visible_or_remembered(zombies, "zombie")
    inputs[11], inputs[12], inputs[13] = find_closest_visible_or_remembered(items, "item")
    inputs[14], inputs[15], inputs[16] = find_closest_visible_or_remembered(vehicles, "vehicle")
    inputs[17], inputs[18], inputs[19] = find_closest_visible_or_remembered(animals, "animal")

    inputs[20] = 1.0 if world.is_walkable(survivor.x + 0.5, survivor.y, survivor.z) else 0.0
    inputs[21] = 1.0 if world.is_walkable(survivor.x, survivor.y + 0.5, survivor.z) else 0.0
    inputs[22] = float(survivor.z) / 20.0

    from src.utils.tile_interaction_utility import TileInteractionUtility
    z_idx = world.z_to_idx(survivor.z)
    has_furniture_adj = 0.0
    sx_i, sy_i = int(survivor.x), int(survivor.y)

    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        fx, fy = sx_i + dx, sy_i + dy
        if 0 <= fx < world.width and 0 <= fy < world.height:
            if world.grid[z_idx, fy, fx] in TileInteractionUtility.MOVABLE_FURNITURE_TILES:
                has_furniture_adj = 1.0
                break

    inputs[23] = has_furniture_adj
    inputs[24] = getattr(survivor, 'fear', 0.0) / 100.0

    # 7 Inputs for expanded BrainNet (Total: 32)
    inputs[25] = getattr(survivor, 'panic', 0.0) / 100.0
    inputs[26] = getattr(survivor, 'morale', 50.0) / 100.0

    # Anatomical health status
    if hasattr(survivor, 'anatomical_health'):
        inputs[27] = survivor.anatomical_health.head_health / 100.0
        inputs[28] = survivor.anatomical_health.torso_health / 100.0
        inputs[29] = min(survivor.anatomical_health.left_leg_health, survivor.anatomical_health.right_leg_health) / 100.0
    else:
        inputs[27], inputs[28], inputs[29] = 1.0, 1.0, 1.0

    # Building shelter indicator (2D coordinate lookup)
    building = world.building_grid.get((int(survivor.x), int(survivor.y)))
    inputs[30] = 1.0 if building is not None else 0.0

    # Exploration coverage indicator
    visited_count = len(getattr(survivor, 'visited_tiles', set()))
    inputs[31] = min(1.0, visited_count / 500.0)

    # 25 Local Spatial Grid Vision Inputs (5x5 matrix around survivor)
    idx_grid = 32
    z_val = survivor.z

    for dy_g in range(-2, 3):
        for dx_g in range(-2, 3):
            gx, gy = sx_i + dx_g, sy_i + dy_g
            if world.is_walkable(gx, gy, z_val):
                inputs[idx_grid] = 1.0
            else:
                inputs[idx_grid] = -1.0
            idx_grid += 1

    return inputs
