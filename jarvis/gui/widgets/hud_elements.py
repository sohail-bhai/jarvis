import math
import random
import tkinter as tk
import customtkinter as ctk
from gui import theme

class GlowingOrb(ctk.CTkCanvas):
    def __init__(self, master, size=300, **kwargs):
        super().__init__(
            master, 
            width=size, 
            height=size, 
            bg=theme.BACKGROUND, 
            highlightthickness=0, 
            **kwargs
        )
        self.size = size
        self.center = size // 2
        self.radius = int(size * 0.25)
        self.breathing_offset = 0
        self.breathing_dir = 1
        
        # Start animation loop
        self.after(50, self.animate_orb)
        
    def animate_orb(self):
        self.delete("all")
        
        # Breathing effect
        self.breathing_offset += 0.5 * self.breathing_dir
        if self.breathing_offset > 8 or self.breathing_offset < 0:
            self.breathing_dir *= -1
            
        current_radius = self.radius + self.breathing_offset
        
        # Outer faint rings
        self.create_oval(
            self.center - current_radius - 20, self.center - current_radius - 20,
            self.center + current_radius + 20, self.center + current_radius + 20,
            outline=theme.BORDER, width=1
        )
        
        self.create_oval(
            self.center - current_radius - 40, self.center - current_radius - 40,
            self.center + current_radius + 40, self.center + current_radius + 40,
            outline=theme.SURFACE_ALT, width=2
        )
        
        # Inner glowing core (simulated with multiple ovals)
        for i in range(5, 0, -1):
            alpha_color = self._fade_color(theme.ACCENT, i * 20)
            r = current_radius + (i * 2)
            self.create_oval(
                self.center - r, self.center - r,
                self.center + r, self.center + r,
                outline=alpha_color, width=2
            )
            
        # Core solid
        self.create_oval(
            self.center - current_radius, self.center - current_radius,
            self.center + current_radius, self.center + current_radius,
            fill=theme.ACCENT_MUTED, outline=theme.ACCENT, width=3
        )
        
        # Triangle in the middle
        tri_size = current_radius * 0.5
        points = [
            self.center - tri_size, self.center - tri_size * 0.5,
            self.center + tri_size, self.center - tri_size * 0.5,
            self.center, self.center + tri_size * 0.8
        ]
        self.create_polygon(points, fill="", outline=theme.ACCENT, width=3)
        
        self.after(50, self.animate_orb)
        
    def _fade_color(self, hex_color, fade_amount):
        # Extremely basic color darkening for a pseudo-glow
        hex_color = hex_color.lstrip('#')
        try:
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            rgb = tuple(max(0, c - fade_amount) for c in rgb)
            return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
        except:
            return hex_color


class AudioWaveform(ctk.CTkCanvas):
    def __init__(self, master, width=400, height=60, **kwargs):
        super().__init__(
            master, 
            width=width, 
            height=height, 
            bg=theme.BACKGROUND, 
            highlightthickness=0, 
            **kwargs
        )
        self.w = width
        self.h = height
        self.bars = 30
        self.bar_width = (width / self.bars) * 0.5
        self.spacing = (width / self.bars) * 0.5
        self.is_listening = False
        
        self.after(100, self.animate_wave)
        
    def set_listening(self, active):
        self.is_listening = active
        
    def animate_wave(self):
        self.delete("all")
        
        center_y = self.h / 2
        
        for i in range(self.bars):
            x = i * (self.bar_width + self.spacing)
            
            if self.is_listening:
                # Random height for active waveform
                height = random.uniform(10, self.h * 0.9)
            else:
                # Flat line for idle
                height = 4
                
            y1 = center_y - (height / 2)
            y2 = center_y + (height / 2)
            
            self.create_rectangle(
                x, y1, x + self.bar_width, y2,
                fill=theme.ACCENT if self.is_listening else theme.BORDER,
                outline=""
            )
            
        self.after(100, self.animate_wave)
