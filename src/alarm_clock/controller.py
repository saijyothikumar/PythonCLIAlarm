"""
Alarm Controller Module.

Orchestrates:
- Engine countdown loop
- Terminal UI live updates
- Multi-threaded non-blocking audio ringer with immediate stop signal
- User keyboard interaction for Snooze [s], Dismiss [d/Enter], and Quit [q]
- Auto-silence safety timeout
"""

from datetime import datetime
import os
import sys
import threading
import time
from typing import Optional

from .engine import AlarmConfig, AlarmEngine, AlarmStatus
from .sound import SoundPlayer
from .ui import TerminalUI, show_cursor, hide_cursor


class AlarmController:
    """Coordinates scheduler engine, UI presentation, and concurrent audio ringer."""

    def __init__(self, config: AlarmConfig):
        self.config = config
        self.ui = TerminalUI()
        self.player = SoundPlayer()
        self._stop_audio = threading.Event()
        self._audio_thread: Optional[threading.Thread] = None

        self.engine = AlarmEngine(
            config=self.config,
            on_tick=self._handle_tick,
            on_pre_alert=self._handle_pre_alert,
            on_trigger=self._handle_trigger,
        )

    def _handle_tick(self, remaining_seconds: float, target_time: datetime, status: AlarmStatus) -> None:
        """Called every countdown tick to update in-place terminal display."""
        is_pre_alert = (status == AlarmStatus.PRE_ALERT)
        self.ui.update_countdown(
            remaining_seconds=remaining_seconds,
            target_time=target_time,
            message=self.config.message,
            is_pre_alert=is_pre_alert,
        )

    def _handle_pre_alert(self, message: str, remaining_seconds: float) -> None:
        """Called when pre-alarm threshold is reached."""
        self.ui.show_pre_alert_banner(message, remaining_seconds)
        # Emit a subtle pre-alert tone asynchronously so countdown timing stays exact
        threading.Thread(target=lambda: self.player.emit_tone(659, 150), daemon=True).start()

    def _audio_loop(self) -> None:
        """Background thread worker to loop alarm audio until stopped."""
        while not self._stop_audio.is_set():
            if self.config.sound_file:
                try:
                    self.player.play_file(
                        self.config.sound_file,
                        duration_sec=self.config.sound_duration,
                        stop_event=self._stop_audio,
                    )
                except Exception:
                    self.player.play_pattern_cycle(self.config.pattern, stop_event=self._stop_audio)
            else:
                self.player.play_pattern_cycle(self.config.pattern, stop_event=self._stop_audio)
            
            # Non-blocking pause between burst cycles; terminates immediately when stopped
            if self._stop_audio.wait(0.35):
                break

    def _start_audio_ringer(self) -> None:
        """Start repeating audio playback on a daemon thread."""
        self._stop_audio.clear()
        self._audio_thread = threading.Thread(target=self._audio_loop, daemon=True)
        self._audio_thread.start()

    def _stop_audio_ringer(self) -> None:
        """Signal and wait for audio thread to stop."""
        self._stop_audio.set()
        # Purge active OS audio streams immediately
        if hasattr(self.player, "stop"):
            self.player.stop()
        if self._audio_thread and self._audio_thread.is_alive():
            self._audio_thread.join(timeout=0.25)

    def _read_user_alarm_action(self, timeout_sec: float = 60.0) -> str:
        """
        Wait for user input to Snooze [s], Dismiss [d/Enter/Space/any key], or Quit [q].
        Falls back to auto-silence if no key is pressed within timeout_sec.
        Immediately stops audio ringer upon receiving ANY input.
        """
        start_time = time.time()
        result_holder: list = []

        # Background listener for standard input (handles line-buffered terminals, Enter key, etc.)
        def _stdin_worker():
            try:
                line = sys.stdin.readline()
                if line:
                    self._stop_audio_ringer()
                    clean = line.strip().lower()
                    if clean == "s":
                        result_holder.append("snooze")
                    elif clean == "q":
                        result_holder.append("quit")
                    else:
                        result_holder.append("dismiss")
            except Exception:
                pass

        try:
            stdin_thread = threading.Thread(target=_stdin_worker, daemon=True)
            stdin_thread.start()
        except Exception:
            pass

        # Windows direct console keystroke listener via msvcrt
        msvcrt_module = None
        if os.name == "nt":
            try:
                import msvcrt
                msvcrt_module = msvcrt
                while msvcrt_module.kbhit():
                    msvcrt_module.getch()
            except ImportError:
                pass

        while (time.time() - start_time) < timeout_sec:
            # 1. Check if stdin thread caught input
            if result_holder:
                self._stop_audio_ringer()
                return result_holder[0]

            # 2. Check if msvcrt caught a raw keystroke
            if msvcrt_module and msvcrt_module.kbhit():
                try:
                    ch = msvcrt_module.getch()
                    # Discard multi-byte prefixes (arrow keys, function keys)
                    if ch in (b"\x00", b"\xe0") and msvcrt_module.kbhit():
                        msvcrt_module.getch()
                        continue
                    # IMMEDIATELY halt audio at the microsecond of key detection!
                    self._stop_audio_ringer()
                    decoded = ch.decode("utf-8", errors="ignore").lower()
                except Exception:
                    decoded = ""

                if decoded == "s":
                    return "snooze"
                elif decoded == "q":
                    return "quit"
                else:
                    # ANY other key (Enter, Space, Esc, d, etc.) dismisses instantly!
                    return "dismiss"

            time.sleep(0.01)

        self._stop_audio_ringer()
        return "auto_snooze"

    def _handle_trigger(self, config: AlarmConfig, missed_by: float) -> None:
        """Triggered when alarm time is reached."""
        self._start_audio_ringer()
        self.ui.show_ringing_banner(config.message, missed_by)

        action = self._read_user_alarm_action(timeout_sec=60.0)
        self._stop_audio_ringer()

        if action in ("snooze", "auto_snooze"):
            new_target = self.engine.snooze(self.config.snooze_minutes)
            self.ui.print_snoozed(self.config.message, new_target)
            # Re-enter countdown loop
            self.start(show_header=False)
        elif action == "dismiss":
            self.engine.dismiss()
            self.ui.print_dismissed(self.config.message)
        else:  # quit or cancelled
            self.engine.cancel()
            self.ui.print_cancelled()

    def start(self, show_header: bool = True, desc: str = "") -> AlarmStatus:
        """Start the alarm process."""
        hide_cursor()
        if show_header:
            sound_name = self.config.sound_file if self.config.sound_file else f"Pattern '{self.config.pattern}'"
            self.ui.print_header(
                message=self.config.message,
                target_time=self.config.target_time,
                desc=desc or "scheduled",
                sound_name=sound_name,
                snooze_min=self.config.snooze_minutes,
            )

        try:
            status = self.engine.run_loop()
            return status
        except KeyboardInterrupt:
            self._stop_audio_ringer()
            self.engine.cancel()
            self.ui.print_cancelled()
            return AlarmStatus.CANCELLED
        finally:
            show_cursor()
