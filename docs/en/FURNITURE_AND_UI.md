# Furniture, Sound Occlusion & UI Themes Guide

## Furniture & Container Searching
The map generator populates building interiors with detailed room furniture:
- **Furniture Types**: Tables, Chairs, Sofas, Beds, Cabinets, Refrigerators, Kitchen Counters, Bookshelves, Desks, Gun Racks, Weapon Safes, Cash Registers, Lockers, Store Shelves, Workbenches, Factory Racks.
- **Interactivity & Searching**:
  - Survivors can search adjacent furniture containers when looting (`survivor_looting.py`).
  - **Refrigerators**: Yield meats, bread, water bottles, apples, and perishable produce.
  - **Cabinets & Safes**: Yield canned food, can openers, ammo, medkits, money, and jewelry.
  - **Gun Racks & Lockers**: Yield rifles, shotguns, handguns, and tactical body armor.
  - **Bookshelves**: Yield skill books (`read_skill_book`) that unlock advanced crafting recipes like stone axes.

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
