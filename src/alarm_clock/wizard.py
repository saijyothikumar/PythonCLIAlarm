"""
Interactive Setup Wizard Module.

Provides an intuitive, guided terminal questionnaire when the user
runs the CLI without arguments or with `--interactive`.
"""

from datetime import datetime
import sys
from typing import Optional, Tuple

from src.alarm_clock.cli import run_sound_diagnostic
from src.alarm_clock.engine import AlarmConfig
from src.alarm_clock.parser import parse_alarm_target, parse_duration, TimeParseError
from src.alarm_clock.presets import PresetManager
from src.alarm_clock.sound import BUILTIN_PATTERNS
from src.alarm_clock.ui import BOLD, CYAN, GREEN, RESET, YELLOW, init_terminal


def prompt_user(prompt_text: str, default: Optional[str] = None) -> str:
    """Prompt user for input with optional default value."""
    if default:
        display = f"{prompt_text} [{default}]: "
    else:
        display = f"{prompt_text}: "
    
    val = input(display).strip()
    return val if val else (default or "")


def run_interactive_wizard() -> Optional[Tuple[AlarmConfig, str]]:
    """
    Run interactive setup wizard.
    
    Returns:
        Optional[Tuple[AlarmConfig, str]]: (AlarmConfig, description) or None if exited.
    """
    init_terminal()
    print()
    print(f"{BOLD}{CYAN}============================================================{RESET}")
    print(f"{BOLD}{CYAN}              ⏰ Interactive Alarm Setup Wizard              {RESET}")
    print(f"{BOLD}{CYAN}============================================================{RESET}")
    print("  1. Set Quick Timer (e.g., 10m, 25m Pomodoro, 45s)")
    print("  2. Set Clock Alarm (e.g., 7:30am, 14:45)")
    print("  3. Run a Saved Preset")
    print("  4. Sound Preview & Audio Diagnostics")
    print("  5. Exit")
    print(f"{BOLD}{CYAN}------------------------------------------------------------{RESET}")

    choice = prompt_user("Select an option (1-5)", default="1")

    if choice == "5":
        print("Goodbye!")
        return None

    if choice == "4":
        pattern = prompt_user("Choose sound to test (chime/digital/pulse/bell)", default="chime")
        run_sound_diagnostic(pattern)
        # Re-run menu
        return run_interactive_wizard()

    if choice == "3":
        manager = PresetManager()
        presets = manager.list_presets_formatted()
        if not presets:
            print("\nNo presets found! Create one first via: alarm save <name> <time>")
            return run_interactive_wizard()
        
        print("\nAvailable Presets:")
        for idx, p in enumerate(presets, 1):
            print(f"  [{idx}] {BOLD}{p['name']}{RESET}: {p['time']} (Label: '{p['message']}', Sound: {p['pattern']})")
        
        sel = prompt_user(f"Choose preset (1-{len(presets)})", default="1")
        try:
            p = presets[int(sel) - 1]
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
        except (ValueError, IndexError):
            print("Invalid preset selection.")
            return None

    # Option 1 or 2: Set timer or clock alarm
    while True:
        default_time = "15m" if choice == "1" else "07:30am"
        time_input = prompt_user("Enter duration or alarm time", default=default_time)
        try:
            target, desc = parse_alarm_target(time_input)
            break
        except TimeParseError as err:
            print(f"{YELLOW}Error:{RESET} {err}\nPlease try again.\n")

    message = prompt_user("Alarm Label / Reminder Message", default="Alarm!")

    print(f"\nSound Options: {', '.join(BUILTIN_PATTERNS.keys())}")
    pattern = prompt_user("Select Sound Pattern", default="chime")
    if pattern not in BUILTIN_PATTERNS:
        pattern = "chime"

    pre_alert_input = prompt_user("Pre-alarm heads-up duration (e.g. '2m', '30s', or blank to disable)", default="")
    pre_sec = None
    if pre_alert_input:
        try:
            pre_sec = int(parse_duration(pre_alert_input).total_seconds())
        except TimeParseError:
            print(f"{YELLOW}Invalid pre-alert duration. Disabling heads-up.{RESET}")

    snooze_input = prompt_user("Snooze duration in minutes", default="5")
    try:
        snooze_min = int(snooze_input)
    except ValueError:
        snooze_min = 5

    config = AlarmConfig(
        target_time=target,
        message=message,
        pattern=pattern,
        snooze_minutes=snooze_min,
        pre_alert_seconds=pre_sec,
    )

    return config, desc
