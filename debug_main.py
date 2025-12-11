# debug_main.py
import pygame, sys
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, HEX_SIZE
from camera import Camera
from hexmap import HexMap
from unit import Unit

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()

camera = Camera()
hexmap = HexMap(screen, camera)

# create a test unit after pygame.init
u = Unit(4, 4, owner=0, unit_class="captain", hp=2, action_points=3)

running = True
while running:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    screen.fill((30, 30, 30))
    # draw a single hex center so we see something
    x,y = hexmap.hex_to_pixel(4,4)
    sx, sy = camera.apply((x,y))
    pygame.draw.circle(screen, (80,80,120), (int(sx), int(sy)), 4)

    # draw the unit
    u.draw(screen, camera, hexmap, show_tooltip=True, mouse_pos=pygame.mouse.get_pos())

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
