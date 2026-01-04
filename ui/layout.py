import pygame
import settings

class UIAnchorLayout:
    def __init__(self, screen_size):
        self.w, self.h = screen_size
        self.scale = settings.ui_scale(self.w, self.h)
        self.padding = int(self.w * settings.UI_PADDING_RATIO)

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
