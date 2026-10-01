import math
from enum import Enum, auto
from concurrent.futures import ThreadPoolExecutor

CHUNK_EXECUTOR = ThreadPoolExecutor(max_workers=4)


class ChunkState(Enum):
    UNLOADED = auto()
    GENERATED = auto()
    INACTIVE = auto()
    ACTIVE = auto()


class Chunk:
    def __init__(self, chunk_x: int, chunk_y: int, size: int = 16):
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.size = size
        self.buildings = []
        self.entities = []
        self.state = ChunkState.GENERATED

    @property
    def loaded(self) -> bool:
        return self.state != ChunkState.UNLOADED

    @loaded.setter
    def loaded(self, value: bool) -> None:
        if not value:
            self.state = ChunkState.UNLOADED
        elif self.state == ChunkState.UNLOADED:
            self.state = ChunkState.INACTIVE


class ChunkManager:
    def __init__(self, world_width: int, world_height: int, chunk_size: int = 16):
        self.chunk_size = chunk_size
        self.world_width = world_width
        self.world_height = world_height
        self.num_chunks_x = int(math.ceil(world_width / chunk_size))
        self.num_chunks_y = int(math.ceil(world_height / chunk_size))
        self.chunks = {}
        self.active_chunks = set()

        for cy in range(self.num_chunks_y):
            for cx in range(self.num_chunks_x):
                chunk = Chunk(cx, cy, chunk_size)
                chunk.state = ChunkState.ACTIVE
                self.chunks[(cx, cy)] = chunk
                self.active_chunks.add((cx, cy))

    def get_chunk_coords(self, world_x: float, world_y: float) -> tuple[int, int]:
        cx = max(0, min(self.num_chunks_x - 1, int(world_x) // self.chunk_size))
        cy = max(0, min(self.num_chunks_y - 1, int(world_y) // self.chunk_size))
        return cx, cy

    def get_chunk(self, cx: int, cy: int) -> Chunk | None:
        return self.chunks.get((cx, cy))

    def get_chunk_at(self, world_x: float, world_y: float) -> Chunk | None:
        cx, cy = self.get_chunk_coords(world_x, world_y)
        return self.get_chunk(cx, cy)

    def get_chunks_covering_area(self, min_x: float, min_y: float, width: float, height: float) -> list[Chunk]:
        min_cx = max(0, int(min_x) // self.chunk_size)
        max_cx = min(self.num_chunks_x - 1, int(min_x + width - 0.001) // self.chunk_size)
        min_cy = max(0, int(min_y) // self.chunk_size)
        max_cy = min(self.num_chunks_y - 1, int(min_y + height - 0.001) // self.chunk_size)

        covering = []
        for cy in range(min_cy, max_cy + 1):
            for cx in range(min_cx, max_cx + 1):
                chunk = self.get_chunk(cx, cy)
                if chunk:
                    covering.append(chunk)
        return covering

    def register_building(self, building_info: dict) -> None:
        """
        Registers a building across all chunks that its footprint overlaps.
        This ensures entire building coverage without chunk boundary severed issues.
        """
        bx = building_info.get("x", 0)
        by = building_info.get("y", 0)
        bw = building_info.get("w", 1)
        bh = building_info.get("h", 1)

        covering_chunks = self.get_chunks_covering_area(bx, by, bw, bh)
        for chunk in covering_chunks:
            if building_info not in chunk.buildings:
                chunk.buildings.append(building_info)

    def update_active_chunks(self, entity_positions, view_distance_chunks: int = 2) -> set:
        """
        Loads / activates chunks around active entities and deactivates far chunks.
        If any chunk containing a building is activated, all other chunks covering
        that same building are also activated to prevent boundary clipping.
        """
        new_active = set()
        for x, y in entity_positions:
            cx, cy = self.get_chunk_coords(x, y)
            for dy in range(-view_distance_chunks, view_distance_chunks + 1):
                for dx in range(-view_distance_chunks, view_distance_chunks + 1):
                    target_cx, target_cy = cx + dx, cy + dy
                    if (target_cx, target_cy) in self.chunks:
                        new_active.add((target_cx, target_cy))

        # Full building footprint coverage check
        building_chunks_to_add = set()
        for cx, cy in new_active:
            chunk = self.chunks[(cx, cy)]
            for building in chunk.buildings:
                bx = building.get("x", 0)
                by = building.get("y", 0)
                bw = building.get("w", 1)
                bh = building.get("h", 1)
                for b_chunk in self.get_chunks_covering_area(bx, by, bw, bh):
                    building_chunks_to_add.add((b_chunk.chunk_x, b_chunk.chunk_y))

        new_active.update(building_chunks_to_add)

        # Update chunk states
        for coords, chunk in self.chunks.items():
            if coords in new_active:
                chunk.state = ChunkState.ACTIVE
            else:
                chunk.state = ChunkState.INACTIVE

        self.active_chunks = new_active
        return self.active_chunks

    def update_active_chunks_async(self, entity_positions, view_distance_chunks: int = 2) -> set:
        return self.update_active_chunks(entity_positions, view_distance_chunks)
