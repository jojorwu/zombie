class DynamicLight:
    """Represents a localized dynamic point/cone light source (muzzle flash, flashlight, headlight, lightning)."""
    def __init__(self, x, y, z, radius=8.0, color=(255, 255, 200), intensity=1.0, lifetime=1):
        self.x = float(x)
        self.y = float(y)
        self.z = int(z)
        self.radius = float(radius)
        self.color = color
        self.intensity = float(intensity)
        self.lifetime = lifetime

    def update(self):
        self.lifetime -= 1
