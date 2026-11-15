class Engine:
    """Coordinate one frame without owning platform timing or resources."""

    def __init__(self, display, input_source, scene):
        self.display = display
        self.input_source = input_source
        self.scene = scene

    def step(self, dt):
        buttons = self.input_source.poll()
        if self.input_source.quit_requested:
            return False
        self.scene.update(dt, buttons)
        self.display.clear()
        self.scene.render(self.display)
        self.display.present()
        return True
