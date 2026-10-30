"""Maze rules. Rendering and keyboard handling live in main.py."""
import math

MAP = (
    "#########################",
    "#S..................#...#",
    "#.#.###.###.#.#.###.#.#.#",
    "#.#...#*..#.#...#.#...#.#",
    "#.###.###...###.#.#####.#",
    "#.#...#...#.....#....*#.#",
    "#.#.###.###########.#.#.#",
    "#...#.........#.....#...#",
    "#.#.#.#.#.#.###.#.#.#.###",
    "#...#.#...#.......#.#...#",
    "#.#.#.#######.#.#.###.#.#",
    "#...#.......#.#.#.....#.#",
    "#########.###.#.###.#.#.#",
    "#....*....#...#.....#.#.#",
    "#.#.#.#.#.#..##.#.#####.#",
    "#...#.....#.....#......E#",
    "#########################",
)
FLASH_DURATION = 1.7


def line_cells(start, end):
    """Integer Bresenham line, including both endpoints."""
    x, y = start
    ex, ey = end
    dx, dy = abs(ex - x), -abs(ey - y)
    sx, sy = (1 if x < ex else -1), (1 if y < ey else -1)
    error = dx + dy
    while True:
        yield x, y
        if (x, y) == (ex, ey):
            return
        twice = 2 * error
        if twice >= dy:
            error += dy
            x += sx
        if twice <= dx:
            error += dx
            y += sy


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid = MAP
        self.width, self.height = len(MAP[0]), len(MAP)
        self.player = next((x, y) for y, row in enumerate(MAP) for x, c in enumerate(row) if c == "S")
        self.exit = next((x, y) for y, row in enumerate(MAP) for x, c in enumerate(row) if c == "E")
        self.lights = {(x, y) for y, row in enumerate(MAP) for x, c in enumerate(row) if c == "*"}
        self.total_lights = len(self.lights)
        self.collected = 0
        self.charges = 2
        self.flashes_used = 0
        self.flash_remaining = 0.0
        self.steps = 0
        self.elapsed = 0.0
        self.won = False
        self.seen = set()
        self.visible = set()
        self.visited = {self.player}
        self.message = "Find three light fragments. Your first two flashes are ready."
        self.reveal()

    @property
    def radius(self):
        return 3 + self.collected * 0.4

    def walkable(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] != "#"

    def reveal(self):
        radius = 7 if self.flash_remaining > 0 else self.radius
        px, py = self.player
        visible = set()
        for y in range(max(0, py - 7), min(self.height, py + 8)):
            for x in range(max(0, px - 7), min(self.width, px + 8)):
                if math.hypot(x - px, y - py) > radius:
                    continue
                # Ordinary light stops at walls; a scarce flash reveals through them.
                if self.flash_remaining > 0 or all(self.grid[cy][cx] != "#" for cx, cy in list(line_cells(self.player, (x, y)))[1:-1]):
                    visible.add((x, y))
        self.visible = visible
        self.seen.update(visible)

    def move(self, dx, dy):
        if self.won:
            return "finished"
        if (dx, dy) not in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            raise ValueError("Use one cardinal step")
        x, y = self.player[0] + dx, self.player[1] + dy
        if not self.walkable(x, y):
            self.message = "A wall blocks the way. Try another direction."
            return "wall"
        self.player = x, y
        self.visited.add(self.player)
        self.steps += 1
        if self.message.startswith("A wall"):
            self.message = "The way is clear. Keep exploring for the three light fragments."
        result = "moved"
        if self.player in self.lights:
            self.lights.remove(self.player)
            self.collected += 1
            self.charges += 1
            self.message = f"Fragment {self.collected}/3 found. +1 flash, and your light grows."
            if self.collected == self.total_lights:
                self.message = "All fragments found. The exit is now open — find the green portal."
            result = "collected"
        if self.player == self.exit:
            if self.collected == self.total_lights:
                self.won = True
                self.message = "You found your way through the mist."
                result = "won"
            else:
                remaining = self.total_lights - self.collected
                self.message = f"The exit needs {remaining} more light fragment{'s' if remaining != 1 else ''}. Keep exploring."
                result = "locked"
        self.reveal()
        return result

    def flash(self):
        if self.won:
            return False
        if self.flash_remaining > 0:
            self.message = "Your flash is still lighting the maze. Save the next one."
            return False
        if self.charges == 0:
            self.message = "No flashes left. You can still explore; each fragment restores one."
            return False
        self.charges -= 1
        self.flashes_used += 1
        self.flash_remaining = FLASH_DURATION
        self.message = "Flash! Nearby routes are revealed through walls. Their outlines will remain."
        self.reveal()
        return True

    def update(self, dt):
        if dt < 0:
            raise ValueError("Time cannot run backwards")
        if self.won:
            return
        self.elapsed += dt
        if self.flash_remaining > 0:
            self.flash_remaining = max(0.0, self.flash_remaining - dt)
            self.reveal()
            if self.flash_remaining == 0 and self.message.startswith(("Flash!", "Your flash is still")):
                self.message = "The flash faded. Revealed paths stay dim so you can plan your next move."
