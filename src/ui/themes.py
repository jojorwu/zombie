class UITheme:
    DARK = "Dark Survival"
    NEON = "Neon Synthwave"
    TACTICAL = "Tactical Military"
    RETRO = "Retro Terminal"

THEME_COLORS = {
    UITheme.DARK: {
        "bg": (20, 20, 20),
        "sidebar_bg": (30, 30, 30),
        "sidebar_line": (100, 100, 100),
        "title": (255, 215, 0),
        "header": (0, 255, 127),
        "text": (220, 220, 220),
        "accent": (70, 130, 180),
    },
    UITheme.NEON: {
        "bg": (15, 5, 25),
        "sidebar_bg": (25, 10, 40),
        "sidebar_line": (255, 0, 128),
        "title": (0, 255, 255),
        "header": (255, 0, 255),
        "text": (240, 220, 255),
        "accent": (255, 215, 0),
    },
    UITheme.TACTICAL: {
        "bg": (15, 20, 15),
        "sidebar_bg": (25, 35, 25),
        "sidebar_line": (80, 120, 80),
        "title": (180, 220, 100),
        "header": (120, 200, 120),
        "text": (200, 220, 200),
        "accent": (220, 180, 80),
    },
    UITheme.RETRO: {
        "bg": (0, 10, 0),
        "sidebar_bg": (0, 20, 0),
        "sidebar_line": (0, 180, 0),
        "title": (0, 255, 0),
        "header": (50, 255, 50),
        "text": (0, 220, 0),
        "accent": (100, 255, 100),
    },
}
