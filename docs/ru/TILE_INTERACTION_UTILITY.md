# Утилита Взаимодействия с Тайлами и Мебелью (`utils/tile_interaction_utility.py`)

## Обзор
Утилита взаимодействия с тайлами позволяет выжившим и нейросети перемещать предметы интерьера, взламывать замки и сейфы, сливать топливо с колонок и заготовлять природные ресурсы.

## Действия и Механики
1. **Толкать / Передвигать Мебель (`push_furniture`)**:
   - Толкает соседнюю мебель (шкафы, столы, диваны, кровати, холодильники, сейфы) на 1 тайл вперед.
   - Позволяет баррикадировать дверные проемы от орд зомби.
2. **Разбирать Мебель (`dismantle_furniture`)**:
   - Разбирает мебель на доски (wood) и металл (metal) с помощью топора или лома в инвентарь.
3. **Взлом Замков и Сейфов (`lockpick_door_or_safe`)**:
   - Позволяет выжившим с отмычкой или ломом отпирать закрытые двери (`TileType.DOOR_LOCKED` -> `DOOR_OPEN`) или вскрывать оружейные сейфы (`TileType.WEAPON_SAFE`) с получением денег и драгоценностей.
4. **Сбор Палок с Кустов (`harvest_bush_sticks`)**:
   - Собирает палки и ветки с лесных кустов (`TileType.BUSH`) в инвентарь, превращая куст в травостой.
5. **Слив Топлива с Колонок (`siphon_fuel_from_pump`)**:
   - Сливает бензин напрямую с бензоколонок (`TileType.GAS_PUMP`) в инвентарь выжившего.

## API Утилиты
- `TileInteractionUtility.is_movable_furniture(tile_type)`
- `TileInteractionUtility.get_adjacent_furniture(world, x, y, z)`
- `TileInteractionUtility.push_furniture(world, x, y, z, push_dx, push_dy)`
- `TileInteractionUtility.dismantle_furniture(world, x, y, z, inventory)`
- `TileInteractionUtility.lockpick_door_or_safe(world, x, y, z, inventory)`
- `TileInteractionUtility.harvest_bush_sticks(world, x, y, z, inventory)`
- `TileInteractionUtility.siphon_fuel_from_pump(world, x, y, z, inventory)`
