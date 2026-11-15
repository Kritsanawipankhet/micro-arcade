class Network:
    """Nonblocking message transport injected into a game session.

    status: connecting, connected, error, or closed. error is displayable text.
    poll() returns decoded dictionaries; send() queues one dictionary.
    """

    def poll(self):
        raise NotImplementedError

    def send(self, message):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
