# menu_screen.py
from screen_base import Screen
import pygame

class MenuScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.selected = 0
        self.font = pygame.font.SysFont("arial", 28)

    def handle_event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_UP:
                self.selected = (self.selected - 1) % 3
            elif ev.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % 3
            elif ev.key == pygame.K_RETURN:
                if self.selected == 0:
                    from game_setup_screen import GameSetupScreen
                    self.next_screen = GameSetupScreen(self.app)
                    self.done = True
                elif self.selected == 1:
                    from map_editor_screen import MapEditorScreen
                    self.next_screen = MapEditorScreen(self.app)
                    self.done = True
                elif self.selected == 2:
                    self.app.running = False

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill((20, 20, 30))

        # Title
        title = pygame.font.SysFont("arial", 48).render(
            "HexGame", True, (240, 240, 240)
        )
        surface.blit(title, (40, 40))

        # Menu entries
        items = ["Play Game", "Map Editor", "Exit"]
        y = 140

        for i, text in enumerate(items):
            color = (255, 255, 255) if i == self.selected else (160, 160, 160)
            label = self.font.render(text, True, color)
            surface.blit(label, (60, y))
            y += 60

