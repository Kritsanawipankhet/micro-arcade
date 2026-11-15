from contracts.game import BaseGame


class DinoGame(BaseGame):
    WIDTH = 320
    GROUND_Y = 200
    PLAYER_X = 40
    PLAYER_WIDTH = 18
    PLAYER_HEIGHT = 26
    GRAVITY = 900.0
    JUMP_SPEED = 350.0
    OBSTACLE_SPEED = 140.0
    OBSTACLE_WIDTH = 14
    OBSTACLE_HEIGHT = 28
    SPAWN_INTERVAL = 1.8
    MAX_STEP = 1.0 / 120

    def __init__(self):
        self.on_enter()

    def on_enter(self):
        self.player_y = float(self.GROUND_Y - self.PLAYER_HEIGHT)
        self.velocity_y = 0.0
        self.obstacles = []
        self.spawn_timer = 0.0
        self.elapsed = 0.0
        self.score = 0
        self.game_over = False
        self._jump_held = False
        self._restart_held = False

    def update(self, dt, buttons):
        if dt < 0:
            raise ValueError("dt must be nonnegative")
        jump = "jump" in buttons
        restart = "restart" in buttons
        if restart and not self._restart_held:
            self.on_enter()
            self._jump_held = jump
            self._restart_held = restart
            return
        if (not self.game_over and jump and not self._jump_held
                and self.player_y == self.GROUND_Y - self.PLAYER_HEIGHT):
            self.velocity_y = -self.JUMP_SPEED
        self._jump_held = jump
        self._restart_held = restart
        remaining = dt
        while remaining > 0 and not self.game_over:
            step = min(remaining, self.MAX_STEP)
            self._advance(step)
            remaining -= step

    def _advance(self, dt):
        self.player_y += self.velocity_y * dt + 0.5 * self.GRAVITY * dt * dt
        self.velocity_y += self.GRAVITY * dt
        floor = self.GROUND_Y - self.PLAYER_HEIGHT
        if self.player_y >= floor:
            self.player_y = float(floor)
            self.velocity_y = 0.0

        self.spawn_timer += dt
        if self.spawn_timer >= self.SPAWN_INTERVAL:
            self.spawn_timer -= self.SPAWN_INTERVAL
            self.obstacles.append(float(self.WIDTH))
        for index in range(len(self.obstacles)):
            self.obstacles[index] -= self.OBSTACLE_SPEED * dt
        while self.obstacles and self.obstacles[0] + self.OBSTACLE_WIDTH <= 0:
            self.obstacles.pop(0)

        for x in self.obstacles:
            if (self.PLAYER_X < x + self.OBSTACLE_WIDTH
                    and self.PLAYER_X + self.PLAYER_WIDTH > x
                    and self.player_y < self.GROUND_Y
                    and self.player_y + self.PLAYER_HEIGHT
                    > self.GROUND_Y - self.OBSTACLE_HEIGHT):
                self.game_over = True
                return
        self.elapsed += dt
        self.score = int(self.elapsed * 10)

    def render(self, display):
        white = (240, 240, 240)
        display.text("DINO RUNNER", 12, 12, white)
        display.text("Score: " + str(self.score), 12, 36, white)
        display.rect(0, self.GROUND_Y, self.WIDTH, 2, white)
        display.rect(self.PLAYER_X, int(self.player_y), self.PLAYER_WIDTH,
                     self.PLAYER_HEIGHT, (80, 220, 120))
        for x in self.obstacles:
            display.rect(int(x), self.GROUND_Y - self.OBSTACLE_HEIGHT,
                         self.OBSTACLE_WIDTH, self.OBSTACLE_HEIGHT,
                         (240, 140, 60))
        if self.game_over:
            display.text("GAME OVER - R to restart", 50, 90, white)
        display.text("Space: jump   R: restart", 12, 218, white)

    def on_exit(self):
        self.obstacles.clear()
