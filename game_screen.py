# game_screen.py
import pygame
import random
from collections import deque

from screen_base import Screen
from settings import *
from camera import Camera
from hexmap import HexMap
from unit import Unit
from unit_catalog import UNIT_CATALOG
from turn_manager import TurnManager
from ui.layout import UIAnchorLayout
from ui.hud import UnitHUD

class GameScreen(Screen):
    def __init__(self, app, map_name, roster):
        super().__init__(app)
        
        self.screen = app.screen
        self.font = pygame.font.SysFont("arial", 24)
        self.ui = UIAnchorLayout(self.screen.get_size())
        self.unit_hud = UnitHUD()

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
                u = Unit(q=0, r=0, owner=player,unit_class=name, **info["stats"])
                u.cost = info["cost"]
                u.load_icon(info["icon"])
                units.append(u)
            self.player_units.append(units)

        self.selected_unit = None
        self.reachable_tiles = set()
        self.attackable_enemies = set()
        self.moving = False
        self.move_path = []
        self.move_timer = 0
        self.move_delay = 0.2
        self.move_highlight = None

        # Turn system
        units_per_player = [len(units) for units in self.player_units]
        self.turns = TurnManager(NUM_PLAYERS, units_per_player)
        self.player_moved = [False] * NUM_PLAYERS

        # Combat log
        self.combat_log = []
        self.MAX_LOG_LINES = 8

        self.ui.define(
            "end_turn",
            anchor="bottom_right",
            w=END_TURN_BUTTON["w"],
            h=END_TURN_BUTTON["h"]
        )

        self.ui.define(
            "unit_hud",
            anchor="top_right",
            w=UNIT_HUD["w"],
            h=UNIT_HUD["h"]
        )

        self.ui.define(
            "turn_label",
            anchor="top_left",
            w=TURN_INDICATOR["w"],
            h=TURN_INDICATOR["h"]
        )


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
            if self.handle_ui_click(ev.pos):
                return
            self.handle_world_click(ev.pos)

        elif ev.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode(ev.size, pygame.RESIZABLE)
            self.ui.update(ev.size)

            # redefine UI elements
            self.ui.define(
                "end_turn",
                anchor="bottom_right",
                w=END_TURN_BUTTON["w"],
                h=END_TURN_BUTTON["h"]
            )

            self.ui.define(
                "unit_hud",
                anchor="top_right",
                w=UNIT_HUD["w"],
                h=UNIT_HUD["h"]
            )

            self.ui.define(
                "turn_label",
                anchor="top_left",
                w=TURN_INDICATOR["w"],
                h=TURN_INDICATOR["h"]
            )


    def handle_ui_click(self, pos):
        if self.turns.phase == "play":
            end_btn = self.ui.get("end_turn")
            if end_btn.collidepoint(pos):
                self.end_turn()
                return True
        return False
               

    def handle_world_click(self, pos):
        mx, my = pos

        if self.moving:
            return 
        
        print("click screen coords:", mx, my)

        wx, wy = self.camera.screen_to_world((mx, my))
        print("world coords:", wx, wy)
        q, r = self.hexmap.pixel_to_hex(wx, wy)
        print("computed hex:", (q, r), "inside:", self.hexmap.is_inside_grid(q, r),
            "in_spawn:", self.in_spawn_zone(self.turns.current_player, r))

        if not self.hexmap.is_inside_grid(q, r):
            return

        tile = (q, r)
        clicked_unit = next(
                (u for u in self.units if (u.q, u.r) == tile),
                None
        )

        # Placement
        if self.turns.phase == "setup":
            if self.turns.units_placed[self.turns.current_player] < len(self.player_units[self.turns.current_player]):
                if self.in_spawn_zone(self.turns.current_player, r):
                    if not any((u.q, u.r) == tile for u in self.units):
                        u = self.player_units[self.turns.current_player][self.turns.units_placed[self.turns.current_player]]
                        u.q, u.r = q, r
                        self.units.append(u)
                        self.turns.record_placement(self.turns.current_player)
                        if not self.turns.can_place_unit(self.turns.current_player):
                            self.turns.next_turn()
            return
        
        if self.turns.phase == "setup":
            if self.turns.units_placed[self.turns.current_player] >= len(self.player_units[self.turns.current_player]):
                print("No remaining units to place for player", self.turns.current_player)
                return
            if not self.in_spawn_zone(self.turns.current_player, r):
                print("Tile not in spawn zone:", (q, r))
                return
            if any((u.q, u.r) == tile for u in self.units):
                print("Tile occupied:", tile)
                return
            # place unit:
            print("Placing unit for player", self.turns.current_player, "at", tile)


        # Selection
        if clicked_unit and clicked_unit.owner == self.turns.current_player:
            self.selected_unit = clicked_unit
            self.update_attackable_enemies()
            blocked = {(u.q, u.r) for u in self.units if u is not self.selected_unit}
            self.reachable_tiles = self.hexmap.get_reachable_tiles(
                tile, clicked_unit.move_range, blocked
            )

        elif self.selected_unit and tile in self.reachable_tiles:
            if self.selected_unit.action_points > 0:
                blocked = {(u.q, u.r) for u in self.units if u is not self.selected_unit}
                path = self.hexmap.find_path(
                    (self.selected_unit.q, self.selected_unit.r),
                    tile,
                    blocked
                )
                if len(path) > 1:
                    self.move_path = path[1:]
                    self.moving = True
                    self.move_timer = 0
                    self.selected_unit.action_points -= 1

        elif self.selected_unit and clicked_unit and clicked_unit.owner != self.turns.current_player:
            if self.selected_unit.action_points > 0:
                if self.attack(self.selected_unit, clicked_unit):
                    self.auto_end_turn()

        elif not clicked_unit and self.turns.phase == "play":
            # ignore empty clicks to preserve selection
            return


    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------
    def update(self, dt):
        self.move_timer += dt

        # --- HANDLE MOVEMENT ---
        if self.moving and self.move_path:
            if self.move_timer >= self.move_delay:
                self.move_timer = 0

                next_q, next_r = self.move_path.pop(0)
                self.selected_unit.q = next_q
                self.selected_unit.r = next_r

        # --- END MOVEMENT ---

        # Movement animation
        if not self.move_path:
            self.moving = False

            if self.selected_unit:
                if self.selected_unit.action_points > 0:
                    blocked = {(u.q, u.r) for u in self.units if u is not self.selected_unit}
                    self.reachable_tiles = self.hexmap.get_reachable_tiles(
                        (self.selected_unit.q, self.selected_unit.r),
                        self.selected_unit.move_range,
                        blocked
                    )
                    self.update_attackable_enemies()
                else:
                    self.reachable_tiles.clear()
                    self.attackable_enemies.clear()
                    self.auto_end_turn()

        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        

        self.camera.handle_input(events, keys)


    # ---------------------------------------------------------
    # DRAW
    # ---------------------------------------------------------
    def draw(self, surface):
        surface.fill((30, 30, 30))
        self.draw_world(surface)
        self.draw_overlays(surface)
        self.draw_ui(surface)

    def draw_world(self, surface):
        self.hexmap.draw()
        for u in self.units:
            u.draw(surface, self.camera, self.hexmap)
            
    def draw_overlays(self, surface):
        
        if self.selected_unit and self.turns.phase == "play":
            for q, r in self.reachable_tiles:
                self.hexmap.draw_highlight(q, r, color=(80, 200, 120, 80))

        if self.selected_unit:
            self.hexmap.draw_highlight(
                self.selected_unit.q,
                self.selected_unit.r,
                color=(0, 150, 255, 120)
            )


        # --- Attackable enemies ---
        if (
            self.selected_unit
            and self.turns.phase == "play"
            and self.selected_unit.action_points > 0
        ):
            for q, r in self.attackable_enemies:
                self.hexmap.draw_highlight(
                    q, r,
                    color=(200, 60, 60, 120)  # red
                )

        # --- Deployment zone ---
        if self.turns.phase == "setup":
            current_player = self.turns.current_player
            for q in range(self.hexmap.width):
                for r in range(self.hexmap.height):
                    if self.in_spawn_zone(current_player, r):
                        self.hexmap.draw_highlight(
                            q, r,
                            color=(200, 200, 80, 80)
                        )

    def draw_ui(self, surface):
        self.draw_turn_label(surface)
        self.draw_end_turn_button(surface)

        if self.selected_unit:
            rect = self.ui.get("unit_hud")
            self.unit_hud.draw(surface, self.selected_unit, rect)

    def draw_end_turn_button(self, surface):
        rect = self.ui.get("end_turn")
        hover = rect.collidepoint(pygame.mouse.get_pos())

        bg = UI_COLORS["button_hover"] if hover else UI_COLORS["button"]
        pygame.draw.rect(surface, bg, rect, border_radius=self.ui.radius("small"))
        pygame.draw.rect(surface, UI_COLORS["button_border"], rect, 2)

        txt = self.font.render("End Turn", True, UI_COLORS["text"])
        surface.blit(txt, txt.get_rect(center=rect.center))

    def draw_turn_label(self, surface):
        rect = self.ui.get("turn_label")

        # --- Panel background ---
        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        bg.fill(UI_BG_COLOR)
        surface.blit(bg, rect.topleft)

        pygame.draw.rect(
            surface,
            UI_COLORS["panel_border"],
            rect,
            1,
            border_radius=self.ui.radius("small")
        )

        # --- Text ---
        font = pygame.font.Font(
            None,
            int(18 * self.ui.scale)
        )

        player_text = f"Player {self.turns.current_player + 1}"

        if self.turns.phase == "setup":
            turn_text = "Deployment"
        else:
            turn_text = f"Turn {self.turns.turn_count}"

        txt_player = font.render(player_text, True, UI_COLORS["text"])
        txt_turn   = font.render(turn_text,   True, UI_COLORS["text"])

        x = rect.left + int(12 * self.ui.scale)
        y = rect.top  + int(10 * self.ui.scale)

        surface.blit(txt_player, (x, y))
        surface.blit(txt_turn,   (x, y + txt_player.get_height() + int(6 * self.ui.scale)))

    
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
            f"Player {self.turns.current_player + 1} Roster",
            True, (255, 255, 255)
        )
        self.screen.blit(title, (panel_x + 10, panel_y + 10))

        y = panel_y + 50
        for i, unit in enumerate(self.player_units[self.turns.current_player]):
            color = (200, 200, 200)
            if i == self.turns.units_placed[self.turns.current_player]:
                color = (255, 255, 120)  # next unit to place

            txt = self.font.render(unit.unit_class, True, color)
            self.screen.blit(txt, (panel_x + 20, y))
            y += 28

    def end_turn(self):
        
        if self.turns.phase == "setup":
            if self.turns.can_place_unit(self.turns.current_player):
                print("Cannot end turn: units still to place")
                return
        self.selected_unit = None
        self.reachable_tiles.clear()
        self.attackable_enemies.clear()
        self.moving = False
        self.move_path.clear()
        self.hexmap.selected_hex = None

        self.turns.next_turn()

        # reset AP for new player's units
        for u in self.units:
            if u.owner == self.turns.current_player:
                u.reset_actions()

    def auto_end_turn(self):
        if self.selected_unit and self.selected_unit.action_points <= 0:
            self.end_turn()

    def attack(self, attacker, defender):
        if attacker.action_points <= 0:
            return False

        # 1. Melee has priority
        if attacker.can_attack(defender, "melee"):
            weapon_type = "melee"

        # 2. Try ranged
        elif (
            attacker.can_attack(defender, "ranged")
            and not self.is_adjacent_to_enemy(attacker)
        ):
            weapon_type = "ranged"

        else:
            print("No valid attack (range or adjacency restriction)")
            return False

        hits, unsaved, killed = attacker.perform_attack(defender, weapon_type)

        self.combat_log.insert(
            0,
            f"P{attacker.owner+1} {attacker.unit_class} "
            f"{weapon_type} attacks {defender.unit_class}: "
            f"{hits} hits, {unsaved} unsaved"
        )

        if killed:
            self.units.remove(defender)
            self.combat_log.insert(0, f"{defender.unit_class} destroyed")

        return True

    
    def is_adjacent_to_enemy(self, unit):
        for dq, dr in self.hexmap.AXIAL_DIRECTIONS:
            nq, nr = unit.q + dq, unit.r + dr
            for other in self.units:
                if other.owner != unit.owner and (other.q, other.r) == (nq, nr):
                    return True
        return False
    
    def update_attackable_enemies(self):
        self.attackable_enemies.clear()

        if not self.selected_unit:
            return

        attacker = self.selected_unit

        for enemy in self.units:
            if enemy.owner == attacker.owner:
                continue

            # melee possible
            if attacker.can_attack(enemy, "melee"):
                self.attackable_enemies.add((enemy.q, enemy.r))
                continue

            # ranged possible
            if (
                attacker.can_attack(enemy, "ranged")
                and not self.is_adjacent_to_enemy(attacker)
            ):
                self.attackable_enemies.add((enemy.q, enemy.r))


