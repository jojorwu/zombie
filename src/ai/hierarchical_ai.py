import math
import random
from enum import Enum, auto
from src.ai.inference import check_line_of_sight


class HighLevelGoal(Enum):
    SURVIVE = auto()
    FLEE_THREAT = auto()
    ATTACK_THREAT = auto()
    LOOT_SUPPLIES = auto()
    SEEK_SHELTER = auto()
    REST_AND_HEAL = auto()
    EXPLORE = auto()


class BehaviourNodeState(Enum):
    SUCCESS = auto()
    FAILURE = auto()
    RUNNING = auto()


class HierarchicalDecisionPlanner:
    """
    Hierarchical AI Planner combining high-level goal selection with low-level
    Behaviour Tree execution to eliminate action jitter and ensure long-term goal coherence.
    """
    __slots__ = ("goal_eval_interval", "last_eval_tick", "current_goal", "target_entity", "target_pos")

    def __init__(self, goal_eval_interval: int = 15):
        self.goal_eval_interval = goal_eval_interval
        self.last_eval_tick = -goal_eval_interval
        self.current_goal = HighLevelGoal.SURVIVE
        self.target_entity = None
        self.target_pos = None

    def evaluate_goal(self, survivor, world, items, vehicles, zombies, animals, action_idx: int = None) -> HighLevelGoal:
        """Determines the survivor's current high-level goal based on needs, threats, Line-of-Sight, and spatial memory."""
        self.target_entity = None
        self.target_pos = None

        surv_health = getattr(survivor, 'health', 100.0)
        surv_hunger = getattr(survivor, 'hunger', 100.0)
        surv_thirst = getattr(survivor, 'thirst', 100.0)
        surv_sleep = getattr(survivor, 'sleep', 100.0)

        if surv_health < 30.0 or surv_hunger < 20.0 or surv_thirst < 20.0:
            if surv_health < 30.0 and survivor.inventory.get("medkit", 0) > 0:
                self.current_goal = HighLevelGoal.REST_AND_HEAL
                return self.current_goal

        closest_zombie = None
        min_z_dist = 999.0
        sx, sy, sz = survivor.x, survivor.y, int(survivor.z)

        # Fast AABB filtering before expensive distance & raycasting
        for z in zombies:
            if getattr(z, "is_alive", True) and int(z.z) == sz:
                dx = z.x - sx
                dy = z.y - sy
                if abs(dx) < 8.0 and abs(dy) < 8.0:
                    d = math.hypot(dx, dy)
                    if d < min_z_dist:
                        if check_line_of_sight(world, sx, sy, z.x, z.y, sz):
                            min_z_dist = d
                            closest_zombie = z

        if closest_zombie and min_z_dist < 6.0:
            has_weapon = survivor.inventory.get("weapon", 0) > 0 or survivor.inventory.get("pistol", 0) > 0
            if has_weapon and surv_health > 40.0:
                self.current_goal = HighLevelGoal.ATTACK_THREAT
                self.target_entity = closest_zombie
                self.target_pos = (closest_zombie.x, closest_zombie.y, closest_zombie.z)
            else:
                self.current_goal = HighLevelGoal.FLEE_THREAT
                self.target_entity = closest_zombie
                self.target_pos = (closest_zombie.x, closest_zombie.y, closest_zombie.z)
            return self.current_goal

        current_tick = getattr(world, 'current_tick', 0)
        if hasattr(survivor, 'spatial_memory') and "zombie" in survivor.spatial_memory:
            zx, zy, zz, ztick = survivor.spatial_memory["zombie"]
            if current_tick - ztick <= 150 and int(zz) == sz:
                d = math.hypot(zx - sx, zy - sy)
                if d < 5.0:
                    self.current_goal = HighLevelGoal.FLEE_THREAT
                    self.target_pos = (zx, zy, zz)
                    return self.current_goal

        if surv_hunger < 40.0 or surv_thirst < 40.0:
            self.current_goal = HighLevelGoal.LOOT_SUPPLIES
            return self.current_goal

        building_grid = getattr(world, 'building_grid', {})
        building = building_grid.get((int(sx), int(sy))) if building_grid else None
        light_lvl = world.get_light_level() if hasattr(world, 'get_light_level') else 1.0

        if building is None and (light_lvl < 0.3 or surv_sleep < 40.0):
            self.current_goal = HighLevelGoal.SEEK_SHELTER
            return self.current_goal

        if action_idx is not None:
            goal_map = {
                0: HighLevelGoal.EXPLORE,
                1: HighLevelGoal.LOOT_SUPPLIES,
                2: HighLevelGoal.ATTACK_THREAT,
                3: HighLevelGoal.FLEE_THREAT,
                4: HighLevelGoal.SEEK_SHELTER,
                5: HighLevelGoal.REST_AND_HEAL,
            }
            self.current_goal = goal_map.get(action_idx % 6, HighLevelGoal.EXPLORE)
        else:
            self.current_goal = HighLevelGoal.EXPLORE

        return self.current_goal

    def execute_low_level_behaviour(self, survivor, world, items, vehicles, zombies, animals, raw_dx: float, raw_dy: float, raw_action: int) -> tuple:
        """
        Translates high-level goal into stable, low-level (dx, dy, action) commands
        preventing rapid directional oscillation.
        """
        goal = self.current_goal

        if goal == HighLevelGoal.REST_AND_HEAL:
            return 0.0, 0.0, 5

        elif goal == HighLevelGoal.FLEE_THREAT:
            tx, ty = (self.target_entity.x, self.target_entity.y) if self.target_entity else (self.target_pos[0], self.target_pos[1]) if self.target_pos else (survivor.x, survivor.y)
            dx = survivor.x - tx
            dy = survivor.y - ty
            dist = math.hypot(dx, dy)
            if dist > 0.001:
                return dx / dist, dy / dist, 0
            return -raw_dx, -raw_dy, 0

        elif goal == HighLevelGoal.ATTACK_THREAT and self.target_entity:
            dx = self.target_entity.x - survivor.x
            dy = self.target_entity.y - survivor.y
            dist = math.hypot(dx, dy)
            if dist <= 1.5:
                return 0.0, 0.0, 1
            elif dist > 0.001:
                return dx / dist, dy / dist, 0

        elif goal == HighLevelGoal.LOOT_SUPPLIES:
            closest_item = None
            min_i_dist = 999.0
            sx, sy, sz = survivor.x, survivor.y, int(survivor.z)

            for item in items:
                if not getattr(item, 'collected', False) and int(item.z) == sz:
                    dx = item.x - sx
                    dy = item.y - sy
                    if abs(dx) < 12.0 and abs(dy) < 12.0:
                        d = math.hypot(dx, dy)
                        if d < min_i_dist and check_line_of_sight(world, sx, sy, item.x, item.y, sz):
                            min_i_dist = d
                            closest_item = item

            if closest_item and min_i_dist < 12.0:
                dx = closest_item.x - survivor.x
                dy = closest_item.y - survivor.y
                if min_i_dist <= 1.2:
                    return 0.0, 0.0, 2
                return dx / min_i_dist, dy / min_i_dist, 0

        elif goal == HighLevelGoal.SEEK_SHELTER:
            buildings = getattr(world, 'buildings', None)
            if buildings:
                min_b_dist = 999.0
                best_bx, best_by = survivor.x, survivor.y
                for b in buildings:
                    bx = b.get("x", 0) + b.get("w", 1) / 2.0
                    by = b.get("y", 0) + b.get("h", 1) / 2.0
                    d = math.hypot(bx - survivor.x, by - survivor.y)
                    if d < min_b_dist:
                        min_b_dist = d
                        best_bx, best_by = bx, by
                if min_b_dist < 50.0 and min_b_dist > 1.0:
                    dx = best_bx - survivor.x
                    dy = best_by - survivor.y
                    return dx / min_b_dist, dy / min_b_dist, 0

        mag = math.hypot(raw_dx, raw_dy)
        if mag > 0.1:
            return raw_dx / mag, raw_dy / mag, raw_action
        return raw_dx, raw_dy, raw_action
