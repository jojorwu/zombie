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
    __slots__ = (
        'chunk_x', 'chunk_y', 'size', 'buildings', 'entities',
        'stored_zombies', 'stored_vehicles', 'stored_items',
        'furniture_states', 'item_states', 'state'
    )

    def __init__(self, chunk_x: int, chunk_y: int, size: int = 16):
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.size = size
        self.buildings = []
        self.entities = []
        self.stored_zombies = []
        self.stored_vehicles = []
        self.stored_items = []
        self.furniture_states = {}
        self.item_states = {}
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

    def add_entity_to_chunk(self, world_x: float, world_y: float, entity: any) -> None:
        chunk = self.get_chunk_at(world_x, world_y)
        if chunk and entity not in chunk.entities:
            chunk.entities.append(entity)

    def remove_entity_from_chunk(self, world_x: float, world_y: float, entity: any) -> None:
        chunk = self.get_chunk_at(world_x, world_y)
        if chunk and entity in chunk.entities:
            chunk.entities.remove(entity)

    def rebind_entity(self, entity: any, old_x: float, old_y: float, new_x: float, new_y: float) -> None:
        """Transfers an entity's chunk membership when crossing 16x16 chunk boundaries."""
        old_cx, old_cy = self.get_chunk_coords(old_x, old_y)
        new_cx, new_cy = self.get_chunk_coords(new_x, new_y)

        if (old_cx, old_cy) != (new_cx, new_cy):
            old_chunk = self.get_chunk(old_cx, old_cy)
            new_chunk = self.get_chunk(new_cx, new_cy)

            if old_chunk and entity in old_chunk.entities:
                old_chunk.entities.remove(entity)
            if new_chunk and entity not in new_chunk.entities:
                new_chunk.entities.append(entity)

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
        Optimized with delta updates (O(N_changed) instead of O(N_total)) and boundary checks.
        """
        new_active = set()
        for x, y in entity_positions:
            cx, cy = self.get_chunk_coords(x, y)
            for dy in range(-view_distance_chunks, view_distance_chunks + 1):
                for dx in range(-view_distance_chunks, view_distance_chunks + 1):
                    target_cx, target_cy = cx + dx, cy + dy
                    if (target_cx, target_cy) in self.chunks:
                        new_active.add((target_cx, target_cy))

        # Full building footprint coverage check across chunk boundaries
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

        # Delta chunk state updates: only modify newly activated or deactivated chunks
        newly_deactivated = self.active_chunks - new_active
        newly_activated = new_active - self.active_chunks

        for coords in newly_deactivated:
            chunk = self.chunks.get(coords)
            if chunk:
                chunk.state = ChunkState.INACTIVE

        for coords in newly_activated:
            chunk = self.chunks.get(coords)
            if chunk:
                chunk.state = ChunkState.ACTIVE

        self.active_chunks = new_active
        return self.active_chunks

    def store_zombies_in_chunks(self, zombies: list) -> list:
        """
        Stores active zombies located in INACTIVE chunks into chunk persistence without duplicates,
        returning only the zombies located inside ACTIVE chunks.
        """
        active_zombies = []
        for z in zombies:
            if not getattr(z, 'is_alive', True):
                continue
            cx, cy = self.get_chunk_coords(z.x, z.y)
            chunk = self.get_chunk(cx, cy)
            if chunk and chunk.state == ChunkState.ACTIVE:
                active_zombies.append(z)
            elif chunk:
                if z not in chunk.stored_zombies:
                    chunk.stored_zombies.append(z)
        return active_zombies

    def rehydrate_zombies_from_active_chunks(self) -> list:
        """
        Re-hydrates zombies stored in newly activated chunks back into the simulation without duplicates.
        """
        rehydrated = []
        seen_ids = set()
        for coords in self.active_chunks:
            chunk = self.get_chunk(coords[0], coords[1])
            if chunk and chunk.stored_zombies:
                for z in chunk.stored_zombies:
                    if getattr(z, 'is_alive', True) and id(z) not in seen_ids:
                        seen_ids.add(id(z))
                        rehydrated.append(z)
                chunk.stored_zombies.clear()
        return rehydrated

    def store_vehicles_in_chunks(self, vehicles: list) -> list:
        """
        Stores parked vehicles located in INACTIVE chunks into chunk persistence,
        returning only vehicles located inside ACTIVE chunks or currently driven.
        """
        active_vehicles = []
        for v in vehicles:
            if getattr(v, 'is_occupied', lambda: False)():
                active_vehicles.append(v)
                continue
            cx, cy = self.get_chunk_coords(v.x, v.y)
            chunk = self.get_chunk(cx, cy)
            if chunk and chunk.state == ChunkState.ACTIVE:
                active_vehicles.append(v)
            elif chunk:
                if v not in chunk.stored_vehicles:
                    chunk.stored_vehicles.append(v)
        return active_vehicles

    def rehydrate_vehicles_from_active_chunks(self) -> list:
        """
        Re-hydrates parked vehicles stored in newly activated chunks back into the simulation.
        """
        rehydrated = []
        seen_ids = set()
        for coords in self.active_chunks:
            chunk = self.get_chunk(coords[0], coords[1])
            if chunk and chunk.stored_vehicles:
                for v in chunk.stored_vehicles:
                    if id(v) not in seen_ids:
                        seen_ids.add(id(v))
                        rehydrated.append(v)
                chunk.stored_vehicles.clear()
        return rehydrated

    def store_items_in_chunks(self, items: list) -> list:
        """
        Stores floor items located in INACTIVE chunks into chunk persistence,
        returning only items located inside ACTIVE chunks.
        """
        active_items = []
        for item in items:
            if getattr(item, 'collected', False):
                continue
            cx, cy = self.get_chunk_coords(item.x, item.y)
            chunk = self.get_chunk(cx, cy)
            if chunk and chunk.state == ChunkState.ACTIVE:
                active_items.append(item)
            elif chunk:
                if item not in chunk.stored_items:
                    chunk.stored_items.append(item)
        return active_items

    def rehydrate_items_from_active_chunks(self) -> list:
        """
        Re-hydrates floor items stored in newly activated chunks back into the simulation.
        """
        rehydrated = []
        seen_ids = set()
        for coords in self.active_chunks:
            chunk = self.get_chunk(coords[0], coords[1])
            if chunk and chunk.stored_items:
                for item in chunk.stored_items:
                    if not getattr(item, 'collected', False) and id(item) not in seen_ids:
                        seen_ids.add(id(item))
                        rehydrated.append(item)
                chunk.stored_items.clear()
        return rehydrated

    def update_active_chunks_async(self, entity_positions, view_distance_chunks: int = 2):
        """Asynchronously updates active chunks using CHUNK_EXECUTOR background thread worker."""
        future = CHUNK_EXECUTOR.submit(self.update_active_chunks, entity_positions, view_distance_chunks)
        return future

    def clear(self) -> None:
        """Clears all stored entities and references in chunks for memory cleanup."""
        for chunk in self.chunks.values():
            chunk.entities.clear()
            chunk.stored_zombies.clear()
            chunk.stored_vehicles.clear()
            chunk.stored_items.clear()
            chunk.furniture_states.clear()
            chunk.item_states.clear()
        self.chunks.clear()
        self.active_chunks.clear()
