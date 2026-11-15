# AGENTS.md — Micro Arcade

## 1. Project Overview

**Micro Arcade** is a modular, lightweight, multi-game console platform designed for embedded hardware.

### Target Platforms

| Component | Technology |
|---|---|
| Development Environment | Windows + VS Code |
| Language | Python / MicroPython |
| PC Simulator | Pygame |
| Hardware | M5Stack CoreS3 (ESP32-S3) |
| Firmware | UIFlow 2 MicroPython |
| Controller | M5Stack FACES Gamepad3 |
| Display | 320 × 240 pixels |
| Target FPS | 30 |
| Package Manager | uv |
| Testing | pytest |

The first game is **Dino Runner**.

The system must support adding new games without modifying platform-specific code or introducing game-specific logic into the shared engine.

---

## 2. Architecture

The project follows **Lightweight Hexagonal Architecture (Ports & Adapters)**.

### Directory Structure

```text
micro-arcade/
├── AGENTS.md
├── core/
│   ├── __init__.py
│   ├── engine.py
│   └── game_manager.py
├── contracts/
│   ├── __init__.py
│   └── game.py
├── games/
│   ├── __init__.py
│   └── dino/
│       ├── __init__.py
│       └── game.py
├── adapters/
│   ├── __init__.py
│   ├── pc/
│   │   ├── __init__.py
│   │   ├── display.py
│   │   └── input.py
│   └── cores3/
│       ├── __init__.py
│       ├── display.py
│       └── gamepad.py
├── scenes/
│   ├── __init__.py
│   └── launcher.py
├── tests/
├── simulator.py
├── main.py
└── pyproject.toml
```

### Layer Responsibilities

**`contracts/`**

Defines shared interfaces and game lifecycle contracts.

**`core/`**

Contains the game engine, game manager, state transitions, and shared platform-independent logic.

**`games/`**

Contains independent games and their gameplay logic.

**`scenes/`**

Contains platform-independent scenes such as the launcher, pause menu, and settings.

**`adapters/pc/`**

Contains Pygame rendering, keyboard input, and desktop-specific implementations.

**`adapters/cores3/`**

Contains M5Stack display, FACES Gamepad3 input, and hardware-specific implementations.

**Entry Points**

- `simulator.py` — CPython/Pygame entry point.
- `main.py` — CoreS3/MicroPython entry point.

---

## 3. Mandatory Architecture Rules

### Rule 1 — Platform Independence

The following directories MUST remain platform-independent:

- `core/`
- `contracts/`
- `games/`
- `scenes/`

**NEVER import the following modules in these directories:**

```python
import pygame
import M5
import machine
import esp32
import esp
import network
import socket
```

These modules are permitted only in platform-specific adapters or entry points when appropriate.

Game logic must never access hardware APIs directly.

### Rule 2 — Dependency Direction

Allowed dependencies:

```text
Entry Points
    |
    v
Core / Scenes / Games
    |
    v
Contracts

Platform Adapters
    |
    v
Contracts
```

Rules:

- `core/` may depend on `contracts/`.
- `games/` may depend on `contracts/`.
- `scenes/` may depend on `core/` and `contracts/`.
- Platform-independent layers must never import concrete adapters.
- Adapters may implement contracts.
- Entry points are responsible for dependency injection and composition.

### Rule 3 — MicroPython Compatibility

All shared runtime code must be compatible with MicroPython.

Prefer:

- Simple classes
- Functions
- Lists, tuples, and dictionaries
- Basic loops and conditions
- Lightweight modules
- Explicit state management

Avoid unless verified on the target firmware:

- `dataclasses`
- `abc`
- Runtime dependencies on `typing`
- `asyncio`
- CPython-only standard library modules
- Heavy third-party packages
- Unsupported language features

Do not assume that successful execution on CPython guarantees MicroPython compatibility.

### Rule 4 — Game Contract

