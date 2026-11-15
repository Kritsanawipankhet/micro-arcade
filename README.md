# Micro Arcade

Run the desktop simulator with `uv run python simulator.py`.
Use Up/Down and Enter to select a game; Esc returns to the launcher.

## Pong over LAN (PC to PC)

Connect both PCs to the same LAN. Find the host PC's LAN IPv4 address
in its network settings (Windows: `ipconfig`, IPv4 Address).

On the host:

```sh
uv run python simulator.py --pong-host
```

On the second PC, replace the example IP with the host's address:

```sh
uv run python simulator.py --pong-join 192.168.1.10
```

Both players use Up/Down. Host controls the left paddle, Join the right.
Only Host uses Enter to serve and R to restart. The four-minute timer starts
on the first serve and continues between points. Highest score wins; equal
scores draw. The Host computes all gameplay; Join displays received snapshots.

The default TCP port is 50007. To change it, supply `--port 50008` on **both**
PCs. Allow incoming traffic for this port on the Host's firewall if prompted.
Wi-Fi client isolation can prevent peers from connecting even on the same Wi-Fi.
There is no room discovery, automatic reconnect, or CoreS3 network adapter yet.
Numeric IPv4 addresses are required; hostnames and IPv6 are not supported.

The connection waits up to 30 seconds. Missing peer messages for five seconds
during a session stops the match. Esc closes the connection and returns to
the launcher. Select the Pong LAN entry to connect again; both players must
reconnect for a new session. A fresh connection starts a fresh match.

For local testing, run Host and Join in separate terminals and use `127.0.0.1`.
Only the focused window receives physical keyboard input.

## Tests

```sh
uv run pytest -q
```

Network integration tests bind only to loopback. Testing on two physical PCs
is still needed to verify a particular LAN and firewall configuration.
