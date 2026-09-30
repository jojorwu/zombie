# Zombie AI Neuroevolution Simulation - Firearms, Items & Zombie Horde AI

## New Firearms & Ammunition Mechanics
The simulation now supports realistic firearm ballistics and ammunition management:
1. **Pistol (`pistol`)**: Uses `pistol_ammo`. Medium range (8.0), 50.0 damage, noise volume 35.0.
2. **Shotgun (`shotgun`)**: Uses `shotgun_shells`. Close range (5.0), high damage 90.0, noise volume 55.0.
3. **Rifle (`rifle`)**: Uses `rifle_ammo`. Long range (14.0), extreme damage 120.0, noise volume 45.0.

Firing a weapon generates acoustic `NoiseEvent` waves that alert and pull nearby zombies towards the shooter's coordinates.

## Expanded Melee, Food & Kitchen Items
- **4 Melee Weapons**: Knife, Axe, Baseball Bat, Crowbar.
- **5 Food Types**: Canned Food, Bread, Apple, Meat, MRE.
- **6 Kitchen Items**: Frying Pan, Pot, Chef Knife, Can Opener, Water Bottle, Cutting Board.
  - Can Opener / Chef Knife required to open Canned Food.
  - Frying Pan and Chef Knife double as melee weapons.

## Enhanced Zombie Behavior & Horde Flocking
- **Light Sensitivity**: Zombie vision range expands during daylight and shrinks in blackouts/darkness.
- **Scent Trail Tracking**: Survivors leave fading olfactory scent trails (`ScentTrail`) that zombies track by smell when idling.
- **Obstacle Avoidance**: Smart vector steering around walls and obstacles.
- **Flocking & Horde Mechanics**: Zombies close to each other align and aggregate into hunting hordes.
