import math
import torch
import numpy as np
from src.ai.brain_net import DEVICE


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


def extract_survivor_inputs(survivor, world, items, vehicles, zombies, animals) -> np.ndarray:
    """Extracts 57 numerical input features (32 status/closest entity inputs + 25 local 5x5 spatial grid inputs) for PyTorch neural network inference."""
    inputs = np.zeros(57, dtype=np.float32)
    inputs[0] = survivor.health / 100.0
    inputs[1] = survivor.hunger / 100.0
    inputs[2] = survivor.thirst / 100.0
    inputs[3] = survivor.sleep / 100.0
    inputs[4] = world.get_light_level()
    inputs[5] = 1.0 if survivor.in_vehicle else 0.0
    inputs[6] = 1.0 if survivor.inventory.get("weapon", 0) > 0 or survivor.inventory.get("pistol", 0) > 0 else 0.0
    inputs[7] = 1.0 if survivor.inventory.get("medkit", 0) > 0 else 0.0

    def find_closest_fast(entities, max_dist: float = 15.0):
        min_dist = max_dist
        best_dx, best_dy, best_dz = 0.0, 0.0, 0.0
        sx, sy, sz = survivor.x, survivor.y, survivor.z

        for e in entities:
            if getattr(e, 'is_alive', True) and not getattr(e, 'collected', False):
                dx = e.x - sx
                dy = e.y - sy
                dz = getattr(e, 'z', 0) - sz
                d = math.hypot(dx, dy) + abs(dz) * 2.0
                if d < min_dist:
                    min_dist = d
                    best_dx = dx / max_dist
                    best_dy = dy / max_dist
                    best_dz = dz / 20.0

        return best_dx, best_dy, best_dz

    inputs[8], inputs[9], inputs[10] = find_closest_fast(zombies)
    inputs[11], inputs[12], inputs[13] = find_closest_fast(items)
    inputs[14], inputs[15], inputs[16] = find_closest_fast(vehicles)
    inputs[17], inputs[18], inputs[19] = find_closest_fast(animals)
    inputs[20] = 1.0 if world.is_walkable(survivor.x + 0.5, survivor.y, survivor.z) else 0.0
    inputs[21] = 1.0 if world.is_walkable(survivor.x, survivor.y + 0.5, survivor.z) else 0.0
    inputs[22] = float(survivor.z) / 20.0

    from utils.tile_interaction_utility import TileInteractionUtility
    z_idx = world.z_to_idx(survivor.z)
    has_furniture_adj = 0.0
    sx, sy = int(survivor.x), int(survivor.y)

    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        fx, fy = sx + dx, sy + dy
        if 0 <= fx < world.width and 0 <= fy < world.height:
            if world.grid[z_idx, fy, fx] in TileInteractionUtility.MOVABLE_FURNITURE_TILES:
                has_furniture_adj = 1.0
                break

    inputs[23] = has_furniture_adj
    inputs[24] = getattr(survivor, 'fear', 0.0) / 100.0

    # 7 New Inputs for expanded BrainNet (Total: 32)
    inputs[25] = getattr(survivor, 'panic', 0.0) / 100.0
    inputs[26] = getattr(survivor, 'morale', 50.0) / 100.0

    # Anatomical health status
    if hasattr(survivor, 'anatomical_health'):
        inputs[27] = survivor.anatomical_health.head_health / 100.0
        inputs[28] = survivor.anatomical_health.torso_health / 100.0
        inputs[29] = min(survivor.anatomical_health.left_leg_health, survivor.anatomical_health.right_leg_health) / 100.0
    else:
        inputs[27], inputs[28], inputs[29] = 1.0, 1.0, 1.0

    # Building shelter indicator
    building = world.building_grid.get((int(survivor.x), int(survivor.y), int(survivor.z)))
    inputs[30] = 1.0 if building is not None else 0.0

    # Exploration coverage indicator
    visited_count = len(getattr(survivor, 'visited_tiles', set()))
    inputs[31] = min(1.0, visited_count / 500.0)

    # 25 Local Spatial Grid Vision Inputs (5x5 matrix around survivor)
    idx_grid = 32
    sx_i, sy_i = int(survivor.x), int(survivor.y)
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
