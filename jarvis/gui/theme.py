SIDEBAR_BG = "#111827"
SIDEBAR_CARD = "#1F2937"
SIDEBAR_TEXT = "#FFFFFF"
SIDEBAR_TEXT_MUTED = "#9CA3AF"

BACKGROUND = "#F3F5F9"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#F9FAFB"
BORDER = "#E5E7EB"

ACCENT = "#3B82F6"
ACCENT_MUTED = "#E0E7FF"
TEXT = "#111827"
TEXT_MUTED = "#6B7280"
ERROR = "#EF4444"
SUCCESS = "#10B981"
WARNING = "#F59E0B"

FONT_FAMILY = "Segoe UI"


def configure_theme(ctk):
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")


def font(size=14, weight="normal"):
    return (FONT_FAMILY, size, weight)
