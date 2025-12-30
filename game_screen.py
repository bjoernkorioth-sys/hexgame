# game_screen.py
import pygame
import random
from collections import deque

from screen_base import Screen
from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    NUM_PLAYERS, UNITS_PER_PLAYER,
    BOTTOM_UI_HEIGHT, LOG_WIDTH
)
from camera import Camera
from hexmap import HexMap
from unit import Unit
from unit_catalog import UNIT_CATALOG


class GameScreen(Screen):
    def __init__(self, app, map_name, roster):
        super().__init__(app)
        
        self.screen = app.screen
        self.font = pygame.font.SysFont("arial", 24)

        # External choices
        self.map_name = map_name
        self.roster_data = roster

        # Core objects
        self.camera = Camera()
        self.hexmap = HexMap(self.screen, self.camera)
        self.load_chosen_map()
        self.center_camera_on_map()

        # --- State ---
        self.units = []
        self.player_units = []

        for player, list_of_names in self.roster_data.items():
            units = []
            for name in list_of_names:
                print("Adding", name, "to player", player)
                info = UNIT_CATALOG[name]
                u = Unit(q=0, r=0, owner=player, **info["stats"])
                u.cost = info["cost"]
                u.load_icon(info["icon"])
                units.append(u)
            self.player_units.append(units)

        self.selected_unit = None
        self.reachable_tiles = set()
        self.moving = False
        self.move_path = []
        self.move_timer = 0
        self.move_delay = 0.2
        self.move_highlight = None

        # Turn system
        self.current_player = 0
        self.placement_phase = True
        self.placed_units = [0] * NUM_PLAYERS
        self.player_moved = [False] * NUM_PLAYERS

        # Combat log
        self.combat_log = []
        self.MAX_LOG_LINES = 8

        # UI
        self.end_btn = pygame.Rect(WINDOW_WIDTH - 180, 40, 140, 50)

    # ---------------------------------------------------------
    # INITIALIZATION
    # ---------------------------------------------------------
    def center_camera_on_map(self):
        usable_w = WINDOW_WIDTH
        usable_h = WINDOW_HEIGHT - BOTTOM_UI_HEIGHT

        xs, ys = [], []
        for r in range(self.hexmap.height):
            for q in range(self.hexmap.width):
                x, y = self.hexmap.hex_to_pixel(q, r)
                xs.append(x)
                ys.append(y)

        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2

        self.camera.zoom = 1.0
        self.camera.x = (usable_w / 2) - cx
        self.camera.y = (usable_h / 2) - cy

    def in_spawn_zone(self, player, r):
        zone = 4
        if player == 0:
            return r < zone
        return r >= self.hexmap.height - zone
    # ---------------------------------------------------------
    # MAP LOADING
    # ---------------------------------------------------------
    def load_chosen_map(self):
        from settings import MAPS_DIR
        import os, json

        path = os.path.join(MAPS_DIR, self.map_name)
        if not os.path.isfile(path):
            print(f"Map file not found: {path}")
            return

        with open(path, "r") as fh:
            data = json.load(fh)

        self.hexmap.width = data.get("width", self.hexmap.width)
        self.hexmap.height = data.get("height", self.hexmap.height)

        for key, info in data.get("tiles", {}).items():
            q, r = map(int, key.split(","))
            self.hexmap.terrain[(q, r)] = info

    # ---------------------------------------------------------
    # INPUT
    # ---------------------------------------------------------
    def handle_event(self, ev):
        #print("GameScreen.handle_event:", ev)
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                from menu_screen import MenuScreen
                self.next_screen = MenuScreen(self.app)
                self.done = True

        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            print("EVENT:", ev)
            self.handle_left_click(ev)
               

    def handle_left_click(self, ev):
        mx, my = getattr(ev, "pos", pygame.mouse.get_pos())
        print("click screen coords:", mx, my)
        wx, wy = self.camera.screen_to_world((mx, my))
        print("world coords:", wx, wy)
        q, r = self.hexmap.pixel_to_hex(wx, wy)
        print("computed hex:", (q, r), "inside:", self.hexmap.is_inside_grid(q, r),
            "in_spawn:", self.in_spawn_zone(self.current_player, r))
        print("placed_units:", self.placed_units, "player_units_len:", len(self.player_units[self.current_player]))

        if not self.hexmap.is_inside_grid(q, r):
            return

        tile = (q, r)
        clicked_unit = next(
                (u for u in self.units if (u.q, u.r) == tile),
                None
        )

        # Placement
        if self.placement_phase:
            if self.placed_units[self.current_player] < len(self.player_units[self.current_player]):
                if self.in_spawn_zone(self.current_player, r):
                    if not any((u.q, u.r) == tile for u in self.units):
                        u = self.player_units[self.current_player][self.placed_units[self.current_player]]
                        u.q, u.r = q, r
                        self.units.append(u)
                        self.placed_units[self.current_player] += 1
            return
        
        if self.placement_phase:
            if self.placed_units[self.current_player] >= len(self.player_units[self.current_player]):
                print("No remaining units to place for player", self.current_player)
                return
            if not self.in_spawn_zone(self.current_player, r):
                print("Tile not in spawn zone:", (q, r))
                return
            if any((u.q, u.r) == tile for u in self.units):
                print("Tile occupied:", tile)
                return
            # place unit:
            print("Placing unit for player", self.current_player, "at", tile)


        # Selection
        if clicked_unit and clicked_unit.owner == self.current_player:
            self.selected_unit = clicked_unit
            self.hexmap.selected_hex = tile
            blocked = {(u.q, u.r) for u in self.units if u is not self.selected_unit}
            self.reachable_tiles = self.hexmap.get_reachable_tiles(
                tile, clicked_unit.move_range, blocked
            )

        elif self.selected_unit and tile in self.reachable_tiles:
            if self.selected_unit.action_points > 0:
                blocked = {(u.q, u.r) for u in self.units if u is not self.selected_unit}
                path = self.bfs_path(
                    (self.selected_unit.q, self.selected_unit.r),
                    tile,
                    blocked
                )
                if len(path) > 1:
                    self.move_path = path[1:]
                    self.moving = True
                    self.move_timer = 0
                    self.selected_unit.action_points -= 1

        elif self.selected_unit and clicked_unit and clicked_unit.owner != self.current_player:
            if self.selected_unit.action_points > 0:
                if self.attack(self.selected_unit, clicked_unit):
                    self.selected_unit.action_points -= 1
                    self.auto_end_turn()

        else:
            self.selected_unit = None
            self.hexmap.selected_hex = None
            self.reachable_tiles.clear()

        # Movement animation
        if self.moving and self.selected_unit and self.move_path:
            if self.move_timer >= self.move_delay:
                self.move_timer = 0
                step = self.move_path.pop(0)
                self.selected_unit.q, self.selected_unit.r = step

                if not self.move_path:
                    self.moving = False
                    self.reachable_tiles.clear()
                    self.auto_end_turn()

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------
    def update(self, dt):
        self.move_timer += dt

        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        

        self.camera.handle_input(events, keys)


    # ---------------------------------------------------------
    # DRAW
    # ---------------------------------------------------------
    def draw(self, surface):
        surface.fill((30, 30, 30))
        self.hexmap.draw()
        
        if self.placement_phase:
            self.draw_roster_panel()
            for r in range(self.hexmap.height):
                for q in range(self.hexmap.width):
                    if self.in_spawn_zone(self.current_player, r):
                        self.hexmap.draw_highlight(
                            q, r,
                            color=(80, 120, 200, 80)
                        )

        self.draw_ui()

    def draw_ui(self):
        mx, my = pygame.mouse.get_pos()
        hover = self.end_btn.collidepoint((mx, my))
        color = (90, 150, 200) if hover else (70, 130, 180)

        pygame.draw.rect(self.screen, color, self.end_btn, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), self.end_btn, 2, border_radius=8)

        txt = self.font.render("End Turn", True, (255, 255, 255))
        self.screen.blit(txt, (self.end_btn.x + 20, self.end_btn.y + 10))

        ui_y = WINDOW_HEIGHT - BOTTOM_UI_HEIGHT
        pygame.draw.rect(self.screen, (25, 25, 40), (0, ui_y, WINDOW_WIDTH, BOTTOM_UI_HEIGHT))
        pygame.draw.rect(self.screen, (100, 100, 150),
                         (10, ui_y + 10, LOG_WIDTH, BOTTOM_UI_HEIGHT - 20), 2)

        for i, line in enumerate(self.combat_log[:self.MAX_LOG_LINES]):
            txt = self.font.render(line, True, (220, 220, 220))
            self.screen.blit(txt, (20, ui_y + 20 + i * 22))

    def draw_roster_panel(self):
        panel_x = 20
        panel_y = 80
        panel_w = 260
        panel_h = 300

        pygame.draw.rect(self.screen, (35, 35, 50),
                        (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(self.screen, (120, 120, 160),
                        (panel_x, panel_y, panel_w, panel_h), 2)

        title = self.font.render(
            f"Player {self.current_player + 1} Roster",
            True, (255, 255, 255)
        )
        self.screen.blit(title, (panel_x + 10, panel_y + 10))

        y = panel_y + 50
        for i, unit in enumerate(self.player_units[self.current_player]):
            color = (200, 200, 200)
            if i == self.placed_units[self.current_player]:
                color = (255, 255, 120)  # next unit to place

            txt = self.font.render(unit.unit_class, True, color)
            self.screen.blit(txt, (panel_x + 20, y))
            y += 28
