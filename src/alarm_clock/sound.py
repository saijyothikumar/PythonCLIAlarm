"""
Zero-dependency Cross-Platform Sound Engine.

Supports:
- Built-in synthesized audio patterns (chime, digital, pulse, bell)
- Custom WAV file playback with duration slicing and bounds validation
- Platform-native sound dispatchers (Windows winsound, macOS afplay, Linux aplay, ASCII bell)
"""

import os
import platform
import subprocess
import sys
import threading
import time
from typing import Dict, List, Optional, Tuple
import wave


class AudioError(Exception):
    """Base exception for audio-related errors."""
    pass


class AudioValidationError(AudioError):
    """Raised when audio configuration or slicing bounds are invalid."""
    pass


# Sound pattern frequency (Hz) & duration (ms) tuples: (freq, duration_ms, pause_after_ms)
BUILTIN_PATTERNS: Dict[str, List[Tuple[int, int, int]]] = {
    "chime": [
        (523, 120, 30),   # C5
        (659, 120, 30),   # E5
        (784, 120, 30),   # G5
        (1046, 250, 300), # C6
    ],
    "digital": [
        (850, 80, 50),
        (850, 80, 150),
        (850, 80, 50),
        (850, 80, 400),
    ],
    "pulse": [
        (1200, 100, 80),
        (1200, 100, 80),
        (1200, 100, 400),
    ],
    "bell": [
        (0, 0, 300),  # Handled via \a
    ],
}


