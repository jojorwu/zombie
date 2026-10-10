import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.world import World, TileType, ChunkState
from src.entities import (
    FurnitureState, FurnitureCondition, FurnitureStateManager,
    ExtendedItemState, ItemCondition, ItemStateManager, ItemEntity, ResourceItem
)
from src.utils.tile_interaction_utility import TileInteractionUtility


class TestStateManagers(unittest.TestCase):
    def test_furniture_state_manager_lifecycle(self):
        f_mgr = FurnitureStateManager()
        state = f_mgr.register_furniture(x=5, y=5, z=0, tile_type=TileType.CABINET, building_id="bldg_1", building_type="residential", durability=100.0)

        self.assertIsNotNone(state)
        self.assertEqual(state.condition, FurnitureCondition.INTACT)
        self.assertFalse(state.is_searched)

        # Damage furniture
        is_destroyed = state.take_damage(60.0)
        self.assertFalse(is_destroyed)
        self.assertEqual(state.condition, FurnitureCondition.DAMAGED)

        # Destroy furniture
        is_destroyed = state.take_damage(50.0)
        self.assertTrue(is_destroyed)
        self.assertEqual(state.condition, FurnitureCondition.DESTROYED)

        # Move furniture state
        f_mgr.register_furniture(x=10, y=10, z=0, tile_type=TileType.SOFA, building_id="bldg_2")
        moved_state = f_mgr.move_state(10, 10, 11, 10, 0)
        self.assertIsNotNone(moved_state)
        self.assertTrue(moved_state.is_pushed)
        self.assertEqual(moved_state.x, 11)
        self.assertIsNone(f_mgr.get_state(10, 10, 0))
        self.assertIsNotNone(f_mgr.get_state(11, 10, 0))

    def test_item_state_manager_spoilage(self):
        i_mgr = ItemStateManager()
        item = ItemEntity(10.0, 10.0, ResourceItem.BREAD)
        state = i_mgr.register_item(item, building_id="bldg_1", building_type="residential")

        self.assertEqual(state.condition, ItemCondition.PRISTINE)
        state.update_spoilage(50.0)
        self.assertEqual(state.freshness, 50.0)
        self.assertEqual(state.condition, ItemCondition.PRISTINE)

        state.update_spoilage(60.0)
        self.assertEqual(state.freshness, 0.0)
        self.assertEqual(state.condition, ItemCondition.SPOILED)

    def test_world_furniture_and_tile_interaction_integration(self):
        world = World(width=30, height=30)
        g_idx = world.z_to_idx(0)

        # Ensure a furniture tile is placed
        world.grid[g_idx, 5, 5] = TileType.SOFA
        world.grid[g_idx, 5, 6] = TileType.BUILDING_FLOOR
        world.furniture_state_manager.register_furniture(5, 5, 0, TileType.SOFA, building_id="b1", building_type="residential")

        # Push furniture
        success = TileInteractionUtility.push_furniture(world, 5, 5, 0, push_dx=1, push_dy=0)
        self.assertTrue(success)
        self.assertEqual(world.grid[g_idx, 5, 6], TileType.SOFA)
        self.assertIsNotNone(world.furniture_state_manager.get_state(6, 5, 0))

        # Dismantle furniture
        inventory = {}
        success, wood, metal = TileInteractionUtility.dismantle_furniture(world, 6, 5, 0, inventory)
        self.assertTrue(success)
        self.assertGreater(inventory.get(ResourceItem.WOOD, 0), 0)
        self.assertIsNone(world.furniture_state_manager.get_state(6, 5, 0))


if __name__ == "__main__":
    unittest.main()
