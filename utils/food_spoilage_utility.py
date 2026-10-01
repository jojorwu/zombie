import random
from src.entities.item import ResourceItem

class FoodSpoilageUtility:
    """
    Utility module for food perishability, refrigeration, and spoilage simulation:
    - Fresh perishable foods (meat, bread, apples, steak, cheese) decay over time.
    - Cold storage inside powered refrigerators reduces decay rate by 80%.
    - Canned/mre items do not spoil.
    - High ambient temperatures accelerate spoilage.
    """
    PERISHABLE_SPOIL_RATES = {
        ResourceItem.BREAD: 0.05,       # Per tick decay
        ResourceItem.APPLE: 0.02,
        ResourceItem.MEAT: 0.10,
        ResourceItem.CANNED_FOOD: 0.0,  # Non-perishable
        ResourceItem.MRE: 0.0,
    }

    @classmethod
    def calculate_spoilage_decay(cls, item_type, current_freshness, ambient_temp_c, is_refrigerated=False, power_online=True):
        """
        Calculates updated freshness (1.0 = fresh, 0.0 = spoiled/rotten) after a decay interval.
        """
        base_rate = cls.PERISHABLE_SPOIL_RATES.get(item_type, 0.01)
        if base_rate <= 0.0:
            return current_freshness  # Non-perishable

        # Refrigeration effect
        decay_modifier = 1.0
        if is_refrigerated and power_online:
            decay_modifier *= 0.20  # 80% slower decay

        # Temperature effect (heat accelerates rot)
        if ambient_temp_c > 20.0:
            decay_modifier *= (1.0 + (ambient_temp_c - 20.0) * 0.05)

        updated_freshness = max(0.0, current_freshness - (base_rate * decay_modifier * 0.1))
        return updated_freshness

    @classmethod
    def is_spoiled(cls, freshness):
        return freshness <= 0.05
