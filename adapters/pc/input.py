import pygame

from contracts.input import Input


class PCInput(Input):
    KEY_ACTIONS = {
        pygame.K_UP: "up",
        pygame.K_DOWN: "down",
        pygame.K_LEFT: "left",
        pygame.K_RIGHT: "right",
        pygame.K_SPACE: "jump",
        pygame.K_RETURN: "confirm",
        pygame.K_ESCAPE: "back",
        pygame.K_r: "restart",
    }

    def __init__(self):
        super().__init__()
        self._held = set()

    def poll(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_requested = True
            elif event.type == pygame.WINDOWFOCUSLOST:
                self._held.clear()
            elif event.type in (pygame.KEYDOWN, pygame.KEYUP):
                action = self.KEY_ACTIONS.get(event.key)
                if action is not None:
                    if event.type == pygame.KEYDOWN:
                        self._held.add(action)
                    else:
                        self._held.discard(action)
        return self._held.copy()
