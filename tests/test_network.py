import json
import time

import pytest

from adapters.pc.network import TCPNetwork


def spin(condition, *peers):
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        messages = [peer.poll() for peer in peers]
        if condition(messages):
            return messages
        time.sleep(0.001)
    pytest.fail("Loopback operation timed out")


@pytest.fixture
def pair():
    host = TCPNetwork("host", "127.0.0.1", 0)
    assert host.status == "connecting", host.error
    join = TCPNetwork("join", "127.0.0.1", host.port)
    try:
        spin(lambda _: host.status == join.status == "connected", host, join)
        yield host, join
    finally:
        host.close()
        join.close()


def test_real_loopback_bidirectional_messages_and_disconnect(pair):
    host, join = pair
    host.send({"value": 1})
    received = spin(lambda batches: bool(batches[1]), host, join)
    assert received[1] == [{"value": 1}]
    join.send({"buttons": ["up"]})
    received = spin(lambda batches: bool(batches[0]), host, join)
    assert received[0] == [{"buttons": ["up"]}]
    join.close()
    spin(lambda _: host.status == "error", host)
    assert "disconnected" in host.error
    host.close()
    host.close()
    assert host.listener is host.connection is None


def test_partial_and_combined_messages(pair):
    host, join = pair
    join.connection.sendall(b'{"value":')
    assert host.poll() == []
    join.connection.sendall(b'1}\n{"value":2}\n')
    messages = spin(lambda batches: bool(batches[0]), host)[0]
    assert messages == [{"value": 1}, {"value": 2}]


@pytest.mark.parametrize("data", [b'not json\n', b'[]\n', b'\xff\n',
                                  b'x' * 4096, b'x' * 4097 + b'\n'])
def test_invalid_or_oversized_messages_close_connection(pair, data):
    host, join = pair
    join.connection.sendall(data)
    spin(lambda _: host.status == "error", host)
    assert host.connection is None


def test_outgoing_limits_and_invalid_address(pair):
    host, join = pair
    host.send({"value": "x" * 4096})
    assert host.status == "error"
    invalid = TCPNetwork("join", "not-an-ip")
    assert invalid.status == "error" and invalid.connection is None
    with pytest.raises(ValueError):
        TCPNetwork("unknown")


def test_queued_output_is_bounded(pair):
    host, join = pair
    for _ in range(100):
        host.send({"value": "x" * 1000})
    assert host.status == "error"
    assert "slow" in host.error


def test_partial_send_and_would_block_preserve_pending_bytes():
    class Connection:
        def __init__(self):
            self.bytes = bytearray()
            self.block = True

        def send(self, data):
            if self.block:
                self.block = False
                raise BlockingIOError
            self.bytes.extend(data[:3])
            return min(3, len(data))

        def recv(self, count):
            raise BlockingIOError

        def close(self):
            pass

    network = TCPNetwork("host", "127.0.0.1", 0)
    network.listener.close()
    network.listener = None
    network.connection = Connection()
    network.status = "connected"
    network.send({"value": 1})
    original = bytes(network._outgoing)
    network.poll()
    assert bytes(network._outgoing) == original
    while network._outgoing:
        network.poll()
    assert json.loads(network.connection.bytes) == {"value": 1}
    network.close()


def test_port_in_use_reports_error_without_leaking_listener():
    host = TCPNetwork("host", "127.0.0.1", 0)
    try:
        other = TCPNetwork("host", "127.0.0.1", host.port)
        assert other.status == "error"
        assert other.listener is None
    finally:
        host.close()
