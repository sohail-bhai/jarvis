"""
Theme definitions for the VAVE Desktop UI.

One neutral grey ground, white cards, a single blue accent, and semantic
colours used only where they carry meaning. Purple is deliberately absent:
a second decorative hue makes the interface read as a demo rather than as a
tool. Sizes live here as tokens so nothing is spaced by eye at the call site.
"""
import sys

# Overall Appearance
APPEARANCE_MODE = "light"
DEFAULT_COLOR_THEME = "blue"

# Primary Surfaces
MAIN_BG = "#FBF7F2"           # Warm off-white ground
CARD_BG = "#FFFFFF"
CARD_BORDER = "#F0E5D8"
CARD_HOVER = "#FFF9F2"
SURFACE_SUBTLE = "#FFF4E8"    # One step off a card: icon chips, inset rows

# Sidebar Surfaces. The rail is white like the rest of the app; the current
# row is the only place the pastel is used as a full fill.
SIDEBAR_BG = "#FFFFFF"
SIDEBAR_HOVER = "#FFF4E8"
SIDEBAR_ACTIVE = "#FFD4A1"
SIDEBAR_BORDER = "#F0E5D8"
SIDEBAR_TEXT = "#2A211A"
SIDEBAR_TEXT_MUTED = "#8B7B6B"

# Text Colors
TEXT_PRIMARY = "#241C14"      # Warm charcoal
TEXT_SECONDARY = "#5A4E43"
TEXT_MUTED = "#96887A"
TEXT_LIGHT = "#FFFFFF"

# The pastel is a fill, not an ink: at #FFD4A1 it cannot carry text or a
# glyph on white, so anything drawn on a light surface uses ACCENT_DEEP and
# anything drawn on the pastel uses ON_ACCENT.
ACCENT = "#FFD4A1"            # Pastel orange fill
ACCENT_HOVER = "#FFC684"
ACCENT_DEEP = "#B4712B"       # Readable orange for glyphs, links, dots
ACCENT_DEEP_HOVER = "#95591D"
ACCENT_LIGHT = "#FFF3E4"
ACCENT_BORDER = "#FFD4A1"
ON_ACCENT = "#3B2A18"         # Text and glyphs sitting on the pastel

SUCCESS = "#2F8F6B"
SUCCESS_HOVER = "#247355"
SUCCESS_LIGHT = "#EDF8F3"
SUCCESS_BORDER = "#B6E2D1"

WARNING = "#B4712B"
WARNING_HOVER = "#95591D"
WARNING_LIGHT = "#FFF3E4"
WARNING_BORDER = "#FFD4A1"

DANGER = "#C0453B"            # Destructive only
DANGER_HOVER = "#A2372F"
DANGER_LIGHT = "#FDF1F0"
DANGER_BORDER = "#F1C7C3"

INFO = "#B4712B"              # Status ink matches the accent ink
INFO_LIGHT = "#FFF3E4"
INFO_BORDER = "#FFD4A1"

NEUTRAL = "#7A6B5D"
NEUTRAL_LIGHT = "#F6F1EA"
NEUTRAL_BORDER = "#F0E5D8"

# Shape tokens
RADIUS_SM = 8
RADIUS = 12
RADIUS_LG = 16

# Spacing scale. Every gap in the app is one of these, so pages keep the same
# rhythm instead of each screen inventing its own padding.
SPACE_XS = 4
SPACE_SM = 8
SPACE = 12
SPACE_MD = 16
SPACE_LG = 24

# A page is easier to read when its text does not stretch the full width of a
# wide monitor, so the content column stops growing past this.
CONTENT_MAX_WIDTH = 1120

# Icon sizes
ICON_SM = 15
ICON = 17
ICON_LG = 20

# Typography. Tk silently falls back to a default face for a family the
# machine does not have, which is how the interface ended up in a different
# font on each desktop, so the first family actually installed is used.
_FONT_CANDIDATES = {
    "darwin": ["SF Pro Display", "SF Pro Text", "Helvetica Neue"],
    "win32": ["Segoe UI Variable Text", "Segoe UI"],
}
_LINUX_FONTS = ["Inter", "Cantarell", "Noto Sans", "Ubuntu", "DejaVu Sans",
                "Liberation Sans"]

