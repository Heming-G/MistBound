"""Gameplay outcomes, random map constraints and interruption behavior."""
from itertools import combinations
import math
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
from game import FLASH_DURATION, FLASH_RADIUS, NORMAL_RADIUS, Game
from maze import MAX_SEED, distances, generate, route

SEED = 261030
DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def collect_all(game, move=None):
    move = move or (lambda step: game.move(*step))
    while game.lights:
        reachable = distances(game.grid, game.player)
        target = min(game.lights, key=lambda cell: (reachable[cell], cell))
        for step in route(game.grid, game.player, target):
            move(step)
            game.update(0.145)
    for step in route(game.grid, game.player, game.exit):
        move(step)
        game.update(0.145)


class MazeTests(unittest.TestCase):
    def test_fifty_maps_have_connected_separated_objectives(self):
        for seed in range(50):
            with self.subTest(seed=seed):
                g = Game(seed)
                self.assertTrue(all(len(row) == g.width for row in g.grid))
                self.assertTrue(all(c == '#' for c in g.grid[0] + g.grid[-1]))
                self.assertTrue(all(row[0] == row[-1] == '#' for row in g.grid))
                self.assertEqual(sum(row.count('S') for row in g.grid), 1)
                self.assertEqual(sum(row.count('E') for row in g.grid), 1)
                self.assertEqual(g.total_lights, 4)
                floor = {(x, y) for y, row in enumerate(g.grid) for x, c in enumerate(row) if c != '#'}
                reachable = distances(g.grid, g.player)
                self.assertEqual(set(reachable), floor)
                self.assertGreaterEqual(reachable[g.exit], 18)
                for fragment in g.lights:
                    self.assertGreaterEqual(reachable[fragment], 8)
                    self.assertGreaterEqual(distances(g.grid, g.exit)[fragment], 5)
                for a, b in combinations(g.lights, 2):
                    self.assertGreaterEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 5)
                    self.assertGreaterEqual(distances(g.grid, a)[b], 8)

    def test_seed_replays_and_varies_layout_positions(self):
        self.assertEqual(generate(SEED), generate(SEED))
        games = [Game(seed) for seed in range(20)]
        self.assertEqual(len({g.grid for g in games}), 20)
        for values in ({g.player for g in games}, {g.exit for g in games}, {tuple(sorted(g.lights)) for g in games}):
            self.assertGreater(len(values), 10)
        for seed in (0, MAX_SEED):
            self.assertEqual(Game(seed).seed, seed)
        for seed in (-1, MAX_SEED + 1, True, '123'):
            with self.assertRaises(ValueError):
                generate(seed)


