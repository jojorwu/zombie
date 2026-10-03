import random
from src.entities.item import ResourceItem


class FoodSpoilageUtility:
    """
    Utility module for food perishability, refrigeration, and spoilage simulation:
    - Fresh perishable foods (meat, steak, bread, apples, cheese, berries, mushrooms, stew, soup) decay over time.
    - Cold storage inside powered refrigerators reduces decay rate by 80% (0.2x).
    - Sub-zero freezing inside powered freezers halts/reduces decay by 95% (0.05x).
    - Canned items, MREs, cereal, and dry rice do not spoil.
    - High ambient temperatures accelerate spoilage.
    """
    PERISHABLE_SPOIL_RATES = {
        ResourceItem.MEAT: 0.10,        # Per tick decay
        ResourceItem.STEAK: 0.10,
        ResourceItem.STEW: 0.06,
        ResourceItem.SOUP: 0.06,
        ResourceItem.BREAD: 0.05,
        ResourceItem.CHEESE: 0.04,
        ResourceItem.BERRIES: 0.03,
        ResourceItem.MUSHROOM: 0.03,
        ResourceItem.APPLE: 0.02,
        ResourceItem.POTATO: 0.01,
        ResourceItem.CANNED_FOOD: 0.0,  # Non-perishable
        ResourceItem.CANNED_BEANS: 0.0,
        ResourceItem.CANNED_TUNA: 0.0,
        ResourceItem.MRE: 0.0,
        ResourceItem.CEREAL: 0.0,
        ResourceItem.RICE: 0.0,
        ResourceItem.CHOCOLATE: 0.0,
    }

    @classmethod
    def calculate_spoilage_decay(cls, item_type, current_freshness, ambient_temp_c, is_refrigerated=False, is_freezer=False, power_online=True):
        """
        Calculates updated freshness (1.0 = fresh, 0.0 = spoiled/rotten) after a decay interval.
        Freezer storage slows decay by 95%, Refrigerator by 80%.
        """
        base_rate = cls.PERISHABLE_SPOIL_RATES.get(item_type, 0.0)
        if base_rate <= 0.0:
            return current_freshness  # Non-perishable

        # Refrigeration & Freezer effect
        decay_modifier = 1.0
        if power_online:
            if is_freezer:
                decay_modifier *= 0.05  # 95% slower decay (frozen)
            elif is_refrigerated:
                decay_modifier *= 0.20  # 80% slower decay in cold storage

        # Temperature effect (heat accelerates rot)
        if ambient_temp_c > 20.0:
            decay_modifier *= (1.0 + (ambient_temp_c - 20.0) * 0.05)

        updated_freshness = max(0.0, current_freshness - (base_rate * decay_modifier * 0.1))
        return updated_freshness

    @classmethod
    def is_spoiled(cls, freshness):
        return freshness <= 0.05
