from src.world import TileType
from src.entities.item import ResourceItem

class TileInteractionUtility:
    """
    Utility module for managing tile and furniture interactions:
    - Moving / pushing furniture (cabinets, tables, sofas, beds) to create barricades or unblock paths
    - Dismantling furniture for wood and metal resources
    - Barricading doors and entrances
    """
    MOVABLE_FURNITURE = {
        TileType.TABLE: {"weight": 1.0, "dismantle_wood": 2, "dismantle_metal": 1},
        TileType.CHAIR: {"weight": 0.5, "dismantle_wood": 1, "dismantle_metal": 0},
        TileType.SOFA: {"weight": 1.5, "dismantle_wood": 3, "dismantle_metal": 1},
        TileType.BED: {"weight": 2.0, "dismantle_wood": 4, "dismantle_metal": 2},
        TileType.CABINET: {"weight": 2.5, "dismantle_wood": 4, "dismantle_metal": 2},
        TileType.REFRIGERATOR: {"weight": 3.0, "dismantle_wood": 0, "dismantle_metal": 5},
        TileType.KITCHEN_COUNTER: {"weight": 2.0, "dismantle_wood": 3, "dismantle_metal": 2},
    }

    @staticmethod
    def push_furniture(world, x, y, z, push_dx, push_dy):
        """Pushes furniture at (x, y, z) in direction (push_dx, push_dy) if target tile is walkable floor."""
        z_idx = world.z_to_idx(z)
        ix, iy = int(x), int(y)
        if not (0 <= ix < world.width and 0 <= iy < world.height):
            return False

        tile = world.grid[z_idx, iy, ix]
        if tile not in TileInteractionUtility.MOVABLE_FURNITURE:
            return False

        tx, ty = ix + push_dx, iy + push_dy
        if 0 <= tx < world.width and 0 <= ty < world.height:
            target_tile = world.grid[z_idx, ty, tx]
            if target_tile in (TileType.BUILDING_FLOOR, TileType.UNDERGROUND_FLOOR, TileType.GRASS, TileType.SIDEWALK):
                world.grid[z_idx, ty, tx] = tile
                world.grid[z_idx, iy, ix] = TileType.BUILDING_FLOOR if z >= 0 else TileType.UNDERGROUND_FLOOR
                return True
        return False

    @staticmethod
    def dismantle_furniture(world, x, y, z, inventory):
        """Dismantles furniture at (x, y, z) returning harvested wood and metal into inventory."""
        z_idx = world.z_to_idx(z)
        ix, iy = int(x), int(y)
        if not (0 <= ix < world.width and 0 <= iy < world.height):
            return False, 0, 0

        tile = world.grid[z_idx, iy, ix]
        if tile in TileInteractionUtility.MOVABLE_FURNITURE:
            data = TileInteractionUtility.MOVABLE_FURNITURE[tile]
            wood = data["dismantle_wood"]
            metal = data["dismantle_metal"]

            inventory[ResourceItem.WOOD] = inventory.get(ResourceItem.WOOD, 0) + wood
            inventory[ResourceItem.METAL] = inventory.get(ResourceItem.METAL, 0) + metal

            world.grid[z_idx, iy, ix] = TileType.BUILDING_FLOOR if z >= 0 else TileType.UNDERGROUND_FLOOR
            return True, wood, metal
        return False, 0, 0
