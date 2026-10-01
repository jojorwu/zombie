import random
import math
from src.entities.item import ResourceItem
from src.world.tiles import TileType
from src.entities.sensory import NoiseEvent
from utils.p_np_math import PolynomialKnapsackSolver


class SurvivorLooting:
    """Handles item pickup optimization via Knapsack and searching furniture containers."""
    @staticmethod
    def gather(survivor, world, items, noise_events):
        nearby_items = [
            item for item in items
            if not item.collected and item.z == survivor.z and math.hypot(item.x - survivor.x, item.y - survivor.y) < 1.5
        ]

        if nearby_items:
            optimal_subset = PolynomialKnapsackSolver.optimize_inventory(nearby_items, max_capacity=15)
            for item in optimal_subset:
                item.collected = True
                survivor.inventory[item.item_type] = survivor.inventory.get(item.item_type, 0) + item.amount
                survivor.score += 5.0
        elif world:
            z_idx = world.z_to_idx(survivor.z)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                fx, fy = int(survivor.x + dx), int(survivor.y + dy)
                if 0 <= fx < world.width and 0 <= fy < world.height:
                    ftile = world.grid[z_idx, fy, fx]
                    if ftile in (TileType.CABINET, TileType.REFRIGERATOR, TileType.KITCHEN_COUNTER, TileType.TABLE):
                        if ftile == TileType.REFRIGERATOR:
                            found_item = random.choice([ResourceItem.STEAK, ResourceItem.STEW, ResourceItem.MEAT, ResourceItem.BREAD, ResourceItem.WATER_BOTTLE, ResourceItem.CHEESE])
                        elif ftile == TileType.CABINET:
                            found_item = random.choice([ResourceItem.CANNED_FOOD, ResourceItem.CANNED_BEANS, ResourceItem.CANNED_TUNA, ResourceItem.CAN_OPENER, ResourceItem.PISTOL_AMMO, ResourceItem.MEDKIT])
                        else:
                            found_item = random.choice([ResourceItem.CHEF_KNIFE, ResourceItem.KATANA, ResourceItem.FRYING_PAN, ResourceItem.POT, ResourceItem.CUTTING_BOARD])

                        survivor.inventory[found_item] = survivor.inventory.get(found_item, 0) + 1
                        survivor.score += 10.0
                        if noise_events is not None:
                            noise_events.append(NoiseEvent(survivor.x, survivor.y, survivor.z, volume=11.0, source_type="dismantling"))
                        break
