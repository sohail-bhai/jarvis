"""
Theme definitions for the VAVE Desktop UI.

The look is a quiet gallery: bone paper, ivory cards that lift off it on a warm
shadow, ink text, and a single deep forest accent. No pure white, no pure
black, no saturated colour anywhere - the contrast comes from weight and space
rather than from hue.

Type does the heavy lifting. Headings are set in a serif, everything
functional in a geometric sans, and small labels are tracked-out uppercase.
That pairing is what stops an interface reading as a template.

Rules the rest of the UI follows:
  - Colour marks state, never decoration.
  - Depth comes from painted shadows (gui/surfaces.py), not from borders on
    everything.
  - One accent. If two things on a screen both want it, one of them is not
    the primary action.
"""
import sys

# Overall Appearance
APPEARANCE_MODE = "dark"
DEFAULT_COLOR_THEME = "blue"

# Primary Surfaces. Near-black ground with panels lifted a few points above
# it - the contrast between them is what gives the interface depth, so neither
# is ever pure black.
MAIN_BG = "#0C0C0D"
CARD_BG = "#17171A"
CARD_BORDER = "#2A2A2E"       # Hairline, meant to be felt rather than seen
CARD_HOVER = "#1B1B1E"
SURFACE_SUBTLE = "#1A1A1D"
DIVIDER = "#202023"

# The sidebar sinks below the page rather than rising above it.
SIDEBAR_BG = "#080809"
SIDEBAR_HOVER = "#161618"
SIDEBAR_ACTIVE = "#1E1E21"
SIDEBAR_BORDER = "#1C1C1F"
SIDEBAR_TEXT = "#F2F0EC"
SIDEBAR_TEXT_MUTED = "#77767A"
SIDEBAR_LABEL = "#4F4E52"
SIDEBAR_ACCENT = "#D9A441"

# Text. Warm off-white on black reads as paper; pure white reads as a screen.
TEXT_PRIMARY = "#F2F0EC"
TEXT_SECONDARY = "#A5A3A0"
TEXT_MUTED = "#6E6D71"
TEXT_LIGHT = "#0C0C0D"        # Type that sits *on* the accent

# One accent: aged gold. Warm enough to feel considered, dark enough not to
# glow. Nothing else on screen is allowed to be this colour.
ACCENT = "#D9A441"
ACCENT_HOVER = "#C08F32"
ACCENT_LIGHT = "#211B0F"
ACCENT_BORDER = "#3A2F1A"
BRASS = "#D9A441"
BRASS_LIGHT = "#211B0F"

# Semantic colours, all desaturated to sit on black without vibrating.
SUCCESS = "#6FAE7F"
SUCCESS_HOVER = "#5C9A6C"
SUCCESS_LIGHT = "#121A14"
SUCCESS_BORDER = "#25382A"

WARNING = "#D9A441"
WARNING_HOVER = "#C08F32"
WARNING_LIGHT = "#211B0F"
WARNING_BORDER = "#3A2F1A"

DANGER = "#D2705F"
DANGER_HOVER = "#B85C4C"
DANGER_LIGHT = "#1F1311"
DANGER_BORDER = "#3B241F"

# INFO is the accent under another name so neutral states stay in one family.
INFO = ACCENT
INFO_LIGHT = ACCENT_LIGHT
INFO_BORDER = ACCENT_BORDER

PURPLE = ACCENT
PURPLE_LIGHT = ACCENT_LIGHT
PURPLE_BORDER = ACCENT_BORDER

# Shape
RADIUS_CARD = 14
RADIUS_CONTROL = 9
RADIUS_CHIP = 8
RADIUS_PILL = 999

# Elevation presets for gui/surfaces.card_image, as (opacity, blur, offset).
ELEVATION_FLAT = (0.0, 0, 0)
ELEVATION_LOW = (0.30, 10, 3)
ELEVATION_HIGH = (0.45, 18, 6)

# Icon sizes, so a glyph is never sized by eye at the call site.
ICON_NAV = 17
ICON_INLINE = 16
ICON_CARD = 18

# Type scale.
SIZE_DISPLAY = 29
SIZE_HEADING = 19
SIZE_TITLE = 15
SIZE_BODY = 12
SIZE_SMALL = 11
SIZE_LABEL = 9


def _first_available(candidates, fallback):
    """Pick the first font actually installed, so nothing renders as Fixed."""
    try:
        import subprocess

        installed = subprocess.run(["fc-list", ":", "family"],
                                   capture_output=True, text=True, timeout=4).stdout
    except Exception:
        return fallback

    lowered = installed.lower()
    for name in candidates:
        if name.lower() in lowered:
            return name
    return fallback


if sys.platform == "darwin":
    FONT_FAMILY = "SF Pro Text"
    DISPLAY_FAMILY = "New York"
elif sys.platform == "win32":
    FONT_FAMILY = "Segoe UI"
    DISPLAY_FAMILY = "Georgia"
else:
    # Geometric sans for the interface, serif for headings. The pairing is the
    # single biggest reason this does not look like every other dashboard.
    FONT_FAMILY = _first_available(["Montserrat", "Cantarell", "Noto Sans"], "DejaVu Sans")
    DISPLAY_FAMILY = _first_available(["Noto Serif", "Liberation Serif"], "DejaVu Serif")

FALLBACK_FONT = "Helvetica"


def configure_theme(ctk):
    """Sets CustomTkinter appearance mode."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def font(size=14, weight="normal"):
    """Interface type: the geometric sans."""
    return (FONT_FAMILY, size, weight)


def display(size=SIZE_DISPLAY, weight="normal"):
    """Editorial type: the serif, for headings only."""
    return (DISPLAY_FAMILY, size, weight)


def label_font():
    """Tracked-out uppercase label used above groups and on quiet metadata."""
    return (FONT_FAMILY, SIZE_LABEL, "bold")


def tracked(text: str) -> str:
    """Letter-spacing, the only way Tk offers it: spaces between characters."""
    return " ".join(text.upper())
