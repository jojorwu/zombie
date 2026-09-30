import math
import random

class Animal:
    def __init__(self, x, y, hp=30.0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.hp = hp
        self.max_hp = hp
        self.is_alive = True
        self.speed = 0.08

    def update(self, world):
        if not self.is_alive:
            return
        # Random wander
        angle = random.uniform(0, 2 * math.pi)
        nx = self.x + math.cos(angle) * self.speed
        ny = self.y + math.sin(angle) * self.speed
        if world.is_walkable(nx, ny, self.z):
            self.x, self.y = nx, ny
