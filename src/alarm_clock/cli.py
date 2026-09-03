"""
Command Line Interface (CLI) Argument Parser & Dispatcher.

Handles:
- Quick positional alarm input ('15m', '7:30am')
- Custom flags (-m message, --sound, --pattern, --snooze, --pre-alert)
- Audio diagnostic & preview flags (--test-sound, --preview)
- Preset management subcommands (save, list, run, delete)
- Rich, structured help output (--help)
"""

import argparse
import sys
from typing import List, Optional

from src.alarm_clock.sound import BUILTIN_PATTERNS, SoundPlayer, AudioValidationError, inspect_wav_file

HELP_BANNER = """
============================================================
              Python CLI Alarm Clock (v1.0.0)
============================================================
A fast, resilient, zero-dependency alarm clock for your terminal.

QUICK USAGE:
  alarm 10m                      # 10-minute timer
  alarm 7:30am                   # Alarm for 7:30 AM (auto-rolls to tomorrow if passed)
  alarm 14:45 -m "Sprint Sync"   # Alarm with custom message

CUSTOM OPTIONS:
  alarm 25m -m "Pomodoro" --sound digital --pre-alert 2m --snooze 10
  alarm 08:00 --sound /path/to/song.wav --sound-duration 30s

PRESET MANAGEMENT:
  alarm save standup 09:30 -m "Team Sync" --sound chime
  alarm run standup
  alarm list
  alarm delete standup

DIAGNOSTICS & HELP:
  alarm --test-sound             # Verify speaker output and audio drivers
  alarm --preview digital        # Preview specific sound pattern
  alarm --help                   # Show this detailed help manual
"""


def build_parser() -> argparse.ArgumentParser:
    """Construct and configure the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="alarm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=HELP_BANNER,
        add_help=True,
    )

    # Positional target (optional; if omitted and no flags, launches interactive wizard)
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Target time ('07:30', '7:30am', '14:45') or duration ('10s', '15m', '1h30m').",
    )

    # Optional customization flags
    parser.add_argument(
        "-m", "--message",
        dest="message",
        default="Alarm!",
        help="Alarm label or custom reminder message (default: 'Alarm!').",
    )

    parser.add_argument(
        "-p", "--pattern",
        dest="pattern",
        choices=list(BUILTIN_PATTERNS.keys()),
        default="chime",
        help=f"Built-in sound pattern to play. Choices: {', '.join(BUILTIN_PATTERNS.keys())} (default: chime).",
    )

    parser.add_argument(
        "--sound",
        dest="sound_file",
        default=None,
        help="Path to custom audio file (.wav) to play instead of built-in pattern.",
    )

    parser.add_argument(
        "--sound-duration",
        dest="sound_duration",
        default=None,
        help="Limit custom audio playback duration (e.g. '30s', '45s').",
    )

    parser.add_argument(
        "--snooze",
        dest="snooze_minutes",
        type=int,
        default=5,
        help="Snooze duration in minutes when pressing [s] (default: 5).",
    )

    parser.add_argument(
        "--pre-alert",
        dest="pre_alert",
        default=None,
        help="Gentle heads-up notification before alarm (e.g. '2m', '30s').",
    )

    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Launch interactive setup wizard regardless of arguments.",
    )

    # Audio diagnostics
    parser.add_argument(
        "--test-sound",
        action="store_true",
        help="Test speaker output and audio drivers, then exit.",
    )

    parser.add_argument(
        "--preview",
        dest="preview_pattern",
        choices=list(BUILTIN_PATTERNS.keys()),
        help="Preview a specific built-in sound pattern, then exit.",
    )

    # Subcommands for preset management
    subparsers = parser.add_subparsers(dest="subcommand", help="Preset management commands")

    # Subcommand: save
    parser_save = subparsers.add_parser("save", help="Save an alarm preset")
    parser_save.add_argument("name", help="Unique preset name (e.g. standup, tea)")
    parser_save.add_argument("time", help="Preset time ('09:30', '15m')")
    parser_save.add_argument("-m", "--message", default="Alarm!", help="Preset message")
    parser_save.add_argument("-p", "--pattern", choices=list(BUILTIN_PATTERNS.keys()), default="chime", help="Sound pattern")
    parser_save.add_argument("--snooze", type=int, default=5, help="Snooze minutes")
    parser_save.add_argument("--pre-alert", default=None, help="Pre-alert duration")

    # Subcommand: run
    parser_run = subparsers.add_parser("run", help="Run a saved preset")
    parser_run.add_argument("name", help="Name of preset to run")

    # Subcommand: list
    subparsers.add_parser("list", help="List all saved presets")

    # Subcommand: delete
    parser_del = subparsers.add_parser("delete", help="Delete a saved preset")
    parser_del.add_argument("name", help="Name of preset to delete")

    return parser


def run_sound_diagnostic(pattern: Optional[str] = None) -> int:
    """Run an audio system diagnostic and playback test."""
    player = SoundPlayer()
    selected_pattern = pattern or "chime"

    print("==================================================")
    print("           Audio Diagnostic & Preview             ")
    print("==================================================")
    print(f"• Operating System   : {player.os_type}")
    print(f"• Winsound Active    : {player._has_winsound}")
    print(f"• Selected Pattern   : {selected_pattern}")
    print(f"• Available Patterns : {', '.join(BUILTIN_PATTERNS.keys())}")
    print("--------------------------------------------------")
    print("Playing test audio burst... ", end="", flush=True)

    try:
        player.play_pattern_cycle(selected_pattern)
        print("DONE (Audio played successfully)")
        print("==================================================")
        return 0
    except Exception as err:
        print(f"FAILED\n[Error] {err}")
        print("==================================================")
        return 1
