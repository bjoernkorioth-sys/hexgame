# settings.py
import math

# --- Hex and grid configuration ---
HEX_SIZE = 20           # Radius of each hex
GRID_WIDTH = 13         # Number of columns (q)
GRID_HEIGHT = 13        # Number of rows (r)

# --- UI Layout ---
SIDEBAR_WIDTH = 260     # Right-side editor/tools panel
BOTTOM_UI_HEIGHT = 160    # Set >0 if you want a bottom panel later

# --- Calculate hex grid pixel size (pointy-top axial) ---
GRID_PIXEL_WIDTH = math.sqrt(3) * HEX_SIZE * (GRID_WIDTH + (GRID_HEIGHT - 1) / 2.0)
GRID_PIXEL_HEIGHT = (1.5 * HEX_SIZE) * (GRID_HEIGHT - 1) + (2 * HEX_SIZE)

# --- Optional margins around the map ---
# Keep these small; they only help visually (not layout-critical)
MARGIN_LEFT = 20
MARGIN_TOP = 20
MARGIN_RIGHT = 20
MARGIN_BOTTOM = 20

MAP_OFFSET_X = MARGIN_LEFT
MAP_OFFSET_Y = MARGIN_TOP


LOG_WIDTH = 500

# --- Final responsive window size ---
WINDOW_WIDTH = int(
    MARGIN_LEFT +
    GRID_PIXEL_WIDTH +
    MARGIN_RIGHT +
    SIDEBAR_WIDTH
)

WINDOW_HEIGHT = int(
    MARGIN_TOP +
    GRID_PIXEL_HEIGHT +
    MARGIN_BOTTOM +
    BOTTOM_UI_HEIGHT
)

# --- Camera / frame ---
FPS = 60

# --- Visuals ---
BG_COLOR = (20, 20, 30)
HEX_COLOR = (60, 80, 100)
HEX_OUTLINE = (100, 120, 160)
FONT_COLOR = (255, 255, 255)

# --- Gameplay ---
NUM_PLAYERS = 2
UNITS_PER_PLAYER = 2

DEBUG = True

# -------------------------------------------------------
# Terrain definitions (ONE SOURCE OF TRUTH)
# -------------------------------------------------------
# name: {
#     "color": (R,G,B),
#     "move_cost": int,
#     "height": int,
#     "passable": bool
# }

TERRAIN_TYPES = {
    "plain": {
        "color": (180, 170, 110),
        "move_cost": 1,
        "height": 1,
        "passable": True
    },
    "forest": {
        "color": (34, 139, 34),
        "move_cost": 2,
        "height": 1,
        "passable": True
    },
    "mountain": {
        "color": (90, 90, 90),
        "move_cost": 999,
        "height": 3,
        "passable": False
    },
    "water": {
        "color": (40, 100, 160),
        "move_cost": 999,
        "height": 0,
        "passable": False
    },
    "building": {
        "color": (150, 120, 60),
        "move_cost": 1,
        "height": 2,
        "passable": False
    }
}

# List version for UI ordering
TERRAIN_LIST = list(TERRAIN_TYPES.keys())

