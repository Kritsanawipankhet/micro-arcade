import errno
import json
import select
import socket

from contracts.network import Network


class TCPNetwork(Network):
    MAX_MESSAGE = 4096
    MAX_PENDING = 65536

    def __init__(self, role, address="0.0.0.0", port=50007):
        if role not in ("host", "join"):
            raise ValueError("Unknown network role")
        self.status = "connecting"
        self.error = ""
        self.port = port
        self.listener = None
        self.connection = None
        self._incoming = bytearray()
        self._outgoing = bytearray()
        try:
            # Numeric IPv4 only: do not block the frame loop on DNS lookup.
            socket.inet_pton(socket.AF_INET, address)
            if role == "host":
                self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.listener.setblocking(False)
                self.listener.bind((address, port))
                self.listener.listen(1)
                self.port = self.listener.getsockname()[1]
            else:
                self.port = port
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.setblocking(False)
                result = self.connection.connect_ex((address, port))
                if result not in (0, errno.EINPROGRESS, errno.EWOULDBLOCK,
                                  errno.EALREADY):
                    raise OSError(result, "Connection failed")
                if result == 0:
                    self._connected()
        except (OSError, ValueError, OverflowError) as error:
            self._fail(str(error))

    def _connected(self):
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.status = "connected"

    def _fail(self, error):
        self.close()
        self.status = "error"
        self.error = error

    def send(self, message):
        if self.status != "connected":
            return
        try:
            data = json.dumps(message, allow_nan=False).encode("utf-8") + b"\n"
            if len(data) > self.MAX_MESSAGE:
                raise ValueError("Message too large")
            if len(self._outgoing) + len(data) > self.MAX_PENDING:
                raise ValueError("Connection too slow")
            self._outgoing.extend(data)
        except (TypeError, ValueError) as error:
            self._fail(str(error))

    def poll(self):
        messages = []
        if self.status in ("error", "closed"):
            return messages
        try:
            if self.status == "connecting":
                if self.listener is not None:
                    try:
                        self.connection, _ = self.listener.accept()
                    except BlockingIOError:
                        return messages
                    self.connection.setblocking(False)
                    self.listener.close()
                    self.listener = None
                    self._connected()
                else:
                    _, writable, failed = select.select(
                        [], [self.connection], [self.connection], 0)
                    if not writable and not failed:
                        return messages
                    result = self.connection.getsockopt(socket.SOL_SOCKET,
                                                        socket.SO_ERROR)
                    if result:
                        raise OSError(result, "Connection failed")
                    self._connected()
            if self._outgoing:
                try:
                    sent = self.connection.send(self._outgoing)
                except BlockingIOError:
                    sent = 0
                del self._outgoing[:sent]
            # Bound work per frame even if a peer sends continuously.
            for _ in range(8):
                try:
                    data = self.connection.recv(4096)
                except BlockingIOError:
                    break
                if not data:
                    self._fail("Peer disconnected")
                    return []
                self._incoming.extend(data)
                while b"\n" in self._incoming:
                    index = self._incoming.index(b"\n")
                    if index + 1 > self.MAX_MESSAGE:
                        raise ValueError("Message too large")
                    raw = bytes(self._incoming[:index])
                    del self._incoming[:index + 1]
                    message = json.loads(raw)
                    if not isinstance(message, dict):
                        raise ValueError("Expected a message object")
                    messages.append(message)
                if len(self._incoming) >= self.MAX_MESSAGE:
                    raise ValueError("Message too large")
        except (OSError, ValueError, UnicodeError, RecursionError) as error:
            self._fail(str(error))
            return []
        return messages

    def close(self):
        for connection in (self.connection, self.listener):
            if connection is not None:
                connection.close()
        self.connection = self.listener = None
        self._incoming.clear()
        self._outgoing.clear()
        self.status = "closed"