class GameTests(unittest.TestCase):
    def test_walls_preserve_steps_and_feedback_recovers(self):
        g = Game(SEED)
        for step in route(g.grid, g.player, (1, 1)):
            g.move(*step)
        baseline = g.steps
        for _ in range(20):
            self.assertEqual(g.move(-1, 0), 'wall')
        self.assertEqual((g.player, g.steps), ((1, 1), baseline))
        self.assertFalse(g.walkable(-1, 1))
        self.assertFalse(g.walkable(999, 1))
        direction = next((dx, dy) for dx, dy in DIRECTIONS if g.walkable(1 + dx, 1 + dy))
        g.move(*direction)
        self.assertNotIn('wall blocks', g.message)

    def test_flash_consumption_repeat_expiry_and_exhaustion(self):
        g = Game(SEED)
        self.assertTrue(g.flash())
        self.assertFalse(g.flash())
        self.assertEqual((g.charges, g.flashes_used), (1, 1))
        g.update(FLASH_DURATION)
        self.assertIn('flash faded', g.message)
        self.assertTrue(g.flash())
        g.update(FLASH_DURATION)
        self.assertFalse(g.flash())
        self.assertEqual((g.charges, g.flashes_used), (0, 2))
        self.assertIn('still explore', g.message)

    def test_midpoint_visibility_wall_occlusion_flash_and_memory(self):
        g = Game(SEED)
        g.grid = ('#########', '#.......#', '#.......#', '#...#...#', '#.......#', '#.......#', '#########')
        g.width, g.height = 9, 7
        g.player = (3, 3)
        g.seen.clear()
        g.reveal()
        target = (5, 3)
        self.assertNotIn(target, g.visible)
        self.assertIn((1, 2), g.visible)
        self.assertNotIn((3, 0), g.visible)
        self.assertEqual(NORMAL_RADIUS, 2.5)
        self.assertTrue(all(math.dist(g.player, cell) <= NORMAL_RADIUS for cell in g.visible))
        g.flash()
        self.assertIn(target, g.visible)
        self.assertIn((8, 3), g.visible)
        self.assertNotIn((8, 5), g.visible)
        self.assertEqual(FLASH_RADIUS, 5)
        self.assertTrue(all(math.dist(g.player, cell) <= FLASH_RADIUS for cell in g.visible))
        revealed = set(g.visible)
        g.update(FLASH_DURATION + 1)
        self.assertNotIn(target, g.visible)
        self.assertTrue(revealed <= g.seen)

    def test_collection_rewards_and_grows_sight_only_once(self):
        g = Game(SEED)
        reachable = distances(g.grid, g.player)
        target = min(g.lights, key=lambda cell: (reachable[cell], cell))
        steps = route(g.grid, g.player, target)
        g.flash()
        for step in steps:
            g.move(*step)
        self.assertEqual((g.collected, g.charges), (1, 2))
        self.assertAlmostEqual(g.radius, 2.7)
        dx, dy = steps[-1]
        g.move(-dx, -dy)
        g.move(dx, dy)
        self.assertEqual((g.collected, g.charges), (1, 2))
        self.assertAlmostEqual(g.radius, 2.7)
        self.assertIn('grows', g.message)

    def test_exit_explains_missing_fragments(self):
        g = Game(SEED)
        ex, ey = g.exit
        dx, dy = next((dx, dy) for dx, dy in DIRECTIONS if g.walkable(ex - dx, ey - dy))
        g.player = ex - dx, ey - dy
        self.assertEqual(g.move(dx, dy), 'locked')
        self.assertFalse(g.won)
        self.assertIn('4 more', g.message)

    def test_ten_maps_complete_without_flash_and_freeze_on_win(self):
        for seed in range(10):
            g = Game(seed)
            collect_all(g)
            self.assertTrue(g.won)
            self.assertEqual(g.collected, 4)
            self.assertAlmostEqual(g.radius, 3.3)
            self.assertEqual(g.flashes_used, 0)
            snapshot = g.player, g.steps, g.elapsed, g.charges
            g.move(-1, 0)
            g.flash()
            g.update(10)
            self.assertEqual(snapshot, (g.player, g.steps, g.elapsed, g.charges))

    def test_retry_restores_same_map_and_new_changes_it(self):
        g = Game(SEED)
        g.flash()
        g.update(10)
        g.reset()
        fresh = Game(SEED)
        for field in ('seed', 'grid', 'player', 'seen', 'lights', 'charges', 'steps', 'elapsed', 'won'):
            self.assertEqual(getattr(g, field), getattr(fresh, field))
        old_key = g.map_key
        self.assertEqual(old_key, f'v4-{SEED:06d}')
        g.new_map()
        self.assertNotEqual(g.seed, SEED)
        self.assertNotEqual(g.map_key, old_key)
        self.assertNotEqual(g.grid, fresh.grid)
        self.assertEqual((g.steps, g.collected, g.charges), (0, 0, 2))


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        import pygame
        from main import App
        self.pg = pygame
        self.temp = tempfile.TemporaryDirectory()
        self.score_file = Path(self.temp.name) / 'records.json'
        self.app = App(seed=SEED, scores_path=self.score_file)

    def tearDown(self):
        self.pg.quit()
        self.temp.cleanup()

    def key(self, key):
        self.app.handle(self.pg.event.Event(self.pg.KEYDOWN, key=key))

    def test_focus_loss_pauses_timer_and_flash(self):
        a = self.app
        a.fresh_game()
        a.action('flash')
        a.update(0.2)
        snapshot = a.game.elapsed, a.game.flash_remaining, a.game.player
        a.handle(self.pg.event.Event(self.pg.WINDOWFOCUSLOST))
        a.update(5)
        self.key(self.pg.K_RIGHT)
        self.assertEqual(a.mode, 'paused')
        self.assertEqual(snapshot, (a.game.elapsed, a.game.flash_remaining, a.game.player))
        self.key(self.pg.K_ESCAPE)
        a.update(0.1)
        self.assertGreater(a.game.elapsed, snapshot[0])

    def test_retry_and_new_map_confirmations(self):
        a = self.app
        a.fresh_game()
        a.game.steps = 9
        self.key(self.pg.K_n)
        self.key(self.pg.K_ESCAPE)
        self.assertEqual((a.mode, a.game.seed, a.game.steps), ('playing', SEED, 9))
        self.key(self.pg.K_r)
        self.key(self.pg.K_RETURN)
        self.assertEqual((a.game.seed, a.game.steps), (SEED, 0))
        self.key(self.pg.K_n)
        self.key(self.pg.K_RETURN)
        self.assertNotEqual(a.game.seed, SEED)
        self.assertEqual(a.game.steps, 0)
        self.assertFalse(self.score_file.exists())

    def test_keyboard_moves_flashes_and_board_freezes_run(self):
        from main import MOVES
        a = self.app
        self.key(self.pg.K_RETURN)
        x, y = a.game.player
        key = next(key for key, (dx, dy) in MOVES.items() if a.game.walkable(x + dx, y + dy))
        a.next_move = 0
        self.key(key)
        self.assertEqual(a.game.steps, 1)
        self.key(self.pg.K_SPACE)
        self.assertEqual(a.game.charges, 1)
        snapshot = a.game.elapsed, a.game.flash_remaining
        self.key(self.pg.K_l)
        a.update(5)
        self.key(self.pg.K_SPACE)
        self.assertEqual(a.mode, 'board')
        self.assertEqual(snapshot, (a.game.elapsed, a.game.flash_remaining))
        self.assertEqual(a.game.charges, 1)
        self.key(self.pg.K_ESCAPE)
        self.assertEqual(a.mode, 'playing')

    def test_win_records_once_persists_and_retry_keeps_board(self):
        from scores import Leaderboard
        a = self.app
        a.fresh_game()
        collect_all(a.game, a.move)
        self.assertEqual(a.mode, 'won')
        self.assertEqual(a.run_rank, 1)
        self.assertTrue(a.run_saved)
        key = a.game.map_key
        a.move((1, 0))
        self.assertEqual(len(a.scores.for_map(key)), 1)
        self.assertEqual(len(Leaderboard(self.score_file).for_map(key)), 1)
        self.key(self.pg.K_RETURN)
        self.assertEqual(a.game.seed, SEED)
        self.assertEqual(a.game.steps, 0)
        self.assertEqual(len(a.scores.for_map(key)), 1)
        a.action('new')
        a.action('confirm')
        self.assertEqual(a.scores.for_map(a.game.map_key), [])
        self.assertEqual(len(a.scores.for_map(key)), 1)

    def test_all_screens_render_and_modal_blocks_hidden_buttons(self):
        a = self.app
        for mode in ('home', 'playing', 'paused', 'restart', 'won', 'board'):
            a.mode = mode
            a.draw()
            self.assertTrue(a.click_targets)
            if mode != 'playing':
                self.assertNotIn('flash', [action for _, action in a.click_targets])
        a.mode = 'home'
        a.action('flash')
        self.assertEqual(a.game.charges, 2)


if __name__ == '__main__':
    unittest.main()
