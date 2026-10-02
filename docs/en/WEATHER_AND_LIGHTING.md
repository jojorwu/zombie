# Dynamic Weather, Wind, Lighting & Climate Engine

## Dynamic Wind Simulation
The `WeatherManager` continuously simulates changing wind directions (0-360°) and speeds (0-100 km/h):
- **Tailwinds & Headwinds**: Movement speed increases when walking with wind direction and decreases when walking against headwinds.
- **Bullet Trajectory Drift**: Ballistics calculations (`BallisticsUtility`) drift bullet flight trajectories under strong crosswinds.
- **Scent Trailing Drift**: Survivor olfactory scent trails (`ScentTrail`) drift along the active wind vector.
- **Visual Particle Slant**: Visual rain and snow particle rendering tilts dynamically to match wind vectors.

## Localized 100x100 Rainstorm & Snowstorm Fronts
Storm fronts form dynamically every ~3 in-game days over localized 100x100 tile regions:
- **Visibility & Lighting**: Storm fronts dim local illumination and lower ambient temperatures.
- **Scent Trail Washing**: Heavy rainfall rapidly washes away survivor scent trails at 4x normal speed.
- **Noise Dampening**: Ambient rainfall dampens acoustic sound decibel levels.

## Astronomical Solar Zenith & Synodic Lunar Lighting
- **Solar Zenith Angles**: Sun elevation rotates across 3,600 tick 24-hour cycles (1 real hour = 1 in-game month).
- **29.5-Day Synodic Lunar Cycle**: Moon phases (New Moon to Full Moon) determine night ambient brightness.
- **Dynamic Point & Cone Lights (`DynamicLight`)**:
  - **Muzzle Flashes**: Bright orange/yellow bursts on firearm discharges.
  - **Vehicle Headlights**: Directed beam cones illuminating driving paths.
  - **Storm Lightning**: Random blue-white flashes illuminating active storm fronts.
- **Raycasted Fog of War (`compute_fog_of_war`)**: Evaluates directional FOV angle cones (`facing_angle`, `fov_degrees`) and opacity walls (`_OPAQUE_FOW_TILES`).
