class FoodSpoilageUtility:
    @staticmethod
    def calculate_spoilage_decay(item_type: str, freshness: float = 1.0, ambient_temp_c: float = 20.0,
                                is_refrigerated: bool = False, is_freezer: bool = False, power_online: bool = True) -> float:
        rate = 0.05
        if is_freezer and power_online:
            rate *= 0.05
        elif is_refrigerated and power_online:
            rate *= 0.2
        else:
            rate *= max(0.5, ambient_temp_c / 20.0)
        return max(0.0, freshness - rate)
