"""Mistbound: run with `uv run python main.py`."""
import argparse
import math
import os
from pathlib import Path
import random

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame
from game import Game

WIDTH, HEIGHT = 1040, 800
TILE, MAP_X, MAP_Y = 30, 36, 170
BG, TEXT, MUTED = (10, 15, 26), (228, 235, 244), (143, 162, 184)
CYAN, VIOLET, GOLD, GREEN = (106, 227, 235), (181, 163, 255), (255, 213, 131), (132, 231, 177)
MOVES = {pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
         pygame.K_UP: (0, -1), pygame.K_w: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1)}


def format_time(seconds):
    seconds = int(seconds)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class App:
    def __init__(self):
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Mistbound — find your way through the light")
        self.clock = pygame.time.Clock()
        self.fonts = {s: pygame.font.Font(None, s) for s in (18, 20, 22, 24, 28, 32, 38, 48, 64)}
        self.game = Game()
        self.mode, self.previous_mode = "home", "playing"
        self.running = True
        self.next_move = 0
        self.visual_player = list(self.game.player)
        self.effects, self.click_targets = [], []
        self.wall_until, self.sim_time = 0, 0.0
        rng = random.Random(10)
        self.stars = [(rng.randrange(20, WIDTH - 20), rng.randrange(12, HEIGHT - 12), rng.random() * math.tau) for _ in range(58)]
        icon = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(icon, CYAN, (16, 16), 9)
        pygame.draw.circle(icon, (255, 255, 255), (16, 16), 4)
        pygame.display.set_icon(icon)

    def text(self, words, x, y, size=22, color=TEXT, center=False):
        surface = self.fonts[size].render(words, True, color)
        rect = surface.get_rect(center=(x, y)) if center else surface.get_rect(topleft=(x, y))
        self.screen.blit(surface, rect)
        return rect

    def paragraph(self, words, x, y, width, size=20, color=MUTED):
        line = ""
        for word in words.split():
            candidate = f"{line} {word}".strip()
            if self.fonts[size].size(candidate)[0] > width and line:
                self.text(line, x, y, size, color)
                y += size + 4
                line = word
            else:
                line = candidate
        if line:
            self.text(line, x, y, size, color)
            y += size + 4
        return y

    def button(self, title, rect, action, accent=CYAN):
        rect = pygame.Rect(rect)
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, (31, 49, 64) if hovered else (22, 34, 49), rect, border_radius=9)
        pygame.draw.rect(self.screen, accent if hovered else (61, 81, 101), rect, 1, border_radius=9)
        self.text(title, rect.centerx, rect.centery, 22, accent, True)
        self.click_targets.append((rect, action))

    def glow(self, position, color, radius=24):
        layer = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        for r in range(radius, 0, -3):
            pygame.draw.circle(layer, (*color, int((1 - r / (radius + 1)) * 45)), (radius + 1, radius + 1), r)
        self.screen.blit(layer, (position[0] - radius - 1, position[1] - radius - 1))

    def fresh_game(self):
        self.game.reset()
        self.visual_player = list(self.game.player)
        self.effects.clear()
        self.wall_until = 0
        self.next_move = pygame.time.get_ticks() + 150
        self.mode = "playing"

    def action(self, action):
        allowed = {"home": {"begin"}, "playing": {"pause", "restart", "flash"},
                   "paused": {"resume", "restart"}, "restart": {"begin", "cancel"},
                   "won": {"begin", "quit"}}
        if action not in allowed.get(self.mode, set()):
            return
        if action == "begin":
            self.fresh_game()
        elif action == "resume":
            self.mode = "playing"
            self.next_move = pygame.time.get_ticks() + 150
        elif action == "pause" and self.mode == "playing":
            self.mode = "paused"
        elif action == "restart":
            self.previous_mode, self.mode = self.mode, "restart"
        elif action == "cancel":
            self.mode = self.previous_mode
        elif action == "flash" and self.mode == "playing":
            if self.game.flash():
                self.effects.append([self.game.player, self.sim_time, CYAN])
        elif action == "quit":
            self.running = False

    def move(self, direction):
        result = self.game.move(*direction)
        self.next_move = pygame.time.get_ticks() + 145
        if result == "wall":
            self.wall_until = self.sim_time + 0.18
        elif result == "collected":
            self.effects.append([self.game.player, self.sim_time, GOLD])
        elif result == "won":
            self.mode = "won"

    def handle(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.WINDOWFOCUSLOST and self.mode == "playing":
            self.mode = "paused"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in self.click_targets:
                if rect.collidepoint(event.pos):
                    self.action(action)
                    break
        elif event.type == pygame.KEYDOWN:
            key = event.key
            if self.mode == "home":
                if key == pygame.K_RETURN:
                    self.fresh_game()
            elif self.mode == "restart":
                if key == pygame.K_RETURN:
                    self.fresh_game()
                elif key == pygame.K_ESCAPE:
                    self.action("cancel")
            elif self.mode == "paused":
                if key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.action("resume")
                elif key == pygame.K_r:
                    self.action("restart")
            elif self.mode == "won":
                if key in (pygame.K_RETURN, pygame.K_r):
                    self.fresh_game()
            elif self.mode == "playing":
                if key in MOVES and pygame.time.get_ticks() >= self.next_move:
                    self.move(MOVES[key])
                elif key == pygame.K_SPACE:
                    self.action("flash")
                elif key == pygame.K_ESCAPE:
                    self.action("pause")
                elif key == pygame.K_r:
                    self.action("restart")

    def update(self, dt):
        self.sim_time += dt
        if self.mode == "playing":
            self.game.update(dt)
            if pygame.time.get_ticks() >= self.next_move:
                keys = pygame.key.get_pressed()
                for key, direction in MOVES.items():
                    if keys[key]:
                        self.move(direction)
                        break
        for i in (0, 1):
            self.visual_player[i] += (self.game.player[i] - self.visual_player[i]) * min(1, dt * 19)
        self.effects = [e for e in self.effects if self.sim_time - e[1] < 0.8]

    def draw_map(self):
        g = self.game
        frame = pygame.Rect(MAP_X - 5, MAP_Y - 5, g.width * TILE + 10, g.height * TILE + 10)
        pygame.draw.rect(self.screen, (7, 12, 21), frame, border_radius=10)
        pygame.draw.rect(self.screen, (40, 59, 77), frame, 1, border_radius=10)
        for x, y in g.seen:
            rect = pygame.Rect(MAP_X + x * TILE + 1, MAP_Y + y * TILE + 1, TILE - 2, TILE - 2)
            visible, wall = (x, y) in g.visible, g.grid[y][x] == "#"
            if visible:
                distance = math.hypot(x - g.player[0], y - g.player[1])
                shade = max(0.3, 1 - distance / (10 if g.flash_remaining else 6))
                base = (64, 87, 112) if wall else (33, 59, 77)
                memory = (25, 35, 49) if wall else (15, 24, 36)
                color = tuple(max(memory[i] + 8, int(v * shade)) for i, v in enumerate(base))
            else:
                color = (25, 35, 49) if wall else (15, 24, 36)
            pygame.draw.rect(self.screen, color, rect, border_radius=3)
            if wall and visible:
                pygame.draw.line(self.screen, (70, 94, 116), rect.topleft, rect.topright)
            if (x, y) in g.visited and not wall:
                pygame.draw.circle(self.screen, (48, 80, 93) if visible else (30, 45, 58), rect.center, 2)
            center = rect.center
            if (x, y) in g.lights:
                if visible:
                    self.glow(center, GOLD)
                color = GOLD if visible else (104, 91, 65)
                r = int(7 * (1 + math.sin(self.sim_time * 3 + x) * 0.12)) if visible else 7
                pygame.draw.polygon(self.screen, color, [(center[0], center[1] - r), (center[0] + r, center[1]),
                                                         (center[0], center[1] + r), (center[0] - r, center[1])])
            if (x, y) == g.exit:
                unlocked = g.collected == g.total_lights
                color = (GREEN if unlocked else VIOLET) if visible else (67, 66, 91)
                if visible:
                    self.glow(center, color, 26)
                pygame.draw.rect(self.screen, color, (center[0] - 8, center[1] - 10, 16, 21), 2, border_radius=5)
                if not unlocked:
                    pygame.draw.line(self.screen, color, (center[0] - 4, center[1]), (center[0] + 4, center[1]), 2)
        self.screen.set_clip(frame.inflate(-2, -2))
        for (x, y), born, color in self.effects:
            age = (self.sim_time - born) / 0.8
            ring = pygame.Surface((g.width * TILE, g.height * TILE), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*color, int(155 * (1 - age))),
                               (x * TILE + TILE // 2, y * TILE + TILE // 2), int(12 + age * 130), 2)
            self.screen.blit(ring, (MAP_X, MAP_Y))
        px = MAP_X + self.visual_player[0] * TILE + TILE / 2
        py = MAP_Y + self.visual_player[1] * TILE + TILE / 2
        self.glow((px, py), CYAN, 36)
        pygame.draw.circle(self.screen, (255, 172, 155) if self.sim_time < self.wall_until else CYAN, (px, py), 8)
        pygame.draw.circle(self.screen, (239, 255, 255), (px - 2, py - 2), 3)
        self.screen.set_clip(None)

    def draw_dashboard(self):
        g, x = self.game, 818
        self.text("YOUR JOURNEY", x, 175, 18, MUTED)
        self.text(f"{g.collected} / 3", x, 202, 48, GOLD)
        self.text("light fragments", x, 250, 20, MUTED)
        for i in range(3):
            pygame.draw.circle(self.screen, GOLD if i < g.collected else (53, 57, 64), (x + 10 + i * 30, 285), 7)
        pygame.draw.line(self.screen, (40, 55, 74), (x, 314), (1001, 314))
        self.text(f"{g.charges:02d}", x, 335, 48, CYAN)
        self.text("flashes remaining", x, 383, 20, MUTED)
        self.button("Flash [Space]", (x, 416, 184, 42), "flash")
        self.paragraph("See through nearby walls for 1.7 seconds. Each fragment restores one flash.", x, 471, 182, 20)
        self.text(format_time(g.elapsed), x, 578, 32)
        self.text(f"{g.steps} steps", x, 617, 22, MUTED)
        if g.flash_remaining > 0:
            self.text("FLASH ACTIVE", MAP_X + 590, 142, 18, CYAN)
        else:
            self.text("EXIT OPEN" if g.collected == 3 else "EXIT LOCKED", MAP_X + 608, 142, 18, GREEN if g.collected == 3 else MUTED)

    def modal(self):
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((4, 8, 17, 218))
        self.screen.blit(shade, (0, 0))
        self.click_targets.clear()
        card = pygame.Rect(222, 126, 596, 552)
        pygame.draw.rect(self.screen, (16, 25, 40), card, border_radius=20)
        pygame.draw.rect(self.screen, (61, 78, 102), card, 1, border_radius=20)
        cx = WIDTH // 2
        if self.mode == "home":
            self.text("A SMALL EXPLORATION IN LIGHT & MEMORY", cx, 172, 18, CYAN, True)
            self.text("MISTBOUND", cx, 230, 64, TEXT, True)
            self.paragraph("The paths are hidden. Your light is small. Find three fragments to open the way home.", 280, 285, 480, 24, TEXT)
            for i, (key, meaning) in enumerate([("WASD / Arrows", "Move through the maze"), ("Space", "Flash: reveal routes through walls"), ("Esc", "Pause / help"), ("R", "Start over, with confirmation")]):
                self.text(key, 280, 386 + i * 33, 20, CYAN)
                self.text(meaning, 448, 386 + i * 33, 20, MUTED)
            self.text("Explored paths stay dim. Two flashes to start. No time limit.", cx, 551, 20, MUTED, True)
            self.button("Begin exploration [Enter]", (300, 591, 440, 48), "begin")
        elif self.mode == "paused":
            self.text("TAKE A BREATH", cx, 190, 18, CYAN, True)
            self.text("Journey paused", cx, 242, 48, TEXT, True)
            self.paragraph("Your timer and flash are paused. Move with WASD or arrow keys. Press Space to reveal nearby routes through walls.", 280, 299, 480, 24, TEXT)
            self.paragraph("Bright = visible now. Dim = explored before. Black = unknown. Collect all three gold fragments, then find the green exit.", 280, 402, 480, 22)
            self.button("Continue [Esc / Enter]", (300, 520, 440, 48), "resume")
            self.button("Start over [R]", (300, 582, 440, 44), "restart", VIOLET)
        elif self.mode == "restart":
            self.text("A FRESH START", cx, 205, 18, VIOLET, True)
            self.text("Restart this journey?", cx, 266, 38, TEXT, True)
            self.paragraph("This resets your explored map, fragments, steps and timer. You will begin with two flashes again.", 280, 332, 480, 24, TEXT)
            self.button("Restart [Enter]", (300, 474, 440, 48), "begin", VIOLET)
            self.button("Cancel [Esc]", (300, 540, 440, 48), "cancel")
        elif self.mode == "won":
            self.text("ALL THREE LIGHTS BROUGHT HOME", cx, 185, 18, GOLD, True)
            self.text("Through the mist.", cx, 248, 48, TEXT, True)
            for i, (value, label) in enumerate([(format_time(self.game.elapsed), "TIME"), (str(self.game.steps), "STEPS"), (str(self.game.flashes_used), "FLASHES USED")]):
                x = 340 + i * 180
                self.text(value, x, 356, 38, CYAN, True)
                self.text(label, x, 398, 18, MUTED, True)
            self.text("A remembered path. A different way next time?", cx, 467, 22, TEXT, True)
            self.button("Explore again [Enter]", (300, 530, 440, 48), "begin")
            self.button("Close game", (300, 592, 440, 40), "quit", MUTED)

    def draw(self):
        self.click_targets.clear()
        self.screen.fill(BG)
        for x, y, phase in self.stars:
            intensity = int(25 + (math.sin(self.sim_time * 0.4 + phase) + 1) * 8)
            pygame.draw.circle(self.screen, (intensity, intensity + 8, intensity + 17), (x, y), 1)
        self.text("M I S T B O U N D", 35, 31, 38)
        self.text("Find the light. Remember the way.", 37, 78, 22, MUTED)
        for x, color, label in [(40, CYAN, "Bright: visible"), (226, (82, 102, 127), "Dim: remembered"),
                                (454, (24, 31, 43), "Black: unexplored")]:
            pygame.draw.circle(self.screen, color, (x + 4, 120), 4)
            self.text(label, x + 17, 113, 18, MUTED)
        if self.mode == "playing":
            self.button("Pause / help [Esc]", (813, 35, 192, 40), "pause", MUTED)
        self.text("THE UNSEEN PATH", MAP_X, 142, 18, MUTED)
        self.draw_map()
        self.draw_dashboard()
        pygame.draw.line(self.screen, (40, 55, 74), (36, 709), (1003, 709))
        self.paragraph(self.game.message, 37, 728, 965, 22, TEXT)
        self.text("WASD / Arrows  move     Space  flash     Esc  pause     R  restart", 37, 775, 18, MUTED)
        if self.mode != "playing":
            self.modal()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                self.handle(event)
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()


def preview(destination):
    """Render real application frames for documentation, using a scripted example."""
    app = App()
    folder = Path(destination)
    folder.mkdir(parents=True, exist_ok=True)
    app.draw()
    pygame.image.save(app.screen, folder / "start.png")
    app.fresh_game()
    app.game.flash()
    for _ in range(6):
        app.game.move(1, 0)
    for _ in range(2):
        app.game.move(0, 1)
    app.visual_player = list(app.game.player)
    app.game.update(1.8)
    app.draw()
    pygame.image.save(app.screen, folder / "gameplay.png")
    app.game.flash()
    app.draw()
    pygame.image.save(app.screen, folder / "flash.png")
    pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mistbound — a small maze of light and memory")
    parser.add_argument("--screenshots", metavar="FOLDER", help="render example application frames and exit")
    args = parser.parse_args()
    if args.screenshots:
        preview(args.screenshots)
    else:
        App().run()
