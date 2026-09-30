from src.entities.item import ResourceItem

class CraftingSystem:
    RECIPES = {
        ResourceItem.MEDKIT: {ResourceItem.WOOD: 1, ResourceItem.WATER: 1},
        ResourceItem.WEAPON: {ResourceItem.WOOD: 2, ResourceItem.METAL: 2},
    }

    @staticmethod
    def can_craft(inventory, item_type):
        recipe = CraftingSystem.RECIPES.get(item_type)
        if not recipe:
            return False
        for req_item, req_amount in recipe.items():
            if inventory.get(req_item, 0) < req_amount:
                return False
        return True

    @staticmethod
    def craft(inventory, item_type):
        if not CraftingSystem.can_craft(inventory, item_type):
            return False
        recipe = CraftingSystem.RECIPES[item_type]
        for req_item, req_amount in recipe.items():
            inventory[req_item] -= req_amount
        inventory[item_type] = inventory.get(item_type, 0) + 1
        return True
