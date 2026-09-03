"""
Main Application Entry Point.

Handles:
- Signal trapping (SIGINT / Ctrl+C) with terminal cursor restoration
- Subcommand routing (save, list, run, delete)
- Argument validation, audio slice checking, and dispatching
- Interactive wizard fallback
"""

import signal
import sys
from typing import List, Optional

from src.alarm_clock.cli import build_parser, parse_cli_args, run_sound_diagnostic
from src.alarm_clock.controller import AlarmController
from src.alarm_clock.engine import AlarmConfig
from src.alarm_clock.parser import parse_alarm_target, parse_duration, TimeParseError
from src.alarm_clock.presets import PresetManager
from src.alarm_clock.sound import AudioValidationError, validate_audio_slice
from src.alarm_clock.ui import BOLD, CYAN, DIM, GREEN, RED, RESET, YELLOW, init_terminal, show_cursor
from src.alarm_clock.wizard import run_interactive_wizard


def setup_signal_handlers() -> None:
    """Ensure cursor is restored and output is clean on Ctrl+C."""
    def _sigint_handler(sig, frame):
        show_cursor()
        print(f"\n{DIM}[Alarm cancelled. Goodbye!]{RESET}")
        sys.exit(130)

    signal.signal(signal.SIGINT, _sigint_handler)


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI execution entry point."""
    init_terminal()
    setup_signal_handlers()
    args = parse_cli_args(argv)

    # 1. Diagnostics
    if getattr(args, "test_sound", False):
        return run_sound_diagnostic()

    if getattr(args, "preview_pattern", None):
        return run_sound_diagnostic(args.preview_pattern)

    # 2. Preset Subcommands
    preset_manager = PresetManager()
    if getattr(args, "subcommand", None) == "save":
        try:
            # Validate time format before saving
            parse_alarm_target(args.time)
            preset_manager.save_preset(
                name=args.name,
                time_str=args.time,
                message=args.message,
                pattern=args.pattern,
                snooze=args.snooze,
                pre_alert=args.pre_alert,
            )
            print(f"\n{GREEN}✓ Preset '{args.name}' saved successfully!{RESET}")
            print(f"  Run anytime with: {BOLD}alarm run {args.name}{RESET}\n")
            return 0
        except TimeParseError as err:
            print(f"{RED}Error:{RESET} Cannot save invalid time '{args.time}': {err}")
            return 1

    elif args.subcommand == "list":
        presets = preset_manager.list_presets_formatted()
        print()
        print(f"{BOLD}{CYAN}============================================================{RESET}")
        print(f"{BOLD}{CYAN}                     SAVED ALARM PRESETS                    {RESET}")
        print(f"{BOLD}{CYAN}============================================================{RESET}")
        if not presets:
            print(f"  {DIM}No presets saved yet. Create one via:{RESET}")
            print(f"  {BOLD}alarm save standup 09:30 -m \"Daily Standup\"{RESET}\n")
            return 0

        print(f"  {BOLD}{'NAME':<12} {'TIME':<10} {'SOUND':<10} {'SNOOZE':<8} {'MESSAGE'}{RESET}")
        print(f"  {DIM}{'-'*56}{RESET}")
        for p in presets:
            print(f"  {BOLD}{p['name']:<12}{RESET} {p['time']:<10} {p['pattern']:<10} {p['snooze']}m{' ':<6} {p['message']}")
        print(f"{BOLD}{CYAN}============================================================{RESET}")
        print(f"  {DIM}To run a preset:{RESET} {BOLD}alarm run <name>{RESET}\n")
        return 0

    elif args.subcommand == "run":
        p = preset_manager.get_preset(args.name)
        if not p:
            print(f"{RED}Error:{RESET} Preset '{args.name}' not found. Use {BOLD}alarm list{RESET} to see saved presets.")
            return 1
        try:
            target, desc = parse_alarm_target(p["time"])
            pre_sec = None
            if p.get("pre_alert"):
                pre_sec = int(parse_duration(p["pre_alert"]).total_seconds())

            config = AlarmConfig(
                target_time=target,
                message=p["message"],
                pattern=p["pattern"],
                snooze_minutes=p["snooze"],
                pre_alert_seconds=pre_sec,
            )
            controller = AlarmController(config)
            controller.start(desc=desc)
            return 0
        except Exception as err:
            print(f"{RED}Error running preset '{args.name}':{RESET} {err}")
            return 1

    elif args.subcommand == "delete":
        deleted = preset_manager.delete_preset(args.name)
        if deleted:
            print(f"\n{GREEN}✓ Preset '{args.name}' deleted.{RESET}\n")
            return 0
        else:
            print(f"{RED}Error:{RESET} Preset '{args.name}' does not exist.")
            return 1

    # 3. Interactive Mode Fallback (if -i or no target given)
    if args.interactive or args.target is None:
        result = run_interactive_wizard()
        if result is None:
            return 0
        config, desc = result
        controller = AlarmController(config)
        controller.start(desc=desc)
        return 0

    # 4. Direct CLI Alarm Mode
    try:
        target, desc = parse_alarm_target(args.target)
    except TimeParseError as err:
        print(f"{RED}Error:{RESET} {err}")
        return 1

    # Pre-alert validation
    pre_alert_seconds = None
    if args.pre_alert:
        try:
            pre_alert_seconds = int(parse_duration(args.pre_alert).total_seconds())
            total_duration = (target - target.now()).total_seconds()
            if pre_alert_seconds >= total_duration:
                print(f"{YELLOW}Warning:{RESET} Pre-alert duration ({args.pre_alert}) exceeds alarm time. Heads-up will fire immediately.")
        except TimeParseError as err:
            print(f"{RED}Error:{RESET} Invalid pre-alert duration '{args.pre_alert}': {err}")
            return 1

    # Custom audio file validation & slicing
    sound_duration = None
    if args.sound_file:
        try:
            if args.sound_duration:
                sound_duration = parse_duration(args.sound_duration).total_seconds()
            # Validate slice bounds
            _, clamped_end = validate_audio_slice(args.sound_file, 0.0, sound_duration)
            sound_duration = clamped_end
        except AudioValidationError as err:
            print(f"{RED}Audio Error:{RESET} {err}")
            return 1
        except TimeParseError as err:
            print(f"{RED}Error:{RESET} Invalid sound duration '{args.sound_duration}': {err}")
            return 1

    config = AlarmConfig(
        target_time=target,
        message=args.message,
        pattern=args.pattern,
        sound_file=args.sound_file,
        sound_duration=sound_duration,
        snooze_minutes=args.snooze_minutes,
        pre_alert_seconds=pre_alert_seconds,
    )

    controller = AlarmController(config)
    controller.start(desc=desc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
