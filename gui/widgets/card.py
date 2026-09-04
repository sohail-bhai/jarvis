"""
A card that paints its own surface.

CustomTkinter can draw a rounded rectangle with a border, and that is all. It
has no shadow, so every card in a stock CTk app sits flat on the page and the
interface reads as a wireframe of itself.

This widget paints a rounded card with a soft warm shadow at whatever size it
happens to be, puts that image behind itself, and gives callers `.body` to pack
their content into. It repaints only when its size actually changes, so a
window drag does not re-render on every pixel.
"""
from __future__ import annotations

import customtkinter as ctk

from gui import surfaces, theme


class Card(ctk.CTkFrame):
    def __init__(self, parent, *, page: str | None = None, fill: str | None = None,
                 radius: int | None = None, elevation=None,
                 border: str | None = None, **kwargs):
        page = page or theme.MAIN_BG
        super().__init__(parent, fg_color=page, corner_radius=0, **kwargs)

        self._page = page
        self._fill = fill or theme.CARD_BG
        self._radius = theme.RADIUS_CARD if radius is None else radius
        self._border = border
        opacity, blur, offset = elevation or theme.ELEVATION_LOW
        self._shadow = (opacity, blur, offset)
        self._size = (0, 0)

        # How far the shadow spreads: content must stay inside it.
        self._inset = blur + offset + 2 if opacity else 0

        self._backdrop = ctk.CTkLabel(self, text="", image=None)
        self._backdrop.place(x=0, y=0, relwidth=1, relheight=1)

        # Packed rather than placed: CustomTkinter refuses width/height in
        # place(), and padding is how the content stays clear of the shadow.
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True,
                       padx=self._inset, pady=self._inset)

        self.bind("<Configure>", self._on_configure)

    @property
    def inset(self) -> int:
        """Pixels of shadow around the card, for callers aligning to its edge."""
        return self._inset

    def _on_configure(self, event):
        if (event.width, event.height) == self._size:
            return
        self._size = (event.width, event.height)
        self._repaint(event.width, event.height)

    def _repaint(self, width: int, height: int):
        opacity, blur, offset = self._shadow
        image = surfaces.card_image(
            width, height,
            fill=self._fill, page=self._page, radius=self._radius,
            border=self._border, shadow=opacity, shadow_blur=blur,
            shadow_offset=offset)

        if image is None:
            # No Pillow: fall back to a plain filled frame so the card is still
            # a card, just without the lift.
            self.configure(fg_color=self._fill, corner_radius=self._radius)
            return

        self._image = image          # Tk drops an image with no reference.
        self._backdrop.configure(image=image)
