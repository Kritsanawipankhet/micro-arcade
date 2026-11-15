import pytest

from core.game_manager import GameManager


class FakeGame:
    def __init__(self):
        self.calls = []

    def on_enter(self):
        self.calls.append("enter")

    def update(self, dt, buttons):
        self.calls.append((dt, buttons))

    def render(self, display):
        self.calls.append(display)

    def on_exit(self):
        self.calls.append("exit")


def test_factory_lifecycle_and_forwarding():
    manager = GameManager()
    manager.register("test", FakeGame)
    assert manager.active_game is None
    manager.launch("test")
    first = manager.active_game
    manager.update(0.1, {"jump"})
    output = object()
    manager.render(output)
    assert first.calls == ["enter", (0.1, {"jump"}), output]
    manager.launch("test")
    assert manager.active_game is not first
    assert first.calls[-1] == "exit"
    second = manager.active_game
    manager.close()
    manager.close()
    assert second.calls == ["enter", "exit"]
    assert manager.active_game is None
    manager.update(0.1, set())
    manager.render(output)


def test_invalid_registration_and_launch_preserve_active_game():
    manager = GameManager()
    manager.register("test", FakeGame)
    manager.launch("test")
    active = manager.active_game
    with pytest.raises(ValueError):
        manager.register("test", FakeGame)
    with pytest.raises(TypeError):
        manager.register("bad", None)
    with pytest.raises(ValueError):
        manager.launch("missing")
    assert manager.active_game is active
    assert active.calls == ["enter"]


def test_failed_enter_can_be_cleaned_up():
    class FailingGame(FakeGame):
        def on_enter(self):
            raise RuntimeError("startup failed")

    manager = GameManager()
    manager.register("bad", FailingGame)
    with pytest.raises(RuntimeError):
        manager.launch("bad")
    failed = manager.active_game
    manager.close()
    assert failed.calls == ["exit"]


def test_game_listing_is_ordered_and_returns_a_copy():
    manager = GameManager()
    assert manager.list_games() == []
    manager.register("first", FakeGame)
    manager.register("second", FakeGame, "Second Game")
    games = manager.list_games()
    assert games == [("first", "first"), ("second", "Second Game")]
    games.clear()
    assert len(manager.list_games()) == 2
