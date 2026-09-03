"""
Unit tests for AlarmEngine and Pre-Alarm Alert Triggering.
"""

from datetime import datetime, timedelta
import unittest

from src.alarm_clock.engine import AlarmConfig, AlarmEngine, AlarmStatus


class TestAlarmEngine(unittest.TestCase):

    def test_engine_trigger_lifecycle(self):
        # 0.5s timer
        target = datetime.now() + timedelta(seconds=0.5)
        config = AlarmConfig(target_time=target, message="Quick Test")
        
        triggered = []
        engine = AlarmEngine(
            config=config,
            on_trigger=lambda cfg, missed: triggered.append((cfg.message, missed))
        )
        status = engine.run_loop()
        
        self.assertEqual(status, AlarmStatus.RINGING)
        self.assertEqual(len(triggered), 1)
        self.assertEqual(triggered[0][0], "Quick Test")

    def test_engine_snooze_updates_target(self):
        target = datetime.now() + timedelta(seconds=1)
        config = AlarmConfig(target_time=target, snooze_minutes=10)
        engine = AlarmEngine(config=config)
        
        new_target = engine.snooze()
        self.assertEqual(engine.status, AlarmStatus.SNOOZED)
        self.assertGreater(new_target, datetime.now())
        self.assertEqual(config.target_time, new_target)

    def test_pre_alert_firing(self):
        # Target 2 seconds away, pre-alert threshold at 3 seconds remaining
        target = datetime.now() + timedelta(seconds=1.5)
        config = AlarmConfig(
            target_time=target,
            message="Meeting",
            pre_alert_seconds=3  # threshold is higher than current remaining, so fires immediately
        )
        
        pre_alerts = []
        engine = AlarmEngine(
            config=config,
            on_pre_alert=lambda msg, rem: pre_alerts.append((msg, rem)),
        )
        
        # Run loop
        status = engine.run_loop()
        self.assertEqual(status, AlarmStatus.RINGING)
        self.assertGreaterEqual(len(pre_alerts), 1)
        self.assertEqual(pre_alerts[0][0], "Meeting")


if __name__ == "__main__":
    unittest.main()
