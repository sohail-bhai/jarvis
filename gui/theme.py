"""Shared design tokens for the JARVIS desktop UI.

The palette is deliberately light, calm and neutral. Colour is used to carry
meaning (success, attention, destructive) rather than for decoration, so the
app reads like a productivity tool instead of a control panel.

Token names are kept stable so widgets can be restyled from one place.
"""

import platform

# Surfaces ------------------------------------------------------------------
BACKGROUND = "#F6F7F9"      # app canvas
SURFACE = "#FFFFFF"         # cards and panels
SURFACE_ALT = "#F1F3F6"     # insets, hovered rows, input wells
BORDER = "#E4E7EC"          # hairline separators
BORDER_STRONG = "#D3D8E0"   # emphasised separators

# Text ----------------------------------------------------------------------
TEXT = "#1F2430"            # primary charcoal
TEXT_MUTED = "#6B7280"      # secondary
TEXT_FAINT = "#9AA1AC"      # timestamps, meta

# Meaning -------------------------------------------------------------------
ACCENT = "#4F5BD5"          # restrained indigo
ACCENT_HOVER = "#4450C0"
ACCENT_SOFT = "#ECEEFB"     # tinted background for selected nav
SUCCESS = "#3E8E5A"
SUCCESS_SOFT = "#EAF3ED"
WARNING = "#B07813"
WARNING_SOFT = "#FBF3E4"
ERROR = "#C0483F"           # destructive only
ERROR_SOFT = "#FAECEB"

# Legacy alias: older widgets referenced a muted accent for button fills.
ACCENT_MUTED = ACCENT_SOFT

# Geometry ------------------------------------------------------------------
RADIUS_SM = 10
RADIUS = 14
RADIUS_LG = 16

PAD_XS = 4
PAD_SM = 8
PAD = 16
PAD_LG = 24


def _default_font_family():
    """Pick a clean system sans-serif that actually exists on this platform."""
    system = platform.system()
    if system == "Windows":
        return "Segoe UI"
    if system == "Darwin":
        return "Helvetica Neue"
    return "DejaVu Sans"


FONT_FAMILY = _default_font_family()


def configure_theme(ctk):
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")


def font(size=14, weight="normal"):
    return (FONT_FAMILY, size, weight)
