try:
    from rust_engine import RustZombieEngine as ZombieEngine
    from rust_engine import compute_zombie_flock_steering
except ImportError:
    ZombieEngine = None
    compute_zombie_flock_steering = None

from src.entities.zombie.zombie import Zombie, ZombieState, ZombieType

__all__ = ["Zombie", "ZombieEngine", "ZombieState", "ZombieType", "compute_zombie_flock_steering"]
