import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pytest

from adapters.pc.input import PCInput


@pytest.fixture
def source():
    pygame.init()
    pygame.display.set_mode((1, 1))
    pygame.event.clear()
    yield PCInput()
    pygame.quit()


@pytest.mark.parametrize("key,action", [
    (pygame.K_UP, "up"), (pygame.K_DOWN, "down"),
    (pygame.K_LEFT, "left"), (pygame.K_RIGHT, "right"),
    (pygame.K_SPACE, "jump"), (pygame.K_RETURN, "confirm"),
    (pygame.K_ESCAPE, "back"), (pygame.K_r, "restart"),
])
def test_keyboard_mapping_and_release(source, key, action):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    assert source.poll() == {action}
    assert source.poll() == {action}
    assert not source.quit_requested
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key))
    assert source.poll() == set()


def test_multiple_keys_focus_loss_and_quit(source):
    for key in (pygame.K_LEFT, pygame.K_SPACE, pygame.K_a):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    buttons = source.poll()
    assert buttons == {"left", "jump"}
    buttons.clear()
    assert source.poll() == {"left", "jump"}
    pygame.event.post(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert source.poll() == set()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    source.poll()
    assert source.quit_requested
