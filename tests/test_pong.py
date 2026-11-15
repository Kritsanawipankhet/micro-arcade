import pytest

from contracts.game import BaseGame
from games.pong.game import PongGame


@pytest.mark.parametrize("mode", ["bot", "multiplayer"])
def test_initialization_serve_and_restart(mode):
    game = PongGame(mode)
    assert isinstance(game, BaseGame)
    assert game.scores == [0, 0] and game.serving
    x = game.ball_x
    game.update(0.1, set())
    assert game.ball_x == x
    game.update(0.1, {"confirm"})
    assert game.ball_x > x and not game.serving
    game.scores = [3, 2]
    game.winner = 0
    game.update(0.1, {"restart"})
    assert game.scores == [0, 0] and game.winner is None
    assert game.serving and game.mode == mode
    game.scores[0] = 1
    game.update(0.1, {"restart"})
    assert game.scores == [1, 0]
    game.on_exit()
    assert not game._held


def test_two_players_independent_movement_and_limits():
    game = PongGame("multiplayer")
    start = game.left_y
    game.update(0.1, {"up", "p2_down"})
    assert game.left_y == pytest.approx(start - 18)
    assert game.right_y == pytest.approx(start + 18)
    game.update(2, {"up", "p2_down"})
    assert game.left_y == game.TOP
    assert game.right_y == game.BOTTOM - game.PADDLE_HEIGHT
    positions = (game.left_y, game.right_y)
    game.update(0.1, {"up", "down", "p2_up", "p2_down"})
    assert (game.left_y, game.right_y) == positions


def test_bot_moves_at_limited_speed_and_ignores_player_two():
    game = PongGame()
    game.ball_y = game.TOP
    start = game.right_y
    game.update(0.1, {"p2_down"})
    assert game.right_y == pytest.approx(start - game.BOT_SPEED * 0.1)
    game.update(2, set())
    assert game.right_y == game.TOP


@pytest.mark.parametrize("bottom", [False, True])
def test_wall_reflection(bottom):
    game = PongGame("multiplayer")
    game.serving = False
    game.ball_y = game.BOTTOM - game.BALL_SIZE - 0.1 if bottom else game.TOP + 0.1
    game.ball_vy = 100 if bottom else -100
    game.update(0.01, set())
    assert game.TOP <= game.ball_y <= game.BOTTOM - game.BALL_SIZE
    assert (game.ball_vy < 0) == bottom


@pytest.mark.parametrize("right", [False, True])
def test_paddle_collision_and_hit_position(right):
    game = PongGame("multiplayer")
    game.serving = False
    game.ball_x = game.RIGHT_X - game.BALL_SIZE - 0.1 if right else (
        game.LEFT_X + game.PADDLE_WIDTH + 0.1)
    game.ball_y = game.left_y + 1
    game.ball_vx = game.BALL_SPEED if right else -game.BALL_SPEED
    game.ball_vy = 0
    game.update(0.01, set())
    assert (game.ball_vx < 0) == right
    assert game.ball_vy < 0
    assert game.scores == [0, 0]


@pytest.mark.parametrize("scorer", [0, 1])
def test_scoring_once_serve_requires_release_and_no_score_limit(scorer):
    game = PongGame("multiplayer")
    game.update(0, {"confirm"})
    game.ball_x = game.WIDTH if scorer == 0 else -game.BALL_SIZE
    game.ball_vx = game.BALL_SPEED if scorer == 0 else -game.BALL_SPEED
    game.update(0.02, {"confirm"})
    assert game.scores[scorer] == 1 and game.serving
    game.update(0.1, {"confirm"})
    assert game.serving and game.scores[scorer] == 1
    game.update(0, set())
    game.update(0, {"confirm"})
    assert not game.serving
    game.scores[scorer] = 4
    game.ball_x = game.WIDTH if scorer == 0 else -game.BALL_SIZE
    game.ball_vx = game.BALL_SPEED if scorer == 0 else -game.BALL_SPEED
    game.update(0.02, set())
    assert game.winner is None and game.scores[scorer] == 5
    assert not game.finished
    game.time_left = 0.01
    game.update(0.02, set())
    assert game.finished and game.winner == scorer
    state = (game.ball_x, game.ball_y, game.left_y)
    game.update(1, {"up", "confirm"})
    assert (game.ball_x, game.ball_y, game.left_y) == state


