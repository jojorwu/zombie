# Firearms, Ballistics, Item Metal Quality & Zombie Horde AI

## Enhanced Raycast Ballistics Engine (`BallisticsUtility`)
Firearms execute step-by-step raycast projectile flight simulations including air drag velocity loss, wind deflection drift, gravitational bullet drop, material overpenetration, glass shattering, and shallow-angle ricochets:
1. **9mm (Pistol & SMG)**: Muzzle velocity 360 m/s, base damage 35.0, initial kinetic energy 518.4 J. Penetrates glass windows and wooden doors; ricochets off brick/concrete walls at shallow angles.
2. **5.56mm (Assault Rifle & Rifle)**: Muzzle velocity 940 m/s, base damage 75.0, initial kinetic energy 1767.2 J. High-velocity penetration through wood, glass, and brick walls; overpenetrates flesh to hit secondary targets in line of fire.
3. **12gauge (Shotgun)**: Muzzle velocity 475 m/s, base damage 110.0, initial kinetic energy 3158.8 J. Extreme close-range impact energy breaching doors and shattering windows.
4. **.357 Magnum**: Muzzle velocity 440 m/s, base damage 85.0, initial kinetic energy 968.0 J. Heavy stopping power penetrating wooden doors and brick walls.
5. **.308 Sniper**: Muzzle velocity 850 m/s, base damage 160.0, initial kinetic energy 3973.8 J. Armor-piercing rifle round penetrating concrete, brick, and multiple lined-up targets.
6. **Arrow**: Muzzle velocity 90 m/s, base damage 75.0, initial kinetic energy 101.3 J. Silent projectile with zero acoustic noise report.

Firing firearms generates acoustic decibel impulses (`NoiseEvent`) that alert and pull nearby zombies towards shooter coordinates.

## Material Penetration Thresholds & Ricochet Physics
- **Glass / Windows (`TileType.WINDOW`)**: 30 J resistance. Bullet shatters window (`WINDOW_BROKEN`) and continues with minimal velocity drop.
- **Wood / Doors (`TileType.WALL_WOOD`, `DOOR`)**: 160 J resistance. Bullet overpenetrates wood if kinetic energy exceeds threshold.
- **Brick (`TileType.WALL_BRICK`)**: 420 J resistance. Stopped by 9mm, penetrated by 5.56mm and .308 rounds.
- **Concrete & Metal (`WALL_CONCRETE`, `WALL_REINFORCED`)**: 850 - 1200 J resistance. High hardness surface causing shallow-angle (<35°) ricochet reflections with sound report (`ricochet`).
- **Multi-Target Overpenetration**: High-energy bullets pass through flesh (100 J loss per target) to strike additional zombies or survivors behind.

## Metal Quality Purity Tiers (`MetalQuality`)
Weapons and tools possess metal quality tiers that scale damage and durability:
- **Scrap Metal**: 0.7x damage multiplier.
- **Iron**: 1.0x standard base multiplier.
- **Steel**: 1.3x damage multiplier.
- **Hardened Steel**: 1.6x damage multiplier.
- **Titanium**: 2.0x maximum damage multiplier.

## Item Categories & Perishable Foods
- **Melee Weapons**: Knife, Axe, Baseball Bat, Crowbar, Stone Axe, Frying Pan, Chef Knife, Katana, Sledgehammer, Machete, Spear, Pipe.
- **Natural Resources & Crafting**: Stick, Stone, Rags, Clothes, Book, Skill Book, Wood, Metal.
- **Vehicle & Maintenance**: Gas Canister, Car Battery, Spare Wheel, Engine Parts, Wrench.
- **Valuables & Utility**: Money, Gold Ingot, Jewelry, Lockpick, Medkit.
- **Food & Spoilage (`FoodSpoilageUtility`)**: Perishable foods decay over time. Refrigerators (80% slower decay) and Freezers (95% slower decay / frozen) preserve food. Non-perishable items (Canned Food, MREs) never spoil. Wild forage items include Berries and Mushrooms.
- **Protective Armor**: Helmets, Tactical Body Armor, Leather Jackets, Pads reducing anatomical limb damage.

## Zombie AI Behavior & Horde Dynamics
- **Light Sensitivity**: Zombie vision ranges adapt dynamically based on ambient solar/lunar lighting, muzzles, vehicle headlights, and interior lights. Zombies can detect survivors driving vehicles.
- **Acoustic & Scent Tracking**: Zombies investigate decibel acoustic noise events and follow wind-drifted olfactory scent trails (`ScentTrail`).
- **Anatomical Health & Dismemberment (`AnatomicalHealth`)**: Target body parts (head, torso, legs, arms) take localized damage. Dismembering zombie legs forces them to crawl at reduced speed; severing arms disables grab attacks.
- **3D A* Navigation & Obstacle Destruction**: Zombies navigate 3D stairs/ladders and break through closed doors and windows.
- **Hurt Response**: Taking ranged or melee damage alerts zombies to the precise location of the attacker.
- **Grab Slowdown, Infection & Reanimation**: Zombie grab attacks slow survivors down. Bites increase infection progress; infected survivors reanimate as hostile zombies upon death.
- **Spatial Grid Bucketing Flocking**: High-performance spatial grid bucketing aligns adjacent zombies into cohesive hunting hordes.
