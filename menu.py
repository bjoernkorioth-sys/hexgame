# menu.py
import pygame
import sys
from camera import Camera
from map_editor import MapEditor
from settings import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    SETUP_WINDOW_WIDTH,
    SETUP_WINDOW_HEIGHT,
    FPS
)

pygame.init()
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 28)


def draw_menu(surface, selected_idx):
    surface.fill((20, 20, 30))
    title = pygame.font.SysFont("arial", 48).render(
        "HexGame", True, (240, 240, 240)
    )
    surface.blit(title, (40, 40))

    items = ["Play Game", "Map Editor", "Exit"]
    y = 140
    for i, it in enumerate(items):
        color = (255, 255, 255) if i == selected_idx else (160, 160, 160)
        txt = font.render(it, True, color)
        surface.blit(txt, (60, y))
        y += 60


def main():
    # 🔑 ONE place that owns the screen
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("HexGame")

    selected = 0

    while True:
        clock.tick(FPS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    selected = (selected - 1) % 3
                elif ev.key == pygame.K_DOWN:
                    selected = (selected + 1) % 3
                elif ev.key == pygame.K_RETURN:

                    # ---------------- PLAY GAME ----------------
                    if selected == 0:
                        screen = pygame.display.set_mode(
                            (SETUP_WINDOW_WIDTH, SETUP_WINDOW_HEIGHT)
                        )

                        from game_setup import GameSetupScreen
                        setup = GameSetupScreen(screen)
                        setup.run()

                        # restore menu resolution
                        screen = pygame.display.set_mode(
                            (WINDOW_WIDTH, WINDOW_HEIGHT)
                        )

                    # ---------------- MAP EDITOR ----------------
                    elif selected == 1:
                        cam = Camera()
                        editor = MapEditor(screen, cam)
                        editor.run()

                    # ---------------- EXIT ----------------
                    elif selected == 2:
                        pygame.quit()
                        sys.exit()

        draw_menu(screen, selected)
        pygame.display.flip()


if __name__ == "__main__":
    main()
