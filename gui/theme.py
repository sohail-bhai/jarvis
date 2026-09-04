"""
Theme definitions for the JARVIS Desktop UI.

One neutral base, one accent, and muted semantic colors that are only used
to say something the user needs to know (success, attention, danger).
Nothing here exists to decorate the interface.
"""
import sys

# Overall Appearance
APPEARANCE_MODE = "light"
DEFAULT_COLOR_THEME = "blue"

# Primary Surfaces
MAIN_BG = "#F6F6F7"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#E6E7EA"
CARD_HOVER = "#F4F4F6"

# Dark Sidebar Surfaces (neutral graphite, not blue)
SIDEBAR_BG = "#191A1D"
SIDEBAR_HOVER = "#232427"
SIDEBAR_ACTIVE = "#2B2D31"
SIDEBAR_BORDER = "#26282C"
SIDEBAR_TEXT = "#F4F4F5"
SIDEBAR_TEXT_MUTED = "#8E9198"

# Text Colors
TEXT_PRIMARY = "#1A1B1E"      # Near-black charcoal
TEXT_SECONDARY = "#5A5E68"    # Balanced gray
TEXT_MUTED = "#8E9198"        # Soft muted gray
TEXT_LIGHT = "#FFFFFF"

# Single restrained accent. Used for the one primary action on a screen.
ACCENT = "#3F5AA6"            # Muted indigo
ACCENT_HOVER = "#354C8C"
ACCENT_LIGHT = "#EEF1F8"
ACCENT_BORDER = "#D3DAEB"

# Semantic colors. Muted on purpose: they carry meaning, not emphasis.
SUCCESS = "#3F8F6B"           # Muted green
SUCCESS_HOVER = "#347759"
SUCCESS_LIGHT = "#EFF5F2"
SUCCESS_BORDER = "#CFE2D8"

WARNING = "#A9762B"           # Muted amber
WARNING_HOVER = "#8E6222"
WARNING_LIGHT = "#F7F3EB"
WARNING_BORDER = "#E7DCC5"

DANGER = "#B04A45"            # Muted red, destructive actions only
DANGER_HOVER = "#953D39"
DANGER_LIGHT = "#F8F0EF"
DANGER_BORDER = "#E8CFCD"

# INFO is the accent under another name so neutral states stay in one family.
INFO = ACCENT
INFO_LIGHT = ACCENT_LIGHT
INFO_BORDER = ACCENT_BORDER

# Kept so older imports keep working; new UI should not introduce a
# fifth color family.
PURPLE = ACCENT
PURPLE_LIGHT = ACCENT_LIGHT
PURPLE_BORDER = ACCENT_BORDER

# Shape
RADIUS_CARD = 12
RADIUS_CONTROL = 10
RADIUS_PILL = 999

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
