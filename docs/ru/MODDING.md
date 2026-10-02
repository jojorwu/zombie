# Руководство по модингу на Lua

Моды находятся в папке `mods/` и динамически загружаются менеджером `LuaModManager` (`src/modding/manager.py`) с помощью `lupa`.

## Доступные колбэки
- `on_init()` / `on_mod_load()`: Вызываются при загрузке скрипта мода.
- `on_tick(tick)`: Вызываются на каждом тике симуляции.
- `on_survivor_action(survivor_id, action)`: Вызываются, когда выживший совершает действие.

## Функции API

### Логирование и Регистрация
- `py_log(message)` / `log(message)`: Печать сообщения в консоль симулятора.
- `add_item_type(id, name, type)`: Регистрация новых типов предметов в реестре предметов.
- `execute_lua_math(expr)`: Вычисление математических выражений прямо в контексте Lua.

### API Инвентаря и Контейнеров Project Zomboid (`ContainerUtility`)
- `get_item_weight(item_type)`: Возвращает вес предмета в кг.
- `get_item_category(item_type)`: Возвращает категорию предмета в стиле Project Zomboid.
- `get_container_capacity(container)`: Возвращает максимальную вместимость контейнера в кг.
- `get_container_weight(container)`: Возвращает суммарный вес содержимого в кг.
- `can_fit_item(container, item_type, amount)`: Проверяет, помещается ли предмет по весу.
- `add_item_to_container(container, item_type, amount)`: Добавляет предметы в пределах лимита веса.
- `remove_item_from_container(container, item_type, amount)`: Извлекает предметы из контейнера.
- `transfer_item(source, target, item_type, amount)`: Переносит предметы между любыми контейнерами.

## Утилита управления модами (`utils/mod_utility.py`)
Инструмент командной строки для создания, проверки и упаковки модов:
- **Создание шаблона мода**:
  ```bash
  python3 -m utils.mod_utility create custom_weapons
  ```
- **Проверка валидности модов**:
  ```bash
  python3 -m utils.mod_utility validate
  ```
- **Упаковка модов в zip-архив**:
  ```bash
  python3 -m utils.mod_utility package
  ```
