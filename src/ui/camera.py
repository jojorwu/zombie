class Camera:
    """Handles viewport transformation, culling range calculations, and screen coordinate mapping."""
    def __init__(self, tile_size=16):
        self.tile_size = tile_size

    def get_viewport_bounds(self, center_x, center_y, width_px, height_px, world_w, world_h):
        map_draw_w = (width_px - 300) // self.tile_size
        map_draw_h = height_px // self.tile_size

        min_x = max(0, int(center_x - map_draw_w // 2))
        max_x = min(world_w, min_x + map_draw_w)
        min_x = max(0, max_x - map_draw_w)

        min_y = max(0, int(center_y - map_draw_h // 2))
        max_y = min(world_h, min_y + map_draw_h)
        min_y = max(0, max_y - map_draw_h)

        return min_x, max_x, min_y, max_y, map_draw_w, map_draw_h

    def world_to_screen(self, wx, wy, min_x, min_y):
        return int((wx - min_x) * self.tile_size), int((wy - min_y) * self.tile_size)
