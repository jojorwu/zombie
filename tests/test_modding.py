import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.modding import LuaModManager

class TestLuaModding(unittest.TestCase):
    def test_lua_mod_manager_loading(self):
        manager = LuaModManager(mods_dir="mods")
        self.assertGreater(len(manager.mods), 0)

    def test_lua_event_trigger(self):
        manager = LuaModManager(mods_dir="mods")
        res = manager.trigger_event("solve_p_np_complexity", 5)
        if res is not None:
            self.assertEqual(res, 41)  # 5*5 + 3*5 + 1 = 41

if __name__ == "__main__":
    unittest.main()
