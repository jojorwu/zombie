# Firearms, Ballistics, Item Metal Quality & Zombie Horde AI

## Ballistics Engine & Calibers (`BallisticsUtility`)
Firearms simulate ballistics calculations including air drag velocity loss, wind deflection drift, gravitational bullet drop, and kinetic impact energy:
1. **9mm (Pistol)**: Muzzle velocity 360 m/s, base damage 35.0, max range 50m.
2. **5.56mm (Rifle)**: Muzzle velocity 940 m/s, base damage 75.0, max range 150m.
3. **12gauge (Shotgun)**: Muzzle velocity 475 m/s, base damage 110.0, max range 35m.
4. **.357 Magnum**: Muzzle velocity 440 m/s, base damage 85.0, max range 65m.
5. **.308 Sniper**: Muzzle velocity 850 m/s, base damage 160.0, max range 300m.
6. **Arrow**: Muzzle velocity 90 m/s, base damage 75.0, max range 40m.

Firing firearms generates acoustic decibel impulses (`NoiseEvent`) that alert and pull nearby zombies towards shooter coordinates.

## Metal Quality Purity Tiers (`MetalQuality`)
Weapons and tools possess metal quality tiers that scale damage and durability:
- **Scrap Metal**: 0.7x damage multiplier.
- **Iron**: 1.0x standard base multiplier.
- **Steel**: 1.3x damage multiplier.
- **Hardened Steel**: 1.6x damage multiplier.
- **Titanium**: 2.0x maximum damage multiplier.

## Item Categories & Perishable Foods
- **Melee Weapons**: Knife, Axe, Baseball Bat, Crowbar, Stone Axe, Frying Pan, Chef Knife.
- **Natural Resources & Crafting**: Stick, Stone, Rags, Clothes, Book, Skill Book, Wood, Metal.
- **Vehicle & Maintenance**: Gas Canister, Car Battery, Spare Wheel, Engine Parts, Wrench.
- **Valuables & Utility**: Money, Gold Ingot, Jewelry, Lockpick, Medkit.
- **Food & Spoilage (`FoodSpoilageUtility`)**: Perishable foods (Meat, Bread, Apples) decay over time. Cold storage in powered refrigerators reduces spoilage by 80%. Non-perishable items (Canned Food, MREs) never spoil. Wild forage items include Berries and Mushrooms.
- **Protective Armor**: Helmets, Tactical Body Armor, Leather Jackets, Pads reducing anatomical limb damage.

## Zombie AI Behavior & Horde Dynamics
- **Light Sensitivity**: Zombie vision ranges adapt dynamically based on ambient solar/lunar lighting, muzzles, vehicle headlights, and interior lights. Zombies can detect survivors driving vehicles.
- **Acoustic & Scent Tracking**: Zombies investigate decibel acoustic noise events and follow wind-drifted olfactory scent trails (`ScentTrail`).
- **Anatomical Health & Dismemberment (`AnatomicalHealth`)**: Target body parts (head, torso, legs, arms) take localized damage. Dismembering zombie legs forces them to crawl at reduced speed; severing arms disables grab attacks.
- **3D A* Navigation & Obstacle Destruction**: Zombies navigate 3D stairs/ladders and break through closed doors and windows.
- **Hurt Response**: Taking ranged or melee damage alerts zombies to the precise location of the attacker.
- **Grab Slowdown, Infection & Reanimation**: Zombie grab attacks slow survivors down. Bites increase infection progress; infected survivors reanimate as hostile zombies upon death.
- **Spatial Grid Bucketing Flocking**: High-performance spatial grid bucketing aligns adjacent zombies into cohesive hunting hordes.
