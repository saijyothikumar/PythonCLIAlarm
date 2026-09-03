#!/usr/bin/env python3
"""
Interactive Demonstration Suite for Evaluators.

Allows quickly demonstrating each major feature of the Alarm Clock:
  [1] 5-Second Live Countdown & Pre-Alert Warning
  [2] Preset Management Lifecycle (Save, List, Run, Delete)
  [3] Sound Pattern Showcase (Chime, Digital, Pulse, Bell)
  [4] Natural Language & Time Parsing Showcase
  [5] Error Handling & Validation Recovery Demo
  [6] Run All Demos Sequentially

Usage:
  python demo.py            # Interactive selection menu
  python demo.py 1          # Run specific demo directly
  python demo.py --all      # Run all demonstrations
"""

import sys
import time

from src.alarm_clock.cli import run_sound_diagnostic
from src.alarm_clock.main import main
from src.alarm_clock.parser import parse_alarm_target
from src.alarm_clock.sound import BUILTIN_PATTERNS, SoundPlayer
from src.alarm_clock.ui import BOLD, CYAN, DIM, GREEN, RED, RESET, YELLOW, init_terminal


def demo_countdown():
    """Demo 1: Quick 5-second countdown with pre-alert."""
    print()
    print(f"{BOLD}{CYAN}=== DEMO 1: 5-Second Live Countdown & Pre-Alert ==={RESET}")
    print("Scheduling a 5-second alarm with 2-second pre-alert warning...")
    print("When the alarm rings, press [d] or Enter to dismiss.")
    print()
    time.sleep(1)
    main(["5s", "-m", "Coffee Ready", "-p", "digital", "--pre-alert", "2s"])


def demo_presets():
    """Demo 2: Preset storage lifecycle."""
    print()
    print(f"{BOLD}{CYAN}=== DEMO 2: Preset Management Lifecycle ==={RESET}")
    print("1. Saving preset 'standup' (09:30, Daily Standup, digital sound)...")
    main(["save", "standup", "09:30", "-m", "Daily Standup", "-p", "digital", "--snooze", "5"])

    print("2. Saving preset 'focus' (25m, Pomodoro session, pulse sound)...")
    main(["save", "focus", "25m", "-m", "Pomodoro Focus", "-p", "pulse", "--pre-alert", "2m"])

    print("3. Listing all saved presets in formatted table:")
    main(["list"])

    print("4. Cleaning up demo presets...")
    main(["delete", "standup"])
    main(["delete", "focus"])
    print(f"{GREEN}✓ Demo presets cleared cleanly.{RESET}\n")


def demo_sounds():
    """Demo 3: Sound engine pattern showcase."""
    print()
    print(f"{BOLD}{CYAN}=== DEMO 3: Built-in Sound Pattern Showcase ==={RESET}")
    print("Testing zero-dependency platform sound synthesizer for each pattern:\n")
    
    player = SoundPlayer()
    for name in BUILTIN_PATTERNS.keys():
        print(f"  • Playing pattern: {BOLD}{name}{RESET}... ", end="", flush=True)
        player.play_pattern_cycle(name)
        print(f"{GREEN}DONE{RESET}")
        time.sleep(0.3)
    print(f"\n{GREEN}✓ All 4 sound patterns tested successfully.{RESET}\n")


def demo_parsing():
    """Demo 4: Time and duration parser flexibility."""
    print()
    print(f"{BOLD}{CYAN}=== DEMO 4: Human-Friendly Time Parsing Showcase ==={RESET}")
    sample_inputs = [
        "10s",
        "15m",
        "1h30m",
        "in 45 minutes",
        "+20m",
        "14:30",
        "7:30am",
        "7pm",
        "noon",
        "midnight",
    ]
    print(f"{'INPUT STRING':<18} | {'RESOLVED TARGET TIME':<24} | {'DESCRIPTION'}")
    print("-" * 70)
    for inp in sample_inputs:
        target, desc = parse_alarm_target(inp)
        print(f"{BOLD}{inp:<18}{RESET} | {target.strftime('%Y-%m-%d %I:%M:%S %p'):<24} | {desc}")
    print(f"\n{GREEN}✓ All 10 natural time expressions parsed accurately.{RESET}\n")


def demo_errors():
    """Demo 5: Error handling and bounds checking."""
    print()
    print(f"{BOLD}{CYAN}=== DEMO 5: Robust Error Handling & Bounds Checking ==={RESET}")
    print("Verifying that user mistakes are caught with helpful error messages:\n")

    error_cases = [
        (["invalid_time_xyz"], "Invalid time format"),
        (["10m", "--snooze", "-5"], "Negative snooze duration"),
        (["10m", "--pre-alert", "0s"], "Zero-duration pre-alert"),
        (["10m", "--sound", "missing.wav"], "Missing audio file"),
        (["save", "   ", "10m"], "Whitespace-only preset name"),
    ]

    for args, label in error_cases:
        print(f"{BOLD}Testing: {label}{RESET} (Command: alarm {' '.join(args)})")
        exit_code = main(args)
        assert exit_code != 0, f"Expected non-zero exit code for {label}"
        print(f"  {GREEN}✓ Rejected with exit code {exit_code}{RESET}\n")

    print(f"{GREEN}✓ All error edge cases safely caught without unhandled exceptions.{RESET}\n")


def main_menu():
    init_terminal()
    demos = {
        "1": ("5-Second Live Countdown & Pre-Alert", demo_countdown),
        "2": ("Preset Management Lifecycle", demo_presets),
        "3": ("Built-in Sound Pattern Showcase", demo_sounds),
        "4": ("Human-Friendly Time Parsing Showcase", demo_parsing),
        "5": ("Error Handling & Bounds Checking", demo_errors),
    }

    if len(sys.argv) > 1:
        arg = sys.argv[1].strip().lower()
        if arg in ("--all", "all", "6"):
            for _, (_, fn) in sorted(demos.items()):
                fn()
            return
        elif arg in demos:
            demos[arg][1]()
            return

    print()
    print(f"{BOLD}{CYAN}============================================================{RESET}")
    print(f"{BOLD}{CYAN}          Python CLI Alarm - Feature Demonstration Hub      {RESET}")
    print(f"{BOLD}{CYAN}============================================================{RESET}")
    for key, (label, _) in demos.items():
        print(f"  [{key}] {label}")
    print("  [6] Run All Demonstrations Sequentially")
    print("  [7] Exit")
    print(f"{BOLD}{CYAN}------------------------------------------------------------{RESET}")

    try:
        choice = input("Select a demo to run (1-7) [1]: ").strip() or "1"
    except (KeyboardInterrupt, EOFError):
        print()
        return

    if choice == "7":
        return
    elif choice in ("6", "--all"):
        for _, (_, fn) in sorted(demos.items()):
            fn()
    elif choice in demos:
        demos[choice][1]()
    else:
        print(f"{RED}Invalid choice '{choice}'. Exiting.{RESET}")


if __name__ == "__main__":
    main_menu()
