# game.py
import pygame
import random
import time
from collections import deque
from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, NUM_PLAYERS, UNITS_PER_PLAYER,
    BOTTOM_UI_HEIGHT, LOG_WIDTH
)
from camera import Camera
from hexmap import HexMap
from unit import Unit, create_roster


class Game:
    def __init__(self, screen, map_name, roster):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24)

        # External choices
        self.map_name = map_name
        self.roster_data = roster

        # Core objects
        self.camera = Camera()
        self.hexmap = HexMap(screen, self.camera)
        self.center_camera_on_map()

        # --- State ---
        self.running = True
        self.units = []
        self.player_units = [create_roster(i) for i in range(NUM_PLAYERS)]
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

    # ---------------------------------------------------------
    # LOGGING
    # ---------------------------------------------------------
    def log(self, text):
        self.combat_log.insert(0, text)
        if len(self.combat_log) > self.MAX_LOG_LINES:
            self.combat_log.pop()

    # ---------------------------------------------------------
    # GAME HELPERS
    # ---------------------------------------------------------
    def in_spawn_zone(self, player, r):
        zone = 4
        if player == 0:
            return r < zone
        return r >= self.hexmap.height - zone

    def bfs_path(self, start, goal, blocked):
        if start == goal:
            return [start]

        q = deque([start])
        came = {start: None}

        while q:
            cur = q.popleft()
            if cur == goal:
                break
            for n in self.hexmap.neighbors(*cur):
                if n in came:
                    continue
                if n in blocked:
                    continue
                if not self.hexmap.is_inside_grid(*n):
                    continue
                came[n] = cur
                q.append(n)

        if goal not in came:
            return []

        path = []
        c = goal
        while c is not None:
            path.append(c)
            c = came[c]
        path.reverse()
        return path

    def hex_distance(self, a, b):
        aq, ar = a
        bq, br = b
        ax, az = aq, ar
        ay = -ax - az
        bx, bz = bq, br
        by = -bx - bz
        return int((abs(ax - bx) + abs(ay - by) + abs(az - bz)) / 2)

    # ---------------------------------------------------------
    # COMBAT
    # ---------------------------------------------------------
    def resolve_combat(self, attacker, defender, weapon):
        for _ in range(weapon["attack"]):
            hit = random.randint(1, 6)
            self.log(f"{attacker.unit_class} rolls {hit} to hit (needs {weapon['hit']}+).")
            if hit >= weapon["hit"]:
                save_roll = random.randint(1, 6)
                if save_roll > defender.save:
                    defender.hp -= weapon["damage"]
                    self.log(f"{attacker.unit_class} hits {defender.unit_class}! HP now {defender.hp}")
                    if defender.hp <= 0:
                        self.log(f"{defender.unit_class} is slain!")
                        if defender in self.units:
                            self.units.remove(defender)
                        break
                else:
                    self.log(f"{defender.unit_class} saves successfully!")
            else:
                self.log(f"{attacker.unit_class} misses.")

    def attack(self, attacker, defender):
        dist = self.hex_distance((attacker.q, attacker.r), (defender.q, defender.r))

        melee_range = attacker.melee.get("range", 1)
        if dist <= melee_range and attacker.melee.get("attack", 0) > 0:
            self.log(f"{attacker.unit_class} attacks {defender.unit_class} in melee!")
            self.resolve_combat(attacker, defender, attacker.melee)
            return True

        if dist <= attacker.ranged.get("range", 0):
            self.log(f"{attacker.unit_class} shoots at {defender.unit_class} (range {dist}).")
            self.resolve_combat(attacker, defender, attacker.ranged)
            return True

        self.log("Out of range.")
        return False

    # ---------------------------------------------------------
    # TURN LOGIC
    # ---------------------------------------------------------
    def end_turn(self):
        self.selected_unit = None
        self.reachable_tiles.clear()
        self.moving = False
        self.move_highlight = None
        self.hexmap.selected_hex = None

        self.player_moved[self.current_player] = False

        done = all(c >= UNITS_PER_PLAYER for c in self.placed_units)
        self.current_player = (self.current_player + 1) % NUM_PLAYERS

        for u in self.units:
            if u.owner == self.current_player and hasattr(u, "reset_actions"):
                u.reset_actions()

        if done:
            self.placement_phase = False

    def auto_end_turn(self):
        if not self.selected_unit:
            return
        if self.selected_unit.action_points <= 0:
            self.log(f"{self.selected_unit.unit_class} has 0 AP — turn ends.")
            self.end_turn()

    # ---------------------------------------------------------
    # MAIN LOOP
    # ---------------------------------------------------------
    def run(self):
        end_btn = pygame.Rect(WINDOW_WIDTH - 180, 40, 140, 50)

        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.move_timer += dt

            events = pygame.event.get()
            keys = pygame.key.get_pressed()
            mouse_pos = pygame.mouse.get_pos()

            # Quit
            for ev in events:
                if ev.type == pygame.QUIT:
                    self.running = False

            # Camera
            self.camera.handle_input(events, keys)

            # ------------------------------
            # Input Handling
            # ------------------------------
            if pygame.mouse.get_pressed()[0]:
                mx, my = mouse_pos

                if end_btn.collidepoint((mx, my)):
                    if not (self.placement_phase and
                            self.placed_units[self.current_player] < UNITS_PER_PLAYER):
                        self.end_turn()

                # Convert click to hex
                wx, wy = self.camera.screen_to_world(mouse_pos)
                q, r = self.hexmap.pixel_to_hex(wx, wy)

                if self.hexmap.is_inside_grid(q, r):
                    tile = (q, r)
                    clicked_unit = next((u for u in self.units if (u.q, u.r) == tile), None)

                    # Placement Phase
                    if self.placement_phase:
                        if self.placed_units[self.current_player] < len(self.player_units[self.current_player]):
                            if self.in_spawn_zone(self.current_player, r):
                                if not any((u.q, u.r) == tile for u in self.units):
                                    u = self.player_units[self.current_player][self.placed_units[self.current_player]]
                                    u.q, u.r = q, r
                                    self.units.append(u)
                                    self.placed_units[self.current_player] += 1
                        continue

                    # Select unit
                    if clicked_unit and clicked_unit.owner == self.current_player:
                        self.selected_unit = clicked_unit
                        self.hexmap.selected_hex = tile
                        blocked = {(u.q, u.r) for u in self.units if u is not self.selected_unit}
                        self.reachable_tiles = self.hexmap.get_reachable_tiles(tile, clicked_unit.move_range, blocked)

                    # Movement
                    elif self.selected_unit and tile in self.reachable_tiles:
                        if self.selected_unit.action_points > 0:
                            blocked = {(u.q, u.r) for u in self.units if u is not self.selected_unit}
                            path = self.bfs_path((self.selected_unit.q, self.selected_unit.r), tile, blocked)
                            if len(path) > 1:
                                self.move_path = path[1:]
                                self.moving = True
                                self.move_timer = 0
                                self.move_highlight = None
                                self.selected_unit.action_points -= 1

                    # Attack
                    elif self.selected_unit and clicked_unit and clicked_unit.owner != self.current_player:
                        if self.selected_unit.action_points > 0:
                            valid = self.attack(self.selected_unit, clicked_unit)
                            if valid:
                                self.selected_unit.action_points -= 1
                                self.auto_end_turn()

                    else:
                        self.selected_unit = None
                        self.hexmap.selected_hex = None
                        self.reachable_tiles.clear()

            # ------------------------------
            # Animation
            # ------------------------------
            if self.moving and self.selected_unit and self.move_path:
                if self.move_timer >= self.move_delay:
                    self.move_timer = 0
                    step = self.move_path.pop(0)
                    self.selected_unit.q, self.selected_unit.r = step
                    self.move_highlight = step

                    if not self.move_path:
                        self.moving = False
                        self.move_highlight = None
                        self.reachable_tiles.clear()

                        if self.selected_unit.action_points > 0:
                            blocked = {(u.q, u.r) for u in self.units if u is not self.selected_unit}
                            cur = (self.selected_unit.q, self.selected_unit.r)
                            self.reachable_tiles = self.hexmap.get_reachable_tiles(cur, self.selected_unit.move_range, blocked)
                        else:
                            self.auto_end_turn()

            # ------------------------------
            # DRAW
            # ------------------------------
            self.draw_ui(end_btn)
            pygame.display.flip()

        pygame.quit()

    # ---------------------------------------------------------
    # DRAW LOGIC
    # ---------------------------------------------------------
    def draw_ui(self, end_btn):
        self.screen.fill((30, 30, 30))
        self.hexmap.draw()

        # --- End Turn Button ---
        mx, my = pygame.mouse.get_pos()
        hover = end_btn.collidepoint((mx, my))
        btn_color = (90, 150, 200) if hover else (70, 130, 180)
        pygame.draw.rect(self.screen, btn_color, end_btn, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), end_btn, 2, border_radius=8)
        txt = self.font.render("End Turn", True, (255, 255, 255))
        self.screen.blit(txt, (end_btn.x + 20, end_btn.y + 10))

        # --- Combat Log ---
        ui_y = WINDOW_HEIGHT - BOTTOM_UI_HEIGHT
        pygame.draw.rect(self.screen, (25, 25, 40), (0, ui_y, WINDOW_WIDTH, BOTTOM_UI_HEIGHT))
        pygame.draw.rect(self.screen, (100, 100, 150), (10, ui_y + 10, LOG_WIDTH, BOTTOM_UI_HEIGHT - 20), 2)

        for i, line in enumerate(self.combat_log[:self.MAX_LOG_LINES]):
            txt = self.font.render(line, True, (220, 220, 220))
            self.screen.blit(txt, (20, ui_y + 20 + i * 22))