Every game must implement the following lifecycle:

```python
class BaseGame:
    def on_enter(self):
        pass

    def update(self, dt, buttons):
        pass

    def render(self, display):
        pass

    def on_exit(self):
        pass
```

Requirements:

- `dt` represents elapsed time in seconds.
- `buttons` contains platform-independent input actions.
- `render(display)` uses only the shared display contract.
- Games must not directly read keyboard or Gamepad3 input.
- Games must not directly create Pygame windows.
- Games must release resources in `on_exit()` when necessary.

### Rule 5 — Game Registration

All games must be registered through `GameManager`.

Use factories to create game instances.

The engine must not contain hardcoded references to specific games.

Example:

```python
manager.register("dino", DinoGame)
manager.launch("dino")
```

### Rule 6 — Display and Input Abstraction

Shared display operations should use a minimal API:

```python
display.clear()
display.rect(x, y, width, height, color)
display.text(value, x, y, color)
display.present()
```

The exact interface must be consistent across supported platforms.

Input actions should use logical names:

```python
{
    "up",
    "down",
    "left",
    "right",
    "jump",
    "confirm",
    "back",
    "restart",
}
```

Platform adapters translate physical inputs into these logical actions.

---

## 4. Human-in-the-loop (HITL) — Mandatory

**The agent must use an approval-first workflow for every implementation task.**

### Phase 1 — Analyze

Before changing files:

1. Read this `AGENTS.md`.
2. Inspect relevant project files.
3. Understand the requested behavior.
4. Identify affected modules.
5. Evaluate architecture and compatibility risks.
6. Identify necessary tests.

Do not modify files during analysis.

### Phase 2 — Plan

Present an implementation plan containing:

- Objective
- Files to create or modify
- Proposed implementation
- Architecture impact
- Potential risks
- Verification plan

Prefer small, independently reviewable changes.

### Phase 3 — Approval Gate

**STOP and wait for explicit user approval.**

Acceptable approval examples:

- Approved
- Proceed
- อนุมัติ
- ดำเนินการตามแผน

Do not interpret silence as approval.

Do not modify source files before approval.

### Phase 4 — Implement

After approval:

1. Modify only approved files.
2. Follow architecture rules.
3. Avoid unrelated refactoring.
4. Do not introduce new dependencies without separate approval.
5. Do not perform destructive operations.
6. Keep changes small and reviewable.

If implementation requires a material scope change, stop and request approval again.

### Phase 5 — Verify

After implementation, perform permitted verification:

- Syntax checks
- Unit tests
- Architecture dependency tests
- MicroPython compatibility checks
- Simulator smoke tests when possible

Never claim a test passed unless it was executed.

### Phase 6 — Report

Report:

- Changes implemented
- Files modified
- Tests executed
- Test results
- Known limitations
- Remaining risks
- Recommended next steps

---

## 5. Approval Boundaries

The agent MUST obtain explicit approval before:

- Creating, modifying, renaming, or deleting project files
- Installing or upgrading dependencies
- Changing architecture or public contracts
- Modifying project configuration
- Flashing firmware
- Uploading code to hardware
- Executing destructive commands
- Creating commits or pushing to remote repositories
- Opening or updating pull requests

Approval for one operation does not authorize unrelated operations.

Reading files and proposing changes do not require implementation approval.

**Project-level approval does not replace IDE, sandbox, terminal, or operating-system permissions.**

---

## 6. Coding Standards

### General

- Follow PEP 8 where practical.
- Prefer readable and maintainable code.
- Avoid unnecessary abstractions.
- Keep functions focused.
- Use descriptive names.
- Avoid hidden global state.
- Do not introduce premature optimization.

### Game Development

- Separate gameplay state from rendering.
- Prefer time-based movement using `dt`.
- Keep collision detection deterministic.
- Avoid large allocations inside the game loop.
- Avoid unnecessary object creation every frame.
- Use simple data structures suitable for embedded systems.
- Ensure games can be restarted without restarting the entire engine.

