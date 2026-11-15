class Input:
    """Poll held logical actions; window closure is separate from back.

    up/down control player one; p2_up/p2_down control player two.
    Other actions: left, right, jump, confirm, back, restart.
    """

    def __init__(self):
        self.quit_requested = False

    def poll(self):
        raise NotImplementedError
