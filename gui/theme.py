BACKGROUND = "#050912"
SURFACE = "#0B111F"
SURFACE_ALT = "#10182A"
BORDER = "#1E2D4A"
ACCENT = "#00E5FF"
ACCENT_MUTED = "#005566"
TEXT = "#FFFFFF"
TEXT_MUTED = "#8B9BB4"
ERROR = "#FF4B4B"
SUCCESS = "#00FF9D"
WARNING = "#FFB800"

FONT_FAMILY = "Segoe UI"


def configure_theme(ctk):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def font(size=14, weight="normal"):
    return (FONT_FAMILY, size, weight)