### Error Handling

- Handle expected errors explicitly.
- Do not silently ignore exceptions.
- Avoid platform-specific exception handling in shared modules.
- Report hardware integration limitations clearly.

---

## 7. Testing Requirements

### Unit Tests

Write tests for:

- Game initialization
- Input handling
- Player movement
- Jumping and gravity
- Collision detection
- Score updates
- Game over
- Restart
- Game registration and lifecycle

### Architecture Tests

Verify that platform-independent directories do not import forbidden modules.

### Simulator Tests

Verify:

- Window initialization
- Display resolution
- Keyboard input
- Game loop execution
- Game exit behavior

### Hardware Tests

When hardware becomes available, verify:

- Display initialization
- Gamepad3 input mapping
- Frame timing
- Memory usage
- Firmware compatibility
- Game startup and shutdown

Do not report hardware tests as passed without testing on actual hardware.

---

## 8. Agent Communication Protocol

### Before Implementation

Use the following format:

**Analysis**

Explain the task and current state.

**Proposed Changes**

List the files and modifications.

**Architecture Impact**

Explain how the changes respect dependency rules.

**Risks**

Identify potential issues.

**Verification Plan**

Describe tests to execute.

**Approval Required**

Ask for explicit approval and stop.

### After Implementation

Use the following format:

**Implementation Summary**

Describe what was completed.

**Files Changed**

List actual modified files.

**Verification Results**

Report executed checks and outcomes.

**Known Limitations**

Explain unverified behavior or remaining issues.

**Next Steps**

Recommend the next development milestone.

---

## 9. Security and Operational Safety

- Never expose credentials or secrets.
- Never commit `.env` files containing secrets.
- Never flash firmware without explicit approval.
- Never erase device storage without explicit approval.
- Never install untrusted dependencies without review.
- Never execute downloaded scripts without permission.
- Never push source code to remote repositories without approval.
- Do not bypass sandbox restrictions.

---

## 10. Project Roadmap

### Milestone 1 — Simulator Foundation

- Initialize project with uv.
- Configure Pygame.
- Create PC display adapter.
- Create PC input adapter.
- Establish game loop.

### Milestone 2 — Dino Runner

- Implement Dino game logic.
- Add jumping and gravity.
- Add obstacles.
- Add collision detection.
- Add scoring and restart.
- Write unit tests.

### Milestone 3 — Multi-Game Platform

- Implement Game Manager.
- Implement Launcher.
- Add game registry.
- Support game switching.
- Add additional games.

### Milestone 4 — CoreS3 Integration

- Install and verify MicroPython firmware.
- Implement CoreS3 display adapter.
- Implement Gamepad3 input adapter.
- Validate hardware behavior.
- Deploy Micro Arcade.

### Milestone 5 — Optimization

- Improve memory usage.
- Optimize rendering.
- Improve frame timing.
- Add settings and persistence.
- Evaluate OTA updates.

---

## 11. Definition of Done

A task is complete only when:

1. The implementation matches the approved scope.
2. Architecture rules are respected.
3. Relevant tests have been executed or explicitly reported as not run.
4. No unapproved dependencies were introduced.
5. No unrelated files were modified.
6. Known limitations are documented.
7. The implementation summary has been delivered.

---

## 12. Non-Negotiable Rules

1. **Always analyze and propose a plan before implementation.**
2. **Always wait for explicit human approval before modifying project files.**
3. **Never import Pygame or M5Stack APIs into platform-independent modules.**
4. **Never mix game-specific logic into the shared engine.**
5. **Never assume CPython compatibility guarantees MicroPython compatibility.**
6. **Never invent hardware APIs or test results.**
7. **Never expand the approved scope without additional approval.**

**The human developer has final authority over implementation, dependencies, architecture changes, and hardware deployment.**