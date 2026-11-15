from core.engine import Engine


def test_frame_order_and_forwarding():
    calls = []

    class FakeInput:
        quit_requested = False

        def poll(self):
            calls.append("poll")
            return {"jump"}

    class FakeDisplay:
        def clear(self):
            calls.append("clear")

        def present(self):
            calls.append("present")

    class FakeScene:
        def update(self, dt, buttons):
            calls.append((dt, buttons))

        def render(self, display):
            assert display is output
            calls.append("render")

    source = FakeInput()
    output = FakeDisplay()
    engine = Engine(output, source, FakeScene())
    assert engine.step(0.033)
    assert calls == ["poll", (0.033, {"jump"}), "clear", "render", "present"]
    calls.clear()
    source.quit_requested = True
    assert not engine.step(0.033)
    assert calls == ["poll"]
