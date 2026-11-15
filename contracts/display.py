class Display:
    """Logical pixels and RGB tuple colors, independent of physical display."""

    def clear(self):
        raise NotImplementedError

    def rect(self, x, y, width, height, color):
        raise NotImplementedError

    def text(self, value, x, y, color):
        raise NotImplementedError

    def present(self):
        raise NotImplementedError
