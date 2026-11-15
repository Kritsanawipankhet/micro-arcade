from contracts.game import BaseGame


class PongGame(BaseGame):
    WIDTH = 320
    TOP = 36
    BOTTOM = 208
    PADDLE_WIDTH = 6
    PADDLE_HEIGHT = 36
    LEFT_X = 12
    RIGHT_X = 302
    BALL_SIZE = 6
    PADDLE_SPEED = 180.0
    BOT_SPEED = 115.0
    BALL_SPEED = 165.0
    MATCH_DURATION = 240.0
    MAX_STEP = 1.0 / 120

    def __init__(self, mode="bot"):
        if mode not in ("bot", "multiplayer"):
            raise ValueError("Unknown Pong mode: " + mode)
        self.mode = mode
        self.lan_role = None
        self.on_enter()

    def on_enter(self):
        self.left_y = self.right_y = (self.TOP + self.BOTTOM
                                      - self.PADDLE_HEIGHT) / 2.0
        self.scores = [0, 0]
        self.winner = None
        self.finished = False
        self.started = False
        self.time_left = self.MATCH_DURATION
        self._held = set()
        self._reset_ball(1)

    def _reset_ball(self, direction):
        self.ball_x = (self.WIDTH - self.BALL_SIZE) / 2.0
        self.ball_y = (self.TOP + self.BOTTOM - self.BALL_SIZE) / 2.0
        self.ball_vx = direction * self.BALL_SPEED
        self.ball_vy = 55.0
        self.serving = True

    def get_state(self):
        return {
            "left_y": self.left_y, "right_y": self.right_y,
            "ball_x": self.ball_x, "ball_y": self.ball_y,
            "ball_vx": self.ball_vx, "ball_vy": self.ball_vy,
            "scores": self.scores[:], "winner": self.winner,
            "finished": self.finished, "started": self.started,
            "time_left": self.time_left, "serving": self.serving,
        }

    def set_state(self, state):
        """Validate the complete snapshot before changing local state."""
        if not isinstance(state, dict):
            raise ValueError("Invalid game state")
        limits = {
            "left_y": (self.TOP, self.BOTTOM - self.PADDLE_HEIGHT),
            "right_y": (self.TOP, self.BOTTOM - self.PADDLE_HEIGHT),
            "ball_x": (-self.BALL_SIZE - 10, self.WIDTH + 10),
            "ball_y": (self.TOP, self.BOTTOM - self.BALL_SIZE),
            "ball_vx": (-200, 200), "ball_vy": (-200, 200),
            "time_left": (0, self.MATCH_DURATION),
        }
        for name, bounds in limits.items():
            value = state.get(name)
            if (type(value) not in (int, float)
                    or not bounds[0] <= value <= bounds[1]):
                raise ValueError("Invalid state field: " + name)
        for name in ("finished", "started", "serving"):
            if type(state.get(name)) is not bool:
                raise ValueError("Invalid state field: " + name)
        scores = state.get("scores")
        if (not isinstance(scores, list) or len(scores) != 2
                or any(type(score) is not int or not 0 <= score <= 10000
                       for score in scores)):
            raise ValueError("Invalid scores")
        winner = state.get("winner")
        if winner is not None and (type(winner) is not int or winner not in (0, 1)):
            raise ValueError("Invalid winner")
        for name in limits:
            setattr(self, name, state[name])
        for name in ("finished", "started", "serving"):
            setattr(self, name, state[name])
        self.scores = scores[:]
        self.winner = winner

    def update(self, dt, buttons):
        if dt < 0:
            raise ValueError("dt must be nonnegative")
        pressed = buttons - self._held
        self._held = buttons.copy()
        if "restart" in pressed:
            self.on_enter()
            self._held = buttons.copy()
            return
        if self.finished:
            return
        if self.serving and "confirm" in pressed:
            self.serving = False
            self.started = True
        remaining = dt
        while remaining > 0 and not self.finished:
            step = min(remaining, self.MAX_STEP)
            if self.started:
                step = min(step, self.time_left)
            self._advance(step, buttons)
            remaining -= step
            if self.started:
                self.time_left = max(0.0, self.time_left - step)
                if self.time_left <= 0:
                    self.finished = True
                    if self.scores[0] != self.scores[1]:
                        self.winner = 0 if self.scores[0] > self.scores[1] else 1

    def _move_paddle(self, y, direction, speed, dt):
        return max(self.TOP, min(self.BOTTOM - self.PADDLE_HEIGHT,
                                y + direction * speed * dt))

    def _advance(self, dt, buttons):
        direction = int("down" in buttons) - int("up" in buttons)
        self.left_y = self._move_paddle(
            self.left_y, direction, self.PADDLE_SPEED, dt)
        if self.mode == "multiplayer":
            direction = int("p2_down" in buttons) - int("p2_up" in buttons)
            self.right_y = self._move_paddle(
                self.right_y, direction, self.PADDLE_SPEED, dt)
        else:
            target = self.ball_y + self.BALL_SIZE / 2 - self.PADDLE_HEIGHT / 2
            # Move toward the ball without teleporting or overshooting.
            distance = max(-self.BOT_SPEED * dt,
                           min(self.BOT_SPEED * dt, target - self.right_y))
            self.right_y = max(self.TOP, min(
                self.BOTTOM - self.PADDLE_HEIGHT, self.right_y + distance))
        if self.serving:
            return

        previous_x = self.ball_x
        self.ball_x += self.ball_vx * dt
        self.ball_y += self.ball_vy * dt
        if self.ball_y < self.TOP:
            self.ball_y = 2 * self.TOP - self.ball_y
            self.ball_vy = abs(self.ball_vy)
        elif self.ball_y + self.BALL_SIZE > self.BOTTOM:
            self.ball_y = 2 * (self.BOTTOM - self.BALL_SIZE) - self.ball_y
            self.ball_vy = -abs(self.ball_vy)

        left_face = self.LEFT_X + self.PADDLE_WIDTH
        right_face = self.RIGHT_X - self.BALL_SIZE
        if (self.ball_vx < 0 and previous_x >= left_face
                and self.ball_x <= left_face and self._overlaps(self.left_y)):
            self.ball_x = left_face
            self._bounce(self.left_y, 1)
        elif (self.ball_vx > 0 and previous_x <= right_face
                and self.ball_x >= right_face and self._overlaps(self.right_y)):
            self.ball_x = right_face
            self._bounce(self.right_y, -1)

        scorer = None
        if self.ball_x + self.BALL_SIZE <= 0:
            scorer = 1
        elif self.ball_x >= self.WIDTH:
            scorer = 0
        if scorer is not None:
            self.scores[scorer] += 1
            self._reset_ball(-1 if scorer == 0 else 1)

    def _overlaps(self, paddle_y):
        return (self.ball_y < paddle_y + self.PADDLE_HEIGHT
                and self.ball_y + self.BALL_SIZE > paddle_y)

    def _bounce(self, paddle_y, direction):
        offset = ((self.ball_y + self.BALL_SIZE / 2
                   - paddle_y - self.PADDLE_HEIGHT / 2)
                  / (self.PADDLE_HEIGHT / 2))
        self.ball_vx = direction * self.BALL_SPEED
        self.ball_vy = max(-1.0, min(1.0, offset)) * 140.0

    def render(self, display):
        white = (240, 240, 240)
        title = "PONG VS BOT" if self.mode == "bot" else "PONG 2 PLAYERS"
        if self.lan_role is not None:
            title = "PONG LAN " + self.lan_role.upper()
        display.text(title, 12, 4, white)
        seconds = int(self.time_left)
        if self.time_left > seconds:
            seconds += 1
        display.text("Time " + str(seconds // 60) + ":"
                     + ("0" if seconds % 60 < 10 else "")
                     + str(seconds % 60), 12, 20, white)
        display.text(str(self.scores[0]) + " : " + str(self.scores[1]),
                     240, 8, white)
        display.rect(0, self.TOP - 2, self.WIDTH, 2, white)
        display.rect(0, self.BOTTOM, self.WIDTH, 2, white)
        for y in range(self.TOP + 4, self.BOTTOM, 12):
            display.rect(159, y, 2, 6, (60, 60, 60))
        display.rect(self.LEFT_X, int(self.left_y), self.PADDLE_WIDTH,
                     self.PADDLE_HEIGHT, (80, 220, 120))
        display.rect(self.RIGHT_X, int(self.right_y), self.PADDLE_WIDTH,
                     self.PADDLE_HEIGHT, (80, 180, 240))
        display.rect(int(self.ball_x), int(self.ball_y), self.BALL_SIZE,
                     self.BALL_SIZE, white)
        if self.finished:
            result = "DRAW"
            if self.winner is not None:
                winner = "BOT" if self.mode == "bot" and self.winner == 1 else (
                    "PLAYER " + str(self.winner + 1))
                result = winner + " WINS!"
            display.text(result, 96, 82, white)
            display.text("Host R: new match" if self.lan_role else "R: new match",
                         90, 106, white)
        elif self.serving:
            display.text("Host Enter: serve" if self.lan_role else "Enter: serve",
                         90, 82, white)
        display.text("You: Up/Down" if self.lan_role else "P1: Up/Down  P2: W/S",
                     12, 212, white)
        display.text("Host R: restart  Esc: menu" if self.lan_role
                     else "R: restart  Esc: menu", 12, 228, white)

    def on_exit(self):
        self._held.clear()
