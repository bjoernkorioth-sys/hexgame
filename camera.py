import pygame

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.zoom = 1.0

        self.pan_speed = 20
        self.zoom_speed = 0.1

        # Mouse drag state
        self.dragging = False
        self.last_mouse_pos = None

    def apply(self, pos):
        """Apply camera translation and zoom to a world position."""
        x, y = pos
        return (x * self.zoom + self.x, y * self.zoom + self.y)

    def screen_to_world(self, screen_pos):
        """Convert a screen position to world coordinates."""
        sx, sy = screen_pos
        wx = (sx - self.x) / self.zoom
        wy = (sy - self.y) / self.zoom
        return wx, wy

    def handle_input(self, events, keys):
        """Handle keyboard, mouse wheel, and drag panning."""
        # --- Keyboard Panning ---
        if keys[pygame.K_LEFT]:
            self.x += self.pan_speed
        if keys[pygame.K_RIGHT]:
            self.x -= self.pan_speed
        if keys[pygame.K_UP]:
            self.y += self.pan_speed
        if keys[pygame.K_DOWN]:
            self.y -= self.pan_speed

        # --- Mouse Input ---
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.dragging = True
                    self.last_mouse_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False
                    self.last_mouse_pos = None
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                if self.last_mouse_pos:
                    mx, my = event.pos
                    lx, ly = self.last_mouse_pos
                    dx = mx - lx
                    dy = my - ly
                    self.x += dx
                    self.y += dy
                    self.last_mouse_pos = event.pos
            elif event.type == pygame.MOUSEWHEEL:
                # --- Zoom centered on mouse ---
                mouse_pos = pygame.mouse.get_pos()
                before_zoom = self.screen_to_world(mouse_pos)

                if event.y > 0:
                    self.zoom = min(self.zoom + self.zoom_speed, 3.0)
                elif event.y < 0:
                    self.zoom = max(self.zoom - self.zoom_speed, 0.4)

                after_zoom = self.screen_to_world(mouse_pos)

                # Adjust offset so zoom centers on cursor
                self.x += (after_zoom[0] - before_zoom[0]) * self.zoom
                self.y += (after_zoom[1] - before_zoom[1]) * self.zoom
