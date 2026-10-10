from typing import Dict, Any, Tuple
import random
from src.entities.item import ARMOR_STATS

try:
    from rust_engine import RustAnatomicalHealth
    RUST_HEALTH_AVAILABLE = True
except ImportError:
    RUST_HEALTH_AVAILABLE = False


class BodyPart:
    HEAD = "head"
    TORSO = "torso"
    LEFT_ARM = "left_arm"
    RIGHT_ARM = "right_arm"
    LEFT_LEG = "left_leg"
    RIGHT_LEG = "right_leg"


class AnatomicalHealth:
    """
    Realistic anatomical health model tracking discrete body parts and armor protection:
    - Head: Critical multiplier, helmet armor protection.
    - Torso: Vital body core, high health pool, body armor/jacket protection.
    - Arms/Legs: Limb protection via pads, affects movement & attack power.
    """
    __slots__ = ("parts", "armor", "total_bleeding", "rust_health")

    def __init__(self, max_head: float = 35.0, max_torso: float = 100.0, max_arm: float = 40.0, max_leg: float = 45.0) -> None:
        self.parts: Dict[str, Dict[str, Any]] = {
            BodyPart.HEAD: {"hp": max_head, "max": max_head, "bleeding": 0.0, "crippled": False},
            BodyPart.TORSO: {"hp": max_torso, "max": max_torso, "bleeding": 0.0, "crippled": False},
            BodyPart.LEFT_ARM: {"hp": max_arm, "max": max_arm, "bleeding": 0.0, "crippled": False},
            BodyPart.RIGHT_ARM: {"hp": max_arm, "max": max_arm, "bleeding": 0.0, "crippled": False},
            BodyPart.LEFT_LEG: {"hp": max_leg, "max": max_leg, "bleeding": 0.0, "crippled": False},
            BodyPart.RIGHT_LEG: {"hp": max_leg, "max": max_leg, "bleeding": 0.0, "crippled": False},
        }
        self.armor: Dict[str, Any] = {
            "head": None,
            "torso": None,
            "limbs": None,
        }
        self.total_bleeding: float = 0.0
        self.rust_health = RustAnatomicalHealth(max_head, max_torso, max_arm, max_arm, max_leg, max_leg) if RUST_HEALTH_AVAILABLE else None

    @property
    def head_health(self) -> float:
        return self.parts[BodyPart.HEAD]["hp"]

    @property
    def torso_health(self) -> float:
        return self.parts[BodyPart.TORSO]["hp"]

    @property
    def left_leg_health(self) -> float:
        return self.parts[BodyPart.LEFT_LEG]["hp"]

    @property
    def right_leg_health(self) -> float:
        return self.parts[BodyPart.RIGHT_LEG]["hp"]

    @property
    def overall_health_percent(self) -> float:
        if self.rust_health:
            return self.rust_health.get_total_health()
        total_hp = sum(p["hp"] for p in self.parts.values())
        total_max = sum(p["max"] for p in self.parts.values())
        return max(0.0, min(100.0, (total_hp / total_max) * 100.0))

    @property
    def is_dead(self) -> bool:
        return self.parts[BodyPart.HEAD]["hp"] <= 0 or self.parts[BodyPart.TORSO]["hp"] <= 0

    @property
    def movement_speed_multiplier(self) -> float:
        if self.rust_health:
            return self.rust_health.get_speed_multiplier()
        multiplier = 1.0
        if self.parts[BodyPart.LEFT_LEG]["crippled"]:
            multiplier *= 0.65
        if self.parts[BodyPart.RIGHT_LEG]["crippled"]:
            multiplier *= 0.65
        if self.parts[BodyPart.LEFT_LEG]["hp"] <= 0 and self.parts[BodyPart.RIGHT_LEG]["hp"] <= 0:
            multiplier = 0.25
        return max(0.2, multiplier)

    @property
    def attack_damage_multiplier(self) -> float:
        multiplier = 1.0
        if self.parts[BodyPart.LEFT_ARM]["crippled"]:
            multiplier *= 0.8
        if self.parts[BodyPart.RIGHT_ARM]["crippled"]:
            multiplier *= 0.7
        return max(0.3, multiplier)

    def equip_armor(self, armor_type: str) -> None:
        if armor_type in ARMOR_STATS:
            slot = ARMOR_STATS[armor_type]["slot"]
            self.armor[slot] = armor_type

    def apply_targeted_damage(self, amount: float, target_part: str = None) -> Tuple[str, float, bool]:
        """Applies damage to specific or probabilistic body part with armor absorption."""
        if target_part is None:
            roll = random.random()
            if roll < 0.15:
                target_part = BodyPart.HEAD
            elif roll < 0.55:
                target_part = BodyPart.TORSO
            elif roll < 0.75:
                target_part = random.choice([BodyPart.LEFT_ARM, BodyPart.RIGHT_ARM])
            else:
                target_part = random.choice([BodyPart.LEFT_LEG, BodyPart.RIGHT_LEG])

        part = self.parts[target_part]
        damage = amount

        if target_part == BodyPart.HEAD:
            damage *= 1.8

        slot = "head" if target_part == BodyPart.HEAD else ("torso" if target_part == BodyPart.TORSO else "limbs")
        equipped = self.armor.get(slot)
        armor_red = 0.0
        if equipped and equipped in ARMOR_STATS:
            armor_red = ARMOR_STATS[equipped]["reduction"]
            damage *= (1.0 - armor_red)

        if self.rust_health:
            self.rust_health.apply_targeted_damage(target_part, amount, armor_red)

        part["hp"] = max(0.0, part["hp"] - damage)

        if part["hp"] <= 0:
            part["crippled"] = True

        if random.random() < 0.4:
            part["bleeding"] = min(2.0, part["bleeding"] + 0.3)

        self.total_bleeding = sum(p["bleeding"] for p in self.parts.values())
        return target_part, damage, part["crippled"]

    def update_bleeding(self) -> float:
        """Processes tick-by-tick bleeding damage across all limbs."""
        if self.rust_health:
            self.rust_health.tick_bleeding()

        bleed_dmg = sum(p["bleeding"] for p in self.parts.values())
        if bleed_dmg > 0:
            self.parts[BodyPart.TORSO]["hp"] = max(0.0, self.parts[BodyPart.TORSO]["hp"] - bleed_dmg * 0.7)
            self.parts[BodyPart.HEAD]["hp"] = max(0.0, self.parts[BodyPart.HEAD]["hp"] - bleed_dmg * 0.3)

            for p in self.parts.values():
                if p["bleeding"] > 0:
                    p["bleeding"] = max(0.0, p["bleeding"] - 0.01)

        self.total_bleeding = sum(p["bleeding"] for p in self.parts.values())
        return bleed_dmg

    def treat_wounds(self) -> None:
        """Uses medical supplies to bandage cuts and stop bleeding."""
        for p in self.parts.values():
            p["bleeding"] = 0.0
            p["hp"] = min(p["max"], p["hp"] + 15.0)
            if p["hp"] > p["max"] * 0.5:
                p["crippled"] = False
        self.total_bleeding = 0.0
