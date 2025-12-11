# game_setup.py
import pygame
import os
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS
from game import Game

pygame.init()
font = pygame.font.SysFont("arial", 28)
smallfont = pygame.font.SysFont("arial", 22)

MAP_FOLDER = "maps"   # folder where maps or previews are stored

class GameSetupScreen:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()

        # --- Selection state ---
        self.maps = self.load_maps()
        self.map_index = 0

        # Temporary placeholder roster
        self.roster = {
            0: ["soldier", "soldier"],
            1: ["soldier", "soldier"]
        }

        self.running = True

    def load_maps(self):
        """
        Return list of map names (for now just placeholders).
        In your engine this will load your .json or .map files.
        """
        if not os.path.isdir(MAP_FOLDER):
            return ["Default"]
        maps = []
        for f in os.listdir(MAP_FOLDER):
            if f.endswith(".png") or f.endswith(".json"):
                maps.append(f)
        return maps if maps else ["Default"]

    def draw_preview(self, surface, x, y):
        """
        Display map preview.
        For now, just a gray rectangle with the name.
        Replace with image loading later.
        """
        pygame.draw.rect(surface, (70, 70, 90), (x, y, 300, 300))
        txt = font.render(self.maps[self.map_index], True, (255, 255, 255))
        surface.blit(txt, (x + 20, y + 20))

    def draw(self):
        self.screen.fill((25,25,35))

        title = font.render("Quick Game Setup", True, (255,255,255))
        self.screen.blit(title, (40, 30))

        # --- Map selection section ---
        self.draw_preview(self.screen, 40, 100)

        left_btn  = smallfont.render("< Prev", True, (255,255,255))
        right_btn = smallfont.render("Next >", True, (255,255,255))

        self.screen.blit(left_btn,  (40, 420))
        self.screen.blit(right_btn, (160, 420))

        # --- Roster section ---
        roster_title = font.render("Roster per Player", True, (255,255,255))
        self.screen.blit(roster_title, (420, 100))

        y = 150
        for player, units in self.roster.items():
            line = f"Player {player+1}: {', '.join(units)}"
            self.screen.blit(smallfont.render(line, True, (200,200,200)), (420, y))
            y += 40

        # --- Start Game Button ---
        start_rect = pygame.Rect(420, 420, 240, 60)
        pygame.draw.rect(self.screen, (100,160,100), start_rect)
        pygame.draw.rect(self.screen, (255,255,255), start_rect, 2)

        txt = font.render("Start Game", True, (255,255,255))
        self.screen.blit(txt, (start_rect.x + 25, start_rect.y + 10))

        return start_rect

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False

                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()

                    # Map scroll buttons
                    if 40 <= mx <= 120 and 420 <= my <= 450:
                        self.map_index = (self.map_index - 1) % len(self.maps)

                    if 160 <= mx <= 240 and 420 <= my <= 450:
                        self.map_index = (self.map_index + 1) % len(self.maps)

                    # Start game
                    start_rect = pygame.Rect(420, 420, 240, 60)
                    if start_rect.collidepoint((mx, my)):
                        chosen_map = self.maps[self.map_index]
                        game = Game(self.screen, chosen_map, self.roster)
                        game.run()
                        return

            start_rect = self.draw()
            pygame.display.flip()
