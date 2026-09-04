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
APPEARANCE_MODE = "light"
DEFAULT_COLOR_THEME = "blue"

# Primary Surfaces. Bone paper and ivory card; neither is pure white.
MAIN_BG = "#F4F1EC"
CARD_BG = "#FCFBF9"
CARD_BORDER = "#E5DFD4"       # Warm hairline, meant to be barely there
CARD_HOVER = "#F6F3EE"
# A quiet fill for chips and inset rows, one step off the card.
SURFACE_SUBTLE = "#EFEBE3"
# Divider inside a surface, lighter than the outer border.
DIVIDER = "#EAE4DA"

# Sidebar: warm ink, close to black but never quite there.
SIDEBAR_BG = "#1C1A17"
SIDEBAR_HOVER = "#262320"
SIDEBAR_ACTIVE = "#302C27"
SIDEBAR_BORDER = "#2A2622"
SIDEBAR_TEXT = "#F2EFE9"
SIDEBAR_TEXT_MUTED = "#8B857B"
SIDEBAR_LABEL = "#6B655B"
# Icon colour for the selected row: the accent, lifted to read on ink.
SIDEBAR_ACCENT = "#9DB8A5"

# Text Colors
TEXT_PRIMARY = "#1F1D19"      # Warm ink
TEXT_SECONDARY = "#5C564C"    # Balanced warm grey
TEXT_MUTED = "#948D82"        # Soft muted grey
TEXT_LIGHT = "#FCFBF9"

# Single restrained accent: deep forest. Dark enough to carry ivory text,
# quiet enough to sit beside ink without announcing itself.
ACCENT = "#33513F"
ACCENT_HOVER = "#284031"
ACCENT_LIGHT = "#EBEFEA"
ACCENT_BORDER = "#CBD8CE"
# A second, non-competing tone for quiet emphasis: aged brass.
BRASS = "#9C7B45"
BRASS_LIGHT = "#F4EFE5"

# Semantic colors. Deep and muted: they carry meaning, not emphasis.
SUCCESS = "#3F6B4F"           # Forest, same family as the accent
SUCCESS_HOVER = "#325740"
SUCCESS_LIGHT = "#EBF0EC"
SUCCESS_BORDER = "#CBDACF"

WARNING = "#946A28"           # Ochre
WARNING_HOVER = "#7A561F"
WARNING_LIGHT = "#F6F1E7"
WARNING_BORDER = "#E3D5BB"

DANGER = "#9A4438"            # Brick, destructive actions only
DANGER_HOVER = "#82382E"
DANGER_LIGHT = "#F6EDEB"
DANGER_BORDER = "#E2C9C3"

# INFO is the accent under another name so neutral states stay in one family.
INFO = ACCENT
INFO_LIGHT = ACCENT_LIGHT
INFO_BORDER = ACCENT_BORDER

# Kept so older imports keep working; new UI should not introduce another
# colour family.
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
ELEVATION_LOW = (0.09, 8, 2)
ELEVATION_HIGH = (0.15, 14, 5)

# Icon sizes, so a glyph is never sized by eye at the call site.
ICON_NAV = 17
ICON_INLINE = 16
ICON_CARD = 18

# Type scale.
SIZE_DISPLAY = 30
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
    ctk.set_appearance_mode("light")
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
