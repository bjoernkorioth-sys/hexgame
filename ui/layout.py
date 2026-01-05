import pygame
import settings

class UIAnchorLayout:
    def __init__(self, screen_size):
        self.elements = {}
        self.update(screen_size)

    def anchor(self, position, w_ratio, h_ratio, x_offset=0, y_offset=0):
        width  = int(self.w * w_ratio)
        height = int(self.h * h_ratio)

        if position == "top_left":
            x = self.padding
            y = self.padding

        elif position == "top_right":
            x = self.w - width - self.padding
            y = self.padding

        elif position == "bottom_left":
            x = self.padding
            y = self.h - height - self.padding

        elif position == "bottom_right":
            x = self.w - width - self.padding
            y = self.h - height - self.padding

        else:
            raise ValueError(f"Unknown anchor: {position}")

        return pygame.Rect(
            x + x_offset,
            y + y_offset,
            width,
            height
        )
    
    def update(self, screen_size):
        self.w, self.h = screen_size
        self.scale = settings.ui_scale(self.w, self.h)
        self.padding = int(self.w * settings.UI_PADDING_RATIO)

    def define(self, key, *, anchor, w, h, x_offset=0, y_offset=0):
        rect = self.anchor(anchor, w, h, x_offset, y_offset)
        self.elements[key] = rect
        return rect

    def get(self, key):
        return self.elements[key]
    
    def radius(self, size="small"):
        base = settings.UI_RADII.get(size, 8)
        return max(1, int(base * self.scale))
