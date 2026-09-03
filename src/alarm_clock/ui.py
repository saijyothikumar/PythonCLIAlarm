"""
Terminal UI & Presentation Module.

Provides:
- In-place dynamic countdown line renderer using `\\r` and ANSI styling
- Terminal cursor show/hide management
- Colorized status banners for active, heads-up, ringing, and snooze states
- Cross-platform ANSI escape sequence support (Windows 10+ Virtual Terminal Processing)
"""

from datetime import datetime
import os
import sys


# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
WHITE_ON_RED = "\033[41;37;1m"
CLEAR_LINE = "\033[2K\r"


def init_terminal() -> None:
    """Enable ANSI virtual terminal processing and ensure UTF-8 output on Windows."""
    if os.name == "nt":
        os.system("")  # Activates VT100 processing in Windows 10/11 CMD / PowerShell
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def hide_cursor() -> None:
    """Hide the terminal cursor for a clean countdown look."""
    try:
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
    except Exception:
        pass


def show_cursor() -> None:
    """Restore the terminal cursor."""
    try:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
    except Exception:
        pass


def format_duration(seconds: float) -> str:
    """Format total seconds into HH:MM:SS string."""
    total_secs = max(0, int(seconds))
    mins, secs = divmod(total_secs, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d}"


class TerminalUI:
    """Handles all terminal formatting and dynamic line updates."""

    def __init__(self):
        init_terminal()

    def print_header(self, message: str, target_time: datetime, desc: str, sound_name: str, snooze_min: int) -> None:
        """Display the initial configuration banner when the alarm is set."""
        print()
        print(f"{BOLD}{CYAN}============================================================{RESET}")
        print(f"{BOLD}{CYAN}                 ⏰ ALARM CLOCK ACTIVE                      {RESET}")
        print(f"{BOLD}{CYAN}============================================================{RESET}")
        print(f"  {BOLD}Label        :{RESET} {GREEN}{message}{RESET}")
        print(f"  {BOLD}Target Time  :{RESET} {YELLOW}{target_time.strftime('%I:%M:%S %p')} ({desc}){RESET}")
        print(f"  {BOLD}Sound Profile:{RESET} {sound_name}")
        print(f"  {BOLD}Snooze Time  :{RESET} {snooze_min} minutes")
        print(f"  {DIM}Controls     : Press Ctrl+C to cancel anytime{RESET}")
        print(f"{BOLD}{CYAN}------------------------------------------------------------{RESET}")
        print()

    def update_countdown(self, remaining_seconds: float, target_time: datetime, message: str, is_pre_alert: bool = False) -> None:
        """Render in-place countdown line."""
        time_str = format_duration(remaining_seconds)
        color = YELLOW if is_pre_alert else GREEN
        icon = "⚠️ " if is_pre_alert else "⏳"
        
        target_display = target_time.strftime("%I:%M:%S %p")
        status_text = (
            f"{CLEAR_LINE}{color}[{icon} {BOLD}{time_str}{RESET}{color} remaining]{RESET}  "
            f"{DIM}Target: {target_display}{RESET}  •  {BOLD}{message}{RESET}"
        )
        sys.stdout.write(status_text)
        sys.stdout.flush()

    def show_pre_alert_banner(self, message: str, remaining_seconds: float) -> None:
        """Emit a visual heads-up banner above the countdown."""
        sys.stdout.write(CLEAR_LINE)
        print(f"\n{BOLD}{YELLOW}🔔 [HEADS-UP]{RESET} {BOLD}{message}{RESET} in {format_duration(remaining_seconds)}! Wrap up your tasks.")
        print()

    def show_ringing_banner(self, message: str, missed_by: float = 0.0) -> None:
        """Display ringing alarm banner."""
        show_cursor()
        sys.stdout.write(CLEAR_LINE)
        print()
        if missed_by > 5.0:
            print(f"{WHITE_ON_RED}                                                            {RESET}")
            print(f"{WHITE_ON_RED}   ⚠️  MISSED ALARM! (System slept past scheduled time)     {RESET}")
            print(f"{WHITE_ON_RED}   Scheduled: {message} (Missed by {format_duration(missed_by)})               {RESET}")
            print(f"{WHITE_ON_RED}                                                            {RESET}")
        else:
            print(f"{WHITE_ON_RED}                                                            {RESET}")
            print(f"{WHITE_ON_RED}   ⏰  ALARM RINGING: {message.upper()}                     {RESET}")
            print(f"{WHITE_ON_RED}                                                            {RESET}")
        print()
        print(f"  {BOLD}[s]{RESET} Snooze   |   {BOLD}[d / Enter]{RESET} Dismiss   |   {BOLD}[q]{RESET} Quit")
        print()

    def print_dismissed(self, message: str) -> None:
        """Print dismissal summary."""
        show_cursor()
        print(f"\n{GREEN}✓ Alarm '{message}' dismissed. Have a great day!{RESET}\n")

    def print_snoozed(self, message: str, new_target: datetime) -> None:
        """Print snooze confirmation."""
        print(f"\n{YELLOW}💤 Snoozed '{message}'. Next alarm at {new_target.strftime('%I:%M:%S %p')}.{RESET}\n")

    def print_cancelled(self) -> None:
        """Print cancellation on Ctrl+C."""
        show_cursor()
        print(f"\n{DIM}[Alarm cancelled. Goodbye!]{RESET}\n")
