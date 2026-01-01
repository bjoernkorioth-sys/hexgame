# hexmap.py
import pygame
import math
import random
from settings import HEX_SIZE, GRID_WIDTH, GRID_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT, MAP_OFFSET_X, MAP_OFFSET_Y, TERRAIN_TYPES
from collections import deque

SQRT3 = math.sqrt(3.0)

class HexMap:
    AXIAL_DIRECTIONS = [
        (1, 0), (1, -1), (0, -1),
        (-1, 0), (-1, 1), (0, 1)
    ]

    def __init__(self, surface, camera):
        self.surface = surface
        self.camera = camera
        self.size = HEX_SIZE
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT

        # compute centering offsets (world-space)
        self.offset_x = MAP_OFFSET_X
        self.offset_y = MAP_OFFSET_Y
        
        # selection state
        self.hover_hex = None
        self.selected_hex = None

        # terrain: (q,r) -> dict{type,move_cost,height,passable}
        self.terrain = {}
        self.corner_cache = {}
        self._init_terrain()
        self._cache_corners()

    # -----------------------
    # Setup helpers
    # -----------------------
    def _init_terrain(self):
        for r in range(self.height):
            for q in range(self.width):
                # default plain
                self.terrain[(q, r)] = {
                    "type": "plain",
                    **TERRAIN_TYPES["plain"]
                }


    def _cache_corners(self):
        # precompute world-space center & corner points for each tile (unzoomed)
        for r in range(self.height):
            for q in range(self.width):
                px, py = self.hex_to_pixel(q, r)  # world pixel (includes offset)
                corners = []
                for i in range(6):
                    angle = math.radians(60 * i + 30)
                    corners.append((px + self.size * math.cos(angle),
                                    py + self.size * math.sin(angle)))
                self.corner_cache[(q, r)] = corners

    def hex_corners(self, cx, cy):
        """
        Return the 6 corner points of a pointy-top hex centered at (cx, cy)
        in screen coordinates.
        """
        corners = []
        for i in range(6):
            angle_deg = 60 * i - 30  # pointy-top orientation
            angle_rad = math.radians(angle_deg)
            x = cx + self.size * math.cos(angle_rad)
            y = cy + self.size * math.sin(angle_rad)
            corners.append((x, y))
        return corners

    # -----------------------
    # Coordinate conversions
    # -----------------------
    def hex_to_pixel(self, q, r):
        """Axial (q, r) -> world pixel center (flat-top layout math)."""
        x = self.size * math.sqrt(3) * (q + r / 2)
        y = self.size * 1.5 * r
        return x + self.offset_x, y + self.offset_y

    def pixel_to_hex(self, px, py):
        """World pixel -> axial coords (rounded)."""
        # Convert world pixel to map-local coordinates (remove offset)
        x = (px - self.offset_x)
        y = (py - self.offset_y)

        qf = (math.sqrt(3) / 3 * x - 1.0 / 3 * y) / self.size
        rf = (2.0 / 3 * y) / self.size

        xf, zf = qf, rf
        yf = -xf - zf

        rx, ry, rz = round(xf), round(yf), round(zf)
        x_diff, y_diff, z_diff = abs(rx - xf), abs(ry - yf), abs(rz - zf)
        if x_diff > y_diff and x_diff > z_diff:
            rx = -ry - rz
        elif y_diff > z_diff:
            ry = -rx - rz
        else:
            rz = -rx - ry

        return int(rx), int(rz)

    # -----------------------
    # Drawing
    # -----------------------
    def draw_highlight(self, q, r, color=(100, 100, 200, 80)):
        # Convert hex to pixel
        x, y = self.hex_to_pixel(q, r)
        x, y = self.camera.apply((x, y))

        # Get hex corners
        points = self.hex_corners(x, y)

        # Draw semi-transparent overlay
        s = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(s, color, points)
        self.surface.blit(s, (0, 0))

    
    def draw_hex(self, corners, color, width=0):
        # corners are already in screen space
        pygame.draw.polygon(self.surface, color, corners, width)

    def draw(self):
        # Draw terrain by iterating all tiles and drawing filled polygon using cached corners
        for (q, r), corners in self.corner_cache.items():
            # convert each corner to screen via camera
            screen_corners = [self.camera.apply(point) for point in corners]
            tile = self.terrain[(q, r)]
            ttype = tile["type"]
            tdef = TERRAIN_TYPES[ttype]

            color = tdef["color"]

            screen_corners = [self.camera.apply(pt) for pt in corners]
            pygame.draw.polygon(self.surface, color, screen_corners, 0)

        # Draw hex outlines on top
        for (q, r), corners in self.corner_cache.items():
            screen_corners = [self.camera.apply(point) for point in corners]
            pygame.draw.polygon(self.surface, (100,100,100), screen_corners, 1)

        # Draw hover/selection outlines
        for hex_coord, col in ((self.hover_hex, (255,255,0)), (self.selected_hex, (0,150,255))):
            if hex_coord is None:
                continue
            q, r = hex_coord
            if not self.is_inside_grid(q, r):
                continue
            screen_corners = [self.camera.apply(point) for point in self.corner_cache[(q, r)]]
            pygame.draw.polygon(self.surface, col, screen_corners, 3)

    # -----------------------
    # Helpers for editor & gameplay
    # -----------------------
    def is_inside_grid(self, q, r):
        return 0 <= q < self.width and 0 <= r < self.height

    def neighbors(self, q, r):
        return [(q + dq, r + dr) for dq, dr in self.AXIAL_DIRECTIONS]

    def get_reachable_tiles(self, start, move_points, blocked):
        from collections import deque
        reachable = set()
        frontier = deque([(start, move_points)])
        came_from = {start: None}
        while frontier:
            current, remaining = frontier.popleft()
            if remaining < 0:
                continue
            reachable.add(current)
            for n in self.neighbors(*current):
                if not self.is_inside_grid(*n): continue
                if n in blocked: continue
                terrain = self.terrain.get(n, {"move_cost": 1, "passable": True, "height": 1})
                if not terrain["passable"]: continue
                cur_height = self.terrain.get(current, {"height": 1})["height"]
                if abs(cur_height - terrain["height"]) > 1: continue
                cost = terrain["move_cost"]
                new_remain = remaining - cost
                if n not in came_from or new_remain > 0:
                    came_from[n] = current
                    frontier.append((n, new_remain))
        return reachable
    

    def find_path(self, start, goal, blocked):
        if start == goal:
            return [start]

        frontier = deque([start])
        came_from = {start: None}

        while frontier:
            current = frontier.popleft()

            for neighbor in self.neighbors(*current):
                if not self.is_inside_grid(*neighbor):
                    continue
                if neighbor in blocked:
                    continue

                terrain = self.terrain.get(neighbor)
                if not terrain or not terrain["passable"]:
                    continue

                cur_h = self.terrain[current]["height"]
                if abs(cur_h - terrain["height"]) > 1:
                    continue

                if neighbor not in came_from:
                    came_from[neighbor] = current
                    if neighbor == goal:
                        frontier.clear()
                        break
                    frontier.append(neighbor)

        if goal not in came_from:
            return None

        # reconstruct path
        path = []
        cur = goal
        while cur is not None:
            path.append(cur)
            cur = came_from[cur]
        path.reverse()
        return path
