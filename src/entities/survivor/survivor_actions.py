import random
import math
from src.entities.item import ResourceItem, WEAPON_STATS
from src.world.lighting import DynamicLight
from src.entities.sensory import NoiseEvent
from utils.ballistics_utility import BallisticsUtility
from utils.tile_interaction_utility import TileInteractionUtility
from src.entities.survivor.survivor_state import EmotionalState


class SurvivorActions:
    """Handles combat attacks, ballistics, furniture manipulation, and movement for Survivor."""
    @staticmethod
    def attack(survivor, world, zombies, animals, survivors, noise_events):
        best_weapon = None
        is_firearm = False
        ammo_type = None

        firearms = [
            ResourceItem.SNIPER_RIFLE, ResourceItem.ASSAULT_RIFLE, ResourceItem.RIFLE,
            ResourceItem.SHOTGUN, ResourceItem.MAGNUM, ResourceItem.SMG,
            ResourceItem.REVOLVER, ResourceItem.PISTOL, ResourceItem.CROSSBOW
        ]
        for fa in firearms:
            if survivor.inventory.get(fa, 0) > 0:
                req_ammo = WEAPON_STATS[fa]["ammo"]
                if survivor.inventory.get(req_ammo, 0) > 0:
                    best_weapon = fa
                    is_firearm = True
                    ammo_type = req_ammo
                    break

        if not best_weapon:
            melee_options = [
                ResourceItem.KATANA, ResourceItem.SLEDGEHAMMER, ResourceItem.MACHETE, ResourceItem.SPEAR,
                ResourceItem.AXE, ResourceItem.CROWBAR, ResourceItem.BASEBALL_BAT, ResourceItem.PIPE,
                ResourceItem.FRYING_PAN, ResourceItem.KNIFE, ResourceItem.CHEF_KNIFE, ResourceItem.WEAPON
            ]
            for mw in melee_options:
                if survivor.inventory.get(mw, 0) > 0:
                    best_weapon = mw
                    break

        w_stats = WEAPON_STATS.get(best_weapon, {"damage": 15.0, "range": 1.0, "noise": 4.0})
        attack_range = w_stats["range"]
        damage = w_stats["damage"] * survivor.body.attack_damage_multiplier
        stype = "pistol_shot"

        if is_firearm and ammo_type:
            caliber_map = {
                ResourceItem.SNIPER_RIFLE: ".308sniper",
                ResourceItem.ASSAULT_RIFLE: "5.56mm",
                ResourceItem.RIFLE: "5.56mm",
                ResourceItem.SHOTGUN: "12gauge",
                ResourceItem.MAGNUM: ".357magnum",
                ResourceItem.SMG: "9mm",
                ResourceItem.REVOLVER: "9mm",
                ResourceItem.PISTOL: "9mm",
                ResourceItem.CROSSBOW: "arrow",
            }
            stype_map = {
                ResourceItem.SNIPER_RIFLE: "rifle_shot",
                ResourceItem.ASSAULT_RIFLE: "rifle_shot",
                ResourceItem.RIFLE: "rifle_shot",
                ResourceItem.SHOTGUN: "shotgun_shot",
                ResourceItem.MAGNUM: "pistol_shot",
                ResourceItem.SMG: "pistol_shot",
                ResourceItem.REVOLVER: "pistol_shot",
                ResourceItem.PISTOL: "pistol_shot",
                ResourceItem.CROSSBOW: "footsteps",
            }
            stype = stype_map.get(best_weapon, "pistol_shot")
            caliber = caliber_map.get(best_weapon, "9mm")
            ballistics = BallisticsUtility.calculate_trajectory(
                caliber,
                distance_m=attack_range * 10.0,
                wind_speed_kmh=world.weather.wind_speed,
                wind_angle_rad=world.weather.wind_angle
            )
            damage = ballistics["damage"] * survivor.body.attack_damage_multiplier

        if survivor.emotional_state == EmotionalState.PANICKED and random.random() < 0.25:
            damage *= 0.5
        elif survivor.emotional_state == EmotionalState.TERRIFIED and random.random() < 0.50:
            damage = 0.0

        if is_firearm and ammo_type:
            survivor.inventory[ammo_type] -= 1
            world.dynamic_lights.append(DynamicLight(survivor.x, survivor.y, survivor.z, radius=12.0, color=(255, 200, 100), intensity=1.5, lifetime=2))

        if survivor.in_vehicle and survivor.in_vehicle.fuel > 0:
            attack_range = 1.5
            damage = 60.0

        for z in zombies:
            if z.is_alive and z.z == survivor.z and math.hypot(z.x - survivor.x, z.y - survivor.y) <= attack_range:
                z.take_targeted_damage(damage)
                if not z.is_alive:
                    survivor.kills += 1
                    survivor.score += 20.0
                    survivor.fear = max(0.0, survivor.fear - 15.0)
                    survivor.panic = max(0.0, survivor.panic - 20.0)
                    survivor.morale = min(100.0, survivor.morale + 10.0)
                if noise_events is not None:
                    noise_events.append(NoiseEvent(survivor.x, survivor.y, survivor.z, volume=31.0, source_type=stype))
                return

        for a in animals:
            if a.is_alive and a.z == survivor.z and math.hypot(a.x - survivor.x, a.y - survivor.y) <= attack_range:
                a.hp -= damage
                if a.hp <= 0:
                    a.is_alive = False
                    survivor.inventory[ResourceItem.MEAT] = survivor.inventory.get(ResourceItem.MEAT, 0) + 2
                    survivor.score += 15.0
                if noise_events is not None:
                    noise_events.append(NoiseEvent(survivor.x, survivor.y, survivor.z, volume=31.0, source_type=stype))
                return

        for other in survivors:
            if other is not survivor and other.is_alive and other.z == survivor.z and math.hypot(other.x - survivor.x, other.y - survivor.y) <= attack_range:
                other.take_damage(damage)
                if not other.is_alive:
                    survivor.kills += 1
                    survivor.score += 30.0
                if noise_events is not None:
                    noise_events.append(NoiseEvent(survivor.x, survivor.y, survivor.z, volume=31.0, source_type=stype))
                return

    @staticmethod
    def push_furniture(survivor, world, noise_events):
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            fx, fy = int(survivor.x + dx), int(survivor.y + dy)
            if TileInteractionUtility.push_furniture(world, fx, fy, survivor.z, dx, dy):
                survivor.score += 8.0
                if noise_events is not None:
                    noise_events.append(NoiseEvent(survivor.x, survivor.y, survivor.z, volume=14.0, source_type="furniture_push"))
                break

    @staticmethod
    def dismantle_furniture(survivor, world, noise_events):
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            fx, fy = int(survivor.x + dx), int(survivor.y + dy)
            success, w_amt, m_amt = TileInteractionUtility.dismantle_furniture(world, fx, fy, survivor.z, survivor.inventory)
            if success:
                survivor.score += 12.0
                if noise_events is not None:
                    noise_events.append(NoiseEvent(survivor.x, survivor.y, survivor.z, volume=15.0, source_type="dismantling"))
                break
