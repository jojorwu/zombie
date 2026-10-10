import unittest
from src.entities.item import ResourceItem
from src.world.tiles import TileType
from src.entities.state_manager import FurnitureState, FurnitureStateManager
from src.utils.container_utility import ContainerUtility, ItemCategory
from src.utils.food_spoilage_utility import FoodSpoilageUtility


class TestContainerUtility(unittest.TestCase):
    def test_item_weights_and_categories(self):
        self.assertEqual(ContainerUtility.get_item_weight(ResourceItem.PISTOL), 1.2)
        self.assertEqual(ContainerUtility.get_item_weight(ResourceItem.SLEDGEHAMMER), 4.5)
        self.assertEqual(ContainerUtility.get_item_weight(ResourceItem.RAGS), 0.1)

        self.assertEqual(ContainerUtility.get_item_category(ResourceItem.PISTOL), ItemCategory.FIREARM)
        self.assertEqual(ContainerUtility.get_item_category(ResourceItem.AXE), ItemCategory.WEAPON)
        self.assertEqual(ContainerUtility.get_item_category(ResourceItem.MEAT), ItemCategory.FOOD)
        self.assertEqual(ContainerUtility.get_item_category(ResourceItem.MEDKIT), ItemCategory.MEDICAL)

    def test_container_capacities(self):
        furniture = FurnitureState(x=5, y=5, z=0, tile_type=TileType.CABINET)
        self.assertEqual(furniture.capacity, 50.0)

        fridge = FurnitureState(x=5, y=6, z=0, tile_type=TileType.REFRIGERATOR)
        self.assertEqual(fridge.capacity, 40.0)

        safe = FurnitureState(x=5, y=7, z=0, tile_type=TileType.WEAPON_SAFE)
        self.assertEqual(safe.capacity, 35.0)

    def test_add_and_remove_items(self):
        container = {}
        success, added = ContainerUtility.add_item_to_container(container, ResourceItem.CANNED_FOOD, 10)
        self.assertTrue(success)
        self.assertEqual(added, 10)
        self.assertIn(ResourceItem.CANNED_FOOD, container)
        self.assertEqual(container[ResourceItem.CANNED_FOOD], 10)

        # Total weight = 10 * 0.8 = 8.0 kg (capacity 30.0 kg)
        self.assertEqual(ContainerUtility.get_container_weight(container), 8.0)

        removed = ContainerUtility.remove_item_from_container(container, ResourceItem.CANNED_FOOD, 4)
        self.assertEqual(removed, 4)
        self.assertEqual(container[ResourceItem.CANNED_FOOD], 6)
        self.assertEqual(ContainerUtility.get_container_weight(container), 4.8)

    def test_capacity_overflow_prevention(self):
        container = {"contents": {}}  # Capacity 30.0 kg
        # Heavy item: CAR_BATTERY (10.0 kg)
        success, added = ContainerUtility.add_item_to_container(container, ResourceItem.CAR_BATTERY, 5)
        self.assertTrue(success)
        self.assertEqual(added, 3)  # Only 3 fit (30.0 kg)

        # Attempt adding more
        self.assertFalse(ContainerUtility.can_fit_item(container, ResourceItem.CAR_BATTERY, 1))

    def test_transfer_item_between_containers(self):
        source = {"contents": {ResourceItem.PISTOL_AMMO: 10, ResourceItem.RIFLE: 1}}
        target = {"contents": {}}

        transferred = ContainerUtility.transfer_item(source, target, ResourceItem.PISTOL_AMMO, 6)
        self.assertEqual(transferred, 6)
        self.assertEqual(source["contents"][ResourceItem.PISTOL_AMMO], 4)
        self.assertEqual(target["contents"][ResourceItem.PISTOL_AMMO], 6)

    def test_bag_weight_reduction(self):
        # Bag containing sledgehammer
        bag_contents = {ResourceItem.BACKPACK: 1, ResourceItem.SLEDGEHAMMER: 1}
        weight = ContainerUtility.get_container_weight(bag_contents, inside_bag=True)
        # Sledgehammer 4.5 * 0.3 + Backpack 1.0 = 2.35
        self.assertEqual(weight, 2.35)

    def test_freezer_vs_refrigerator_spoilage(self):
        # Base meat freshness = 1.0, rate = 0.10
        room_temp = FoodSpoilageUtility.calculate_spoilage_decay(ResourceItem.MEAT, 1.0, ambient_temp_c=25.0, is_refrigerated=False, power_online=True)
        refrig = FoodSpoilageUtility.calculate_spoilage_decay(ResourceItem.MEAT, 1.0, ambient_temp_c=25.0, is_refrigerated=True, power_online=True)
        freezer = FoodSpoilageUtility.calculate_spoilage_decay(ResourceItem.MEAT, 1.0, ambient_temp_c=25.0, is_freezer=True, power_online=True)

        self.assertGreater(freezer, refrig)
        self.assertGreater(refrig, room_temp)


if __name__ == "__main__":
    unittest.main()
