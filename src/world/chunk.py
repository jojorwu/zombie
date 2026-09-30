import math
from concurrent.futures import ThreadPoolExecutor

CHUNK_EXECUTOR = ThreadPoolExecutor(max_workers=4)

class Chunk:
    def __init__(self, chunk_x, chunk_y, size=16):
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.size = size
        self.buildings = []
        self.loaded = True


class ChunkManager:
    def __init__(self, world_width, world_height, chunk_size=16):
        self.chunk_size = chunk_size
        self.num_chunks_x = int(math.ceil(world_width / chunk_size))
        self.num_chunks_y = int(math.ceil(world_height / chunk_size))
        self.chunks = {}
        self.active_chunks = set()
        for cy in range(self.num_chunks_y):
            for cx in range(self.num_chunks_x):
                self.chunks[(cx, cy)] = Chunk(cx, cy, chunk_size)
                self.active_chunks.add((cx, cy))

    def get_chunk_coords(self, world_x, world_y):
        cx = int(world_x) // self.chunk_size
        cy = int(world_y) // self.chunk_size
        return cx, cy

    def get_chunk(self, cx, cy):
        return self.chunks.get((cx, cy))

    def get_chunk_at(self, world_x, world_y):
        cx, cy = self.get_chunk_coords(world_x, world_y)
        return self.get_chunk(cx, cy)

    def update_active_chunks(self, entity_positions, view_distance_chunks=2):
        """
        Loads / activates chunks around active entities and deactivates far chunks.
        """
        new_active = set()
        for x, y in entity_positions:
            cx, cy = self.get_chunk_coords(x, y)
            for dy in range(-view_distance_chunks, view_distance_chunks + 1):
                for dx in range(-view_distance_chunks, view_distance_chunks + 1):
                    target_cx, target_cy = cx + dx, cy + dy
                    if (target_cx, target_cy) in self.chunks:
                        new_active.add((target_cx, target_cy))

        self.active_chunks = new_active
        return self.active_chunks

    def update_active_chunks_async(self, entity_positions, view_distance_chunks=2):
        return self.update_active_chunks(entity_positions, view_distance_chunks)
