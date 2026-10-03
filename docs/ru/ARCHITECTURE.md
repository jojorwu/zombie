# Обзор архитектуры

## Модульная структура директорий (`src/`)

Симуляционный движок структурирован по подпакетам в директории `src/`:

### 1. `src/world/`
- **`grid.py`**: Основной класс `World`, управляющий трехмерной сеткой мира ($X \times Y \times Z$).
- **`chunk.py`**: `ChunkManager` и состояния `ChunkState`, обеспечивающие динамическую загрузку чанков 16x16, их активацию и привязку многочаноквых зданий.
- **`generation.py`**: `WorldGenerator` для векторизованной генерации ландшафта, дорожных сеток, зонирования районов, внутренних комнат BSP, подвалов и автомастерских.
- **`tiles.py`**: Перечисление типов тайлов `TileType`, флаги взаимодействия и модификаторы скорости передвижения (`TILE_SPEED_MODIFIERS`).
- **`lighting.py`**: `LightingManager`, рассчитывающий зенитный угол солнца, 29.5-дневный лунный цикл, динамические источники света и туман войны (`compute_fog_of_war`).
- **`weather.py`**: `WeatherManager`, симулирующий вектор ветра, перемещающиеся дождевые фронты 100x100 и 4-сезонный климат.

### 2. `src/ai/`
- **`brain_net.py`**: Рекуррентная нейросеть `BrainNet` на PyTorch (GRU), принимающая 57 входных признаков с 64 скрытыми юнитами. Поддерживает бинарное сжатие `.zbrain`.
- **`brain_actions.py`**: Пакетное матричное умножение тензоров (`batch_get_action_and_movement`) для параллельного вычисления действий выживших.
- **`pathfinding.py`**: `AStar3D` навигация с приоритетной очередью по 3D-сетке, учитывающая лестницы, люки, двери и окна.
- **`brain.py`**: Высокоуровневая логика принятия решений и обертки действий выживших.

### 3. `src/entities/`
- **`survivor/`**: Сущность выжившего (`Survivor`), алгоритмы оптимизации лута (`survivor_looting.py`) и крафтинг.
- **`zombie/`**: ИИ зомби (`zombie_entity.py`), светочувствительное зрение (`zombie_perception.py`), акустический отклик, отслеживание запахов и стайный флоккинг (`zombie_flock.py`).
- **`animal.py`**: Базовый класс `Animal` и сущность крысы (`Rat`) с высокой скоростью навигации в зданиях и обыском мусорок.
- **`vehicle.py`**: Транспортные средства (`Vehicle`), модульные детали `VehiclePart` в стиле CDDA, векторная физика (`VehiclePhysics`) и столкновения.
- **`item.py`**: `ResourceItem`, свойства баллистики, уровни качества металла (`MetalQuality`) и скоропортящиеся продукты.
- **`factory.py`**: `EntityFactory` с пулом объектов (`ObjectPool`) для зомби, запахов, шумов, предметов и животных.
- **`health.py`**: Анатомическая модель здоровья (`AnatomicalHealth`), отслеживающая состояние головы, торса и конечностей, травмы и расчленение.
- **`state_manager.py`**: `FurnitureStateManager` и `ItemStateManager` для отслеживания состояния мебели, прочности, вместимости инвентаря в стиле Project Zomboid (`capacity_kg`) и содержимого контейнеров.

### 4. `src/simulation/`
- **`engine.py`**: `SimulationEngine` симуляционного цикла, обновление чанков, спавн предметов и сброс поколений.
- **`spawner.py`**: `EntitySpawner` для процедурного размещения сущностей.
- **`environment.py`**: Распространение экологических и физических событий.

### 5. `src/ui/`
- **`renderer.py`**: `RendererUI` отрисовки Pygame с отсечением по камере и переключением тем.
- **`hud_renderer.py`**: Отрисовка HUD (здоровье, эмоции, время, погода, инвентарь).
- **`vulkan_bridge.py`**: `VulkanBridge` взаимодействия с нативным Rust Vulkan рендерером (`rust_vulkan_render`).
- **`menu.py`**: Главное меню `MainMenuUI` для настройки параметров мира.
- **`camera.py`**: `Camera` панорамирования и зумирования.

### 6. `src/modding/`
- **`manager.py`**: `LuaModManager` для загрузки и выполнения скриптов Lua из `mods/` с использованием `lupa`, экспортирующий API `ContainerUtility`.

### 7. `utils/`
Модули утилит: `container_utility.py` (инвентарь, вес предметов и вместимость контейнеров в стиле Project Zomboid), `tile_interaction_utility.py`, `p_np_math.py`, `vehicle_utility.py`, `ballistics_utility.py`, `food_spoilage_utility.py`, `electricity_utility.py`, `sound_utility.py`, `item_state_utility.py`, `mod_utility.py`, `dev_utility.py`, `memory_monitor_utility.py`, `plant_utility.py`, `animal_utility.py` и `pathfinding_utility.py`.
