"""Persistent ranking, same-map isolation and recoverable file failures."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scores import Leaderboard, Score


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'scores.json'

    def tearDown(self):
        self.temp.cleanup()

    def test_sort_by_steps_then_time_keep_five_and_reload(self):
        board = Leaderboard(self.path)
        for steps, seconds, flashes in [(20, 10, 4), (18, 20, 3), (18, 10, 6), (19, 1, 0), (22, 1, 0), (18, 10, 0), (21, 1, 0)]:
            board.add('v2-000001', steps, seconds, flashes)
        rows = board.for_map('v2-000001')
        self.assertEqual([row.steps for row in rows], [18, 18, 18, 19, 20])
        self.assertEqual([row.flashes for row in rows[:2]], [6, 0])
        self.assertEqual(Leaderboard(self.path).for_map('v2-000001'), rows)
        rank, saved = board.add('v2-000001', 100, 1, 0)
        self.assertEqual(rank, 6)
        self.assertTrue(saved)
        self.assertEqual(len(board.for_map('v2-000001')), 5)

    def test_map_records_are_independent(self):
        board = Leaderboard(self.path)
        board.add('v2-000001', 100, 50, 1)
        board.add('v2-000002', 200, 90, 3)
        board.add('v3-000001', 1, 1, 0)
        self.assertEqual(board.for_map('v2-000001')[0].steps, 100)
        self.assertEqual(board.for_map('v2-000002')[0].steps, 200)
        self.assertEqual(board.for_map('v2-000003'), [])
        self.assertEqual(board.for_map('v3-000001')[0].steps, 1)
        self.assertEqual(Leaderboard(self.path).for_map('v2-000001')[0].steps, 100)

    def test_corrupt_file_is_preserved_and_game_can_record_in_memory(self):
        self.path.write_text('{broken', encoding='utf-8')
        board = Leaderboard(self.path)
        rank, saved = board.add('v2-000001', 20, 10, 1)
        self.assertEqual(rank, 1)
        self.assertFalse(saved)
        self.assertEqual(len(board.for_map('v2-000001')), 1)
        self.assertEqual(self.path.read_text(encoding='utf-8'), '{broken')

    def test_invalid_record_file_is_handled(self):
        for bad in ({'version': 999, 'maps': {}}, {'version': 1, 'maps': {'v2-000001': [{'steps': -1, 'seconds': 1, 'flashes': 0}]}}):
            self.path.write_text(json.dumps(bad), encoding='utf-8')
            board = Leaderboard(self.path)
            self.assertFalse(board.can_save)
            self.assertEqual(board.for_map('v2-000001'), [])

    def test_unwritable_file_is_nonfatal(self):
        board = Leaderboard(self.path)
        with patch('scores.tempfile.NamedTemporaryFile', side_effect=PermissionError('read only')):
            rank, saved = board.add('v2-000001', 20, 10, 0)
        self.assertEqual(rank, 1)
        self.assertFalse(saved)
        self.assertEqual(len(board.for_map('v2-000001')), 1)
        self.assertFalse(self.path.exists())

    def test_atomic_write_failure_keeps_previous_file(self):
        board = Leaderboard(self.path)
        board.add('v2-000001', 20, 10, 0)
        original = self.path.read_text(encoding='utf-8')
        with patch('scores.Path.replace', side_effect=OSError('failed')):
            rank, saved = board.add('v2-000001', 10, 10, 0)
        self.assertFalse(saved)
        self.assertEqual(rank, 1)
        self.assertEqual(self.path.read_text(encoding='utf-8'), original)
        self.assertEqual(list(self.path.parent.glob('.mistbound-scores-*')), [])

    def test_invalid_scores_rejected_and_memory_only_is_explicit(self):
        for score in [(0, 10, 1), (True, 10, 1), (20, float('nan'), 1), (20, -1, 1), (20, 10, 7)]:
            with self.assertRaises(ValueError):
                Score(*score)
        board = Leaderboard()
        rank, saved = board.add('v2-000001', 20, 10, 1)
        self.assertEqual(rank, 1)
        self.assertFalse(saved)
        self.assertIn('session only', board.notice)


if __name__ == '__main__':
    unittest.main()
