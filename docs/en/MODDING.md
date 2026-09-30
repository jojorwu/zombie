# Lua Modding Guide

Mods are located in the `mods/` directory and loaded via `src/modding.py`.

## Available Callbacks
- `on_init()`: Triggered when the mod is loaded.
- `on_tick(tick)`: Triggered on every simulation step.
- `on_survivor_action(survivor_id, action)`: Triggered when a survivor performs an action.

## Mod API Functions
- `log(message)`: Print a message to the console.
- `add_item_type(id, name, type)`: Register new resource items.
