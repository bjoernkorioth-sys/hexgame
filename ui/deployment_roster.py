import pygame
import settings

class DeploymentRoster:
    def __init__(self):
        self.visible = False
        self.units = []
        self.selected_unit = None

    def set_units(self, units):
        self.units = units
        self.visible = len(units) > 0

    def draw(self, surface, layout):
        if not self.visible:
            return

        cfg = settings.DEPLOYMENT_ROSTER
        rect = layout.anchor("bottom_left", cfg["w"], cfg["h"])

        # --- Panel ---
        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        bg.fill(settings.UI_BG_COLOR)
        surface.blit(bg, rect.topleft)

        pygame.draw.rect(
            surface,
            settings.UI_BORDER_COLOR,
            rect,
            1,
            border_radius=layout.radius("medium")
        )

        # --- Content ---
        font = pygame.font.Font(None, int(18 * layout.scale))

        pad = int(cfg["padding"] * rect.width)
        y = rect.top + pad

        title = font.render("Deploy Units", True, settings.UI_TEXT_COLOR)
        surface.blit(title, (rect.left + pad, y))
        y += title.get_height() + pad

        slot_h = int(cfg["slot_h"] * rect.height)

        for unit in self.units:
            slot_rect = pygame.Rect(
                rect.left + pad,
                y,
                rect.width - pad * 2,
                slot_h
            )

            color = (80, 80, 120) if unit == self.selected_unit else (60, 60, 60)
            pygame.draw.rect(surface, color, slot_rect, border_radius=8)
            pygame.draw.rect(surface, settings.UI_BORDER_COLOR, slot_rect, 1, border_radius=8)

            txt = font.render(unit.unit_class.capitalize(), True, settings.UI_TEXT_COLOR)
            surface.blit(
                txt,
                (slot_rect.left + 8, slot_rect.centery - txt.get_height() // 2)
            )

            y += slot_h + int(6 * layout.scale)
