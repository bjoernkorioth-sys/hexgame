import pygame
import os
from settings import (
    SETUP_MAP_PREVIEW_SIZE,
    SETUP_UNIT_LIST_WIDTH,
    SETUP_ROSTER_WIDTH,
    SETUP_PANEL_GAP,
    SETUP_TOP_MARGIN,
    FPS
)
from game import Game
from unit_catalog import UNIT_CATALOG

pygame.init()
font = pygame.font.SysFont("arial", 28)
smallfont = pygame.font.SysFont("arial", 22)

MAP_FOLDER = "maps"


class GameSetupScreen:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()

        # Maps
        self.maps = self.load_maps()
        self.map_index = 0

        # Drafting
        self.budget = {0: 200, 1: 200}
        self.selected_player = 0
        self.player_rosters = {0: [], 1: []}
        self.unit_list = list(UNIT_CATALOG.keys())
        self.unit_card_scroll = 0

        self.running = True

    # --------------------------------------------------------------

    def load_maps(self):
        if not os.path.isdir(MAP_FOLDER):
            return ["Default"]

        maps = [
            f for f in os.listdir(MAP_FOLDER)
            if f.endswith(".png") or f.endswith(".json")
        ]
        return maps if maps else ["Default"]

    # --------------------------------------------------------------

    def draw_preview(self, surface, x, y):
        map_file = self.maps[self.map_index]
        base, ext = os.path.splitext(map_file)
        img_path = os.path.join(MAP_FOLDER, base + ".png")

        preview_area = pygame.Rect(x, y, 300, 300)
        pygame.draw.rect(surface, (70, 70, 90), preview_area)

        if os.path.isfile(img_path):
            img = pygame.image.load(img_path).convert()
            img = pygame.transform.scale(img, (300, 300))
            surface.blit(img, preview_area)

        txt = font.render(base, True, (255, 255, 255))
        surface.blit(txt, (x + 10, y + 10))

    # --------------------------------------------------------------

    def draw(self):
        self.screen.fill((25, 25, 35))

        map_x = 40
        map_y = SETUP_TOP_MARGIN

        unit_x = map_x + SETUP_MAP_PREVIEW_SIZE + SETUP_PANEL_GAP
        unit_y = SETUP_TOP_MARGIN

        roster_x = unit_x + SETUP_UNIT_LIST_WIDTH + SETUP_PANEL_GAP
        roster_y = SETUP_TOP_MARGIN

        draft_area = pygame.Rect(unit_x, unit_y, SETUP_UNIT_LIST_WIDTH, 300)
        pygame.draw.rect(self.screen, (35, 35, 50), draft_area)

        pygame.draw.rect(
            self.screen,
            (35, 35, 50),
            (roster_x, roster_y, SETUP_ROSTER_WIDTH, 300)
        )

        # Title
        title = font.render("Quick Game Setup", True, (255, 255, 255))
        self.screen.blit(title, (40, 30))

        # ----------------------
        # MAP PREVIEW
        # ----------------------
        self.draw_preview(self.screen, 40, 100)

        prev_btn = smallfont.render("< Prev", True, (255, 255, 255))
        next_btn = smallfont.render("Next >", True, (255, 255, 255))

        prev_rect = pygame.Rect(40, 420, 100, 40)
        next_rect = pygame.Rect(160, 420, 100, 40)

        self.screen.blit(prev_btn, prev_rect)
        self.screen.blit(next_btn, next_rect)

        # ----------------------
        # UNIT SELECTION LIST
        # ----------------------
        pygame.draw.rect(self.screen, (35, 35, 50), draft_area)

        y = 110 - self.unit_card_scroll
        card_rects = []

        for name in self.unit_list:
            card = pygame.Rect(410, y, 480, 70)
            pygame.draw.rect(self.screen, (60, 60, 80), card)

            info = UNIT_CATALOG[name]
            txt = smallfont.render(f"{name.capitalize()} — {info['cost']} pts", True, (255, 255, 255))
            self.screen.blit(txt, (420, y + 10))

            try:
                icon = pygame.image.load(info["icon"]).convert_alpha()
                icon = pygame.transform.scale(icon, (48, 48))
                self.screen.blit(icon, (410 + 420, y + 10))
            except:
                pass

            card_rects.append((name, card))
            y += 80

        # ----------------------
        # PLAYER SWITCH
        # ----------------------
        p1_btn = pygame.Rect(400, 420, 150, 40)
        p2_btn = pygame.Rect(560, 420, 150, 40)

        pygame.draw.rect(self.screen, (120, 80, 80) if self.selected_player == 0 else (70, 70, 90), p1_btn)
        pygame.draw.rect(self.screen, (80, 120, 80) if self.selected_player == 1 else (70, 70, 90), p2_btn)

        self.screen.blit(smallfont.render("Player 1", True, (255, 255, 255)), (p1_btn.x + 20, p1_btn.y + 8))
        self.screen.blit(smallfont.render("Player 2", True, (255, 255, 255)), (p2_btn.x + 20, p2_btn.y + 8))

        # ----------------------
        # ROSTER PREVIEW
        # ----------------------
        roster_y = 100
        roster_w = 300
        roster_h = 300

        pygame.draw.rect(self.screen, (35, 35, 50), (roster_x, roster_y, roster_w, roster_h))
        pygame.draw.rect(self.screen, (120, 120, 160), (roster_x, roster_y, roster_w, roster_h), 2)

        title = smallfont.render(f"Player {self.selected_player + 1} Roster", True, (255,255,255))
        self.screen.blit(title, (roster_x + 10, roster_y + 10))

        budget_txt = smallfont.render(
            f"Budget: {self.budget[self.selected_player]} pts",
            True, (200, 200, 200)
        )
        self.screen.blit(budget_txt, (roster_x + 10, roster_y + 35))

        roster_rects = []
        y = roster_y + 70

        for idx, unit_name in enumerate(self.player_rosters[self.selected_player]):
            info = UNIT_CATALOG[unit_name]

            entry_rect = pygame.Rect(roster_x + 10, y, roster_w - 20, 40)
            pygame.draw.rect(self.screen, (60, 60, 80), entry_rect)

            txt = smallfont.render(
                f"{unit_name.capitalize()} (-{info['cost']})",
                True, (255,255,255)
            )
            self.screen.blit(txt, (entry_rect.x + 45, entry_rect.y + 10))

            # icon
            try:
                icon = pygame.image.load(info["icon"]).convert_alpha()
                icon = pygame.transform.scale(icon, (32, 32))
                self.screen.blit(icon, (entry_rect.x + 5, entry_rect.y + 4))
            except:
                pass

            roster_rects.append((idx, unit_name, entry_rect))
            y += 45

        # ----------------------
        # START BUTTON
        # ----------------------
        start_btn = pygame.Rect(720, 420, 180, 50)
        pygame.draw.rect(self.screen, (100, 160, 100), start_btn)
        pygame.draw.rect(self.screen, (255, 255, 255), start_btn, 2)
        self.screen.blit(font.render("Start", True, (255, 255, 255)),
                         (start_btn.x + 40, start_btn.y + 5))

        return {
            "prev": prev_rect,
            "next": next_rect,
            "cards": card_rects,
            "p1": p1_btn,
            "p2": p2_btn,
            "start": start_btn,
            "roster": roster_rects
        }

    # --------------------------------------------------------------

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)

            rects = self.draw()

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False

                if ev.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()

                    # Scroll
                    if ev.button == 4:
                        self.unit_card_scroll = max(0, self.unit_card_scroll - 20)
                    if ev.button == 5:
                        self.unit_card_scroll += 20

                    # Remove unit from roster
                    for idx, name, rect in rects["roster"]:
                        if rect.collidepoint((mx, my)):
                            cost = UNIT_CATALOG[name]["cost"]
                            self.player_rosters[self.selected_player].pop(idx)
                            self.budget[self.selected_player] += cost
                            break

                    # Unit card clicks
                    for name, rect in rects["cards"]:
                        if rect.collidepoint((mx, my)):
                            cost = UNIT_CATALOG[name]["cost"]
                            if self.budget[self.selected_player] >= cost:
                                self.budget[self.selected_player] -= cost
                                self.player_rosters[self.selected_player].append(name)
                            break

                    # Map buttons
                    if rects["prev"].collidepoint((mx, my)):
                        self.map_index = (self.map_index - 1) % len(self.maps)
                    if rects["next"].collidepoint((mx, my)):
                        self.map_index = (self.map_index + 1) % len(self.maps)

                    # Player switch
                    if rects["p1"].collidepoint((mx, my)):
                        self.selected_player = 0
                    if rects["p2"].collidepoint((mx, my)):
                        self.selected_player = 1

                    # Start game
                    if rects["start"].collidepoint((mx, my)):
                        chosen_map = self.maps[self.map_index]
                        game = Game(self.screen, chosen_map, self.player_rosters)
                        game.run()
                        return

            pygame.display.flip()
