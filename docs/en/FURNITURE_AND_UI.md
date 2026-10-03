# Furniture, Sound Occlusion, UI Themes & PZ Container Inventories

## Furniture, Containers & Project Zomboid Inventories (`ContainerUtility`)
The map generator populates building interiors with detailed room furniture and containers featuring strict weight capacity limits (kg) in Project Zomboid style:
- **Furniture Capacities**:
  - Wardrobes: 60 kg
  - Cabinets: 50 kg
  - Store Shelves: 50 kg
  - Refrigerators: 40 kg (Cooling reduces food spoilage by 80%)
  - Freezers: 20 kg (Sub-zero freezing reduces food spoilage by 95%)
  - Lockers & Factory Racks: 40 - 80 kg
  - Weapon Safes & Gun Racks: 30 - 35 kg
  - Desks & Tables: 25 kg
- **Interactivity & Searching**:
  - Survivors can search adjacent furniture containers when looting (`survivor_looting.py`).
  - **Bag Weight Reduction**: Backpacks and duffel bags placed inside containers or worn by survivors reduce effective weight of stored contents by 70%-80%.
  - **Item Transfers**: `ContainerUtility.transfer_item` allows seamless item transfers between survivors, backpacks, furniture, vehicle trunks, floor tiles, and corpses.

## Acoustic Sound Physics & Wall Occlusion
Acoustic sound propagation (`SoundUtility`) models decibel Sound Pressure Level (dB SPL) physics:
- **Inverse-Square Distance Loss**: Decibel volume drops logarithmically as $20 \log_{10}(\text{distance})$.
- **Obstacle Material Decibel Absorption**:
  - Solid building walls reduce volume by **-25 dB**.
  - Closed wooden doors reduce volume by **-12 dB**.
- **Audibility Threshold**: Hearing threshold set at **20.0 dB SPL**.
- Line-of-sight raycasts attenuate acoustic noise events emitted from gunshot discharges, vehicle engines, dismantling, and footsteps.

## Graphics, Vulkan Bridge & Theme-Switching UI
Press **`[T]`** in the renderer to cycle between 4 distinct HUD visual themes:
1. **Dark Survival**: Classic post-apocalyptic dark HUD with gold highlights.
2. **Neon Synthwave**: Vibrant cyan/magenta cyberpunk display.
3. **Tactical Military**: Camouflage olive-drab tactical HUD.
4. **Retro Terminal**: High-contrast phosphor green CRT terminal interface.

High-performance viewport tile rendering is accelerated using `VulkanBridge` connected to the native Rust Vulkan engine crate (`rust_vulkan_render`).
