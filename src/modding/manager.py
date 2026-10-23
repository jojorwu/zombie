import glob
import logging
import os

try:
    from rust_engine import RustBallisticsUtility as BallisticsUtility
    from rust_engine import RustContainerUtility as ContainerUtility
    from rust_engine import RustLuaModManager
    HAS_RUST_LUA = True
except ImportError:
    HAS_RUST_LUA = False
    from src.systems.container import ContainerUtility

try:
    import lupa
    from lupa import LuaRuntime
    HAS_LUPA = True
except ImportError:
    HAS_LUPA = False
    LuaRuntime = None

logger = logging.getLogger(__name__)

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

        # Expose ContainerUtility API functions to Lua mods
        if hasattr(ContainerUtility, 'get_item_weight'):
            g.get_item_weight = ContainerUtility.get_item_weight
            g.get_container_capacity = ContainerUtility.get_container_capacity
            g.get_container_weight = ContainerUtility.get_container_weight
            g.can_fit_item = ContainerUtility.can_fit_item

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
            except Exception:
                logger.exception("[LuaModManager] Failed to load mod %s", mod_name)

    def trigger_event(self, event_name, *args):
        if self.rust_lua and args:
            try:
                self.rust_lua.trigger_event(event_name, int(args[0]))
            except Exception as e:
                print(f"[LuaModManager] Rust Lua error executing '{event_name}': {e}")

        if not HAS_LUPA or isinstance(self.lua, FallbackLuaRuntime):
            return None
        try:
            fn = self.lua.eval(event_name)
            if fn is not None:
                return fn(*args)
        except Exception as e:
            print(f"[LuaModManager] Error executing event '{event_name}': {e}")
        return None
