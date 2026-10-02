from src.world import TileType
from src.entities.item import ResourceItem

class TileInteractionUtility:
    """
    Utility module for managing tile and furniture interactions:
    - Moving / pushing furniture (cabinets, tables, sofas, beds, safes, racks) to create barricades or unblock paths
    - Dismantling furniture for wood and metal resources
    - Fast spatial search for nearby furniture
    """
    MOVABLE_FURNITURE = {
        TileType.TABLE: {"weight": 1.0, "dismantle_wood": 2, "dismantle_metal": 1},
        TileType.CHAIR: {"weight": 0.5, "dismantle_wood": 1, "dismantle_metal": 0},
        TileType.SOFA: {"weight": 1.5, "dismantle_wood": 3, "dismantle_metal": 1},
        TileType.BED: {"weight": 2.0, "dismantle_wood": 4, "dismantle_metal": 2},
        TileType.CABINET: {"weight": 2.5, "dismantle_wood": 4, "dismantle_metal": 2},
        TileType.REFRIGERATOR: {"weight": 3.0, "dismantle_wood": 0, "dismantle_metal": 5},
        TileType.KITCHEN_COUNTER: {"weight": 2.0, "dismantle_wood": 3, "dismantle_metal": 2},
        TileType.BOOKSHELF: {"weight": 2.5, "dismantle_wood": 5, "dismantle_metal": 1},
        TileType.OFFICE_DESK: {"weight": 2.0, "dismantle_wood": 4, "dismantle_metal": 2},
        TileType.MEDICAL_BED: {"weight": 2.5, "dismantle_wood": 1, "dismantle_metal": 5},
        TileType.GUN_RACK: {"weight": 2.0, "dismantle_wood": 2, "dismantle_metal": 4},
        TileType.WEAPON_SAFE: {"weight": 4.0, "dismantle_wood": 0, "dismantle_metal": 8},
        TileType.CASH_REGISTER: {"weight": 1.0, "dismantle_wood": 0, "dismantle_metal": 3},
        TileType.STORE_SHELF: {"weight": 2.5, "dismantle_wood": 2, "dismantle_metal": 4},
        TileType.SCHOOL_DESK: {"weight": 1.0, "dismantle_wood": 2, "dismantle_metal": 1},
        TileType.WORKBENCH: {"weight": 3.0, "dismantle_wood": 5, "dismantle_metal": 4},
        TileType.LOCKER: {"weight": 2.5, "dismantle_wood": 0, "dismantle_metal": 5},
        TileType.TV_STAND: {"weight": 1.5, "dismantle_wood": 2, "dismantle_metal": 2},
        TileType.DISPLAY_CASE: {"weight": 2.0, "dismantle_wood": 2, "dismantle_metal": 3},
        TileType.FACTORY_RACK: {"weight": 3.5, "dismantle_wood": 0, "dismantle_metal": 7},
    }

    MOVABLE_FURNITURE_TILES = set(MOVABLE_FURNITURE.keys())

    @staticmethod
    def is_movable_furniture(tile_type):
        """Fast O(1) check if tile is movable furniture."""
        return tile_type in TileInteractionUtility.MOVABLE_FURNITURE_TILES

    @staticmethod
    def get_adjacent_furniture(world, x, y, z):
        """Returns list of (fx, fy, tile_type) for adjacent movable furniture."""
        z_idx = world.z_to_idx(z)
        ix, iy = int(x), int(y)
        w, h = world.width, world.height
        grid_z = world.grid[z_idx]
        movable = []

        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            fx, fy = ix + dx, iy + dy
            if 0 <= fx < w and 0 <= fy < h:
                tile = grid_z[fy, fx]
                if tile in TileInteractionUtility.MOVABLE_FURNITURE_TILES:
                    movable.append((fx, fy, tile))
        return movable

    @staticmethod
    def push_furniture(world, x, y, z, push_dx, push_dy):
        """Pushes furniture at (x, y, z) in direction (push_dx, push_dy) if target tile is walkable floor."""
        z_idx = world.z_to_idx(z)
        ix, iy = int(x), int(y)
        if not (0 <= ix < world.width and 0 <= iy < world.height):
            return False

        tile = world.grid[z_idx, iy, ix]
        if tile not in TileInteractionUtility.MOVABLE_FURNITURE_TILES:
            return False

        tx, ty = ix + push_dx, iy + push_dy
        if 0 <= tx < world.width and 0 <= ty < world.height:
            target_tile = world.grid[z_idx, ty, tx]
            if target_tile in (TileType.BUILDING_FLOOR, TileType.UNDERGROUND_FLOOR, TileType.GRASS, TileType.SIDEWALK):
                world.grid[z_idx, ty, tx] = tile
                world.grid[z_idx, iy, ix] = TileType.BUILDING_FLOOR if z >= 0 else TileType.UNDERGROUND_FLOOR

                # Move state in state manager if available
                if hasattr(world, 'furniture_state_manager'):
                    world.furniture_state_manager.move_state(ix, iy, tx, ty, z)
                return True
        return False

    @staticmethod
    def lockpick_door_or_safe(world, x, y, z, inventory):
        """Allows survivors with a lockpick, crowbar, or hammer to open locked doors and weapon safes."""
        z_idx = world.z_to_idx(z)
        ix, iy = int(x), int(y)
        if not (0 <= ix < world.width and 0 <= iy < world.height):
            return False

        tile = world.grid[z_idx, iy, ix]
        if tile == TileType.DOOR_LOCKED:
            if inventory.get(ResourceItem.LOCKPICK, 0) > 0 or inventory.get(ResourceItem.CROWBAR, 0) > 0:
                world.grid[z_idx, iy, ix] = TileType.DOOR_OPEN
                return True
        elif tile == TileType.WEAPON_SAFE:
            if inventory.get(ResourceItem.LOCKPICK, 0) > 0:
                inventory[ResourceItem.MONEY] = inventory.get(ResourceItem.MONEY, 0) + 150
                inventory[ResourceItem.JEWELRY] = inventory.get(ResourceItem.JEWELRY, 0) + 1
                return True
        return False

    @staticmethod
    def harvest_bush_sticks(world, x, y, z, inventory):
        """Allows survivors to harvest sticks/branches from forest bushes at (x, y, z)."""
        z_idx = world.z_to_idx(z)
        ix, iy = int(x), int(y)
        if not (0 <= ix < world.width and 0 <= iy < world.height):
            return False, 0

        tile = world.grid[z_idx, iy, ix]
        if tile == TileType.BUSH:
            inventory[ResourceItem.STICK] = inventory.get(ResourceItem.STICK, 0) + 2
            world.grid[z_idx, iy, ix] = TileType.GRASS
            return True, 2
        return False, 0

    @staticmethod
    def siphon_fuel_from_pump(world, x, y, z, inventory):
        """Allows survivors to siphon fuel from gas station pumps at (x, y, z) into inventory."""
        z_idx = world.z_to_idx(z)
        ix, iy = int(x), int(y)
        if not (0 <= ix < world.width and 0 <= iy < world.height):
            return False, 0

        tile = world.grid[z_idx, iy, ix]
        if tile == TileType.GAS_PUMP:
            inventory[ResourceItem.FUEL] = inventory.get(ResourceItem.FUEL, 0) + 2
            return True, 2
        return False, 0

    @staticmethod
    def dismantle_furniture(world, x, y, z, inventory):
        """Dismantles furniture at (x, y, z) returning harvested wood and metal into inventory."""
        z_idx = world.z_to_idx(z)
        ix, iy = int(x), int(y)
        if not (0 <= ix < world.width and 0 <= iy < world.height):
            return False, 0, 0

        tile = world.grid[z_idx, iy, ix]
        if tile in TileInteractionUtility.MOVABLE_FURNITURE_TILES:
            data = TileInteractionUtility.MOVABLE_FURNITURE[tile]
            wood = data["dismantle_wood"]
            metal = data["dismantle_metal"]

            inventory[ResourceItem.WOOD] = inventory.get(ResourceItem.WOOD, 0) + wood
            inventory[ResourceItem.METAL] = inventory.get(ResourceItem.METAL, 0) + metal

            world.grid[z_idx, iy, ix] = TileType.BUILDING_FLOOR if z >= 0 else TileType.UNDERGROUND_FLOOR

            # Remove state from state manager if available
            if hasattr(world, 'furniture_state_manager'):
                world.furniture_state_manager.remove_state(ix, iy, z)
            return True, wood, metal
        return False, 0, 0
