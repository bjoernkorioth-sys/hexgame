import pygame
import settings

class UnitHUD:
    def __init__(self):
        self.visible = False
        self.unit = None

    def set_unit(self, unit):
        self.unit = unit
        self.visible = unit is not None

    def draw(self, surface, layout):
        if not self.visible or not self.unit:
            return

        cfg = settings.UNIT_HUD
        rect = layout.anchor(
            "top_right",
            cfg["w"],
            cfg["h"]
        )

        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        bg.fill(settings.UI_BG_COLOR)
        surface.blit(bg, rect.topleft)

        pygame.draw.rect(surface, settings.UI_BORDER_COLOR, rect, 1)

        # ---- TEXT ----
        font = pygame.font.Font(None, int(18 * layout.scale))

        lines = [
            self.unit.unit_class.capitalize(),
            f"HP: {self.unit.hp}",
            f"AP: {self.unit.action_points}/{self.unit.max_action_points}",
            f"Move: {self.unit.move_range}",
        ]

        y = rect.top + 8
        for line in lines:
            txt = font.render(line, True, settings.UI_TEXT_COLOR)
            surface.blit(txt, (rect.left + 8, y))
            y += txt.get_height() + 4
