# Mistbound

**Find the light. Remember the way.** A small Python exploration game about navigating uncertainty with a limited resource.

![Gameplay: one light fragment collected, with bright current sight and dim remembered paths](docs/gameplay.png)

## Idea and intended player

Mistbound is for someone who enjoys a short exploration puzzle. You are a small light in a fog-covered maze. Collect **three gold light fragments**, then reach the **green exit**. There are no enemies or time limits. The challenge is deciding where to explore and when to spend a flash.

The map has branches, dead ends and loops. It is fixed, so a second attempt lets you apply what you learned and compare your time, steps and flashes used.

## Interaction

- **Move:** WASD or arrow keys. Holding a direction moves at a controlled rate; walls block movement.
- **Flash:** Space or the Flash button. Start with **two charges**. A flash reveals nearby routes **through walls for 1.7 seconds**, and the dim outlines remain afterward.
- **Collect:** Walk over a gold diamond. Each fragment restores one flash and slightly increases normal sight.
- **Exit:** Enter the portal after collecting all three fragments. Before that, it explains how many are missing.
- **Pause/help:** Esc or the Pause button. Switching to another window also pauses the game. Time and flash duration freeze while paused. Resume explicitly with Esc, Enter or Continue.
- **Restart:** R, then Enter to confirm. Esc cancels. Closing the window stops the game.

**Bright** tiles are visible now; **dim** tiles were explored earlier; **black** areas are unknown. Normal sight stops at walls. Small dots mark tiles you have stepped on. You can finish even after spending every flash: ordinary sight never disappears.

![A flash reveals nearby routes through walls](docs/flash.png)

## Run from a fresh terminal

Requirements: **uv**, Python **3.14**, an internet connection for initial installation, and a desktop display of at least **1040 × 800** plus the window frame. The game runs offline after installation.

Install uv from its official instructions if needed: <https://docs.astral.sh/uv/getting-started/installation/>.

Open a terminal in the downloaded/cloned project folder and run:

```sh
uv python install 3.14
uv sync --locked
uv run python main.py
```

On the development Mac, you can also double-click **Launch.command** after installing uv. The terminal instructions are the primary way to reproduce the setup. In VS Code, open this folder and use its terminal to run the same commands; no editor extension is required.

The dependency is **pygame-ce**, which is imported as `pygame`. Its exact resolved version is recorded in `uv.lock`. Do not separately install the original `pygame` package into this environment; both use the same import name. No API keys, accounts, external assets or microphone are needed.

## Verification

```sh
uv run python -m unittest -v
```

The tests use an offscreen display and check map reachability, wall collisions, limited flashes, repeated input, fog memory, collection rewards, the locked exit, completion with zero flashes, reset, keyboard controls and pause/restart behavior. Automated checks are developer verification, not a participant trial.

Tested on macOS with Python 3.14.7, pygame-ce 2.5.8 and the Cocoa display driver. All 12 tests pass, and a scripted full application playthrough collects three fragments and reaches the completion screen. Windows and Linux have not been tested.

The README images are **actual frames rendered by the game using a scripted example**, not illustrations of an unimplemented design or records of a user trial. To regenerate them:

```sh
uv run python main.py --screenshots docs
```

For a machine with no desktop display, the image command can use `SDL_VIDEODRIVER=dummy` on macOS/Linux. Normal play needs a desktop.

## Files

| File | Purpose |
| --- | --- |
| `main.py` | Window, input, drawing, animation, menus and game loop |
| `game.py` | Map, movement, visibility, collection, flashes and win conditions |
| `test_game.py` | Rules and application interaction tests |
| `pyproject.toml`, `uv.lock`, `.python-version` | Reproducible Python environment |
| `PROCESS.md` | Design decisions, AI contribution and participant-trial status |
| `CREDITS.md` | Code, tool and asset credits |
| `docs/CODE_GUIDE.md` | A short guide to explaining the program |
| `docs/USER_TRIAL.md` | Record for a real participant trial, still to complete |
| `docs/SUBMISSION_CHECKLIST.md` | Remaining submission preparation |

## Limitations and current status

There is one fixed map, no save file, no sound and no hosted browser version. Closing the game loses the current run. The UI is English and uses a fixed window size. The fog and animation are visual; the game has not been evaluated for screen-reader use. Cross-platform behavior and difficulty still need real user feedback.

**Before assignment submission:** complete a real participant trial, record the observation and resulting decision in PROCESS.md, and replace the pending trial text. The student must also follow the run instructions themselves and review the code. A public GitHub upload and signed-out access check are still pending.
