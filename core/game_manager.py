class GameManager:
    """Own registered factories and the active game's lifecycle."""

    def __init__(self):
        self._factories = {}
        self._games = []
        self.active_game = None

    def register(self, name, factory, title=None):
        if name in self._factories:
            raise ValueError("Game already registered: " + name)
        if not callable(factory):
            raise TypeError("Game factory must be callable")
        self._factories[name] = factory
        self._games.append((name, name if title is None else title))

    def list_games(self):
        """Return (identifier, title) pairs in registration order."""
        return self._games[:]

    def launch(self, name):
        if name not in self._factories:
            raise ValueError("Unknown game: " + name)
        game = self._factories[name]()
        self.close()
        self.active_game = game
        game.on_enter()

    def update(self, dt, buttons):
        if self.active_game is not None:
            self.active_game.update(dt, buttons)

    def render(self, display):
        if self.active_game is not None:
            self.active_game.render(display)

    def close(self):
        game = self.active_game
        self.active_game = None
        if game is not None:
            game.on_exit()
