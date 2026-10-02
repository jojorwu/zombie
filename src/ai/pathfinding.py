import heapq
import math
from src.world import TileType

_DIRECTIONS_8 = (
    (0, 1, 1.0), (0, -1, 1.0), (1, 0, 1.0), (-1, 0, 1.0),
    (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)
)


class Node3D:
    def __init__(self, x, y, z, g=0.0, h=0.0, parent=None):
        self.x = int(x)
        self.y = int(y)
        self.z = int(z)
        self.g = g
        self.h = h
        self.f = g + h
        self.parent = parent

    def __lt__(self, other):
        return self.f < other.f

    def pos_tuple(self):
        return (self.x, self.y, self.z)


class AStar3D:
    def __init__(self, world):
        self.world = world

    @staticmethod
    def heuristic(x1, y1, z1, x2, y2, z2):
        dx = abs(x1 - x2)
        dy = abs(y1 - y2)
        dz = abs(z1 - z2)
        return math.hypot(dx, dy) + dz * 3.0

    def find_path(self, start_pos, goal_pos, max_nodes=2000):
        sx, sy, sz = int(start_pos[0]), int(start_pos[1]), int(start_pos[2])
        gx, gy, gz = int(goal_pos[0]), int(goal_pos[1]), int(goal_pos[2])

        if not self.world.is_walkable(sx, sy, sz) or not self.world.is_walkable(gx, gy, gz):
            return []

        start_h = math.hypot(sx - gx, sy - gy) + abs(sz - gz) * 3.0
        open_heap = [(start_h, 0.0, sx, sy, sz)]

        g_scores = {(sx, sy, sz): 0.0}
        parents = {}
        closed_set = set()
        num_levels = self.world.num_levels
        w_grid = self.world.grid

        nodes_searched = 0

        while open_heap and nodes_searched < max_nodes:
            f, g, x, y, z = heapq.heappop(open_heap)
            pos = (x, y, z)

            if pos in closed_set:
                continue
            closed_set.add(pos)
            nodes_searched += 1

            if x == gx and y == gy and z == gz:
                path = []
                curr = pos
                while curr in parents:
                    path.append((curr[0] + 0.5, curr[1] + 0.5, curr[2]))
                    curr = parents[curr]
                path.append((sx + 0.5, sy + 0.5, sz))
                path.reverse()
                return path

            z_idx = self.world.z_to_idx(z)

            for dx, dy, cost in _DIRECTIONS_8:
                nx, ny = x + dx, y + dy
                n_pos = (nx, ny, z)
                if n_pos not in closed_set:
                    is_walk = self.world.is_walkable(nx, ny, z)
                    # Check breakable doors/windows
                    is_breakable = False
                    if not is_walk and 0 <= z_idx < num_levels and 0 <= nx < self.world.width and 0 <= ny < self.world.height:
                        t = w_grid[z_idx, ny, nx]
                        if t in (TileType.DOOR, TileType.DOOR_LOCKED, TileType.WINDOW, TileType.CURTAIN_CLOSED):
                            is_breakable = True

                    if is_walk or is_breakable:
                        step_penalty = 3.0 if is_breakable else 0.0
                        tentative_g = g + cost + step_penalty
                        if tentative_g < g_scores.get(n_pos, 1e9):
                            g_scores[n_pos] = tentative_g
                            parents[n_pos] = pos
                            h = math.hypot(nx - gx, ny - gy) + abs(z - gz) * 3.0
                            heapq.heappush(open_heap, (tentative_g + h, tentative_g, nx, ny, z))

            if 0 <= z_idx < num_levels:
                current_tile = w_grid[z_idx, y, x]
                if current_tile in (TileType.STAIRS, TileType.LADDER):
                    if z < self.world.z_max:
                        n_pos = (x, y, z + 1)
                        if n_pos not in closed_set and self.world.is_walkable(x, y, z + 1):
                            tentative_g = g + 2.0
                            if tentative_g < g_scores.get(n_pos, 1e9):
                                g_scores[n_pos] = tentative_g
                                parents[n_pos] = pos
                                h = math.hypot(x - gx, y - gy) + abs(z + 1 - gz) * 3.0
                                heapq.heappush(open_heap, (tentative_g + h, tentative_g, x, y, z + 1))
                    if z > self.world.z_min:
                        n_pos = (x, y, z - 1)
                        if n_pos not in closed_set and self.world.is_walkable(x, y, z - 1):
                            tentative_g = g + 2.0
                            if tentative_g < g_scores.get(n_pos, 1e9):
                                g_scores[n_pos] = tentative_g
                                parents[n_pos] = pos
                                h = math.hypot(x - gx, y - gy) + abs(z - 1 - gz) * 3.0
                                heapq.heappush(open_heap, (tentative_g + h, tentative_g, x, y, z - 1))

        return []
