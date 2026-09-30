# Dynamic Weather, Wind & Lighting Engine

## Dynamic Wind Simulation
The `WeatherManager` continuously simulates changing wind directions (0-360°) and speeds (0-100 km/h):
- **Tailwinds & Headwinds**: Movement speed increases when walking with wind direction and decreases when walking against headwinds.
- **Bullet Ballistics**: Bullet trajectories drift slightly off target under strong crosswinds.
- **Scent Drifting**: Survivor olfactory scent trails (`ScentTrail`) drift along the active wind vector.
- **Rain Particle Slant**: Visual rain particle rendering tilts dynamically to match wind direction.

## Localized 100x100 Rainstorm Fronts
Rainstorms form dynamically every ~3 in-game days over localized 100x100 tile regions:
- **Visibility & Lighting**: Rain dims local illumination and lowers ambient temperature.
- **Scent Trail Washing**: Rain rapidly washes away survivor scent trails at 4x speed.
- **Noise Dampening**: Rain dampens acoustic sound propagation.

## Dynamic Point & Cone Lighting
Dynamic light sources (`DynamicLight`) render over ambient darkness:
- **Muzzle Flashes**: Bright orange/yellow illumination bursts emitted on firearm discharge.
- **Storm Lightning**: Random blue-white flashes illuminating active rainstorm fronts.
