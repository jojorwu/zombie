# Lua Modding Guide

Mods are located in the `mods/` directory and loaded dynamically by `LuaModManager` (`src/modding/manager.py`) using `lupa`.

## Supported Callbacks
- `on_init()` / `on_mod_load()`: Triggered when the Lua mod script is loaded.
- `on_tick(tick)`: Triggered on every simulation step.
- `on_survivor_action(survivor_id, action)`: Triggered when a survivor entity performs an action.

## Mod API Functions
- `py_log(message)` / `log(message)`: Print a formatted message to the simulation console log.
- `add_item_type(id, name, type)`: Register new item types into the simulation item registry.
- `execute_lua_math(expr)`: Evaluate mathematical formulas directly within the Lua execution context.

## Mod Utility CLI Tool (`utils/mod_utility.py`)
Developer CLI tool for creating, validating, and packaging Lua mods:
- **Create Mod Template**:
  ```bash
  python3 -m utils.mod_utility create custom_weapons
  ```
- **Validate Mods**:
  ```bash
  python3 -m utils.mod_utility validate
  ```
- **Package Mods into Zip Bundle**:
  ```bash
  python3 -m utils.mod_utility package
  ```
