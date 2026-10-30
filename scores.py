"""A small local top-five board for each map and rules version."""
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import re
import tempfile


@dataclass(frozen=True)
class Score:
    steps: int
    seconds: float
    flashes: int

    def __post_init__(self):
        if (type(self.steps) is not int or self.steps < 1
                or type(self.seconds) not in (int, float) or not math.isfinite(self.seconds) or self.seconds < 0
                or type(self.flashes) is not int or not 0 <= self.flashes <= 6):
            raise ValueError("Invalid completion record")


class Leaderboard:
    def __init__(self, path=None):
        # None is intentionally memory-only, useful for previews and tests.
        self.path = Path(path) if path is not None else None
        self.maps = {}
        self.notice = ""
        self.can_save = self.path is not None
        if self.path is not None:
            self.load()

    def load(self):
        try:
            if self.path.stat().st_size > 1_000_000:
                raise ValueError("Records file is too large")
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if (not isinstance(data, dict) or data.get("version") != 1
                    or not isinstance(data.get("maps"), dict)):
                raise ValueError("Unknown records format")
            loaded = {}
            for key, rows in data["maps"].items():
                if not re.fullmatch(r"v[1-9]\d*-\d{6}", key) or not isinstance(rows, list) or len(rows) > 5:
                    raise ValueError("Invalid map records")
                loaded[key] = sorted([Score(**row) for row in rows], key=lambda row: (row.steps, row.seconds))
            self.maps = loaded
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError, OverflowError):
            # Keep an unreadable file intact; records still work for this session.
            self.can_save = False
            self.notice = "Records file unavailable; this session only."

    def for_map(self, key):
        return list(self.maps.get(key, []))

    def add(self, key, steps, seconds, flashes):
        if not re.fullmatch(r"v[1-9]\d*-\d{6}", key):
            raise ValueError("Invalid map key")
        record = Score(steps, round(seconds, 1), flashes)
        rows = self.for_map(key) + [record]
        rows.sort(key=lambda row: (row.steps, row.seconds))
        rank = next(i for i, row in enumerate(rows, 1) if row is record)
        self.maps[key] = rows[:5]
        saved = self.save()
        return rank, saved

    def save(self):
        if not self.can_save:
            self.notice = "Records available this session only."
            return False
        payload = {"version": 1, "maps": {key: [asdict(row) for row in rows] for key, rows in self.maps.items()}}
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix=".mistbound-scores-", suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(payload, handle, indent=2, allow_nan=False)
                handle.write("\n")
            temporary.replace(self.path)
            self.notice = "Saved on this computer."
            return True
        except OSError:
            self.notice = "Could not save records; this session only."
            return False
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
