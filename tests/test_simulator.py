import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pytest

import simulator


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