def test_large_dt_cannot_skip_paddle():
    game = PongGame("multiplayer")
    game.serving = False
    game.ball_x = 80
    game.ball_y = game.left_y + 12
    game.ball_vx = -game.BALL_SPEED
    game.ball_vy = 0
    game.update(0.5, set())
    assert game.ball_vx > 0
    assert game.scores == [0, 0]


def test_time_based_movement():
    first, second = PongGame("multiplayer"), PongGame("multiplayer")
    first.update(0.3, {"confirm", "up"})
    second.update(0.1, {"confirm", "up"})
    second.update(0.2, {"confirm", "up"})
    assert first.ball_x == pytest.approx(second.ball_x)
    assert first.ball_y == pytest.approx(second.ball_y)
    assert first.left_y == pytest.approx(second.left_y)


def test_render_contract_and_invalid_arguments():
    class Display:
        def __init__(self):
            self.texts = []

        def text(self, value, *args):
            self.texts.append(value)

        def rect(self, *args):
            assert all(isinstance(value, int) for value in args[:4])

    game = PongGame()
    display = Display()
    game.render(display)
    assert "Enter: serve" in display.texts
    game.winner = 1
    game.finished = True
    game.render(display)
    assert "BOT WINS!" in display.texts
    assert game.scores == [0, 0]
    with pytest.raises(ValueError):
        PongGame("unknown")
    with pytest.raises(ValueError):
        game.update(-1, set())


@pytest.mark.parametrize("mode", ["bot", "multiplayer"])
def test_timer_starts_on_first_serve_and_runs_between_points(mode):
    game = PongGame(mode)
    game.update(2, set())
    assert game.time_left == 240 and not game.started
    game.update(0.5, {"confirm"})
    assert game.started
    assert game.time_left == pytest.approx(239.5)
    game.serving = True
    game.update(0.5, set())
    assert game.time_left == pytest.approx(239)


@pytest.mark.parametrize("mode", ["bot", "multiplayer"])
@pytest.mark.parametrize("scores,winner", [([8, 2], 0), ([1, 7], 1), ([3, 3], None)])
def test_timeout_result_and_frozen_state(mode, scores, winner):
    game = PongGame(mode)
    game.started = True
    game.time_left = 0.01
    game.scores = scores[:]
    game.update(2, set())
    assert game.time_left == 0
    assert game.finished and game.winner == winner
    state = (game.ball_x, game.ball_y, game.left_y, game.right_y)
    game.update(3, {"confirm", "up", "p2_down"})
    assert game.scores == scores
    assert (game.ball_x, game.ball_y, game.left_y, game.right_y) == state
    game.update(0.1, {"restart"})
    assert game.time_left == 240 and not game.started and not game.finished
    assert game.winner is None and game.scores == [0, 0]


def test_timeout_does_not_simulate_past_deadline():
    game = PongGame("multiplayer")
    game.started = True
    game.serving = False
    game.time_left = 0.001
    game.ball_x = 319
    game.ball_vx = 165
    game.update(1, set())
    assert game.finished and game.scores == [0, 0]
    assert game.ball_x == pytest.approx(319.165)


def test_timer_and_draw_rendering():
    class Display:
        def __init__(self):
            self.texts = []

        def text(self, value, *args):
            self.texts.append(value)

        def rect(self, *args):
            pass

    game = PongGame()
    for time_left, text in [(240, "Time 4:00"), (239.1, "Time 4:00"),
                            (239, "Time 3:59"), (0.1, "Time 0:01")]:
        game.time_left = time_left
        display = Display()
        game.render(display)
        assert text in display.texts
    game.started = True
    game.time_left = 0.001
    game.update(0.01, set())
    display = Display()
    game.render(display)
    assert "Time 0:00" in display.texts and "DRAW" in display.texts
    assert "Enter: serve" not in display.texts