def inspect_wav_file(file_path: str) -> Tuple[float, int, int]:
    """
    Inspect a WAV file and return (duration_in_seconds, sample_rate, channels).
    
    Raises:
        AudioValidationError: If file does not exist or is not a valid WAV file.
    """
    if not os.path.exists(file_path):
        raise AudioValidationError(f"Audio file not found: '{file_path}'")
    
    try:
        with wave.open(file_path, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            channels = wf.getnchannels()
            if rate <= 0:
                raise AudioValidationError("Invalid audio sample rate in WAV header.")
            duration = frames / float(rate)
            return duration, rate, channels
    except wave.Error as err:
        raise AudioValidationError(f"Invalid or unsupported WAV audio file: {err}") from err
    except Exception as err:
        raise AudioValidationError(f"Failed to read audio file '{file_path}': {err}") from err


def validate_audio_slice(file_path: str, start_sec: float = 0.0, end_sec: Optional[float] = None) -> Tuple[float, float]:
    """
    Validate audio slice bounds.
    
    Returns:
        Tuple[float, float]: (clamped_start_sec, clamped_end_sec)
        
    Raises:
        AudioValidationError: If file is missing or start offset exceeds audio length.
    """
    total_duration, _, _ = inspect_wav_file(file_path)

    if start_sec < 0:
        raise AudioValidationError(f"Start time cannot be negative: {start_sec}s.")

    if start_sec >= total_duration:
        raise AudioValidationError(
            f"Start time ({start_sec:.2f}s) is beyond total sound duration ({total_duration:.2f}s)."
        )

    if end_sec is None:
        effective_end = total_duration
    else:
        if end_sec <= start_sec:
            raise AudioValidationError(
                f"End time ({end_sec:.2f}s) must be greater than start time ({start_sec:.2f}s)."
            )
        if end_sec > total_duration:
            # Clamp with notice
            effective_end = total_duration
        else:
            effective_end = end_sec

    return start_sec, effective_end


class SoundPlayer:
    """Cross-platform zero-dependency sound player."""

    def __init__(self):
        self.os_type = platform.system()  # 'Windows', 'Darwin' (macOS), 'Linux'
        self._has_winsound = False
        if self.os_type == "Windows":
            try:
                import winsound
                self._winsound = winsound
                self._has_winsound = True
            except ImportError:
                self._has_winsound = False

    def emit_tone(self, freq_hz: int, duration_ms: int, stop_event: Optional[threading.Event] = None) -> None:
        """Emit a synthetic tone of specified frequency and duration."""
        if stop_event and stop_event.is_set():
            return

        if self._has_winsound and freq_hz > 0:
            try:
                self._winsound.Beep(freq_hz, duration_ms)
                return
            except Exception:
                pass

        if freq_hz == 0:
            # Explicit ASCII terminal bell request
            sys.stdout.write("\a")
            sys.stdout.flush()
            if stop_event:
                stop_event.wait(duration_ms / 1000.0)
            else:
                time.sleep(duration_ms / 1000.0)
        else:
            # Hardware tone was unavailable: sleep for duration without spamming \a
            if stop_event:
                stop_event.wait(duration_ms / 1000.0)
            else:
                time.sleep(duration_ms / 1000.0)

    def stop(self) -> None:
        """Immediately purge and halt all active OS sound output."""
        if self.os_type == "Windows" and self._has_winsound:
            try:
                self._winsound.PlaySound(None, self._winsound.SND_PURGE)
            except Exception:
                pass

    def play_pattern_cycle(self, pattern_name: str = "chime", stop_event: Optional[threading.Event] = None) -> None:
        """
        Play a single cycle of a built-in sound pattern.
        Checks stop_event between notes and during pauses for zero-latency cancellation.
        """
        tones = BUILTIN_PATTERNS.get(pattern_name.lower(), BUILTIN_PATTERNS["chime"])
        
        for freq, dur_ms, pause_ms in tones:
            if stop_event and stop_event.is_set():
                break

            if freq == 0:
                # Explicit terminal bell request
                sys.stdout.write("\a")
                sys.stdout.flush()
                if stop_event and stop_event.wait(dur_ms / 1000.0):
                    break
            else:
                self.emit_tone(freq, dur_ms, stop_event=stop_event)

            if stop_event and stop_event.is_set():
                break

            if pause_ms > 0:
                if stop_event:
                    if stop_event.wait(pause_ms / 1000.0):
                        break
                else:
                    time.sleep(pause_ms / 1000.0)

    def play_file(self, file_path: str, duration_sec: Optional[float] = None, stop_event: Optional[threading.Event] = None) -> None:
        """
        Play a custom audio file using native OS facilities.
        Optionally limits playback to duration_sec.
        """
        if not os.path.exists(file_path):
            raise AudioValidationError(f"Audio file not found: '{file_path}'")

        if self.os_type == "Windows" and self._has_winsound and file_path.lower().endswith(".wav"):
            # Use winsound for WAV
            try:
                self._winsound.PlaySound(file_path, self._winsound.SND_FILENAME | self._winsound.SND_ASYNC)
                start_t = time.time()
                while True:
                    if stop_event and stop_event.is_set():
                        self.stop()
                        break
                    if duration_sec and (time.time() - start_t) >= duration_sec:
                        self.stop()
                        break
                    if stop_event:
                        if stop_event.wait(0.05):
                            self.stop()
                            break
                    else:
                        time.sleep(0.05)
                return
            except Exception:
                pass

        # Fallback using native subprocesses on macOS/Linux
        player_cmd = None
        if self.os_type == "Darwin":
            player_cmd = ["afplay", file_path]
        elif self.os_type == "Linux":
            player_cmd = ["aplay", file_path] if subprocess.run(["which", "aplay"], capture_output=True).returncode == 0 else ["paplay", file_path]

        if player_cmd:
            try:
                proc = subprocess.Popen(player_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                start_t = time.time()
                while proc.poll() is None:
                    if stop_event and stop_event.is_set():
                        proc.terminate()
                        break
                    if duration_sec and (time.time() - start_t) >= duration_sec:
                        proc.terminate()
                        break
                    if stop_event:
                        if stop_event.wait(0.05):
                            proc.terminate()
                            break
                    else:
                        time.sleep(0.05)
                return
            except Exception:
                pass

        # Universal fallback: terminal bell
        self.play_pattern_cycle("chime", stop_event=stop_event)
