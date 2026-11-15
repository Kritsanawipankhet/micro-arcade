import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pytest

import simulator


def test_lan_command_line_options():
    assert simulator.parse_args(["--pong-host"]).pong_host
    assert simulator.parse_args(["--pong-join", "127.0.0.1"]).pong_join == "127.0.0.1"
    assert simulator.parse_args(["--port", "50008"]).port == 50008
    with pytest.raises(SystemExit):
        simulator.parse_args(["--pong-host", "--pong-join", "127.0.0.1"])
    with pytest.raises(SystemExit):
        simulator.parse_args(["--port", "0"])


@pytest.mark.parametrize("role", ["host", "join"])
def test_lan_simulator_starts_waiting_and_closes_transport(monkeypatch, role):
    class Network:
        status = "connecting"
        error = ""

        def poll(self):
            return []

        def close(self):
            self.status = "closed"

    network = Network()
    monkeypatch.setattr(simulator, "TCPNetwork", lambda *args: network)
    simulator.main(max_frames=2, lan_role=role, address="127.0.0.1")
    assert network.status == "closed"
    assert not pygame.get_init()


def test_bounded_loop_uses_seconds_and_cleans_up(monkeypatch):
    steps = []
    ticks = []

    class FakeClock:
        def tick(self, fps):
            ticks.append(fps)
            return 33

    original_step = simulator.Engine.step

    def step(engine, dt):
        steps.append(dt)
        return original_step(engine, dt)

    monkeypatch.setattr(pygame.time, "Clock", FakeClock)
    monkeypatch.setattr(simulator.Engine, "step", step)
    simulator.main(max_frames=3)
    assert ticks == [30, 30, 30]
    assert steps == [0.033, 0.033, 0.033]
    assert not pygame.get_init()


def test_window_close_terminates_loop(monkeypatch):
    original_input = simulator.PCInput

    def closing_input():
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        return original_input()

    monkeypatch.setattr(simulator, "PCInput", closing_input)
    simulator.main(max_frames=3)
    assert not pygame.get_init()


def test_cleanup_after_initialization_failure(monkeypatch):
    def fail():
        raise RuntimeError("display unavailable")

    monkeypatch.setattr(simulator, "PCDisplay", fail)
    with pytest.raises(RuntimeError, match="display unavailable"):
        simulator.main(max_frames=1)
    assert not pygame.get_init()


def test_startup_stays_in_menu_without_creating_game(monkeypatch):
    def unexpected_game():
        raise AssertionError("Game must wait for confirm")

    monkeypatch.setattr(simulator, "DinoGame", unexpected_game)
    simulator.main(max_frames=2)
    assert not pygame.get_init()


@pytest.mark.parametrize("selection,mode", [(1, "bot"), (2, "multiplayer")])
def test_pong_modes_launch_play_and_return_to_menu(monkeypatch, selection, mode):
    launched = []
    original_game = simulator.PongGame
    original_step = simulator.Engine.step
    actions = []
    for _ in range(selection):
        actions.extend([{"down"}, set()])
    actions.extend([{"confirm"}, set(), {"confirm"}, set(), {"back"}])

    class Input:
        quit_requested = False

        def poll(self):
            return actions.pop(0)

    def factory(mode="bot"):
        game = original_game(mode)
        launched.append(game)
        return game

    def step(engine, dt):
        result = original_step(engine, dt)
        if not actions:
            assert engine.scene.manager.active_game is None
        return result

    monkeypatch.setattr(simulator, "PCInput", Input)
    monkeypatch.setattr(simulator, "PongGame", factory)
    monkeypatch.setattr(simulator.Engine, "step", step)
    simulator.main(max_frames=len(actions))
    assert len(launched) == 1
    assert launched[0].mode == mode
    assert not launched[0].serving
    assert not pygame.get_init()


@pytest.mark.parametrize("fail_update", [False, True])
def test_registered_game_lifecycle_and_cleanup(monkeypatch, fail_update):
    calls = []

    class Game:
        def on_enter(self):
            calls.append("enter")

        def update(self, dt, buttons):
            calls.append("update")
            if fail_update:
                raise RuntimeError("update failed")

        def render(self, display):
            calls.append("render")

        def on_exit(self):
            assert pygame.get_init()
            calls.append("exit")

    monkeypatch.setattr(simulator, "DinoGame", Game)
    original_input = simulator.PCInput

    def confirming_input():
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        return original_input()

    monkeypatch.setattr(simulator, "PCInput", confirming_input)
    if fail_update:
        with pytest.raises(RuntimeError, match="update failed"):
            simulator.main(max_frames=2)
        assert calls == ["enter", "render", "update", "exit"]
    else:
        simulator.main(max_frames=2)
        assert calls == ["enter", "render", "update", "render", "exit"]
    assert not pygame.get_init()
