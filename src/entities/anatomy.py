"""Leaf anatomical health model shared by survivors and zombies.

Kept free of any ``src.*`` imports so it can be safely imported from
``src.entities.__init__``, ``src.world.grid`` and ``src.systems.*`` without
creating circular-import chains.
"""

try:
    from rust_engine import RustAnatomicalHealth as AnatomicalHealth
except ImportError:
    class AnatomicalHealth:
        def __init__(self, head=35.0, torso=100.0, left_arm=40.0, right_arm=40.0, left_leg=45.0, right_leg=45.0):
            self.head = head
            self.torso = torso
            self.left_arm = left_arm
            self.right_arm = right_arm
            self.left_leg = left_leg
            self.right_leg = right_leg
            self.bleeding_rate = 0.0

        def apply_targeted_damage(self, part, raw_damage, armor_reduction=0.0):
            actual = max(0.0, raw_damage * (1.0 - armor_reduction))
            self.torso = max(0.0, self.torso - actual)
            return actual

        def tick_bleeding(self):
            return 0.0

        def get_total_health(self):
            return max(0.0, self.head + self.torso + self.left_arm + self.right_arm + self.left_leg + self.right_leg)

        def get_speed_multiplier(self):
            return 1.0

class BodyPart:
    HEAD = "head"
    TORSO = "torso"
    LEFT_ARM = "left_arm"
    RIGHT_ARM = "right_arm"
    LEFT_LEG = "left_leg"
    RIGHT_LEG = "right_leg"
