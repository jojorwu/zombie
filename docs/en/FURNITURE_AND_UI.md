# Furniture, Sound Occlusion & UI Themes Guide

## Furniture & Container Searching
The map generator now places detailed room furniture:
- **Furniture Types**: Tables, Chairs, Sofas, Beds, Cabinets, Refrigerators, Kitchen Counters.
- **Interactivity & Searching**:
  - Survivors can search adjacent furniture containers (`action = 1`) when no loose floor items are present.
  - **Refrigerators**: Yield meats, bread, water bottles, and apples.
  - **Cabinets**: Yield canned food, can openers, pistol ammo, and medkits.
  - **Counters & Tables**: Yield chef knives, frying pans, pots, and cutting boards.

## Realistic Wall Sound Occlusion
Acoustic sound propagation (`NoiseEvent`) now evaluates line-of-sight raycasts through building geometry:
- Solid building & underground walls dampen sound volume by **65%**.
- Closed doors dampen sound volume by **35%**.
- Open tiles allow sound propagation based on standard distance decay.

## Graphics & Theme-Switching UI
Press **`[T]`** in the renderer to cycle between 4 color themes:
1. **Dark Survival**: Classic post-apocalyptic dark HUD with gold highlights.
2. **Neon Synthwave**: Vibrant cyan/magenta cyberpunk theme.
3. **Tactical Military**: Camouflage olive-drab tactical display.
4. **Retro Terminal**: High-contrast phosphor green CRT terminal interface.
