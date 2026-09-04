"""
Theme definitions for the JARVIS Desktop UI.
Designed to feel like a calm, modern, minimal personal assistant.
"""
import sys

# Overall Appearance
APPEARANCE_MODE = "light"
DEFAULT_COLOR_THEME = "blue"

# Primary Surfaces
MAIN_BG = "#F3F4F8"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#E5E7EB"
CARD_HOVER = "#F9FAFB"

# Dark Sidebar Surfaces (matching reference image)
SIDEBAR_BG = "#161922"
SIDEBAR_HOVER = "#232836"
SIDEBAR_ACTIVE = "#2C3244"
SIDEBAR_BORDER = "#252B3B"
SIDEBAR_TEXT = "#F9FAFB"
SIDEBAR_TEXT_MUTED = "#9CA3AF"

# Text Colors
TEXT_PRIMARY = "#111827"      # Deep charcoal
TEXT_SECONDARY = "#4B5563"    # Balanced gray
TEXT_MUTED = "#9CA3AF"        # Soft muted gray
TEXT_LIGHT = "#FFFFFF"

# Restrained Accents & Semantics
ACCENT = "#4F46E5"            # Indigo
ACCENT_HOVER = "#4338CA"
ACCENT_LIGHT = "#EEF2FF"
ACCENT_BORDER = "#C7D2FE"

SUCCESS = "#10B981"           # Emerald green
SUCCESS_HOVER = "#059669"
SUCCESS_LIGHT = "#ECFDF5"
SUCCESS_BORDER = "#A7F3D0"

WARNING = "#F59E0B"           # Amber
WARNING_HOVER = "#D97706"
WARNING_LIGHT = "#FFFBEB"
WARNING_BORDER = "#FDE68A"

DANGER = "#EF4444"            # Rose / Red
DANGER_HOVER = "#DC2626"
DANGER_LIGHT = "#FEF2F2"
DANGER_BORDER = "#FECACA"

INFO = "#3B82F6"              # Sky / Blue
INFO_LIGHT = "#EFF6FF"
INFO_BORDER = "#BFDBFE"

PURPLE = "#8B5CF6"
PURPLE_LIGHT = "#FAF5FF"
PURPLE_BORDER = "#DDD6FE"

# Platform-tuned typography
if sys.platform == "darwin":
    FONT_FAMILY = "SF Pro Display"
elif sys.platform == "win32":
    FONT_FAMILY = "Segoe UI"
else:
    FONT_FAMILY = "DejaVu Sans"

FALLBACK_FONT = "Helvetica"


def configure_theme(ctk):
    """Sets CustomTkinter appearance mode."""
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")


def font(size=14, weight="normal"):
    """Convenience font helper."""
    return (FONT_FAMILY, size, weight)
