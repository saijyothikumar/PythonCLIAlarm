"""
Unit tests for the Alarm Clock Time & Duration Parser.
"""

from datetime import datetime, timedelta
import unittest

from src.alarm_clock.parser import (
    TimeParseError,
    parse_duration,
    parse_clock_time,
    parse_alarm_target,
)


class TestTimeParser(unittest.TestCase):
    def setUp(self):
        # Fixed reference time: 2026-09-03 14:30:00 (Thursday 2:30 PM)
        self.fixed_now = datetime(2026, 9, 3, 14, 30, 0)

    # ------------------ DURATION TESTS ------------------

    def test_parse_simple_seconds(self):
        delta = parse_duration("45s")
        self.assertEqual(delta, timedelta(seconds=45))

    def test_parse_simple_minutes(self):
        delta = parse_duration("15m")
        self.assertEqual(delta, timedelta(minutes=15))

    def test_parse_simple_hours(self):
        delta = parse_duration("2h")
        self.assertEqual(delta, timedelta(hours=2))

    def test_parse_compound_duration(self):
        delta = parse_duration("1h30m15s")
        self.assertEqual(delta, timedelta(hours=1, minutes=30, seconds=15))

    def test_parse_duration_with_words_and_spaces(self):
        delta = parse_duration("1 hour 15 mins 30 secs")
        self.assertEqual(delta, timedelta(hours=1, minutes=15, seconds=30))

    def test_parse_prefixed_plus_duration(self):
        delta = parse_duration("+10m")
        self.assertEqual(delta, timedelta(minutes=10))

    def test_parse_invalid_durations(self):
        invalid_cases = ["", "0s", "-5m", "abc", "10x", "minutes"]
        for case in invalid_cases:
            with self.subTest(case=case):
                with self.assertRaises(TimeParseError):
                    parse_duration(case)

    # ------------------ CLOCK TIME TESTS ------------------

    def test_parse_24h_same_day(self):
        # 16:45 is later today than 14:30
        target, is_tomorrow = parse_clock_time("16:45", now=self.fixed_now)
        self.assertEqual(target, datetime(2026, 9, 3, 16, 45, 0))
        self.assertFalse(is_tomorrow)

    def test_parse_24h_next_day_rollover(self):
        # 09:15 is earlier today than 14:30, so must be tomorrow
        target, is_tomorrow = parse_clock_time("09:15", now=self.fixed_now)
        self.assertEqual(target, datetime(2026, 9, 4, 9, 15, 0))
        self.assertTrue(is_tomorrow)

    def test_parse_12h_pm(self):
        # 7:30pm is 19:30 today
        target, is_tomorrow = parse_clock_time("7:30pm", now=self.fixed_now)
        self.assertEqual(target, datetime(2026, 9, 3, 19, 30, 0))
        self.assertFalse(is_tomorrow)

    def test_parse_12h_am_rollover(self):
        # 7:30am is earlier today, so tomorrow
        target, is_tomorrow = parse_clock_time("7:30am", now=self.fixed_now)
        self.assertEqual(target, datetime(2026, 9, 4, 7, 30, 0))
        self.assertTrue(is_tomorrow)

    def test_parse_midnight_and_noon(self):
        # 12:00am is midnight (00:00:00) -> earlier today, so tomorrow
        target_mid, is_tom_mid = parse_clock_time("12:00am", now=self.fixed_now)
        self.assertEqual(target_mid, datetime(2026, 9, 4, 0, 0, 0))
        self.assertTrue(is_tom_mid)

        # 12:00pm is noon (12:00:00) -> earlier today than 14:30, so tomorrow
        target_noon, is_tom_noon = parse_clock_time("12:00pm", now=self.fixed_now)
        self.assertEqual(target_noon, datetime(2026, 9, 4, 12, 0, 0))
        self.assertTrue(is_tom_noon)

        # Word 'noon'
        target_w_noon, is_tom_w_noon = parse_clock_time("noon", now=self.fixed_now)
        self.assertEqual(target_w_noon, datetime(2026, 9, 4, 12, 0, 0))
        self.assertTrue(is_tom_w_noon)

        # Word 'midnight'
        target_w_mid, is_tom_w_mid = parse_clock_time("midnight", now=self.fixed_now)
        self.assertEqual(target_w_mid, datetime(2026, 9, 4, 0, 0, 0))
        self.assertTrue(is_tom_w_mid)

    def test_parse_duration_with_in_prefix(self):
        delta = parse_duration("in 15 minutes")
        self.assertEqual(delta, timedelta(minutes=15))
        delta2 = parse_duration("in 30s")
        self.assertEqual(delta2, timedelta(seconds=30))

    def test_parse_invalid_clock_times(self):
        invalid_cases = ["25:00", "12:65", "13pm", "invalid", ""]
        for case in invalid_cases:
            with self.subTest(case=case):
                with self.assertRaises(TimeParseError):
                    parse_clock_time(case, now=self.fixed_now)

    # ------------------ UNIFIED TARGET TESTS ------------------

    def test_unified_duration_target(self):
        target, desc = parse_alarm_target("15m", now=self.fixed_now)
        self.assertEqual(target, datetime(2026, 9, 3, 14, 45, 0))
        self.assertIn("15 minutes", desc)

    def test_unified_clock_target(self):
        target, desc = parse_alarm_target("7:30pm", now=self.fixed_now)
        self.assertEqual(target, datetime(2026, 9, 3, 19, 30, 0))
        self.assertIn("today at 07:30:00 PM", desc)


if __name__ == "__main__":
    unittest.main()
