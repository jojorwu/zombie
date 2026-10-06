import os
import glob
import sys
from utils.container_utility import ContainerUtility
from utils.ballistics_utility import BallisticsUtility

try:
    from rust_vulkan_render import RustLuaModManager
    HAS_RUST_LUA = True
except ImportError:
    HAS_RUST_LUA = False

try:
    import lupa
    from lupa import LuaRuntime
    HAS_LUPA = True
except ImportError:
    HAS_LUPA = False
    LuaRuntime = None

class FallbackLuaRuntime:
    """Fallback engine if lupa is not installed."""
    def __init__(self):
        self.globals_dict = {}

    def execute(self, lua_code):
        pass

    def eval(self, lua_expr):
        return None

class LuaModManager:
    def __init__(self, mods_dir="mods"):
        self.mods_dir = mods_dir
        self.mods = {}
        self.rust_lua = RustLuaModManager() if HAS_RUST_LUA else None

        if HAS_LUPA:
            try:
                self.lua = LuaRuntime(unpack_returned_tuples=True)
            except Exception as e:
                print(f"[LuaModManager] Error initializing LuaRuntime: {e}")
                self.lua = FallbackLuaRuntime()
        else:
            self.lua = FallbackLuaRuntime()

        self.setup_python_api()
        self.load_mods()

    def setup_python_api(self):
        if not HAS_LUPA or isinstance(self.lua, FallbackLuaRuntime):
            return

        g = self.lua.globals()
        g.py_log = lambda msg: print(f"[Lua API]: {msg}")

        # Expose Project Zomboid ContainerUtility API functions to Lua mods
        g.get_item_weight = ContainerUtility.get_item_weight
        g.get_item_category = ContainerUtility.get_item_category
        g.get_container_capacity = ContainerUtility.get_container_capacity
        g.get_container_weight = ContainerUtility.get_container_weight
        g.can_fit_item = ContainerUtility.can_fit_item
        g.add_item_to_container = ContainerUtility.add_item_to_container
        g.remove_item_from_container = ContainerUtility.remove_item_from_container
        g.transfer_item = ContainerUtility.transfer_item

        # Expose Raycast Ballistics API functions to Lua mods
        g.calculate_trajectory = BallisticsUtility.calculate_trajectory
        g.simulate_bullet_flight = BallisticsUtility.simulate_bullet_flight

    def load_mods(self):
        if not os.path.exists(self.mods_dir):
            os.makedirs(self.mods_dir, exist_ok=True)

        lua_files = glob.glob(os.path.join(self.mods_dir, "*.lua"))
        for filepath in lua_files:
            mod_name = os.path.basename(filepath)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    lua_code = f.read()

                if self.rust_lua:
                    self.rust_lua.load_mod_script(lua_code)

                if HAS_LUPA and not isinstance(self.lua, FallbackLuaRuntime):
                    self.lua.execute(lua_code)
                    mod_load_fn = self.lua.eval("on_mod_load")
                    if mod_load_fn is not None:
                        mod_load_fn()
                self.mods[mod_name] = filepath
                print(f"[LuaModManager] Loaded Lua mod: {mod_name}")
            except Exception as e:
                print(f"[LuaModManager] Failed to load mod {mod_name}: {e}")

    def trigger_event(self, event_name, *args):
        if self.rust_lua and args and isinstance(args[0], int):
            self.rust_lua.trigger_event(event_name, args[0])

        if not HAS_LUPA or isinstance(self.lua, FallbackLuaRuntime):
            return None
        try:
            fn = self.lua.eval(event_name)
            if fn is not None:
                return fn(*args)
        except Exception as e:
            pass
        return None
