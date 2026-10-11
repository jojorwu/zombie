try:
    from rust_engine import RustZombieEngine as ZombieEngine, compute_zombie_flock_steering
except ImportError:
    ZombieEngine = None
    compute_zombie_flock_steering = None

from src.entities.zombie.zombie_entity import Zombie, ZombieState, ZombieType

__all__ = ["ZombieEngine", "compute_zombie_flock_steering", "Zombie", "ZombieState", "ZombieType"]
