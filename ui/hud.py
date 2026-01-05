import pygame
import settings


class UnitHUD:
    def __init__(self):
        pass

    def draw(self, surface, unit, rect):
        if not unit:
            return

        # --- Background ---
        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        bg.fill(settings.UI_BG_COLOR)
        surface.blit(bg, rect.topleft)

        pygame.draw.rect(
            surface,
            settings.UI_BORDER_COLOR,
            rect,
            2,
            border_radius=settings.UI_RADII.get("medium", 8),
        )

        # --- Font ---
        scale = settings.ui_scale(*surface.get_size())
        font = pygame.font.Font(None, int(18 * scale))
        title_font = pygame.font.Font(None, int(22 * scale))

        padding = int(10 * scale)
        y = rect.top + padding

        # --- Unit name ---
        title = title_font.render(
            unit.unit_class.capitalize(),
            True,
            settings.UI_TEXT_COLOR,
        )
        surface.blit(title, (rect.left + padding, y))
        y += title.get_height() + padding

        # --- Stats ---
        lines = [
            f"HP: {unit.hp}",
            f"AP: {unit.action_points}/{unit.max_action_points}",
            f"Move: {unit.move_range}",
        ]

        for line in lines:
            txt = font.render(line, True, settings.UI_TEXT_COLOR)
            surface.blit(txt, (rect.left + padding, y))
            y += txt.get_height() + int(4 * scale)
