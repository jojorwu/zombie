import random
from src.entities import ResourceItem


class EnvironmentManager:
    """Handles environmental simulation features including day-night updates, dynamic item respawns, and utility states."""
    def __init__(self, world, electricity_utility):
        self.world = world
        self.electricity_utility = electricity_utility

    def update(self):
        self.world.update_day_night()
        self.electricity_utility.update_generators()

    def check_dynamic_item_respawn(self, items_list, factory):
        if self.world.current_tick % 100 == 0:
            active_items = [item for item in items_list if not item.collected]
            if len(active_items) < 20:
                rx, ry = random.randint(0, self.world.width - 1), random.randint(0, self.world.height - 1)
                rz = random.randint(self.world.z_min, self.world.z_max)
                if self.world.is_walkable(rx, ry, rz):
                    itype = random.choice([ResourceItem.FOOD, ResourceItem.WATER, ResourceItem.CANNED_BEANS, ResourceItem.WOOD, ResourceItem.METAL, ResourceItem.FUEL])
                    items_list.append(factory.create_item(rx + 0.5, ry + 0.5, itype, amount=random.randint(1, 2), z=rz))
