"""
Theme definitions for the VAVE Desktop UI.

One neutral base, one accent, and muted semantic colors that are only used
to say something the user needs to know (success, attention, danger).
Nothing here exists to decorate the interface.
"""
import sys

# Overall Appearance
APPEARANCE_MODE = "light"
DEFAULT_COLOR_THEME = "blue"

# Primary Surfaces
MAIN_BG = "#F6F7F9"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#E7E9EE"
CARD_HOVER = "#F3F5F8"
# A quiet fill for icon chips and inset rows, one step off the card.
SURFACE_SUBTLE = "#F0F2F6"

# Dark Sidebar Surfaces (graphite with a trace of blue, so it sits with the
# accent instead of fighting it)
SIDEBAR_BG = "#1A1C22"
SIDEBAR_HOVER = "#24262E"
SIDEBAR_ACTIVE = "#2C3040"
SIDEBAR_BORDER = "#262933"
SIDEBAR_TEXT = "#F2F3F5"
SIDEBAR_TEXT_MUTED = "#9096A2"
# Icon colour for the selected row: the accent, lifted to read on dark.
SIDEBAR_ACCENT = "#93A6E6"

# Text Colors
TEXT_PRIMARY = "#16181D"      # Near-black charcoal
TEXT_SECONDARY = "#565B66"    # Balanced gray
TEXT_MUTED = "#8A8F9A"        # Soft muted gray
TEXT_LIGHT = "#FFFFFF"

# Single restrained accent. Used for the one primary action on a screen.
ACCENT = "#4C63B6"            # Soft indigo
ACCENT_HOVER = "#41569F"
ACCENT_LIGHT = "#EDF0FA"
ACCENT_BORDER = "#D2DAF0"

# Semantic colors. Muted on purpose: they carry meaning, not emphasis.
SUCCESS = "#3E8E6E"           # Muted green
SUCCESS_HOVER = "#347759"
SUCCESS_LIGHT = "#ECF5F1"
SUCCESS_BORDER = "#C9E4D8"

WARNING = "#A8792F"           # Muted amber
WARNING_HOVER = "#8E6222"
WARNING_LIGHT = "#F8F4EC"
WARNING_BORDER = "#E9DCC4"

DANGER = "#B0524D"            # Muted red, destructive actions only
DANGER_HOVER = "#95433F"
DANGER_LIGHT = "#F9F0EF"
DANGER_BORDER = "#EBD0CE"

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
RADIUS_CARD = 14
RADIUS_CONTROL = 10
RADIUS_CHIP = 9
RADIUS_PILL = 999

# Icon sizes, so a glyph is never sized by eye at the call site.
ICON_NAV = 17
ICON_INLINE = 16
ICON_CARD = 18

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
