import time

import pytest

from adapters.pc.network import TCPNetwork
from games.pong.game import PongGame
from games.pong.lan import LANPongGame


class Transport:
    def __init__(self):
        self.status = "connected"
        self.error = ""
        self.messages = []
        self.sent = []

    def poll(self):
        messages, self.messages = self.messages, []
        return messages

    def send(self, message):
        self.sent.append(message)

    def close(self):
        self.status = "closed"


def session(role="host"):
    transport = Transport()
    game = LANPongGame(lambda: transport, role)
    game.on_enter()
    transport.messages = [{"type": "hello", "version": 1,
                           "role": "join" if role == "host" else "host"}]
    game.update(0, set())
    assert game.ready
    return game, transport


def test_host_controls_physics_and_remote_paddle():
    game, transport = session()
    y = game.game.right_y
    transport.messages = [{"type": "input", "buttons": ["down"]}]
    game.update(0.1, {"up", "confirm"})
    assert game.game.right_y > y and game.game.left_y < y
    assert game.game.started and game.game.time_left < 240
    assert transport.sent[-1]["state"] == game.game.get_state()
    transport.messages = [{"type": "input", "buttons": []}]
    game.update(0.1, set())
    assert game.remote_buttons == set()


def test_join_only_sends_controls_and_renders_authoritative_state():
    game, transport = session("join")
    state = PongGame("multiplayer").get_state()
    state.update(scores=[4, 2], time_left=123.0, left_y=50.0)
    transport.messages = [{"type": "state", "state": state}]
    game.update(0.1, {"up", "confirm", "restart", "p2_down"})
    assert game.game.get_state() == state
    assert transport.sent[-1] == {"type": "input", "buttons": ["up"]}
    game.update(1, set())
    assert game.game.get_state() == state


@pytest.mark.parametrize("message", [
    {"type": "hello", "version": 99, "role": "join"},
    {"type": "hello", "version": 1, "role": "host"},
    {"type": "input", "buttons": []},
])
def test_bad_handshake_stops_session(message):
    transport = Transport()
    game = LANPongGame(lambda: transport, "host")
    game.on_enter()
    transport.messages = [message]
    game.update(0.1, set())
    assert game.failure and transport.status == "closed"


@pytest.mark.parametrize("actions", [["restart"], "up", ["up", "down", "up"], [None]])
def test_remote_cannot_restart_or_send_invalid_controls(actions):
    game, transport = session()
    transport.messages = [{"type": "input", "buttons": actions}]
    game.update(0.1, set())
    assert game.failure and not game.ready


def test_timeout_disconnect_and_reenter_cleanup():
    game, transport = session()
    state = game.game.get_state()
    game.update(game.PEER_TIMEOUT, set())
    assert game.failure and transport.status == "closed"
    assert game.game.get_state() == state
    stopped = game.game.get_state()
    game.update(1, {"confirm"})
    assert game.game.get_state() == stopped
    game.on_exit()
    game.on_exit()
    assert game.transport is None
    waiting = Transport()
    waiting.status = "connecting"
    game.transport_factory = lambda: waiting
    game.on_enter()
    game.update(30, set())
    assert game.failure == "Connection timed out"
    assert game.game.get_state() == state


@pytest.mark.parametrize("field,value", [
    ("ball_x", float("nan")), ("time_left", float("inf")),
    ("left_y", -100), ("scores", [-1, 2]), ("scores", [True, 0]),
    ("finished", 1), ("winner", 7), ("ball_vx", "fast"),
])
def test_invalid_snapshot_is_atomic(field, value):
    game = PongGame("multiplayer")
    original = game.get_state()
    state = game.get_state()
    state[field] = value
    with pytest.raises(ValueError):
        game.set_state(state)
    assert game.get_state() == original


def test_invalid_snapshot_stops_join_and_disconnect_freezes_game():
    game, transport = session("join")
    transport.messages = [{"type": "state", "state": {}}]
    game.update(0.1, set())
    assert game.failure
    game, transport = session()
    transport.status = "error"
    transport.error = "Peer disconnected"
    game.update(1, {"confirm"})
    assert game.failure == "Peer disconnected"
    assert not game.game.started


def test_real_loopback_session_sync_and_cleanup():
    host_transport = TCPNetwork("host", "127.0.0.1", 0)
    host = LANPongGame(lambda: host_transport, "host")
    join = LANPongGame(lambda: TCPNetwork(
        "join", "127.0.0.1", host_transport.port), "join")
    host.on_enter()
    join.on_enter()
    try:
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            host.update(0.01, set())
            join.update(0.01, {"down"})
            if host.remote_buttons == {"down"} and join.game.right_y > 110:
                break
            time.sleep(0.001)
        else:
            pytest.fail("LAN session did not synchronize")
        assert host.ready and join.ready
        # Freeze host physics and pump the final snapshot to Join.
        for _ in range(10):
            host.update(0, set())
            join.update(0, set())
            time.sleep(0.001)
        assert join.game.get_state() == host.game.get_state()
        join.on_exit()
        deadline = time.monotonic() + 2
        while not host.failure and time.monotonic() < deadline:
            host.update(0.01, set())
            time.sleep(0.001)
        assert host.failure
    finally:
        host.on_exit()
        join.on_exit()


def test_waiting_and_failure_screens_use_display_contract():
    class Display:
        def __init__(self):
            self.texts = []

        def text(self, value, *args):
            self.texts.append(value)

    transport = Transport()
    transport.status = "connecting"
    game = LANPongGame(lambda: transport, "host")
    game.on_enter()
    display = Display()
    game.render(display)
    assert "Waiting for other player..." in display.texts
    game.update(31, set())
    game.render(display)
    assert "Connection timed out" in display.texts
