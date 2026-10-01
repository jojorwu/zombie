import math
import random
from src.world import TileType
from src.entities.sensory import NoiseEvent


class Animal:
    """Base wild animal entity."""
    def __init__(self, x, y, hp=30.0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.hp = hp
        self.max_hp = hp
        self.is_alive = True
        self.speed = 0.08
        self.species = "generic"

    def update(self, world):
        if not self.is_alive:
            return
        angle = random.uniform(0, 2 * math.pi)
        nx = self.x + math.cos(angle) * self.speed
        ny = self.y + math.sin(angle) * self.speed
        if world.is_walkable(nx, ny, self.z):
            self.x, self.y = nx, ny


class Rat(Animal):
    """Small, fast rat entity that scavenges trash cans and scurries through building interiors."""
    def __init__(self, x, y, z=0):
        super().__init__(x, y, hp=10.0, z=z)
        self.speed = 0.16
        self.species = "rat"
        self.scavenge_cooldown = 0

    def update(self, world, noise_events=None):
        if not self.is_alive:
            return

        z_idx = world.z_to_idx(self.z)
        ix, iy = int(self.x), int(self.y)

        # Scavenge trash cans or building interiors for scraps
        if self.scavenge_cooldown <= 0:
            if 0 <= ix < world.width and 0 <= iy < world.height:
                tile = world.grid[z_idx, iy, ix]
                if tile in (TileType.TRASH_CAN, TileType.BUILDING_FLOOR, TileType.UNDERGROUND_FLOOR):
                    if random.random() < 0.2:
                        self.scavenge_cooldown = 60
                        if noise_events is not None and random.random() < 0.3:
                            noise_events.append(NoiseEvent(self.x, self.y, self.z, volume=4.0, source_type="scurrying"))

        if self.scavenge_cooldown > 0:
            self.scavenge_cooldown -= 1

        # High-speed scurrying behavior
        angle = random.uniform(0, 2 * math.pi)
        cur_speed = self.speed * world.get_tile_speed_modifier(self.x, self.y, self.z)
        nx = self.x + math.cos(angle) * cur_speed
        ny = self.y + math.sin(angle) * cur_speed

        if world.is_walkable(nx, ny, self.z):
            self.x, self.y = nx, ny
