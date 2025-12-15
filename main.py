# main.py
import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, SETUP_WINDOW_WIDTH, SETUP_WINDOW_HEIGHT
from game_setup import GameSetupScreen

pygame.init()

screen = pygame.display.set_mode((SETUP_WINDOW_WIDTH, SETUP_WINDOW_HEIGHT))
pygame.display.set_caption("Hex Game")

setup = GameSetupScreen(screen)
setup.run()

pygame.quit()
