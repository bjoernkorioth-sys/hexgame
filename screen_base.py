# screen_base.py
class Screen:
    def __init__(self, app):
        self.app = app
        self.done = False
        self.next_screen = None

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass
