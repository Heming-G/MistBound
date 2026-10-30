# Development process

## Starting idea and intention

The student wanted a manageable Python project with an English interface and documentation. An earlier plant-care prototype felt too simple, so the student selected a fog-covered exploration map. After discussing how to add challenge, they approved limited-use flashes that are replenished by collecting light fragments.

The intended player enjoys exploring and making small choices. The interaction loop is: choose a direction or use a flash, observe the newly visible route and resource count, then choose where to go next.

## Design decisions

### Limited information, with memory

Ordinary sight is small and blocked by walls. A flash has a larger radius and reveals through walls. Previously revealed tiles remain dim afterward. This makes a flash useful for planning beyond the next corner, while preventing the player from having to memorize everything. A persistent text legend explains bright, dim and unknown areas.

### Scarcity without a permanent failure state

The player starts with two flashes. Each of the three fragments grants one more and slightly increases normal sight. The game remains completable with zero flashes; there is no dying light or irreversible loss. The fixed map lets the player use knowledge from a previous attempt. Time, steps and flashes used support an optional personal challenge rather than a mandatory time limit.

### A map that can be checked

The layout was developed using a deterministic maze-generation sketch, with extra openings to create loops, then stored as an explicit grid in the source. Three fragments and an exit are placed on reachable paths. The generation sketch is not a runtime dependency. Automated graph searches check every floor tile is connected and that collecting everything and reaching the exit is possible.

### Handling interruption and repeated actions

Movement is bounded by walls and limited to one grid step per interval. Pressing Flash again while it is active does not consume another charge; trying with no charges gives a helpful message. Switching windows pauses the timer and flash duration. Restart requires confirmation and can be cancelled. Menus remove hidden gameplay buttons from the set of clickable targets.

### Iteration during implementation

The first render lacked an always-visible explanation of the three fog states; a compact legend was added above the map. Visible distant tiles were also given a brightness floor so they cannot look darker than remembered tiles. Rendered frames of the title, gameplay, flash, pause, restart and completion screens were inspected for layout.

These changes came from developer review. They are **not** findings from a participant trial.

A further feedback check found that a wall warning could remain after a successful move, and an active-flash message could remain after the flash expired. Those messages now update to match the current state; the regression checks verify the transition.

## AI tools and contribution

OpenAI Codex was used for assignment interpretation, idea generation, Python implementation, tests, visual rendering checks and drafting English documentation. The student selected the final idea, required Python and English deliverables, and approved the limited-flash mechanic. The current code and documents were created with substantial AI assistance and still need the student's own review and understanding.

- Suggestion kept: remembered fog plus scarce flashes, with each fragment restoring a charge.
- Suggestion changed: the initial maze proposal relied on exploration and collection alone; after the student asked for more challenge, limited flashes were added as a resource decision.
- Scope decision: enemies and continuous light depletion were discussed but omitted in favor of a small, recoverable exploration experience.

## Developer verification

All 12 automated tests pass. They cover connected map layout, blocked and invalid positions, flash exhaustion and repeated use, normal wall occlusion, flash visibility and memory, one-time collection rewards, a locked exit, completion without flashes, reset, keyboard input, pause on focus loss, restart confirmation and rendering/menu input boundaries.

A separate scripted application playthrough went through three fragments and the exit in 96 steps, entering the real completion screen. The application also opened and rendered using the native macOS Cocoa display driver. README images are game-rendered example frames from a scripted sequence. These checks do not replace a real participant trial.

## Real participant trial — pending

No participant has tried this version yet. Before submission, ask at least one other person to try it without explaining the controls first. Observe what they attempt, where they hesitate, and whether movement, fog, flashes and the exit make sense. Use `docs/USER_TRIAL.md` to record observations without identifying the person.

Replace this section with the actual observation and one resulting improvement, or an explanation of why the design was kept. Do not invent a trial or present the automated playthrough as participant evidence.

## Development history

The first commit records the implemented exploration and resource mechanics with tests. A later commit adds documentation and rendered example frames. After the real participant trial, record any further changes and the reason for them in a new commit.
