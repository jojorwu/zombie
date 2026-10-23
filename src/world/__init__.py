"""
World package: tiles, chunks, generation, grid, lighting, weather.

The Rust native module (rust_engine) is optional; its re-exports and the heavy
Python submodules are resolved lazily via ``__getattr__`` so that importing
any single leaf of this package never drags the whole dependency graph in
(this barrel used to be a hub of circular-import chains).
"""
_rust_names = {
    "EnvironmentManager": "RustEnvironmentManager",
    "check_line_of_sight_rust": "check_line_of_sight_rust",
    "compute_a_star_3d_path": "compute_a_star_3d_path",
    "compute_fog_of_war_rust": "compute_fog_of_war_rust",
}

# name -> canonical leaf module
_lazy = {
    "BUILDING_COLORS": "src.world.tiles",
    "TILE_COLORS": "src.world.tiles",
    "TILE_SPEED_MODIFIERS": "src.world.tiles",
    "TILE_WALKABLE": "src.world.tiles",
    "BuildingType": "src.world.tiles",
    "TileType": "src.world.tiles",
    "Chunk": "src.world.chunk",
    "ChunkManager": "src.world.chunk",
    "ChunkState": "src.world.chunk",
    "ElectricityUtility": "src.systems.electricity",
    "WorldGenerator": "src.world.generation",
    "World": "src.world.grid",
    "DynamicLight": "src.world.lighting",
    "LightingEngine": "src.world.lighting",
    "TileInteractionUtility": "src.systems.tile_interaction",
    "WeatherManager": "src.world.weather",
}


def __getattr__(name):
    if name in _lazy:
        import importlib
        mod = importlib.import_module(_lazy[name])
        val = getattr(mod, name)
        globals()[name] = val
        return val
    if name in _rust_names:
        try:
            import rust_engine
        except ImportError:
            if name == "EnvironmentManager":
                raise AttributeError(
                    f"module {__name__!r} has no attribute {name!r} "
                    "(rust_engine not installed)"
                ) from None
            val = None  # rust helpers degrade to None like before
        else:
            val = getattr(rust_engine, _rust_names[name])
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(_lazy) | set(_rust_names))

__all__ = [
    "BUILDING_COLORS",
    "TILE_COLORS",
    "TILE_SPEED_MODIFIERS",
    "TILE_WALKABLE",
    "BuildingType",
    "Chunk",
    "ChunkManager",
    "ChunkState",
    "DynamicLight",
    "ElectricityUtility",
    "EnvironmentManager",
    "LightingEngine",
    "TileInteractionUtility",
    "TileType",
    "WeatherManager",
    "World",
    "WorldGenerator",
    "check_line_of_sight_rust",
    "compute_a_star_3d_path",
    "compute_fog_of_war_rust",
]
