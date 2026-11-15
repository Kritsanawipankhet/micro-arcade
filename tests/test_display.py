import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

from adapters.pc.display import PCDisplay


def test_display_drawing_and_exact_scaling():
    pygame.init()
    try:
        display = PCDisplay()
        assert display.surface.get_size() == (320, 240)
        assert display.window.get_size() == (640, 480)
        display.clear()
        display.rect(1, 2, 1, 1, (255, 0, 0))
        display.text("Arcade", 10, 10, (255, 255, 255))
        assert any(display.surface.get_at((x, y))[:3] != (0, 0, 0)
                   for x in range(10, 80) for y in range(10, 30))
        display.present()
        for x in (2, 3):
            for y in (4, 5):
                assert display.window.get_at((x, y))[:3] == (255, 0, 0)
        assert display.window.get_at((4, 4))[:3] == (0, 0, 0)
        display.clear()
        assert display.surface.get_at((1, 2))[:3] == (0, 0, 0)
    finally:
        pygame.quit()
