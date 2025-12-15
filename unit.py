# unit.py
import pygame
import random
import hexmap

class Unit:
    FONT = None  # lazy init
    TOOLTIP_FONT = None
    

    CLASS_COLORS = {
        "captain": (255, 215, 0),     # gold
        "soldier": (0, 200, 0),       # green
        "marksman": (100, 100, 255),  # blue
    }

    def __init__(
        self,
        q,
        r,
        owner=0,
        move_range=3,
        hp=1,
        save=3,
        morale=8,
        category="henchman",
        unit_class="soldier",
        melee=None,
        ranged=None,
        action_points=2,
    ):
        
        self.cost = hasattr(self, "cost") and self.cost or 0
        self.icon = None
        
        # Position
        self.q = q
        self.r = r
        self.owner = owner

        # Core stats
        self.move_range = move_range
        self.hp = hp
        self.save = save
        self.morale = morale
        self.category = category
        self.unit_class = unit_class
        self.max_action_points = action_points
        self.action_points = action_points

        # Weapons
        self.melee = melee or {"attack": 1, "hit": 3, "damage": 1, "range": 1}
        self.ranged = ranged or {"attack": 0, "hit": 0, "damage": 0, "range": 0}

        # Visual color by class
        self.color = self.CLASS_COLORS.get(unit_class, (200, 200, 200))

        # lazy font init (safe if pygame wasn't set up earlier)
        if Unit.FONT is None:
            try:
                if not pygame.get_init():
                    pygame.init()
                if not pygame.font.get_init():
                    pygame.font.init()
                Unit.FONT = pygame.font.Font(None, 18)
                Unit.TOOLTIP_FONT = pygame.font.Font(None, 18)
            except Exception:
                # fallback: set to None and avoid any font rendering
                Unit.FONT = None
                Unit.TOOLTIP_FONT = None

    # Drawing
    def draw(self, surface, camera, hexmap, show_tooltip=False, mouse_pos=None):
        # compute pixel pos
        x, y = hexmap.hex_to_pixel(self.q, self.r)
        sx_f, sy_f = camera.apply((x, y))
        sx, sy = int(sx_f), int(sy_f)
        radius = max(4, int(hexmap.size * 0.4))

        # unit body
        pygame.draw.circle(surface, self.color, (sx, sy), radius)

        # outline by owner
        outline_color = (255, 50, 50) if self.owner == 1 else (50, 255, 50)
        pygame.draw.circle(surface, outline_color, (sx, sy), radius, 2)

        # class symbol
        self.draw_symbol(surface, sx, sy, radius)

        # HP bar
        bar_w = radius * 2
        bar_h = 4
        hp_ratio = max(0.0, min(1.0, self.hp / 2.0))
        pygame.draw.rect(surface, (60, 60, 60), (sx - radius, sy + radius + 3, bar_w, bar_h))
        if self.hp > 0:
            pygame.draw.rect(surface, (0, 255, 0), (sx - radius, sy + radius + 3, int(bar_w * hp_ratio), bar_h))

        # AP text (use FONT if available)
        if Unit.FONT:
            ap_text = Unit.FONT.render(str(self.action_points), True, (255, 255, 255))
            surface.blit(ap_text, (sx - 5, sy - 10))

        # tooltip
        if show_tooltip and mouse_pos and Unit.TOOLTIP_FONT:
            self.draw_tooltip(surface, mouse_pos)

    def draw_symbol(self, surface, sx, sy, radius):
        if self.unit_class == "captain":
            pygame.draw.polygon(surface, (255, 255, 255),
                                [(sx, sy - radius // 2), (sx - radius // 2, sy + radius // 2), (sx + radius // 2, sy + radius // 2)])
        elif self.unit_class == "soldier":
            pygame.draw.rect(surface, (255, 255, 255), pygame.Rect(sx - 5, sy - 5, 10, 10))
        elif self.unit_class == "marksman":
            pygame.draw.line(surface, (255, 255, 255), (sx - 6, sy), (sx + 6, sy), 2)
            pygame.draw.line(surface, (255, 255, 255), (sx, sy - 6), (sx, sy + 6), 2)

    def draw_tooltip(self, surface, mouse_pos):
        lines = [
            f"{self.unit_class.capitalize()} ({'P1' if self.owner == 0 else 'P2'})",
            f"HP: {self.hp}",
            f"AP: {self.action_points}/{self.max_action_points}",
            f"Morale: {self.morale}",
            f"Save: {self.save}+",
            f"Move: {self.move_range}",
        ]
        text_surfaces = [Unit.TOOLTIP_FONT.render(line, True, (255, 255, 255)) for line in lines]
        width = max(ts.get_width() for ts in text_surfaces) + 8
        height = sum(ts.get_height() for ts in text_surfaces) + 8

        x, y = mouse_pos
        tooltip_rect = pygame.Rect(int(x + 15), int(y + 15), width, height)
        pygame.draw.rect(surface, (30, 30, 30), tooltip_rect)
        pygame.draw.rect(surface, (200, 200, 200), tooltip_rect, 1)

        y_off = tooltip_rect.top + 4
        for ts in text_surfaces:
            surface.blit(ts, (tooltip_rect.left + 4, y_off))
            y_off += ts.get_height()

    # Combat helpers
    def perform_attack(self, target, weapon_type="melee"):
        weapon = self.melee if weapon_type == "melee" else self.ranged
        if weapon["attack"] <= 0:
            return (0, 0, False)
        hits = unsaved = 0
        for _ in range(weapon["attack"]):
            if random.randint(1, 6) <= weapon["hit"]:
                hits += 1
                if random.randint(1, 6) > target.save:
                    unsaved += 1
        damage = unsaved * weapon["damage"]
        target.hp -= damage
        killed = target.hp <= 0
        # consume AP if available
        if hasattr(self, "action_points") and self.action_points > 0:
            self.action_points -= 1
        return hits, unsaved, killed

    def can_attack(self, target, weapon_type="melee"):
        # approximate axial distance (cube distance)
        dq = abs(self.q - target.q)
        dr = abs(self.r - target.r)
        # convert axial to cube difference and compute distance robustly
        # using axial-to-cube conversion
        ax = self.q
        az = self.r
        ay = -ax - az
        bx = target.q
        bz = target.r
        by = -bx - bz
        return (abs(ax - bx) + abs(ay - by) + abs(az - bz)) // 2 <= (self.melee["range"] if weapon_type=="melee" else self.ranged["range"])

    def reset_actions(self):
        self.action_points = self.max_action_points

    def is_alive(self):
        return self.hp > 0
    
    def load_icon(self, path):
        try:
            img = pygame.image.load(path).convert_alpha()
            self.icon = pygame.transform.scale(img, (48, 48))
        except:
            self.icon = None

# ======================================================
# ROSTER DEFINITIONS
# ======================================================

def create_roster(player_id):
    """Creates a starting roster for the given player (1 or 2)."""
    color_shift = (0, 150, 0) if player_id == 0 else (150, 0, 0)
    start_col = 1 if player_id == 0 else 13

    roster = [
        Unit(
            q=start_col,
            r=2,
            owner=player_id,
            move_range=3,
            hp=2,
            save=3,
            morale=10,
            category="leader",
            unit_class="captain",
            melee={"attack": 2, "hit": 3, "damage": 2, "range": 1},
            action_points=3,
        ),
        Unit(
            q=start_col,
            r=4,
            owner=player_id,
            move_range=3,
            hp=1,
            save=2,
            morale=8,
            category="henchman",
            unit_class="soldier",
            melee={"attack": 2, "hit": 3, "damage": 2, "range": 1},
            action_points=2,
        ),
        Unit(
            q=start_col,
            r=6,
            owner=player_id,
            move_range=3,
            hp=1,
            save=1,
            morale=8,
            category="henchman",
            unit_class="marksman",
            melee={"attack": 1, "hit": 1, "damage": 1, "range": 1},
            ranged={"attack": 1, "hit": 3, "damage": 1, "range": 10},
            action_points=2,
        ),
    ]
    return roster



