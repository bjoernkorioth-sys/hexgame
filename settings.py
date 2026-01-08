# settings.py

print("LOADED SETTINGS FROM:", __file__)

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

MAPS_DIR = "maps"

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


# -------------------------------------------------------
# SETUP SCREEN LAYOUT
# -------------------------------------------------------

SETUP_MAP_PREVIEW_SIZE = 300
SETUP_UNIT_LIST_WIDTH = 500
SETUP_ROSTER_WIDTH = 300
SETUP_PANEL_GAP = 40
SETUP_TOP_MARGIN = 100
SETUP_BOTTOM_MARGIN = 100

SETUP_WINDOW_WIDTH = (
    40 +                              # left margin
    SETUP_MAP_PREVIEW_SIZE +
    SETUP_PANEL_GAP +
    SETUP_UNIT_LIST_WIDTH +
    SETUP_PANEL_GAP +
    SETUP_ROSTER_WIDTH +
    40                               # right margin
)

SETUP_WINDOW_HEIGHT = 600


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

# =========================
# UI GLOBAL SCALING
# =========================

UI_BASE_WIDTH  = 1280
UI_BASE_HEIGHT = 720

# used to compute scale factor
def ui_scale(screen_w, screen_h):
    return min(
        screen_w / UI_BASE_WIDTH,
        screen_h / UI_BASE_HEIGHT
    )

# =========================
# UI ANCHOR RATIOS
# =========================

UI_PADDING_RATIO = 0.015

END_TURN_BUTTON = {
    "w": 0.16,
    "h": 0.07,
}

UNIT_HUD = {
    "w": 0.26,
    "h": 0.18,
}

TURN_INDICATOR = {
    "w": 0.22,
    "h": 0.06,
}

# =========================
# COLORS / STYLE
# =========================

UI_BG_COLOR = (20, 20, 20, 180)
UI_BORDER_COLOR = (180, 180, 180)
UI_TEXT_COLOR = (240, 240, 240)

UI_COLORS = {
    "text": (240, 240, 240),

    "button": (70, 130, 180),
    "button_hover": (90, 150, 200),
    "button_border": (255, 255, 255),

    "panel_bg": (35, 35, 50),
    "panel_border": (120, 120, 160),
}
# =========================
# UI RADII (responsive)
# =========================

UI_RADII = {
    "small": 8,
    "medium": 14,
    "large": 22,
}

DEPLOYMENT_ROSTER = {
    "w": 0.28,   # 28% of screen width
    "h": 0.30,   # 30% of screen height
    "padding": 0.04,
    "slot_h": 0.22,  # per unit row height (relative)
}
