# app.py
import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT)
        )
        pygame.display.set_caption("HexGame")

        self.clock = pygame.time.Clock()
        self.running = True
        self.state = None

    def change_state(self, new_state):
        self.state = new_state

    def run(self, start_state):
        self.change_state(start_state)

        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                else:
                    self.state.handle_event(ev)

            self.state.update(dt)
            self.state.draw(self.screen)

            if self.state.done:
                self.change_state(self.state.next_screen)

            pygame.display.flip()

        pygame.quit()
