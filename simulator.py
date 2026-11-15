import argparse

import pygame

from adapters.pc.display import PCDisplay
from adapters.pc.input import PCInput
from adapters.pc.network import TCPNetwork
from core.engine import Engine
from core.game_manager import GameManager
from games.dino.game import DinoGame
from games.pong.game import PongGame
from games.pong.lan import LANPongGame
from scenes.launcher import Launcher


def main(max_frames=None, lan_role=None, address="0.0.0.0", port=50007):
    """Run interactively, or for a bounded number of frames in smoke tests."""
    manager = GameManager()
    try:
        pygame.init()
        display = PCDisplay()
        input_source = PCInput()
        manager.register("dino", DinoGame, "Dino Runner")
        manager.register("pong_bot", PongGame, "Pong vs Bot")
        manager.register("pong_multi", lambda: PongGame("multiplayer"),
                         "Pong 2 Players")
        if lan_role is not None:
            manager.register("pong_lan", lambda: LANPongGame(
                lambda: TCPNetwork(lan_role, address, port), lan_role),
                "Pong LAN " + lan_role.title())
            manager.launch("pong_lan")
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


def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Micro Arcade simulator")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--pong-host", action="store_true")
    group.add_argument("--pong-join", metavar="HOST_IPV4")
    parser.add_argument("--port", type=int, default=50007)
    options = parser.parse_args(args)
    if not 1 <= options.port <= 65535:
        parser.error("port must be between 1 and 65535")
    return options


if __name__ == "__main__":
    options = parse_args()
    role = "host" if options.pong_host else "join" if options.pong_join else None
    main(lan_role=role, address=options.pong_join or "0.0.0.0", port=options.port)
