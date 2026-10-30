# Explaining Mistbound

## The main loop

`App.run()` repeats three jobs: read input events, update the game's state, then draw the result. `clock.tick(60)` limits drawing to about 60 frames per second; it is not a countdown. Movement has its own delay so holding a key does not move once per rendered frame.

## One user action from beginning to end

Pressing **Space** is a clear example to explain:

1. `App.handle()` receives a keyboard event and calls `App.action("flash")`.
2. If the game is playing, it calls `Game.flash()`.
3. `Game.flash()` checks whether a flash is already active and whether a charge remains.
4. A valid flash subtracts one charge, increments the used count, sets its duration to 1.7 seconds and recalculates visible tiles.
5. The next `draw()` shows a larger visible area, the new charge count, a ring effect and a text message.
6. `Game.update(dt)` reduces the remaining duration during active play. When it expires, ordinary vision returns; `seen` still remembers the revealed tiles.

This connects input, meaningful state change and visible feedback. The repeated-input and no-charge branches explain the chosen error handling.

## Useful data structures

- `grid`: rows of strings. `#` is a wall, `.` a path, `S` the start, `*` a fragment, `E` the exit.
- `player`: an `(x, y)` coordinate.
- `lights`: a set of coordinates of fragments not collected yet. Removing a coordinate prevents collecting it twice.
- `visible`: tiles visible now.
- `seen`: every tile revealed so far. `seen.update(visible)` preserves memory.
- `visited`: coordinates physically stepped on, shown as small dots.
- `mode`: the interface screen: home, playing, paused, confirmation, won or local records.
- `seed`: a six-digit map number. It makes retries reproduce the same challenge.

## Movement and collection

`Game.move(dx, dy)` accepts a single horizontal or vertical step. It checks `walkable()` before moving. A wall leaves the position and step count unchanged. On a fragment tile, it removes that fragment, updates the count and grants a flash. Normal sight starts at radius 3 and grows by 0.4 per fragment, up to 4.6. The exit checks whether all four fragments were collected before setting `won`.

## How the fog works

Ordinary vision checks distance and walls. `line_cells()` lists grid cells along a straight line using the Bresenham algorithm; a wall before the target blocks normal vision. Flash mode skips wall blocking and uses radius 7. A rounded-up bounding box allows the fractional ordinary radius to be checked against actual distances. Drawing then uses `visible` and `seen` to select bright, dim or black tiles.

The smooth movement and glow effects are only drawings. They do not decide whether the player can walk through a wall or collect a fragment; those rules remain in `game.py`.

## Random maps that can be replayed

`maze.generate(seed)` creates a local random generator. Backtracking carves passages between rooms; extra openings add loops. A breadth-first search, `distances()`, measures reachable walking distances. The start, exit and four fragment positions are chosen with minimum spacing. Because all rooms are connected before objectives are placed, each objective has a route.

`Game.reset()` regenerates the same seed and clears progress. `Game.new_map()` chooses a different seed. Both keep completed records. This separates learning a route from exploring a fresh one.

## Why steps and time matter

After `Game.move()` reports a win, `App.move()` sends the completed statistics to `Leaderboard.add()` once. It sorts by `(steps, seconds)` and keeps five records for `game.map_key`, which includes the map number and rules version. Flash use is displayed but is not part of the sort key. JSON preserves the records between launches. A temporary file is replaced only after it has been written; a read/write failure leaves gameplay running with session-only records.

This makes a second interaction loop: complete a map, inspect your record, retry that map and choose a more efficient route. Different random maps have separate boards because their route lengths differ.

## Before explaining the project to a marker

Run the game yourself. Try collecting a fragment, using the final flash, hitting a wall, pausing and cancelling a restart. Then trace the Space example above in the actual code. Be honest about the AI assistance recorded in PROCESS.md.
