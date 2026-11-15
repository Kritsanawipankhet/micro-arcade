import pytest

from contracts.game import BaseGame
from games.dino.game import DinoGame


def test_initialization_and_grounded_state():
    game = DinoGame()
    assert isinstance(game, BaseGame)
    game.update(0.1, set())
    assert game.player_y == game.GROUND_Y - game.PLAYER_HEIGHT
    assert game.velocity_y == 0
    assert not game.game_over
    assert not game.obstacles


def test_jump_gravity_landing_and_held_input():
    game = DinoGame()
    floor = game.player_y
    game.update(0.1, {"jump"})
    assert game.player_y < floor
    assert game.velocity_y < 0
    game.update(0, set())
    velocity = game.velocity_y
    game.update(0, {"jump"})
    assert game.velocity_y == velocity
    game.update(0.8, {"jump"})
    assert game.player_y == floor
    game.update(0.1, {"jump"})
    assert game.player_y == floor
    game.update(0, set())
    game.update(0.1, {"jump"})
    assert game.player_y < floor


def test_obstacle_spawn_movement_and_removal():
    game = DinoGame()
    game.update(1.9, set())
    assert len(game.obstacles) == 1
    assert game.obstacles[0] == pytest.approx(305, abs=2)
    game.obstacles = [-13.9]
    game.update(0.01, set())
    assert not game.obstacles


def test_collision_stops_score_and_movement():
    game = DinoGame()
    game.update(0.5, set())
    assert game.score == 5
    game.obstacles = [float(game.PLAYER_X)]
    game.update(0.01, set())
    assert game.game_over
    state = (game.score, game.player_y, list(game.obstacles))
    game.update(1, {"jump"})
    assert (game.score, game.player_y, game.obstacles) == state


def test_jump_clears_obstacle_and_large_step_does_not_tunnel():
    game = DinoGame()
    game.player_y = 100.0
    game.obstacles = [float(game.PLAYER_X)]
    game.update(0.01, set())
    assert not game.game_over
    game.on_enter()
    game.obstacles = [100.0]
    game.update(1, set())
    assert game.game_over


def test_restart_resets_all_state_without_repeating_when_held():
    game = DinoGame()
    game.update(0.5, set())
    game.obstacles = [40.0]
    game.update(0.01, set())
    game.update(0.1, {"restart", "jump"})
    assert not game.game_over
    assert game.score == game.elapsed == game.spawn_timer == 0
    assert not game.obstacles
    assert game.velocity_y == 0
    game.update(0.1, {"restart", "jump"})
    assert game.elapsed > 0
    assert game.player_y == game.GROUND_Y - game.PLAYER_HEIGHT
    game.update(0, set())
    game.update(0.1, {"jump"})
    assert game.velocity_y < 0


def test_time_based_movement_and_score():
    first, second = DinoGame(), DinoGame()
    first.update(0.3, {"jump"})
    second.update(0.1, {"jump"})
    second.update(0.2, {"jump"})
    assert first.player_y == pytest.approx(second.player_y)
    assert first.velocity_y == pytest.approx(second.velocity_y)
    assert first.elapsed == pytest.approx(second.elapsed)
    assert abs(first.score - second.score) <= 1


def test_render_uses_contract_and_does_not_change_state():
    calls = []

    class Display:
        def text(self, *args):
            calls.append(("text", args))

        def rect(self, *args):
            calls.append(("rect", args))

    game = DinoGame()
    game.obstacles = [200.0]
    game.game_over = True
    game.render(Display())
    assert any(kind == "text" and "GAME OVER" in args[0]
               for kind, args in calls)
    assert sum(kind == "rect" for kind, args in calls) == 3
    assert game.obstacles == [200.0]
    assert game.score == 0
    game.on_exit()
    assert not game.obstacles


def test_negative_dt_is_rejected():
    with pytest.raises(ValueError):
        DinoGame().update(-0.1, set())
