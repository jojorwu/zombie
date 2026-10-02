from src.entities.item import ResourceItem


class CraftingSystem:
    UNLOCKED_RECIPES = set()

    BASE_RECIPES = {
        ResourceItem.MEDKIT: {ResourceItem.WOOD: 1, ResourceItem.WATER: 1},
        ResourceItem.WEAPON: {ResourceItem.WOOD: 2, ResourceItem.METAL: 2},
        ResourceItem.RAGS: {ResourceItem.CLOTHES: 1},
    }

    ADVANCED_RECIPES = {
        ResourceItem.STONE_AXE: {ResourceItem.STICK: 2, ResourceItem.STONE: 2, ResourceItem.RAGS: 1},
    }

    @classmethod
    def rip_clothes_into_rags(cls, inventory) -> bool:
        if inventory.get(ResourceItem.CLOTHES, 0) > 0:
            inventory[ResourceItem.CLOTHES] -= 1
            inventory[ResourceItem.RAGS] = inventory.get(ResourceItem.RAGS, 0) + 3
            return True
        return False

    @classmethod
    def read_skill_book(cls, inventory, book_type: str = ResourceItem.SKILL_BOOK) -> bool:
        if inventory.get(book_type, 0) > 0:
            inventory[book_type] -= 1
            cls.UNLOCKED_RECIPES.add(ResourceItem.STONE_AXE)
            return True
        return False

    @classmethod
    def can_craft(cls, inventory, item_type):
        all_recipes = dict(cls.BASE_RECIPES)
        if item_type in cls.UNLOCKED_RECIPES:
            all_recipes.update(cls.ADVANCED_RECIPES)

        recipe = all_recipes.get(item_type)
        if not recipe:
            return False
        for req_item, req_amount in recipe.items():
            if inventory.get(req_item, 0) < req_amount:
                return False
        return True

    @classmethod
    def craft(cls, inventory, item_type):
        if not cls.can_craft(inventory, item_type):
            return False

        all_recipes = dict(cls.BASE_RECIPES)
        all_recipes.update(cls.ADVANCED_RECIPES)

        recipe = all_recipes[item_type]
        for req_item, req_amount in recipe.items():
            inventory[req_item] -= req_amount
        inventory[item_type] = inventory.get(item_type, 0) + 1
        return True
