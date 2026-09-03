"""
Interactive Setup Wizard Module.

Provides a robust, validated, and user-friendly terminal questionnaire
when the user runs the CLI without arguments or with `--interactive`.
"""

from datetime import datetime
import sys
from typing import Dict, List, Optional, Tuple

from src.alarm_clock.cli import run_sound_diagnostic
from src.alarm_clock.engine import AlarmConfig
from src.alarm_clock.parser import parse_alarm_target, parse_duration, TimeParseError
from src.alarm_clock.presets import PresetManager
from src.alarm_clock.sound import BUILTIN_PATTERNS
from src.alarm_clock.ui import BOLD, CYAN, DIM, GREEN, RED, RESET, YELLOW, init_terminal

PATTERN_INDEX: Dict[str, str] = {
    "1": "chime",
    "2": "digital",
    "3": "pulse",
    "4": "bell",
}


def prompt_user(prompt_text: str, default: Optional[str] = None) -> str:
    """Prompt user for input with optional default value."""
    if default:
        display = f"{prompt_text} [{default}]: "
    else:
        display = f"{prompt_text}: "
    
    try:
        val = input(display).strip()
    except (KeyboardInterrupt, EOFError):
        print(f"\n{DIM}[Setup cancelled]{RESET}")
        sys.exit(130)

    return val if val else (default or "")


def _select_sound_pattern() -> str:
    """Prompt and strictly validate sound pattern selection."""
    print(f"\n{BOLD}Sound Pattern Options:{RESET}")
    print("  [1] chime   (gentle musical ascending tones)")
    print("  [2] digital (classic digital alarm clock beeps)")
    print("  [3] pulse   (high-urgency pulsating alert)")
    print("  [4] bell    (universal ASCII terminal bell)")

    while True:
        choice = prompt_user("Select Sound Pattern (1-4 or name)", default="1").lower()
        if choice in PATTERN_INDEX:
            return PATTERN_INDEX[choice]
        if choice in BUILTIN_PATTERNS:
            return choice

        valid_names = ", ".join(list(BUILTIN_PATTERNS.keys()))
        print(f"{RED}Error:{RESET} Unknown sound pattern '{choice}'. Please choose 1-4 or one of: {valid_names}.\n")


