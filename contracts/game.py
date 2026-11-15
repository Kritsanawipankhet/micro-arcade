class BaseGame:
    def on_enter(self):
        pass

    def update(self, dt, buttons):
        raise NotImplementedError

    def render(self, display):
        raise NotImplementedError

    def on_exit(self):
        pass
