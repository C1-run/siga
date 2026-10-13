"""Unit tests for monie-common."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from monie_common import get_logger, utc_now, utc_iso
from monie_common.time_utils import iso_to_dt
from monie_common.test_helpers import temp_db_path


class TestLogger:
    def test_get_logger_returns_logger(self):
        log = get_logger("test.module")
        assert log is not None
        assert log.name == "test.module"

    def test_get_logger_caches_handlers(self):
        log1 = get_logger("test.cached")
        h_count = len(log1.handlers)
        log2 = get_logger("test.cached")
        assert len(log2.handlers) == h_count


class TestTimeUtils:
    def test_utc_now_is_timezone_aware(self):
        now = utc_now()
        assert now.tzinfo is not None
        assert now.tzinfo == timezone.utc

    def test_utc_iso_format(self):
        dt = datetime(2026, 9, 7, 12, 0, 0, tzinfo=timezone.utc)
        assert utc_iso(dt) == "2026-09-07T12:00:00+00:00"

    def test_utc_iso_default_now(self):
        s = utc_iso()
        assert "T" in s
        assert "+" in s or "Z" in s

    def test_iso_to_dt_roundtrip(self):
        original = utc_now()
        parsed = iso_to_dt(utc_iso(original))
        assert abs((parsed - original).total_seconds()) < 1

    def test_iso_to_dt_naive_adds_utc(self):
        s = "2026-09-07T12:00:00"
        dt = iso_to_dt(s)
        assert dt.tzinfo is not None


class TestTempDbPath:
    def test_creates_and_cleans_up(self):
        with temp_db_path() as path:
            assert isinstance(path, Path)
            path.write_text("test")
            assert path.exists()
        assert not path.exists()