def _prompt_pre_alert(target_time: datetime) -> Optional[int]:
    """Prompt and strictly validate pre-alarm duration."""
    total_seconds = (target_time - datetime.now()).total_seconds()

    while True:
        pre_input = prompt_user(
            "Pre-alarm heads-up duration (e.g. '2m', '30s', or press Enter to disable)",
            default=""
        )
        if not pre_input:
            return None

        try:
            delta = parse_duration(pre_input)
            pre_secs = int(delta.total_seconds())

            if pre_secs <= 0:
                print(f"{RED}Error:{RESET} Pre-alarm duration must be greater than zero seconds.\n")
                continue

            if pre_secs >= total_seconds:
                mins_left = max(1, int(total_seconds // 60))
                print(
                    f"{RED}Error:{RESET} Pre-alert duration ({pre_input}) must be shorter than total alarm time "
                    f"({int(total_seconds)}s remaining / ~{mins_left}m). Please enter a shorter duration or press Enter to skip.\n"
                )
                continue

            return pre_secs
        except TimeParseError as err:
            print(f"{RED}Error:{RESET} {err}\nPlease enter a valid duration like '2m', '30s', or press Enter to skip.\n")


def _prompt_snooze() -> int:
    """Prompt and strictly validate snooze duration."""
    while True:
        snooze_input = prompt_user("Snooze duration in minutes", default="5")
        try:
            val = int(snooze_input)
            if val <= 0:
                print(f"{RED}Error:{RESET} Snooze duration must be a positive integer greater than 0 (e.g. 5, 10).\n")
                continue
            return val
        except ValueError:
            print(f"{RED}Error:{RESET} Invalid number '{snooze_input}'. Please enter a positive integer.\n")


def run_interactive_wizard() -> Optional[Tuple[AlarmConfig, str]]:
    """
    Run interactive setup wizard with strict validation loops.
    
    Returns:
        Optional[Tuple[AlarmConfig, str]]: (AlarmConfig, description) or None if exited.
    """
    init_terminal()

    while True:
        print()
        print(f"{BOLD}{CYAN}============================================================{RESET}")
        print(f"{BOLD}{CYAN}              ⏰ Interactive Alarm Setup Wizard              {RESET}")
        print(f"{BOLD}{CYAN}============================================================{RESET}")
        print("  [1] Set Quick Timer (e.g., 10m, 25m Pomodoro, 45s)")
        print("  [2] Set Clock Alarm (e.g., 7:30am, 14:45, noon)")
        print("  [3] Run a Saved Preset")
        print("  [4] Sound Preview & Audio Diagnostics")
        print("  [5] Exit")
        print(f"{BOLD}{CYAN}------------------------------------------------------------{RESET}")

        choice = prompt_user("Select an option (1-5)", default="1")

        if choice not in ("1", "2", "3", "4", "5"):
            print(f"\n{RED}Error:{RESET} Invalid choice '{choice}'. Please enter a number between 1 and 5.")
            continue

        if choice == "5":
            print(f"\n{DIM}[Setup exited. Goodbye!]{RESET}\n")
            return None

        if choice == "4":
            while True:
                pattern = _select_sound_pattern()
                run_sound_diagnostic(pattern)
                again = prompt_user("Test another sound? (y/n)", default="n").lower()
                if again != "y":
                    break
            continue

        if choice == "3":
            manager = PresetManager()
            presets = manager.list_presets_formatted()
            if not presets:
                print(f"\n{YELLOW}Notice:{RESET} No presets saved yet. Create one via: {BOLD}alarm save <name> <time>{RESET}")
                continue

            print(f"\n{BOLD}Saved Presets:{RESET}")
            for idx, p in enumerate(presets, 1):
                pre_info = f", Pre-alert: {p['pre_alert']}" if p.get("pre_alert") else ""
                print(f"  [{idx}] {BOLD}{p['name']}{RESET}: {p['time']} (Label: '{p['message']}', Sound: {p['pattern']}{pre_info})")
            print(f"  [b] Back to main menu")

            while True:
                sel = prompt_user(f"Choose preset (1-{len(presets)} or 'b')", default="1")
                if sel.lower() == "b":
                    break
                try:
                    idx_val = int(sel)
                    if not (1 <= idx_val <= len(presets)):
                        print(f"{RED}Error:{RESET} Please choose a number between 1 and {len(presets)}.")
                        continue
                    
                    p = presets[idx_val - 1]
                    target, desc = parse_alarm_target(p["time"])
                    pre_sec = int(parse_duration(p["pre_alert"]).total_seconds()) if p.get("pre_alert") else None
                    config = AlarmConfig(
                        target_time=target,
                        message=p["message"],
                        pattern=p["pattern"],
                        snooze_minutes=p["snooze"],
                        pre_alert_seconds=pre_sec,
                    )
                    return config, desc
                except (ValueError, TimeParseError) as err:
                    print(f"{RED}Error with preset '{sel}':{RESET} {err}")
            continue

        # Option 1 (Timer) or 2 (Clock Alarm)
        break

    # Prompt for time / duration
    while True:
        default_time = "15m" if choice == "1" else "07:30am"
        time_input = prompt_user("Enter duration or alarm time", default=default_time)
        try:
            target, desc = parse_alarm_target(time_input)
            break
        except TimeParseError as err:
            print(f"\n{RED}Error:{RESET} {err}\nPlease try again.\n")

    message = prompt_user("Alarm Label / Reminder Message", default="Alarm!")

    pattern = _select_sound_pattern()
    pre_sec = _prompt_pre_alert(target)
    snooze_min = _prompt_snooze()

    config = AlarmConfig(
        target_time=target,
        message=message,
        pattern=pattern,
        snooze_minutes=snooze_min,
        pre_alert_seconds=pre_sec,
    )

    return config, desc
