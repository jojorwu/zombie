import heapq
import math
from src.world import TileType

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

    def heuristic(self, x1, y1, z1, x2, y2, z2):
        dx = abs(x1 - x2)
        dy = abs(y1 - y2)
        dz = abs(z1 - z2)
        return math.hypot(dx, dy) + dz * 3.0

    def get_neighbors(self, node):
        neighbors = []
        x, y, z = node.x, node.y, node.z
        z_idx = self.world.z_to_idx(z)

        # 4-directional horizontal moves
        cardinals = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in cardinals:
            nx, ny = x + dx, y + dy
            if self.world.is_walkable(nx, ny, z):
                cost = 1.0
                neighbors.append((nx, ny, z, cost))

        # Vertical moves via STAIRS or LADDER
        if 0 <= z_idx < self.world.num_levels:
            current_tile = self.world.grid[z_idx, y, x]
            if current_tile in (TileType.STAIRS, TileType.LADDER):
                if z < self.world.z_max and self.world.is_walkable(x, y, z + 1):
                    neighbors.append((x, y, z + 1, 2.0))
                if z > self.world.z_min and self.world.is_walkable(x, y, z - 1):
                    neighbors.append((x, y, z - 1, 2.0))

        return neighbors

    def find_path(self, start_pos, goal_pos, max_nodes=2000):
        sx, sy, sz = int(start_pos[0]), int(start_pos[1]), int(start_pos[2])
        gx, gy, gz = int(goal_pos[0]), int(goal_pos[1]), int(goal_pos[2])

        if not self.world.is_walkable(sx, sy, sz) or not self.world.is_walkable(gx, gy, gz):
            return []

        start_node = Node3D(sx, sy, sz, g=0.0, h=self.heuristic(sx, sy, sz, gx, gy, gz))
        open_set = []
        heapq.heappush(open_set, start_node)

        closed_set = set()
        g_scores = {(sx, sy, sz): 0.0}

        nodes_searched = 0

        while open_set and nodes_searched < max_nodes:
            current = heapq.heappop(open_set)
            nodes_searched += 1

            if current.x == gx and current.y == gy and current.z == gz:
                path = []
                curr = current
                while curr:
                    path.append((curr.x + 0.5, curr.y + 0.5, curr.z))
                    curr = curr.parent
                path.reverse()
                return path

            pos = current.pos_tuple()
            if pos in closed_set:
                continue
            closed_set.add(pos)

            for nx, ny, nz, step_cost in self.get_neighbors(current):
                n_pos = (nx, ny, nz)
                if n_pos in closed_set:
                    continue

                tentative_g = current.g + step_cost
                if tentative_g < g_scores.get(n_pos, float('inf')):
                    g_scores[n_pos] = tentative_g
                    h = self.heuristic(nx, ny, nz, gx, gy, gz)
                    neighbor_node = Node3D(nx, ny, nz, g=tentative_g, h=h, parent=current)
                    heapq.heappush(open_set, neighbor_node)

        return []
