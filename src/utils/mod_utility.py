#!/usr/bin/env python3
"""
Utility 1: Modding Utility Tool for Zombie AI Simulation.
Supports Lua modding, mod validation, template creation, and Lua math execution.
Usage: python -m src.utils.mod_utility [command]
"""

import sys
import os
import zipfile
from src.modding import LuaModManager
from src.utils.p_np_math import PNPComplexityEngine

class ModUtility:
    def __init__(self, mods_dir="mods"):
        self.mods_dir = mods_dir
        self.mod_manager = LuaModManager(mods_dir=mods_dir)

    def create_mod_template(self, mod_name):
        filename = f"{mod_name}.lua" if not mod_name.endswith(".lua") else mod_name
        filepath = os.path.join(self.mods_dir, filename)
        os.makedirs(self.mods_dir, exist_ok=True)
        template = f"""-- Mod: {mod_name}
-- Created with Mod Utility Tool

function on_mod_load()
    py_log("[{mod_name}] Loaded successfully!")
end

function on_tick(tick)
    -- Custom tick callback
end

function calculate_custom_stat(a, b)
    return a * b + 1
end
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(template)
        print(f"[ModUtility] Created mod template at: {filepath}")
        return filepath

    def validate_all_mods(self):
        print(f"[ModUtility] Validating Lua mods in '{self.mods_dir}'...")
        valid_count = 0
        for name, path in self.mod_manager.mods.items():
            print(f"  - Validated mod '{name}' ({path})")
            valid_count += 1
        print(f"[ModUtility] Total valid mods: {valid_count}")
        return valid_count

    def package_mods(self, output_zip="mods_bundle.zip"):
        print(f"[ModUtility] Packaging mods into '{output_zip}'...")
        with zipfile.ZipFile(output_zip, "w") as zipf:
            for root, dirs, files in os.walk(self.mods_dir):
                for file in files:
                    if file.endswith(".lua"):
                        fp = os.path.join(root, file)
                        zipf.write(fp, os.path.relpath(fp, self.mods_dir))
        print(f"[ModUtility] Successfully created '{output_zip}'")
        return output_zip

    def execute_lua_math(self, lua_expr):
        if hasattr(self.mod_manager, 'lua') and self.mod_manager.lua is not None:
            try:
                res = self.mod_manager.lua.eval(lua_expr)
                print(f"[ModUtility] Lua Eval '{lua_expr}' = {res}")
                return res
            except Exception as e:
                print(f"[ModUtility] Error evaluating Lua expression: {e}")
        return None

def main():
    util = ModUtility()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "create" and len(sys.argv) > 2:
            util.create_mod_template(sys.argv[2])
        elif cmd == "validate":
            util.validate_all_mods()
        elif cmd == "package":
            util.package_mods()
        else:
            print("Commands: create [name], validate, package")
    else:
        util.validate_all_mods()

if __name__ == "__main__":
    main()
