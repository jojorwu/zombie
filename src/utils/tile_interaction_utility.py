from src.world.tiles import TileType


class TileInteractionUtility:
    MOVABLE_FURNITURE_TILES = {
        TileType.TABLE, TileType.SOFA, TileType.TV_STAND, TileType.OFFICE_DESK, TileType.SCHOOL_DESK
    }

    @staticmethod
    def siphon_fuel_from_pump(world, x: int, y: int, z: int, inventory: dict) -> tuple:
        z_idx = world.z_to_idx(z)
        if world.grid[z_idx, y, x] == TileType.GAS_PUMP:
            inventory["fuel"] = inventory.get("fuel", 0) + 2
            return True, 2
        return False, 0

    @staticmethod
    def push_furniture(world, x: int, y: int, z: int, dx: int = 0, dy: int = 0, push_dx: int = 0, push_dy: int = 0) -> bool:
        shift_x = push_dx if push_dx != 0 else dx
        shift_y = push_dy if push_dy != 0 else dy
        z_idx = world.z_to_idx(z)
        tile = world.grid[z_idx, y, x]
        if tile in TileInteractionUtility.MOVABLE_FURNITURE_TILES:
            nx, ny = x + shift_x, y + shift_y
            if world.is_walkable(nx, ny, z):
                world.grid[z_idx, y, x] = TileType.BUILDING_FLOOR
                world.grid[z_idx, ny, nx] = tile
                if hasattr(world, 'furniture_state_manager') and world.furniture_state_manager:
                    world.furniture_state_manager.move_state(x, y, nx, ny, z)
                return True
        return False

    @staticmethod
    def dismantle_furniture(world, x: int, y: int, z: int, inventory: dict) -> tuple:
        z_idx = world.z_to_idx(z)
        tile = world.grid[z_idx, y, x]
        if tile in TileInteractionUtility.MOVABLE_FURNITURE_TILES:
            world.grid[z_idx, y, x] = TileType.BUILDING_FLOOR
            inventory["wood"] = inventory.get("wood", 0) + 2
            inventory["metal"] = inventory.get("metal", 0) + 1
            if hasattr(world, 'furniture_state_manager') and world.furniture_state_manager:
                world.furniture_state_manager.remove_state(x, y, z)
            return True, 2, 1
        return False, 0, 0

    @staticmethod
    def lockpick_door_or_safe(world, x: int, y: int, z: int, inventory: dict) -> bool:
        z_idx = world.z_to_idx(z)
        tile = world.grid[z_idx, y, x]
        if tile == TileType.DOOR_LOCKED:
            world.grid[z_idx, y, x] = TileType.DOOR_OPEN
            return True
        if tile == TileType.WEAPON_SAFE:
            from src.entities.item import ResourceItem
            inventory[ResourceItem.MONEY] = inventory.get(ResourceItem.MONEY, 0) + 100
            return True
        return False