FALLBACK_FONT = "Helvetica"
FONT_FAMILY = _FONT_CANDIDATES.get(sys.platform, _LINUX_FONTS)[0]

_resolved_family = None


def _family():
    """The best installed face, looked up once the Tk root exists."""
    global _resolved_family
    if _resolved_family:
        return _resolved_family

    wanted = _FONT_CANDIDATES.get(sys.platform, _LINUX_FONTS)
    try:
        import tkinter.font as tkfont

        installed = set(tkfont.families())
        for name in wanted:
            if name in installed:
                _resolved_family = name
                break
    except Exception:
        # No root yet, or no display: answer with the first choice and let a
        # later call resolve it properly.
        return wanted[0]

    _resolved_family = _resolved_family or FALLBACK_FONT
    return _resolved_family

# Text was small enough on a normal monitor that people leaned in to read it.
# One factor here lifts every label at once, so the type stays in proportion.
FONT_SCALE = 1.15


def configure_theme(ctk):
    """Sets CustomTkinter appearance mode and the shared widget palette.

    CustomTkinter ships a blue built-in theme, which left switches, sliders
    and scrollbars blue in an otherwise warm interface. Patching the theme
    table once here keeps every stock widget on the palette without passing
    colours at each call site.
    """
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    palette = ctk.ThemeManager.theme

    def paint(widget, **values):
        entry = palette.get(widget)
        if not entry:
            return
        for key, value in values.items():
            if key in entry:
                entry[key] = [value, value]

    paint("CTkSwitch",
          progress_color=ACCENT_DEEP,
          fg_color=NEUTRAL_BORDER,
          button_color=CARD_BG,
          button_hover_color=ACCENT_LIGHT,
          text_color=TEXT_PRIMARY)
    paint("CTkScrollbar",
          button_color=CARD_BORDER,
          button_hover_color=ACCENT)
    paint("CTkEntry",
          fg_color=CARD_BG,
          border_color=CARD_BORDER,
          text_color=TEXT_PRIMARY,
          placeholder_text_color=TEXT_MUTED)
    paint("CTkTextbox",
          fg_color=CARD_BG,
          border_color=CARD_BORDER,
          text_color=TEXT_PRIMARY)
    paint("CTkButton",
          fg_color=ACCENT,
          hover_color=ACCENT_HOVER,
          text_color=ON_ACCENT,
          border_color=CARD_BORDER)
    paint("CTkProgressBar",
          fg_color=NEUTRAL_LIGHT,
          progress_color=ACCENT_DEEP)
    paint("CTkSlider",
          button_color=ACCENT_DEEP,
          button_hover_color=ACCENT_DEEP_HOVER,
          progress_color=ACCENT,
          fg_color=NEUTRAL_BORDER)
    paint("CTkCheckBox",
          fg_color=ACCENT_DEEP,
          hover_color=ACCENT_DEEP_HOVER,
          border_color=CARD_BORDER,
          checkmark_color=CARD_BG,
          text_color=TEXT_PRIMARY)
    paint("CTkSegmentedButton",
          fg_color=NEUTRAL_LIGHT,
          selected_color=ACCENT,
          selected_hover_color=ACCENT_HOVER,
          unselected_color=CARD_BG,
          unselected_hover_color=CARD_HOVER,
          text_color=ON_ACCENT)
    paint("CTkOptionMenu",
          fg_color=ACCENT,
          button_color=ACCENT_HOVER,
          button_hover_color=ACCENT_DEEP,
          text_color=ON_ACCENT)
    paint("CTkComboBox",
          fg_color=CARD_BG,
          border_color=CARD_BORDER,
          button_color=ACCENT,
          button_hover_color=ACCENT_HOVER,
          text_color=TEXT_PRIMARY)


def font(size=14, weight="normal"):
    """Convenience font helper, scaled so the interface reads at arm's length."""
    return (_family(), max(9, round(size * FONT_SCALE)), weight)
