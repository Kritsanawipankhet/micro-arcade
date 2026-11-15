class Launcher:
    """Route input and drawing between the menu and registered games."""

    VISIBLE_ROWS = 6

    def __init__(self, manager):
        self.manager = manager
        self.selected = 0
        self.offset = 0
        self._held = set()
        self._blocked = set()

    def update(self, dt, buttons):
        pressed = buttons - self._held
        self._held = buttons.copy()
        self._blocked.intersection_update(buttons)
        if self.manager.active_game is not None:
            if "back" in pressed:
                self.manager.close()
                return
            self.manager.update(dt, buttons - self._blocked)
            return

        games = self.manager.list_games()
        if not games:
            self.selected = self.offset = 0
            return
        self.selected = min(self.selected, len(games) - 1)
        if "up" in pressed and "down" not in buttons:
            self.selected = (self.selected - 1) % len(games)
        elif "down" in pressed and "up" not in buttons:
            self.selected = (self.selected + 1) % len(games)
        if self.selected < self.offset:
            self.offset = self.selected
        elif self.selected >= self.offset + self.VISIBLE_ROWS:
            self.offset = self.selected - self.VISIBLE_ROWS + 1
        if "confirm" in pressed:
            self._blocked = buttons.copy()
            self.manager.launch(games[self.selected][0])

    def render(self, display):
        if self.manager.active_game is not None:
            self.manager.render(display)
            return
        white = (240, 240, 240)
        display.text("MICRO ARCADE", 16, 16, white)
        games = self.manager.list_games()
        if not games:
            display.text("No games registered", 16, 64, white)
        for row, game in enumerate(games[self.offset:
                                         self.offset + self.VISIBLE_ROWS]):
            y = 56 + row * 24
            if self.offset + row == self.selected:
                display.rect(12, y - 2, 296, 22, (30, 70, 100))
            # Bound titles to the logical display's available width.
            display.text(game[1][:28], 20, y, white)
        display.text("Up/Down: select  Enter: play", 12, 208, white)
        display.text("Esc: return from game", 12, 226, white)
