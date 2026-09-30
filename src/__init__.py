from src.entities import (
    ResourceItem, WEAPON_STATS, ItemEntity, NoiseEvent, ScentTrail,
    Animal, Vehicle, Zombie, ZombieState, CraftingSystem, Survivor
)
from src.world import (
    DynamicLight, WeatherManager, Chunk, ChunkManager,
    TileType, BuildingType, TILE_COLORS, BUILDING_COLORS, TILE_WALKABLE, TILE_SPEED_MODIFIERS, World
)
from src.ui import UITheme, THEME_COLORS, MainMenuUI, RendererUI
from src.simulation import SimulationEngine
from src.ai import BrainNet, extract_survivor_inputs, GeneticEvolutionManager, AStar3D
from src.modding import LuaModManager

# Legacy module aliases for backward compatibility with external code imports
import src.brain
import src.pathfinding
import src.entities
import src.world
import src.ui
import src.simulation
import src.modding

__all__ = [
    "ResourceItem", "WEAPON_STATS", "ItemEntity", "NoiseEvent", "ScentTrail",
    "Animal", "Vehicle", "Zombie", "ZombieState", "CraftingSystem", "Survivor",
    "DynamicLight", "WeatherManager", "Chunk", "ChunkManager",
    "TileType", "BuildingType", "TILE_COLORS", "BUILDING_COLORS", "TILE_WALKABLE", "TILE_SPEED_MODIFIERS", "World",
    "UITheme", "THEME_COLORS", "MainMenuUI", "RendererUI",
    "SimulationEngine",
    "BrainNet", "extract_survivor_inputs", "GeneticEvolutionManager", "AStar3D",
    "LuaModManager",
]
