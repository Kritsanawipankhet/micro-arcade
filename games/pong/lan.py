from contracts.game import BaseGame
from games.pong.game import PongGame


class LANPongGame(BaseGame):
    VERSION = 1
    CONNECT_TIMEOUT = 30.0
    PEER_TIMEOUT = 5.0

    def __init__(self, transport_factory, role):
        if role not in ("host", "join"):
            raise ValueError("Unknown LAN role")
        self.transport_factory = transport_factory
        self.role = role
        self.transport = None

    def on_enter(self):
        self.on_exit()
        self.game = PongGame("multiplayer")
        self.game.lan_role = self.role
        self.transport = self.transport_factory()
        self.ready = False
        self.sent_hello = False
        self.silence = 0.0
        self.failure = ""
        self.remote_buttons = set()

    def _fail(self, message):
        self.failure = message
        self.ready = False
        self.remote_buttons.clear()
        self.transport.close()

    def update(self, dt, buttons):
        if dt < 0:
            raise ValueError("dt must be nonnegative")
        if self.failure:
            return
        messages = self.transport.poll()
        if self.transport.status in ("error", "closed"):
            self._fail(self.transport.error or "Disconnected")
            return
        self.silence += dt
        if self.transport.status == "connected":
            if not self.sent_hello:
                self.transport.send({"type": "hello", "version": self.VERSION,
                                     "role": self.role})
                self.sent_hello = True
            try:
                for message in messages:
                    self._receive(message)
                    self.silence = 0.0
            except (ValueError, KeyError, TypeError):
                self._fail("Invalid peer message")
                return
            if self.ready and self.silence >= self.PEER_TIMEOUT:
                self._fail("Connection timed out")
                return
            if self.ready:
                if self.role == "host":
                    actions = buttons & {"up", "down", "confirm", "restart"}
                    if "up" in self.remote_buttons:
                        actions.add("p2_up")
                    if "down" in self.remote_buttons:
                        actions.add("p2_down")
                    self.game.update(dt, actions)
                    self.transport.send({"type": "state",
                                         "state": self.game.get_state()})
                else:
                    self.transport.send({"type": "input",
                                         "buttons": sorted(buttons & {"up", "down"})})
        limit = self.PEER_TIMEOUT if self.ready else self.CONNECT_TIMEOUT
        if self.silence >= limit:
            self._fail("Connection timed out")
        elif self.transport.status == "error":
            self._fail(self.transport.error)

    def _receive(self, message):
        kind = message.get("type")
        if not self.ready:
            expected = "join" if self.role == "host" else "host"
            if (kind != "hello" or message.get("version") != self.VERSION
                    or message.get("role") != expected):
                raise ValueError("Incompatible peer")
            self.ready = True
        elif self.role == "host" and kind == "input":
            actions = message.get("buttons")
            if (not isinstance(actions, list) or len(actions) > 2
                    or any(action not in ("up", "down") for action in actions)):
                raise ValueError("Invalid controls")
            self.remote_buttons = set(actions)
        elif self.role == "join" and kind == "state":
            self.game.set_state(message["state"])
        else:
            raise ValueError("Unexpected message")

    def render(self, display):
        if self.failure:
            display.text("PONG LAN - stopped", 16, 40, (240, 240, 240))
            display.text(self.failure[:30], 16, 76, (240, 140, 60))
            display.text("Esc: menu / reconnect", 16, 112, (240, 240, 240))
        elif not self.ready:
            display.text("PONG LAN " + self.role.upper(), 16, 40, (240, 240, 240))
            display.text("Waiting for other player...", 16, 76, (240, 240, 240))
            display.text("Esc: cancel", 16, 112, (240, 240, 240))
        else:
            self.game.render(display)

    def on_exit(self):
        if self.transport is not None:
            self.transport.close()
            self.transport = None
