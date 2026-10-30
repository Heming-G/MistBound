"""Checks gameplay outcomes and interruption handling, not just individual lines."""
from collections import deque
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
from game import FLASH_DURATION, Game, MAP


def path(game, target, avoid=()):
    queue = deque([game.player])
    previous = {game.player: None}
    blocked = set(avoid) - {game.player, target}
    while queue:
        current = queue.popleft()
        if current == target:
            route = []
            while previous[current] is not None:
                parent = previous[current]
                route.append((current[0] - parent[0], current[1] - parent[1]))
                current = parent
            return list(reversed(route))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cell = current[0] + dx, current[1] + dy
            if game.walkable(*cell) and cell not in previous and cell not in blocked:
                previous[cell] = current
                queue.append(cell)
    raise AssertionError(f"No path to {target}")


class GameTests(unittest.TestCase):
    def test_map_is_enclosed_and_all_floor_is_connected(self):
        g = Game()
        self.assertTrue(all(len(row) == g.width for row in MAP))
        self.assertTrue(all(c == "#" for c in MAP[0] + MAP[-1]))
        self.assertTrue(all(row[0] == row[-1] == "#" for row in MAP))
        self.assertEqual(sum(row.count("S") for row in MAP), 1)
        self.assertEqual(sum(row.count("E") for row in MAP), 1)
        self.assertEqual(g.total_lights, 3)
        for y, row in enumerate(MAP):
            for x, cell in enumerate(row):
                if cell != "#":
                    path(g, (x, y))

    def test_walls_do_not_move_player_or_inflate_steps(self):
        g = Game()
        for _ in range(20):
            self.assertEqual(g.move(-1, 0), "wall")
        self.assertEqual(g.player, (1, 1))
        self.assertEqual(g.steps, 0)
        self.assertFalse(g.walkable(-1, 1))
        self.assertFalse(g.walkable(999, 1))

    def test_flash_consumption_repeat_and_exhaustion(self):
        g = Game()
        self.assertTrue(g.flash())
        self.assertFalse(g.flash())
        self.assertEqual((g.charges, g.flashes_used), (1, 1))
        g.update(FLASH_DURATION)
        self.assertTrue(g.flash())
        g.update(FLASH_DURATION)
        self.assertFalse(g.flash())
        self.assertEqual((g.charges, g.flashes_used), (0, 2))
        self.assertIn("still explore", g.message)

    def test_visibility_wall_occlusion_flash_and_memory(self):
        g = Game()
        behind_wall = (3, 3)
        self.assertNotIn(behind_wall, g.visible)
        g.flash()
        self.assertIn(behind_wall, g.visible)
        revealed = set(g.visible)
        g.update(FLASH_DURATION + 1)
        self.assertNotIn(behind_wall, g.visible)
        self.assertTrue(revealed <= g.seen)
        self.assertLess(len(g.seen), g.width * g.height)

    def test_fragment_restores_flash_once_and_expands_radius(self):
        g = Game()
        target = (7, 3)
        initial_radius = g.radius
        g.flash()
        for step in path(g, target):
            g.move(*step)
        self.assertEqual((g.collected, g.charges), (1, 2))
        self.assertGreater(g.radius, initial_radius)
        g.move(0, -1)
        g.move(0, 1)
        self.assertEqual((g.collected, g.charges), (1, 2))

    def test_exit_remains_locked_without_fragments(self):
        g = Game()
        for step in path(g, g.exit, avoid=g.lights):
            result = g.move(*step)
        self.assertEqual(result, "locked")
        self.assertFalse(g.won)
        self.assertIn("3 more", g.message)

    def test_complete_without_any_flash_and_freeze_after_win(self):
        g = Game()
        for target in sorted(g.lights):
            for step in path(g, target):
                g.move(*step)
                g.update(0.145)
        for step in path(g, g.exit):
            result = g.move(*step)
        self.assertEqual(result, "won")
        self.assertEqual(g.collected, 3)
        self.assertEqual(g.flashes_used, 0)
        snapshot = g.player, g.steps, g.elapsed, g.charges
        g.move(-1, 0)
        g.flash()
        g.update(10)
        self.assertEqual(snapshot, (g.player, g.steps, g.elapsed, g.charges))

    def test_reset_restores_fog_fragments_and_statistics(self):
        g = Game()
        g.flash()
        g.move(1, 0)
        g.update(10)
        g.reset()
        fresh = Game()
        for field in ("player", "seen", "lights", "charges", "steps", "elapsed", "flash_remaining", "collected", "won"):
            self.assertEqual(getattr(g, field), getattr(fresh, field))


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        import pygame
        from main import App
        self.pg = pygame
        self.app = App()

    def tearDown(self):
        self.pg.quit()

    def key(self, key):
        self.app.handle(self.pg.event.Event(self.pg.KEYDOWN, key=key))

    def test_focus_loss_pauses_timer_and_flash(self):
        a = self.app
        a.fresh_game()
        a.action("flash")
        a.update(0.2)
        snapshot = a.game.elapsed, a.game.flash_remaining, a.game.player
        a.handle(self.pg.event.Event(self.pg.WINDOWFOCUSLOST))
        a.update(5)
        self.key(self.pg.K_RIGHT)
        self.assertEqual(a.mode, "paused")
        self.assertEqual(snapshot, (a.game.elapsed, a.game.flash_remaining, a.game.player))
        self.key(self.pg.K_ESCAPE)
        a.update(0.1)
        self.assertGreater(a.game.elapsed, snapshot[0])

    def test_restart_can_be_cancelled_then_confirmed(self):
        a = self.app
        a.fresh_game()
        a.game.move(1, 0)
        self.key(self.pg.K_r)
        self.assertEqual(a.mode, "restart")
        self.key(self.pg.K_ESCAPE)
        self.assertEqual(a.mode, "playing")
        self.assertEqual(a.game.steps, 1)
        self.key(self.pg.K_r)
        self.key(self.pg.K_RETURN)
        self.assertEqual(a.game.steps, 0)
        self.assertEqual(a.mode, "playing")

    def test_keyboard_begin_move_flash_and_pause(self):
        a = self.app
        self.key(self.pg.K_RETURN)
        self.assertEqual(a.mode, "playing")
        a.next_move = 0
        self.key(self.pg.K_RIGHT)
        self.assertEqual((a.game.player, a.game.steps), ((2, 1), 1))
        self.key(self.pg.K_SPACE)
        self.assertEqual(a.game.charges, 1)
        self.key(self.pg.K_ESCAPE)
        self.assertEqual(a.mode, "paused")
        self.key(self.pg.K_SPACE)
        self.assertEqual(a.game.charges, 1)
        self.key(self.pg.K_ESCAPE)
        self.assertEqual(a.mode, "playing")

    def test_all_screens_render_and_modal_blocks_hidden_buttons(self):
        a = self.app
        for mode in ("home", "playing", "paused", "restart", "won"):
            a.mode = mode
            a.draw()
            self.assertTrue(a.click_targets)
            if mode != "playing":
                self.assertNotIn("flash", [action for _, action in a.click_targets])


if __name__ == "__main__":
    unittest.main()
