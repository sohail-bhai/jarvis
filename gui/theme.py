"""
Theme definitions for the VAVE Desktop UI.

The palette is warm-neutral paper with near-black ink and a single deep navy
accent. It avoids the cool grey and violet that every assistant interface
arrives in, because a tool people keep open all day should look like a desk,
not like a product demo.

Rules the rest of the UI follows:
  - Colour marks state, never decoration. A tinted surface means something
    is live, waiting or wrong.
  - Structure comes from hairlines and whitespace, not from boxing every
    element in its own bordered card.
  - One accent. If two things on a screen both want it, one of them is not
    the primary action.
"""
import sys

# Overall Appearance
APPEARANCE_MODE = "light"
DEFAULT_COLOR_THEME = "blue"

# Primary Surfaces. Warm paper rather than blue-grey.
MAIN_BG = "#F7F6F3"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#E4E1DB"       # Warm hairline, meant to be barely there
CARD_HOVER = "#F4F2EE"
# A quiet fill for icon chips and inset rows, one step off the card.
SURFACE_SUBTLE = "#F1EFEA"
# Divider inside a surface, lighter than the outer border.
DIVIDER = "#EDEAE4"

# Sidebar: warm near-black, so it reads as ink beside the paper.
SIDEBAR_BG = "#191817"
SIDEBAR_HOVER = "#232120"
SIDEBAR_ACTIVE = "#2C2A28"
SIDEBAR_BORDER = "#262422"
SIDEBAR_TEXT = "#F5F3F0"
SIDEBAR_TEXT_MUTED = "#8C8781"
# Section labels above nav groups.
SIDEBAR_LABEL = "#6E6963"
# Icon colour for the selected row: the accent, lifted to read on dark.
SIDEBAR_ACCENT = "#8FAAD8"

# Text Colors
TEXT_PRIMARY = "#1A1917"      # Warm near-black
TEXT_SECONDARY = "#57534E"    # Balanced warm grey
TEXT_MUTED = "#8A857E"        # Soft muted grey
TEXT_LIGHT = "#FFFFFF"

# Single restrained accent: deep navy. Dark enough to carry white text, quiet
# enough to sit next to black ink without shouting.
ACCENT = "#24457A"
ACCENT_HOVER = "#1C3862"
ACCENT_LIGHT = "#EDF1F7"
ACCENT_BORDER = "#CCD8E8"

# Semantic colors. Deep and muted: they carry meaning, not emphasis.
SUCCESS = "#2F7A55"           # Evergreen
SUCCESS_HOVER = "#276646"
SUCCESS_LIGHT = "#EDF4F0"
SUCCESS_BORDER = "#C6DED2"

WARNING = "#A16414"           # Burnt amber
WARNING_HOVER = "#85520F"
WARNING_LIGHT = "#F8F3EA"
WARNING_BORDER = "#E6D8BF"

DANGER = "#A33A32"            # Brick, destructive actions only
DANGER_HOVER = "#8A302A"
DANGER_LIGHT = "#F8EEEC"
DANGER_BORDER = "#E5C9C5"

# INFO is the accent under another name so neutral states stay in one family.
INFO = ACCENT
INFO_LIGHT = ACCENT_LIGHT
INFO_BORDER = ACCENT_BORDER

# Kept so older imports keep working; new UI should not introduce a
# fifth color family.
PURPLE = ACCENT
PURPLE_LIGHT = ACCENT_LIGHT
PURPLE_BORDER = ACCENT_BORDER

# Shape. Restrained radii: large ones read as a consumer app, square ones as a
# developer console.
RADIUS_CARD = 10
RADIUS_CONTROL = 8
RADIUS_CHIP = 8
RADIUS_PILL = 999

# Icon sizes, so a glyph is never sized by eye at the call site.
ICON_NAV = 17
ICON_INLINE = 16
ICON_CARD = 18

# Type scale. Named, so a heading is never one point off its twin elsewhere.
SIZE_DISPLAY = 25
SIZE_TITLE = 16
SIZE_BODY = 12
SIZE_SMALL = 11
SIZE_LABEL = 10

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


def label_font():
    """Small caps-style label used above groups and on quiet metadata."""
    return (FONT_FAMILY, SIZE_LABEL, "bold")
