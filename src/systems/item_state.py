class ItemConditionState:
    PRISTINE = "pristine"
    GOOD = "good"
    DAMAGED = "damaged"
    DESTROYED = "destroyed"


class ItemStateUtility:
    @staticmethod
    def get_condition_string(durability: float, max_durability: float = 100.0) -> str:
        ratio = durability / max_durability if max_durability > 0 else 0.0
        if ratio > 0.8:
            return ItemConditionState.PRISTINE
        if ratio > 0.4:
            return ItemConditionState.GOOD
        if ratio > 0.0:
            return ItemConditionState.DAMAGED
        return ItemConditionState.DESTROYED
