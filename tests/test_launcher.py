from core.game_manager import GameManager
from scenes.launcher import Launcher


class Game:
    def __init__(self):
        self.calls = []

    def on_enter(self):
        self.calls.append("enter")

    def update(self, dt, buttons):
        self.calls.append((dt, buttons))

    def render(self, display):
        self.calls.append("render")

    def on_exit(self):
        self.calls.append("exit")


class Display:
    def __init__(self):
        self.texts = []
        self.rects = []

    def text(self, value, x, y, color):
        self.texts.append(value)

    def rect(self, *args):
        self.rects.append(args)


def setup(count=2):
    manager = GameManager()
    for index in range(count):
        manager.register(str(index), Game, "Game " + str(index))
    return manager, Launcher(manager)


def press(launcher, action):
    launcher.update(0.033, set())
    launcher.update(0.033, {action})


def test_selection_wraps_and_does_not_repeat_when_held():
    manager, launcher = setup(3)
    press(launcher, "up")
    assert launcher.selected == 2
    launcher.update(0.033, {"up"})
    assert launcher.selected == 2
    press(launcher, "down")
    assert launcher.selected == 0
    press(launcher, "down")
    assert launcher.selected == 1
    launcher.update(0.033, {"up", "down"})
    assert launcher.selected == 1
    press(launcher, "back")
    assert manager.active_game is None


def test_enter_back_reenter_and_switch_game():
    manager, launcher = setup()
    press(launcher, "down")
    press(launcher, "confirm")
    first = manager.active_game
    assert first.calls == ["enter"]
    launcher.render(Display())
    launcher.update(0.1, {"confirm"})
    assert first.calls == ["enter", "render", (0.1, set())]
    press(launcher, "back")
    assert first.calls[-1] == "exit"
    assert manager.active_game is None
    assert launcher.selected == 1
    launcher.update(0.033, {"back"})
    assert first.calls.count("exit") == 1
    press(launcher, "confirm")
    second = manager.active_game
    assert second is not first
    press(launcher, "back")
    press(launcher, "up")
    press(launcher, "confirm")
    assert launcher.selected == 0
    assert manager.active_game not in (first, second)
    manager.close()


def test_transition_blocks_held_game_actions_until_release():
    manager, launcher = setup()
    launcher.update(0.01, {"confirm", "jump", "back"})
    game = manager.active_game
    launcher.update(0.01, {"confirm", "jump", "back"})
    assert game.calls[-1] == (0.01, set())
    launcher.update(0.01, set())
    launcher.update(0.01, {"jump"})
    assert game.calls[-1] == (0.01, {"jump"})


def test_empty_menu_is_safe():
    manager, launcher = setup(0)
    for action in ("up", "down", "confirm", "back"):
        press(launcher, action)
    display = Display()
    launcher.render(display)
    assert "No games registered" in display.texts
    assert manager.active_game is None


def test_scrolling_and_menu_rendering():
    manager, launcher = setup(9)
    press(launcher, "up")
    assert launcher.selected == 8
    assert launcher.offset == 3
    display = Display()
    launcher.render(display)
    assert "Game 8" in display.texts
    assert "Game 0" not in display.texts
    assert len(display.rects) == 1
    press(launcher, "down")
    assert launcher.offset == 0
    display = Display()
    launcher.render(display)
    assert "Game 0" in display.texts
    assert "Game 8" not in display.texts
