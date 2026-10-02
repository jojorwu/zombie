import math


class ZombieFlocking:
    """Handles spatial grid bucketing and flocking/boids cohesion behaviors for zombie hordes."""
    @staticmethod
    def compute_flocking_vector(zombie, all_zombies, neighbor_radius=6.0, spatial_grid=None, spatial_cell_size=6.0):
        if not all_zombies:
            return 0.0, 0.0

        sep_x, sep_y = 0.0, 0.0
        align_x, align_y = 0.0, 0.0
        count = 0
        rad_sq = neighbor_radius * neighbor_radius
        zx, zy, zz = zombie.x, zombie.y, zombie.z

        if spatial_grid is not None:
            cx, cy = int(zx // spatial_cell_size), int(zy // spatial_cell_size)
            for dcx in (-1, 0, 1):
                for dcy in (-1, 0, 1):
                    neighbors = spatial_grid.get((cx + dcx, cy + dcy, zz), None)
                    if neighbors:
                        for other in neighbors:
                            if other is not zombie and other.is_alive:
                                dx = other.x - zx
                                dy = other.y - zy
                                d_sq = dx * dx + dy * dy
                                if 0.01 < d_sq < rad_sq:
                                    d = math.sqrt(d_sq)
                                    count += 1
                                    sep_x -= dx / d
                                    sep_y -= dy / d
                                    align_x += dx
                                    align_y += dy
        else:
            for other in all_zombies:
                if other is not zombie and other.is_alive and other.z == zz:
                    dx = other.x - zx
                    dy = other.y - zy
                    if abs(dx) < neighbor_radius and abs(dy) < neighbor_radius:
                        d_sq = dx * dx + dy * dy
                        if 0.01 < d_sq < rad_sq:
                            d = math.sqrt(d_sq)
                            count += 1
                            sep_x -= dx / d
                            sep_y -= dy / d
                            align_x += dx
                            align_y += dy

        if count > 0:
            return (sep_x * 0.4 + align_x * 0.2), (sep_y * 0.4 + align_y * 0.2)
        return 0.0, 0.0
