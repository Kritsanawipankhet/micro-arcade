import pygame

from adapters.pc.display import PCDisplay
from adapters.pc.input import PCInput
from core.engine import Engine
from core.game_manager import GameManager
from games.dino.game import DinoGame
from scenes.launcher import Launcher


def main(max_frames=None):
    """Run interactively, or for a bounded number of frames in smoke tests."""
    manager = GameManager()
    try:
        pygame.init()
        display = PCDisplay()
        input_source = PCInput()
        manager.register("dino", DinoGame, "Dino Runner")
        engine = Engine(display, input_source, Launcher(manager))
        clock = pygame.time.Clock()
        frames = 0
        while max_frames is None or frames < max_frames:
            dt = clock.tick(30) / 1000.0
            if not engine.step(dt):
                break
            frames += 1
    finally:
        try:
            manager.close()
        finally:
            pygame.quit()


if __name__ == "__main__":
    main()
