"""
Drift-Free Core Clock Scheduler & Alarm State Machine.

Features:
- Absolute wall-clock delta calculation (zero sleep drift accumulation)
- Adaptive sleeping for CPU efficiency and responsiveness
- System sleep/suspend detection & missed alarm recovery
- Pre-alarm heads-up trigger calculation
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import time
from typing import Callable, Optional


class AlarmStatus(Enum):
    SCHEDULED = "SCHEDULED"
    PRE_ALERT = "PRE_ALERT"
    RINGING = "RINGING"
    SNOOZED = "SNOOZED"
    DISMISSED = "DISMISSED"
    CANCELLED = "CANCELLED"
    MISSED = "MISSED"


@dataclass
class AlarmConfig:
    target_time: datetime
    message: str = "Alarm!"
    pattern: str = "chime"
    sound_file: Optional[str] = None
    sound_duration: Optional[float] = None
    snooze_minutes: int = 5
    pre_alert_seconds: Optional[int] = None


class AlarmEngine:
    """
    Manages the lifecycle of an alarm, providing high-precision
    drift-free timing and state transitions.
    """

    def __init__(
        self,
        config: AlarmConfig,
        on_tick: Optional[Callable[[float, datetime, AlarmStatus], None]] = None,
        on_pre_alert: Optional[Callable[[str, float], None]] = None,
        on_trigger: Optional[Callable[[AlarmConfig, float], None]] = None,
    ):
        self.config = config
        self.status = AlarmStatus.SCHEDULED
        self.on_tick = on_tick
        self.on_pre_alert = on_pre_alert
        self.on_trigger = on_trigger

        self._pre_alert_fired = False
        self._is_running = False

    def snooze(self, custom_minutes: Optional[int] = None) -> datetime:
        """
        Snooze the alarm by a specified number of minutes.
        Resets state to SNOOZED and updates target time.
        """
        mins = custom_minutes if custom_minutes is not None else self.config.snooze_minutes
        new_target = (datetime.now() + timedelta(minutes=mins)).replace(microsecond=0)
        self.config.target_time = new_target
        self.status = AlarmStatus.SNOOZED
        self._pre_alert_fired = False
        return new_target

    def dismiss(self) -> None:
        """Dismiss the alarm."""
        self.status = AlarmStatus.DISMISSED
        self._is_running = False

    def cancel(self) -> None:
        """Cancel the alarm."""
        self.status = AlarmStatus.CANCELLED
        self._is_running = False

    def run_loop(self) -> AlarmStatus:
        """
        Main execution loop.
        Monitors wall clock time until the alarm fires or is cancelled.
        """
        self._is_running = True
        last_check_wall = datetime.now()

        while self._is_running:
            now = datetime.now()
            remaining_seconds = (self.config.target_time - now).total_seconds()

            # 1. Check for system sleep / suspend gap (gap > 4s when sleep was max 0.5s)
            elapsed_wall = (now - last_check_wall).total_seconds()
            if elapsed_wall > 4.0 and remaining_seconds <= 0:
                # System was asleep and woke up past alarm time!
                missed_by = abs(remaining_seconds)
                self.status = AlarmStatus.MISSED
                if self.on_trigger:
                    self.on_trigger(self.config, missed_by)
                return self.status

            last_check_wall = now

            # 2. Check if target time reached
            if remaining_seconds <= 0:
                self.status = AlarmStatus.RINGING
                if self.on_trigger:
                    self.on_trigger(self.config, 0.0)
                return self.status

            # 3. Check pre-alarm heads-up trigger
            if (
                self.config.pre_alert_seconds
                and not self._pre_alert_fired
                and remaining_seconds <= (self.config.pre_alert_seconds + 0.05)
            ):
                self._pre_alert_fired = True
                self.status = AlarmStatus.PRE_ALERT
                if self.on_pre_alert:
                    self.on_pre_alert(self.config.message, self.config.pre_alert_seconds)

            # 4. Tick callback
            if self.on_tick:
                self.on_tick(remaining_seconds, self.config.target_time, self.status)

            # 5. High-precision adaptive sleep: never overshoot target or pre-alert boundary
            sleep_time = min(0.2, max(0.01, remaining_seconds))
            if self.config.pre_alert_seconds and not self._pre_alert_fired:
                time_to_pre = remaining_seconds - self.config.pre_alert_seconds
                if time_to_pre > 0:
                    sleep_time = min(sleep_time, max(0.01, time_to_pre))

            time.sleep(sleep_time)

        return self.status
