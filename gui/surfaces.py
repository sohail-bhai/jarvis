"""
Painted surfaces: soft shadows, rounded cards, hairline rules.

Tk gives you flat rectangles and a border. Everything that makes an interface
feel built - a card lifting off the page, a panel that fades rather than stops,
a rule that is genuinely one pixel of the right colour - has to be painted into
an image and shown behind the widget.

So `card_image()` renders a rounded card with a real blurred drop shadow at the
exact size a widget has, and the widget packs its content on top of that image.
Renders are cached by their exact arguments; a page rebuild asks for the same
handful of sizes over and over.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageDraw, ImageFilter
except Exception:  # pragma: no cover - Pillow is a hard dependency in practice
    Image = None

# Rendering at 2x keeps the corners clean on the way back down.
_SCALE = 2
_cache: dict[tuple, object] = {}


def _hex_to_rgb(value: str) -> tuple:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def available() -> bool:
    return Image is not None


def card_image(width: int, height: int, *, fill: str, page: str,
               radius: int = 12, border: str | None = None,
               shadow: float = 0.10, shadow_blur: int = 9,
               shadow_offset: int = 3):
    """A rounded card with a soft shadow, drawn onto the page colour.

    `page` is the colour behind the card. The shadow is composited against it
    here rather than left transparent, because Tk has no alpha channel to
    blend it with at display time.
    """
    if not available() or width < 4 or height < 4:
        return None

    key = ("card", width, height, fill, page, radius, border,
           round(shadow, 3), shadow_blur, shadow_offset)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    try:
        import customtkinter as ctk

        s = _SCALE
        w, h = width * s, height * s
        r = radius * s
        pad = (shadow_blur + shadow_offset + 2) * s

        canvas = Image.new("RGB", (w, h), _hex_to_rgb(page))

        # The shadow: the card's silhouette, blurred, pushed down a little.
        if shadow > 0:
            layer = Image.new("L", (w, h), 0)
            ImageDraw.Draw(layer).rounded_rectangle(
                [pad, pad + shadow_offset * s, w - pad, h - pad + shadow_offset * s],
                radius=r, fill=int(255 * shadow))
            layer = layer.filter(ImageFilter.GaussianBlur(shadow_blur * s / 2))
            # Shadows in a warm palette should be warm, not grey.
            canvas.paste(Image.new("RGB", (w, h), _hex_to_rgb("#2A241C")), (0, 0), layer)

        body = Image.new("RGB", (w, h), _hex_to_rgb(fill))
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([pad, pad, w - pad, h - pad],
                                               radius=r, fill=255)
        canvas.paste(body, (0, 0), mask)

        if border:
            ImageDraw.Draw(canvas).rounded_rectangle(
                [pad, pad, w - pad, h - pad], radius=r,
                outline=_hex_to_rgb(border), width=s)

        image = ctk.CTkImage(light_image=canvas, dark_image=canvas,
                             size=(width, height))
    except Exception:
        logger.debug("Could not paint a card surface", exc_info=True)
        return None

    _cache[key] = image
    return image


def gradient_image(width: int, height: int, top: str, bottom: str):
    """A vertical two-stop wash, for a panel that should fade rather than stop."""
    if not available() or width < 2 or height < 2:
        return None

    key = ("grad", width, height, top, bottom)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    try:
        import customtkinter as ctk

        start, end = _hex_to_rgb(top), _hex_to_rgb(bottom)
        strip = Image.new("RGB", (1, height))
        for y in range(height):
            t = y / max(height - 1, 1)
            strip.putpixel((0, y), tuple(
                round(start[i] + (end[i] - start[i]) * t) for i in range(3)))
        image = strip.resize((width, height), Image.NEAREST)
        rendered = ctk.CTkImage(light_image=image, dark_image=image,
                                size=(width, height))
    except Exception:
        logger.debug("Could not paint a gradient", exc_info=True)
        return None

    _cache[key] = rendered
    return rendered
