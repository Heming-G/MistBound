"""Seeded maze generation with reachable, separated objectives."""
from collections import deque
import random

WIDTH, HEIGHT = 25, 17
FRAGMENTS = 4
MAP_VERSION = "v2"
MAX_SEED = 999_999


def distances(grid, start):
    """Breadth-first search: the shortest walking distance to every reachable tile."""
    found = {start: 0}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (0 <= ny < len(grid) and 0 <= nx < len(grid[0])
                    and grid[ny][nx] != "#" and (nx, ny) not in found):
                found[nx, ny] = found[x, y] + 1
                queue.append((nx, ny))
    return found


def route(grid, start, target):
    """Shortest directions, used by scripted checks and documentation previews."""
    remaining = distances(grid, target)
    if start not in remaining:
        raise ValueError("Target is unreachable")
    steps = []
    cell = start
    while cell != target:
        x, y = cell
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            next_cell = x + dx, y + dy
            if remaining.get(next_cell) == remaining[cell] - 1:
                steps.append((dx, dy))
                cell = next_cell
                break
    return steps


def generate(seed):
    if type(seed) is not int or not 0 <= seed <= MAX_SEED:
        raise ValueError("Map number must be an integer from 0 to 999999")
    rng = random.Random(seed)
    grid = [["#"] * WIDTH for _ in range(HEIGHT)]
    rooms = [(x, y) for y in range(1, HEIGHT, 2) for x in range(1, WIDTH, 2)]
    start = rng.choice(rooms)
    grid[start[1]][start[0]] = "."
    stack = [start]
    # Backtracking opens a corridor to each unvisited room, so none is isolated.
    while stack:
        x, y = stack[-1]
        neighbors = [(nx, ny) for nx, ny in ((x + 2, y), (x - 2, y), (x, y + 2), (x, y - 2))
                     if 0 < nx < WIDTH - 1 and 0 < ny < HEIGHT - 1 and grid[ny][nx] == "#"]
        if not neighbors:
            stack.pop()
            continue
        nx, ny = rng.choice(neighbors)
        grid[(y + ny) // 2][(x + nx) // 2] = "."
        grid[ny][nx] = "."
        stack.append((nx, ny))

    # Open a few extra walls for alternate routes, without broad open rooms.
    walls = [(x, y) for y in range(1, HEIGHT - 1) for x in range(1, WIDTH - 1) if grid[y][x] == "#"]
    rng.shuffle(walls)
    opened = 0
    for x, y in walls:
        horizontal = grid[y][x - 1] == grid[y][x + 1] == "."
        vertical = grid[y - 1][x] == grid[y + 1][x] == "."
        if horizontal != vertical:
            grid[y][x] = "."
            opened += 1
            if opened == 12:
                break

    from_start = distances(grid, start)
    threshold = max(18, int(max(from_start.values()) * 0.65))
    exit_cell = rng.choice([cell for cell in rooms if from_start[cell] >= threshold])
    from_exit = distances(grid, exit_cell)
    candidates = [cell for cell in rooms if from_start[cell] >= 8 and from_exit[cell] >= 5]
    rng.shuffle(candidates)
    cache = {}

    def choose(remaining, selected):
        if len(selected) == FRAGMENTS:
            return selected
        if len(remaining) < FRAGMENTS - len(selected):
            return None
        for i, cell in enumerate(remaining):
            if cell not in cache:
                cache[cell] = distances(grid, cell)
            separated = [other for other in remaining[i + 1:]
                         if abs(cell[0] - other[0]) + abs(cell[1] - other[1]) >= 5
                         and cache[cell][other] >= 8]
            result = choose(separated, selected + [cell])
            if result is not None:
                return result
        return None

    fragments = choose(candidates, [])
    if fragments is None:
        raise RuntimeError("Could not place separated objectives")
    grid[start[1]][start[0]] = "S"
    grid[exit_cell[1]][exit_cell[0]] = "E"
    for x, y in fragments:
        grid[y][x] = "*"
    return tuple("".join(row) for row in grid)
