# map_editor.py
import pygame
import os
import json
import math
from datetime import datetime
from hexmap import HexMap
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, GRID_WIDTH, GRID_HEIGHT, HEX_SIZE, FPS, SIDEBAR_WIDTH as SIDEBAR_W, TERRAIN_TYPES, TERRAIN_LIST


MAPS_DIR = "maps"

TERRAIN_UI_LIST = TERRAIN_LIST  # ordered list from settings

if not os.path.exists(MAPS_DIR):
    os.makedirs(MAPS_DIR)

class MapEditor:
    def __init__(self, surface, camera):
        self.surface = surface
        self.camera = camera
        
        # -------- FIXED: HexMap only receives map area width, not whole screen --------
        self.map_rect = pygame.Rect(0, 0, WINDOW_WIDTH - SIDEBAR_W, WINDOW_HEIGHT)

        # HexMap now draws ONLY in this region
        self.hexmap = HexMap(self.surface, self.camera)

        # Editor state
        self.selected_terrain_idx = 0
        self.selected_height = 1
        self.passable = True
        self.brush_size = 0
        self.drawing = False
        self.typing_name = False     # <-- FIX
        self.loading_menu = False

        self.sidebar_scroll = 0
        self.sidebar_scroll_speed = 25
        self.sidebar_content_height = 0   # calculated automatically
    


        self.font = pygame.font.SysFont("arial", 16)
        self.title_font = pygame.font.SysFont("arial", 22, bold=True)

        self.map_name = f"map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # -------------------------------------------------------------------
    # Saving / loading logic (unchanged)
    # -------------------------------------------------------------------
    def save_preview_image(self, filename):
        """
        Render a 300x300 preview of the current hex map with:

        ✔ Real hex shapes
        ✔ Height shading
        ✔ Impassable tile overlay
        ✔ Perfect centering

        Saves to: maps/<mapname>.png
        """

        import pygame
        import os
        import math

        PREV_SIZE = 300
        base, ext = os.path.splitext(filename)
        out_path = os.path.join(MAPS_DIR, base + ".png")

        # Create surface
        surf = pygame.Surface((PREV_SIZE, PREV_SIZE))
        surf.fill((25, 25, 30))

        # Collect all pixel-coordinates BEFORE scaling
        pixel_centers = []
        for (q, r) in self.hexmap.terrain.keys():
            px, py = self.hexmap.hex_to_pixel(q, r)
            pixel_centers.append((px, py))

        if not pixel_centers:
            pygame.image.save(surf, out_path)
            return

        xs = [p[0] for p in pixel_centers]
        ys = [p[1] for p in pixel_centers]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        map_w = max_x - min_x + HEX_SIZE * 2
        map_h = max_y - min_y + HEX_SIZE * 2

        # Fit map in preview
        scale = min(PREV_SIZE / map_w, PREV_SIZE / map_h)

        # Perfect centering
        offset_x = (PREV_SIZE - map_w * scale) / 2
        offset_y = (PREV_SIZE - map_h * scale) / 2

        def to_preview(px, py):
            px = (px - min_x) * scale + offset_x
            py = (py - min_y) * scale + offset_y
            return int(px), int(py)

        def hex_corners(px, py, size):
            """Return pixel coords of a scaled hex."""
            corners = []
            for i in range(6):
                angle = math.radians(60 * i - 30)
                cx = px + size * math.cos(angle)
                cy = py + size * math.sin(angle)
                corners.append((cx, cy))
            return corners

        # Render each tile
        for (q, r), data in self.hexmap.terrain.items():
            terr = data["type"]
            height = data.get("height", 0)
            imp = data.get("impassable", False)

            base_color = TERRAIN_TYPES[terr]["color"]

            # HEIGHT SHADING (0–10 expected)
            # Darker for higher elevation
            shade = max(0, min(10, height))
            factor = 1 - shade * 0.04  # reduces brightness
            color = (
                int(base_color[0] * factor),
                int(base_color[1] * factor),
                int(base_color[2] * factor),
            )

            px, py = self.hexmap.hex_to_pixel(q, r)
            sx, sy = to_preview(px, py)
            hex_size_scaled = HEX_SIZE * scale

            corners = hex_corners(sx, sy, hex_size_scaled)

            # Fill hex
            pygame.draw.polygon(surf, color, corners)

            # Impassable overlay (red X)
            if imp:
                pygame.draw.line(
                    surf, (200, 40, 40),
                    corners[0], corners[3], max(1, int(hex_size_scaled * 0.15))
                )
                pygame.draw.line(
                    surf, (200, 40, 40),
                    corners[1], corners[4], max(1, int(hex_size_scaled * 0.15))
                )

            # Hex outline
            pygame.draw.polygon(surf, (20, 20, 20), corners, 1)

        # Save preview PNG
        pygame.image.save(surf, out_path)
        print("Saved preview:", out_path)

    
    def list_maps(self):
        files = [f for f in os.listdir(MAPS_DIR) if f.endswith(".json")]
        files.sort()
        return files

    def save_map(self, filename=None):
        if filename is None:
            filename = self.map_name
        path = os.path.join(MAPS_DIR, filename)
        payload = {
            "width": self.hexmap.width,
            "height": self.hexmap.height,
            "tiles": {}
        }
        for (q,r), data in self.hexmap.terrain.items():
            payload["tiles"][f"{q},{r}"] = data
        with open(path, "w") as fh:
            json.dump(payload, fh, indent=2)
        print("Saved map:", path)

        # ALSO save preview PNG
        self.save_preview_image(filename)

    def load_map(self, filename):
        path = os.path.join(MAPS_DIR, filename)
        with open(path, "r") as fh:
            payload = json.load(fh)
        width = payload.get("width", self.hexmap.width)
        height = payload.get("height", self.hexmap.height)
        tiles = payload.get("tiles", {})
        for key, info in tiles.items():
            q_s, r_s = key.split(",")
            q, r = int(q_s), int(r_s)
            if (q, r) in self.hexmap.terrain:
                self.hexmap.terrain[(q, r)] = info
        print("Loaded map:", path)

    # -------------------------------------------------------------------
    # Painting
    # -------------------------------------------------------------------
    def apply_brush(self, q, r):
        coords = [(q, r)]
        terrain_name = TERRAIN_UI_LIST[self.selected_terrain_idx]
        base = TERRAIN_TYPES[terrain_name]
        if self.brush_size > 0:
            for dq in range(-self.brush_size, self.brush_size + 1):
                for dr in range(-self.brush_size, self.brush_size + 1):
                    if abs(dq + dr) <= self.brush_size:
                        coords.append((q + dq, r + dr))

        for (qq, rr) in coords:
            if not self.hexmap.is_inside_grid(qq, rr):
                continue
            self.hexmap.terrain[(qq, rr)] = {
                "type": terrain_name,
                "move_cost": base["move_cost"],
                "height": self.selected_height,
                "passable": self.passable
            }

    def sample_tile(self, q, r):
        if (q, r) in self.hexmap.terrain:
            t = self.hexmap.terrain[(q, r)]
            terrain_name = t["type"]
            self.selected_terrain_idx = TERRAIN_UI_LIST.index(terrain_name)
            self.selected_height = t["height"]
            self.passable = t["passable"]

    # -------------------------------------------------------------------
