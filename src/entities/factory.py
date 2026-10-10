import collections
from src.entities.zombie.zombie_entity import Zombie, ZombieState
from src.entities.item import ItemEntity
from src.entities.sensory import NoiseEvent, ScentTrail
from src.entities.animal import Animal

class ObjectPool:
    """
    High-performance O(1) object pool using set-based ID tracking to eliminate
    deque linear scan overhead during entity recycling.
    """
    def __init__(self, create_fn, max_size=1000):
        self.create_fn = create_fn
        self.max_size = max_size
        self.pool = collections.deque()
        self.pooled_ids = set()

    def get(self, *args, **kwargs):
        if self.pool:
            obj = self.pool.pop()
            self.pooled_ids.discard(id(obj))
            if hasattr(obj, "reset"):
                obj.reset(*args, **kwargs)
            return obj
        return self.create_fn(*args, **kwargs)

    def release(self, obj):
        obj_id = id(obj)
        if len(self.pool) < self.max_size and obj_id not in self.pooled_ids:
            self.pool.append(obj)
            self.pooled_ids.add(obj_id)


class EntityFactory:
    """
    Factory with object pooling for efficient entity allocation/deallocation,
    minimizing garbage collection overhead during high-entity count simulations.
    """
    def __init__(self, config=None):
        self.config = config
        self._zombie_pool = ObjectPool(lambda x=0, y=0, hp=50.0, z=0: Zombie(x, y, hp, z, config=self.config))
        self._scent_pool = ObjectPool(lambda x=0, y=0, z=0, intensity=100.0: ScentTrail(x, y, z, intensity))
        self._noise_pool = ObjectPool(lambda x=0, y=0, z=0, volume=10.0, lifetime=5, source_type="general": NoiseEvent(x, y, z, volume, lifetime, source_type))
        self._item_pool = ObjectPool(lambda x=0, y=0, item_type="", amount=1, z=0, contents=None: ItemEntity(x, y, item_type, amount, z, contents=contents))
        self._animal_pool = ObjectPool(lambda x=0, y=0, hp=30.0, z=0: Animal(x, y, hp, z))

    def create_zombie(self, x, y, hp=50.0, z=0):
        zombie = self._zombie_pool.get(x, y, hp, z)
        zombie.x, zombie.y, zombie.z = float(x), float(y), int(z)
        zombie.hp, zombie.max_hp = hp, hp
        zombie.is_alive = True
        zombie.state = ZombieState.IDLE
        zombie.target = None
        zombie.investigate_pos = None
        zombie.memory_timer = 0
        zombie.last_known_target_pos = None
        zombie.current_path = []
        zombie.path_target_pos = None
        return zombie

    def release_zombie(self, zombie):
        zombie.is_alive = False
        self._zombie_pool.release(zombie)

    def create_scent_trail(self, x, y, z=0, intensity=100.0):
        scent = self._scent_pool.get(x, y, z, intensity)
        scent.x, scent.y, scent.z = float(x), float(y), int(z)
        scent.intensity = float(intensity)
        return scent

    def release_scent_trail(self, scent):
        self._scent_pool.release(scent)

    def create_noise_event(self, x, y, z=0, volume=10.0, lifetime=5, source_type="general"):
        noise = self._noise_pool.get(x, y, z, volume, lifetime, source_type)
        noise.x, noise.y, noise.z = float(x), float(y), int(z)
        noise.volume = float(volume)
        noise.lifetime = lifetime
        noise.source_type = source_type
        return noise

    def release_noise_event(self, noise):
        self._noise_pool.release(noise)

    def create_item(self, x, y, item_type, amount=1, z=0, contents=None):
        item = self._item_pool.get(x, y, item_type, amount, z)
        item.x, item.y, item.z = float(x), float(y), int(z)
        item.item_type = item_type
        item.amount = amount
        item.collected = False
        item.contents = contents if contents is not None else {}
        return item

    def release_item(self, item):
        item.collected = True
        self._item_pool.release(item)

    def create_animal(self, x, y, hp=30.0, z=0):
        animal = self._animal_pool.get(x, y, hp, z)
        animal.x, animal.y, animal.z = float(x), float(y), int(z)
        animal.hp, animal.max_hp = hp, hp
        animal.is_alive = True
        return animal

    def release_animal(self, animal):
        animal.is_alive = False
        self._animal_pool.release(animal)

    def get_pool_stats(self):
        return {
            "zombies_pooled": len(self._zombie_pool.pool),
            "scents_pooled": len(self._scent_pool.pool),
            "noises_pooled": len(self._noise_pool.pool),
            "items_pooled": len(self._item_pool.pool),
            "animals_pooled": len(self._animal_pool.pool),
        }
