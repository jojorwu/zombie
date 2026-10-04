import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.world import World, TileType
from src.entities import Survivor, Zombie, Vehicle, Animal, ItemEntity, ResourceItem, CraftingSystem, NoiseEvent, ZombieState
from src.simulation import EventBus, NoiseEmittedEvent, InfectionProgressEvent, AcousticSystem, InfectionSystem
from utils.item_state_utility import ItemStateUtility, ItemConditionState
from utils.tile_interaction_utility import TileInteractionUtility


class TestEntities(unittest.TestCase):
    def test_zombie_vision_and_hearing_ai(self):
        world = World(width=30, height=30, z_min=-20, z_max=20)
        world.current_tick = 1800
        g_idx = world.z_to_idx(0)
        world.grid[g_idx, 5, 5:20] = TileType.GRASS

        zombie = Zombie(5.0, 5.0, z=0)
        survivor = Survivor(10.0, 5.0, z=0)
        noise_events = [NoiseEvent(18.0, 5.0, 0, volume=20.0)]

        self.assertTrue(zombie.has_line_of_sight(survivor.x, survivor.y, survivor.z, world))
        seen = zombie.check_vision(world, [survivor])
        self.assertIsNotNone(seen)

        heard = zombie.check_hearing(noise_events)
        self.assertIsNotNone(heard)

        zombie.update(world, [survivor], [], noise_events)
        self.assertEqual(zombie.state, ZombieState.CHASE)

    def test_metabolic_balance_simulator(self):
        world = World(width=30, height=30)
        survivor = Survivor(10.0, 10.0)

        world.weather.temperature = 5.0  # Cold ambient temperature
        survivor.update_needs(world=world)

        self.assertLess(survivor.metabolism.state.body_temperature, 37.0)

    def test_ecs_systems_handling(self):
        bus = EventBus()
        acoustic = AcousticSystem(bus)
        infection = InfectionSystem(bus)

        survivor = Survivor(10.0, 10.0)
        bus.publish(NoiseEmittedEvent(x=10.0, y=10.0, z=0, volume=25.0, source_type="explosion"))
        bus.publish(InfectionProgressEvent(entity=survivor, progress=15.0))

        bus.process_events()

        self.assertEqual(len(acoustic.active_noises), 1)
        self.assertEqual(survivor.infection_progress, 15.0)


if __name__ == "__main__":
    unittest.main()
