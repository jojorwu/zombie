# Lua Modding Guide

Mods are located in the `mods/` directory and loaded dynamically by `LuaModManager` (`src/modding/manager.py`) using `lupa`.

## Supported Callbacks
- `on_init()` / `on_mod_load()`: Triggered when the Lua mod script is loaded.
- `on_tick(tick)`: Triggered on every simulation step.
- `on_survivor_action(survivor_id, action)`: Triggered when a survivor entity performs an action.

## Mod API Functions

### Logging & Registration
- `py_log(message)` / `log(message)`: Print a formatted message to the simulation console log.
- `add_item_type(id, name, type)`: Register new item types into the simulation item registry.
- `execute_lua_math(expr)`: Evaluate mathematical formulas directly within the Lua execution context.

### Project Zomboid Container & Inventory API (`ContainerUtility`)
- `get_item_weight(item_type)`: Returns the weight in kg for an item.
- `get_item_category(item_type)`: Returns the Project Zomboid category string for an item.
- `get_container_capacity(container)`: Returns maximum weight capacity in kg.
- `get_container_weight(container)`: Returns total weight of items stored in container.
- `can_fit_item(container, item_type, amount)`: Checks if item fits within capacity limit.
- `add_item_to_container(container, item_type, amount)`: Adds items up to capacity.
- `remove_item_from_container(container, item_type, amount)`: Removes items from container.
- `transfer_item(source, target, item_type, amount)`: Transfers items between containers.

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
