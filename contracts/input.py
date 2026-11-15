class Input:
    """Poll held logical actions; window closure is separate from back."""

    def __init__(self):
        self.quit_requested = False

    def poll(self):
        raise NotImplementedError
