from typing import Optional, List, Tuple
import numpy as np
import pygame
from src.world import TileType, TILE_COLORS, BUILDING_COLORS

try:
    import rust_engine
    HAS_RUST_VULKAN = True
except ImportError:
    HAS_RUST_VULKAN = False


class VulkanBridge:
    """Wrapper bridge for Rust Vulkan Crate hardware accelerated viewport tile rendering."""
    __slots__ = ("tile_size", "palette", "rust_renderer", "rust_dimensions")

    def __init__(self, tile_size: int, palette: List[Tuple[int, int, int]]):
        self.tile_size = tile_size
        self.palette = palette
        self.rust_renderer = None
        self.rust_dimensions = (0, 0)

    @property
    def is_available(self) -> bool:
        return HAS_RUST_VULKAN

    def render_viewport(self, world, cur_z: int, z_idx: int, min_x: int, max_x: int, min_y: int, max_y: int, map_draw_w: int, map_draw_h: int, light: float, visible_tiles: Optional[set], sim=None) -> Optional[pygame.Surface]:
        if not HAS_RUST_VULKAN:
            return None

        if self.rust_dimensions != (map_draw_w, map_draw_h) or self.rust_renderer is None:
            self.rust_renderer = rust_engine.VulkanTileRenderer(map_draw_w, map_draw_h, self.tile_size)
            self.rust_dimensions = (map_draw_w, map_draw_h)

        grid_sub = world.grid[z_idx, min_y:max_y, min_x:max_x]
        grid_bytes = grid_sub.astype(np.uint8).tobytes()

        b_override = np.zeros((max_y - min_y, max_x - min_x, 3), dtype=np.uint8)
        for (bx, by, bz), btype in world.building_grid.items():
            if bz == cur_z and min_x <= bx < max_x and min_y <= by < max_y:
                sub_y, sub_x = by - min_y, bx - min_x
                if grid_sub[sub_y, sub_x] == TileType.BUILDING_FLOOR:
                    b_override[sub_y, sub_x] = BUILDING_COLORS.get(btype, TILE_COLORS[TileType.BUILDING_FLOOR])
        b_bytes = b_override.tobytes()

        if visible_tiles is not None:
            fog_mask = np.zeros((max_y - min_y, max_x - min_x), dtype=np.uint8)
            for (vx, vy) in visible_tiles:
                if min_x <= vx < max_x and min_y <= vy < max_y:
                    fog_mask[vy - min_y, vx - min_x] = 1
            fog_bytes = fog_mask.tobytes()
        else:
            fog_bytes = None

        light_factor = light if cur_z >= 0 else 0.8

        if sim is not None and hasattr(self.rust_renderer, 'render_composite_viewport'):
            survivors = [
                (s.x - min_x, s.y - min_y, idx == sim.selected_survivor_idx)
                for idx, s in enumerate(sim.survivors)
                if s.is_alive and s.z == cur_z and min_x <= s.x <= max_x and min_y <= s.y <= max_y
            ]
            zombies = [
                (z.x - min_x, z.y - min_y)
                for z in sim.zombies
                if z.is_alive and z.z == cur_z and min_x <= z.x <= max_x and min_y <= z.y <= max_y
            ]
            vehicles = [
                (v.x - min_x, v.y - min_y)
                for v in sim.vehicles
                if v.z == cur_z and min_x <= v.x <= max_x and min_y <= v.y <= max_y
            ]
            items = [
                (it.x - min_x, it.y - min_y)
                for it in sim.items
                if not it.collected and it.z == cur_z and min_x <= it.x <= max_x and min_y <= it.y <= max_y
            ]

            pixel_buf = self.rust_renderer.render_composite_viewport(
                grid_bytes,
                b_bytes,
                self.palette,
                light_factor,
                survivors,
                zombies,
                vehicles,
                items,
                fog_bytes
            )
        else:
            pixel_buf = self.rust_renderer.render_viewport_bytes(
                grid_bytes,
                b_bytes,
                self.palette,
                light_factor,
                fog_bytes
            )

        return pygame.image.frombuffer(
            pixel_buf,
            (map_draw_w * self.tile_size, map_draw_h * self.tile_size),
            "RGBA"
        )
