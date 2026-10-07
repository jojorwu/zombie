# Архитектурный обзор проекта (Python + Rust)

## Двойственная архитектура (Python-Rust Hybrid Architecture)

Проект построен на четком разделении обязанностей между языками:
1. **Python**: Отвечает исключительно за ИИ нейросети (PyTorch, GRU `BrainNet`, PPO, генетические алгоритмы эволюции) и Gymnasium RL-обертку.
2. **Rust (`rust_vulkan_render`)**: Перевыполняет тяжелые симуляционные вычисления, 3D-поиск пути, физику, световые эффекты, акустику и нативную отрисовку с использованием CPython PyO3 C-API и zero-copy NumPy разделяемой памяти.

---

## Модульная структура директорий (`src/` и `rust_vulkan_render/`)

### 1. Rust C-Extension Crate (`rust_vulkan_render/`)
- **`compute_a_star_3d_path`**: Полноценный 3D A* поиск пути по 3D-сетке `[num_levels, height, width]`, учитывающий лестницы, люки, стены и ломаемые тайлы (двери, окна).
- **`compute_zombie_flock_steering`**: Векторное стайное руление ордой зомби по разделяемой памяти NumPy.
- **`check_line_of_sight_rust` & `compute_fog_of_war_rust`**: Быстрый рэйкастинг линии видимости и тумана войны с учетом угловых конусов обзора и типа стен.
- **`RustVehiclePhysics`**: CDDA-физика транспорта, инерция, торможение, расход топлива и столкновения с зомби/стенами.
- **`RustAcousticSystem`**: Симуляция распространения децибел шума в 3D-пространстве с геом-затуханием.
- **`RustAnatomicalHealth`**: Анатомическая модель здоровья (голова, торс, конечности), кровотечение и травматические штрафы к скорости.
- **`RustEnvironmentManager`**: Солнечный зенит, температура, ветер и сезонная климатология.
- **`RustLuaModManager`**: Нативный движок выполнения скриптов Lua 5.4 через `mlua`.
- **`RustContainerUtility` & `RustBallisticsUtility`**: Вычисление вместимости инвентаря, траекторий пуль и порчи продуктов (`RustFoodSpoilageUtility`).
- **`VulkanTileRenderer`**: Высокоскоростная генерация кадров viewport тайлов.

---

### 2. Python AI & Simulation Layers (`src/`)

#### A. `src/ai/` (ИИ и Нейросети)
- **`brain_net.py`**: Рекуррентная нейросеть `BrainNet` на PyTorch (GRU, 57 входов, 13 действий) с бинарным FP16 сжатием `.zbrain`.
- **`brain_actions.py`**: Пакетное матричное умножение тензоров (`batch_get_action_and_movement`) для параллельного вывода нейросетей.
- **`pathfinding.py`**: `AStar3D` обертка над нативной Rust-функцией `compute_a_star_3d_path`.
- **`hierarchical_ai.py`**: Иерархический планировщик целей `HierarchicalDecisionPlanner` (`SURVIVE`, `FLEE`, `ATTACK`, `LOOT`, `SHELTER`).
- **`gym_env.py`**: Gymnasium-совместимая среда `SurvivorGymEnv` для обучения PPO-агентов.

#### B. `src/world/` (Мир и Освещение)
- **`grid.py`**: Класс `World` с трехуровневой пространственной хэш-сеткой ($X \times Y \times Z$), NumPy массивом для $Z=0$ и автоматическим кэшированием `get_3d_grid_array()`.
- **`chunk.py`**: `ChunkManager` динамической загрузки 16x16 чанков.
- **`generation.py`**: `WorldGenerator` процедурного зонирования районов, генерации рек, BSP-комнат, Graph Grammar и WFC-мебели.
- **`lighting.py`**: `LightingEngine` с оберткой над нативным туманом войны Rust.
- **`weather.py`**: `WeatherManager` климатических фронтов и температуры.

#### C. `src/entities/` (Сущности)
- **`survivor/`**: Сущность выжившего `Survivor`, метаболизм (`metabolism.py`) и алгоритмы лута (`survivor_looting.py`).
- **`zombie/`**: Зомби `Zombie`, слух, зрение (`zombie_perception.py`) и стайное поведение (`zombie_flock.py`).
- **`vehicle.py`**: Модульный транспорт `Vehicle` с интеграцией `RustVehiclePhysics`.
- **`health.py`**: `AnatomicalHealth` с интеграцией `RustAnatomicalHealth`.
- **`item.py`**: Внутриигровые предметы, баллистика и качество металла.
- **`factory.py`**: `EntityFactory` с O(1) пулом объектов `ObjectPool`.

#### D. `src/simulation/` (Ядро Симуляции)
- **`engine.py`**: `SimulationEngine` координации тиков мира, связи с `PythonRustEngineBridge` и генетической эволюции `GeneticEvolutionManager`.
- **`rust_engine.py`**: `PythonRustEngineBridge` интерфейса нулевого копирования данных между Python и Rust.
- **`event_bus.py` & `systems.py`**: Шина событий `EventBus` и ECS-системы (`AcousticSystem`, `InfectionSystem`, `ParticleSystem`).

#### E. `src/ui/` (Пользовательский Интерфейс)
- **`renderer.py`**: Pygame интерфейс `RendererUI` с темами и интеграцией Vulkan моста (`vulkan_bridge.py`).
- **`hud_renderer.py`**: Отрисовка HUD показателей здоровья, времени, погоды и чата.
- **`menu.py`**: Главное меню `MainMenuUI` с настройкой генерации мира.

---

### 3. Моддинг и Утилиты (`src/modding/` и `utils/`)
- **`src/modding/manager.py`**: `LuaModManager` с поддержкой `lupa` и `RustLuaModManager`.
- **`utils/`**:
  - `container_utility.py`: Инвентарь Project Zomboid style с `RustContainerUtility`.
  - `ballistics_utility.py`: Баллистика с `RustBallisticsUtility`.
  - `food_spoilage_utility.py`: Скоропортящиеся продукты с `RustFoodSpoilageUtility`.
  - `tile_interaction_utility.py`: Забаррикадирование, разборка мебели и взлом замков.
  - `p_np_math.py`: Оптимизация инвентаря рюкзаков через алгоритм Кнапсака.
