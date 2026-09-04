"""
Theme definitions for the JARVIS Desktop UI.
Designed to feel like a calm, modern, minimal personal assistant.
"""
import sys

# Overall Appearance
APPEARANCE_MODE = "dark"
DEFAULT_COLOR_THEME = "blue"

# True Dark Mode Surfaces (Linear / Vercel style)
MAIN_BG = "#000000"           # Pure black background for depth
CARD_BG = "#09090B"           # Zinc 950 (very deep, slightly warm black)
CARD_BORDER = "#27272A"       # Zinc 800 (subtle border)
CARD_HOVER = "#18181B"        # Zinc 900 (slight lift)

# Sidebar Surfaces (Blends with main background)
SIDEBAR_BG = "#000000"
SIDEBAR_HOVER = "#18181B"
SIDEBAR_ACTIVE = "#27272A"
SIDEBAR_BORDER = "#27272A"
SIDEBAR_TEXT = "#FAFAFA"
SIDEBAR_TEXT_MUTED = "#A1A1AA"

# Text Colors
TEXT_PRIMARY = "#FFFFFF"      # Pure white for high contrast
TEXT_SECONDARY = "#A1A1AA"    # Zinc 400 (legible but soft)
TEXT_MUTED = "#71717A"        # Zinc 500
TEXT_LIGHT = "#FFFFFF"

# Refined Accents (Less saturated, more elegant)
ACCENT = "#818CF8"            # Indigo 400
ACCENT_HOVER = "#6366F1"      # Indigo 500
ACCENT_LIGHT = "#1E1B4B"      # Indigo 950 (dark glow)
ACCENT_BORDER = "#3730A3"     # Indigo 800

SUCCESS = "#34D399"           # Emerald 400
SUCCESS_HOVER = "#10B981"
SUCCESS_LIGHT = "#064E3B"
SUCCESS_BORDER = "#065F46"

WARNING = "#FBBF24"           # Amber 400
WARNING_HOVER = "#F59E0B"
WARNING_LIGHT = "#78350F"
WARNING_BORDER = "#92400E"

DANGER = "#F87171"            # Red 400
DANGER_HOVER = "#EF4444"
DANGER_LIGHT = "#7F1D1D"
DANGER_BORDER = "#991B1B"

INFO = "#60A5FA"              # Blue 400
INFO_LIGHT = "#1E3A8A"
INFO_BORDER = "#1E40AF"

PURPLE = "#A78BFA"            # Violet 400
PURPLE_LIGHT = "#4C1D95"
PURPLE_BORDER = "#5B21B6"

# Platform-tuned typography
if sys.platform == "darwin":
    FONT_FAMILY = "SF Pro Display"
elif sys.platform == "win32":
    FONT_FAMILY = "Segoe UI Variable Display"  # Modern Windows 11 font if available
else:
    FONT_FAMILY = "Inter"

FALLBACK_FONT = "Segoe UI"


def configure_theme(ctk):
    """Sets CustomTkinter appearance mode."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

def font(size=14, weight="normal"):
    """Convenience font helper."""
    return (FONT_FAMILY, size, weight)