# Sidebar UI
# -------------------------------------------------------------------
    def draw_sidebar(self):
        sx = WINDOW_WIDTH - SIDEBAR_W

        # Create an offscreen surface that represents the whole sidebar
        sidebar_surface = pygame.Surface((SIDEBAR_W, WINDOW_HEIGHT))
        sidebar_surface.fill((36, 36, 44))

        # local drawing origin inside sidebar_surface (local coords)
        local_x = 12
        y = 12  # start inside the sidebar surface

        # apply vertical scroll: when we draw element at 'y', actual blit
        # inside the sidebar surface is at y - self.sidebar_scroll
        offset_y = -self.sidebar_scroll

        # --- Title ---
        title_surf = self.title_font.render("Map Editor", True, (230,230,230))
        sidebar_surface.blit(title_surf, (local_x, y + offset_y))
        y += 44

        # --- MAP NAME ---
        name_label = self.font.render("Map name:", True, (200,200,200))
        sidebar_surface.blit(name_label, (local_x, y + offset_y))
        y += 24

        name_box_local = pygame.Rect(local_x, y, SIDEBAR_W - 24, 28)
        pygame.draw.rect(sidebar_surface, (70,70,90), (name_box_local.x, name_box_local.y + offset_y, name_box_local.w, name_box_local.h))
        displayed_name = self.map_name if not self.typing_name else self.map_name + "|"
        sidebar_surface.blit(self.font.render(displayed_name, True, (255,255,255)), (name_box_local.x + 4, name_box_local.y + 6 + offset_y))
        # store local rect for hit testing
        self.name_box_local = name_box_local
        y += 40

        # --- TERRAIN SELECTION ---
        terrain_label = self.font.render("Terrains:", True, (200,200,200))
        sidebar_surface.blit(terrain_label, (local_x, y + offset_y))
        y += 28

        # build terrain buttons and store their local rects
        self.terrain_boxes_local = []
        for idx, name in enumerate(TERRAIN_UI_LIST):
            rect_local = pygame.Rect(local_x, y, SIDEBAR_W - 24, 28)
            color = (80,80,80) if idx != self.selected_terrain_idx else (65,110,180)
            pygame.draw.rect(sidebar_surface, color, (rect_local.x, rect_local.y + offset_y, rect_local.w, rect_local.h))
            sidebar_surface.blit(self.font.render(name.title(), True, (255,255,255)), (rect_local.x + 8, rect_local.y + 6 + offset_y))
            self.terrain_boxes_local.append(rect_local)
            y += 34

        # --- HEIGHT CONTROLS ---
        y += 6
        sidebar_surface.blit(self.font.render("Height:", True, (200,200,200)), (local_x, y + offset_y))
        y += 26
        minus_local = pygame.Rect(local_x, y, 26, 26)
        plus_local = pygame.Rect(local_x + SIDEBAR_W - 24 - 26, y, 26, 26)

        pygame.draw.rect(sidebar_surface, (70,70,90), (minus_local.x, minus_local.y + offset_y, minus_local.w, minus_local.h))
        pygame.draw.rect(sidebar_surface, (70,70,90), (plus_local.x, plus_local.y + offset_y, plus_local.w, plus_local.h))
        sidebar_surface.blit(self.font.render("-", True, (255,255,255)), (minus_local.x + 4, minus_local.y + 4 + offset_y))
        sidebar_surface.blit(self.font.render("+", True, (255,255,255)), (plus_local.x + 4, plus_local.y + 4 + offset_y))

        mid_x = local_x + (SIDEBAR_W // 2) - 8
        sidebar_surface.blit(self.font.render(str(self.selected_height), True, (255,255,255)), (mid_x, y + 4 + offset_y))

        self.height_minus_local = minus_local
        self.height_plus_local = plus_local
        y += 40

        # --- PASSABLE TOGGLE ---
        toggle_local = pygame.Rect(local_x, y, SIDEBAR_W - 24, 28)
        pygame.draw.rect(sidebar_surface, (110,60,60) if not self.passable else (60,110,60),
                        (toggle_local.x, toggle_local.y + offset_y, toggle_local.w, toggle_local.h))
        txt = "Passable: " + ("Yes" if self.passable else "No")
        sidebar_surface.blit(self.font.render(txt, True, (255,255,255)), (toggle_local.x + 8, toggle_local.y + 6 + offset_y))
        self.passable_btn_local = toggle_local
        y += 40

        # --- BRUSH SIZE ---
        sidebar_surface.blit(self.font.render("Brush size:", True, (200,200,200)), (local_x, y + offset_y))
        y += 26
        brush_minus_local = pygame.Rect(local_x, y, 26, 26)
        brush_plus_local = pygame.Rect(local_x + SIDEBAR_W - 24 - 26, y, 26, 26)
        pygame.draw.rect(sidebar_surface, (70,70,90), (brush_minus_local.x, brush_minus_local.y + offset_y, brush_minus_local.w, brush_minus_local.h))
        pygame.draw.rect(sidebar_surface, (70,70,90), (brush_plus_local.x, brush_plus_local.y + offset_y, brush_plus_local.w, brush_plus_local.h))
        sidebar_surface.blit(self.font.render("-", True, (255,255,255)), (brush_minus_local.x + 4, brush_minus_local.y + 4 + offset_y))
        sidebar_surface.blit(self.font.render("+", True, (255,255,255)), (brush_plus_local.x + 4, brush_plus_local.y + 4 + offset_y))
        sidebar_surface.blit(self.font.render(str(self.brush_size), True, (255,255,255)), (mid_x, y + 4 + offset_y))
        self.brush_minus_local = brush_minus_local
        self.brush_plus_local = brush_plus_local
        y += 40

        # --- Buttons (new/save/load/back) ---
        y += 6
        btn_h = 34
        spacing = 8
        self.buttons_local = []  # store (local_rect, key)
        for label, key in [("New Map","new"),("Save","save"),("Load","load"),("Back","back")]:
            btn_local = pygame.Rect(local_x, y, SIDEBAR_W - 24, btn_h)
            pygame.draw.rect(sidebar_surface, (70,70,90), (btn_local.x, btn_local.y + offset_y, btn_local.w, btn_local.h))
            sidebar_surface.blit(self.font.render(label, True, (240,240,240)), (btn_local.x + 8, btn_local.y + 6 + offset_y))
            self.buttons_local.append((btn_local, key))
            y += btn_h + spacing

        # --- List saved maps (simple listing) ---
        y += 12
        sidebar_surface.blit(self.font.render("Saved maps:", True, (200,200,200)), (local_x, y + offset_y))
        y += 22
        for m in self.list_maps()[-16:][::-1]:
            sidebar_surface.blit(self.font.render(m, True, (180,180,180)), (local_x, y + offset_y))
            y += 18

        # compute content height so scrolling clamp can use it
        self.sidebar_content_height = max(y + 10, WINDOW_HEIGHT)

        # finally blit the sidebar surface to the main surface at screen x position
        self.surface.blit(sidebar_surface, (sx, 0))

        # (optional) draw a light border line between map and sidebar
        pygame.draw.line(self.surface, (20,20,26), (sx - 1, 0), (sx - 1, WINDOW_HEIGHT), 2)


# -------------------------------------------------------------------
# Handle sidebar click
# -------------------------------------------------------------------
    def handle_ui_click(self, mx, my):
        sx = WINDOW_WIDTH - SIDEBAR_W
        if mx < sx:
            return False

        # convert screen coords -> sidebar-local coords (same coords used in draw_sidebar)
        mx_local = mx - sx
        my_local = my + self.sidebar_scroll   # add scroll so local y points to the content coordinate

        # MAP NAME FIELD (local)
        if self.name_box_local.collidepoint(mx_local, my_local):
            self.typing_name = True
            return True
        else:
            # clicking elsewhere stops typing
            self.typing_name = False

        # TERRAIN selection (local rects)
        for idx, box_local in enumerate(self.terrain_boxes_local):
            if box_local.collidepoint(mx_local, my_local):
                self.selected_terrain_idx = idx
                return True

        # HEIGHT +/- (local)
        if self.height_minus_local.collidepoint(mx_local, my_local):
            self.selected_height = max(0, self.selected_height - 1)
            return True
        if self.height_plus_local.collidepoint(mx_local, my_local):
            self.selected_height = min(9, self.selected_height + 1)
            return True

        # PASSABLE toggle
        if self.passable_btn_local.collidepoint(mx_local, my_local):
            self.passable = not self.passable
            return True

        # BRUSH size
        if self.brush_minus_local.collidepoint(mx_local, my_local):
            self.brush_size = max(0, self.brush_size - 1)
            return True
        if self.brush_plus_local.collidepoint(mx_local, my_local):
            self.brush_size = min(4, self.brush_size + 1)
            return True

        # Buttons (local)
        for rect_local, action in self.buttons_local:
            if rect_local.collidepoint(mx_local, my_local):
                if action == "new":
                    for k in list(self.hexmap.terrain.keys()):
                        self.hexmap.terrain[k] = {"type":"plain","move_cost":1,"height":1,"passable":True}
                elif action == "save":
                    self.save_map(self.map_name)
                elif action == "load":
                    # show the load overlay
                    self.loading_menu = True
                elif action == "back":
                    return "back"
                return True

        return True

    
    def draw_load_menu(self):
        pygame.draw.rect(self.surface, (20,20,26), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        title = self.title_font.render("Load Map", True, (230,230,230))
        self.surface.blit(title, (40, 20))

        self.load_boxes = []
        y = 80

        for m in self.list_maps():
            rect = pygame.Rect(40, y, WINDOW_WIDTH - 80, 32)
            pygame.draw.rect(self.surface, (60,60,80), rect)
            self.surface.blit(self.font.render(m, True, (255,255,255)), (50, y+6))
            self.load_boxes.append((rect, m))
            y += 40

        back_rect = pygame.Rect(40, y+20, 160, 36)
        pygame.draw.rect(self.surface, (100,60,60), back_rect)
        self.surface.blit(self.font.render("Back", True, (255,255,255)), (85, y+26))
        self.load_back_btn = back_rect

    def handle_load_click(self, mx, my):
        for rect, fname in self.load_boxes:
            if rect.collidepoint(mx, my):
                self.load_map(fname)
                self.loading_menu = False
                return True

        if self.load_back_btn.collidepoint(mx, my):
            self.loading_menu = False
            return True

        return False

    # -------------------------------------------------------------------
    # Main loop
    # -------------------------------------------------------------------
    def run(self):
        pygame.key.set_repeat(300, 35)
        clock = pygame.time.Clock()
        running = True

        while running:
            dt = clock.tick(FPS) / 1000.0
            events = pygame.event.get()

            mx, my = pygame.mouse.get_pos()
            world_x, world_y = self.camera.screen_to_world((mx, my))
            q, r = self.hexmap.pixel_to_hex(world_x, world_y)

            for ev in events:
                if ev.type == pygame.QUIT:
                    running = False
                    return

                if ev.type == pygame.MOUSEWHEEL:
                    self.sidebar_scroll -= ev.y * self.sidebar_scroll_speed

                    # Clamp scrolling so you cannot scroll too far
                    max_scroll = max(0, self.sidebar_content_height - WINDOW_HEIGHT)
                    self.sidebar_scroll = max(0, min(self.sidebar_scroll, max_scroll))

                if self.loading_menu:
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        self.handle_load_click(mx, my)
                    continue

                if ev.type == pygame.MOUSEBUTTONDOWN:
                    if ev.button == 1:
                        # Sidebar click?
                        if mx >= WINDOW_WIDTH - SIDEBAR_W:
                            result = self.handle_ui_click(mx, my)
                            if result == "back":
                                running = False
                                break
                        else:
                            # MAP click
                            self.drawing = True
                            self.apply_brush(q, r)

                    elif ev.button == 3:
                        if mx < WINDOW_WIDTH - SIDEBAR_W:
                            self.sample_tile(q, r)

                if ev.type == pygame.MOUSEBUTTONUP:
                    if ev.button == 1:
                        self.drawing = False

                if ev.type == pygame.MOUSEMOTION:
                    if self.drawing and mx < WINDOW_WIDTH - SIDEBAR_W:
                        self.apply_brush(q, r)

                if ev.type == pygame.KEYDOWN:
                    if self.typing_name:
                        if ev.key == pygame.K_RETURN:
                            self.typing_name = False
                        elif ev.key == pygame.K_BACKSPACE:
                            self.map_name = self.map_name[:-1]
                        else:
                            ch = ev.unicode
                            if ch.isalnum() or ch in "._- ":
                                self.map_name += ch
                        continue
                    if ev.key == pygame.K_UP:
                        self.selected_height = min(9, self.selected_height + 1)
                    elif ev.key == pygame.K_DOWN:
                        self.selected_height = max(0, self.selected_height - 1)
                    elif ev.key == pygame.K_RIGHT:
                        self.brush_size = min(4, self.brush_size + 1)
                    elif ev.key == pygame.K_LEFT:
                        self.brush_size = max(0, self.brush_size - 1)
                    elif ev.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        self.save_map()

            if self.loading_menu:
                self.draw_load_menu()
            else:
                self.surface.fill((30,30,36))
                self.hexmap.draw()
                self.draw_sidebar()

                if self.hexmap.is_inside_grid(q, r):
                    px, py = self.hexmap.hex_to_pixel(q, r)
                    sx2, sy2 = self.camera.apply((px, py))
                    pygame.draw.circle(self.surface, (255,255,0), (int(sx2), int(sy2)), 6, 2)

            pygame.display.flip()
