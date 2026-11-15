import pygame

from contracts.display import Display


class PCDisplay(Display):
    WIDTH = 320
    HEIGHT = 240
    SCALE = 2

    def __init__(self):
        self.window = pygame.display.set_mode(
            (self.WIDTH * self.SCALE, self.HEIGHT * self.SCALE)
        )
        pygame.display.set_caption("Micro Arcade")
        self.surface = pygame.Surface((self.WIDTH, self.HEIGHT))
        self.font = pygame.font.Font(None, 20)

    def clear(self):
        self.surface.fill((0, 0, 0))

    def rect(self, x, y, width, height, color):
        pygame.draw.rect(self.surface, color, (x, y, width, height))

    def text(self, value, x, y, color):
        self.surface.blit(self.font.render(str(value), False, color), (x, y))

    def present(self):
        pygame.transform.scale(self.surface, self.window.get_size(), self.window)
        pygame.display.flip()
