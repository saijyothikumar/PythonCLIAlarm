"""
Time and Duration Parser Module.

Provides robust, human-friendly parsing for:
- Relative durations (e.g., '10s', '15m', '1h30m', '+45s')
- Absolute clock times (e.g., '14:30', '7:30am', '7pm', '00:15:00')
- Next-day rollover resolution
"""

from datetime import datetime, timedelta
import re
from typing import Optional, Tuple


class TimeParseError(ValueError):
    """Raised when an input string cannot be parsed into a valid time or duration."""
    pass


# Regex patterns
_DURATION_REGEX = re.compile(
    r'^\+?\s*(?:(?P<hours>\d+)\s*(?:h|hr|hours?))?\s*'
    r'(?:(?P<minutes>\d+)\s*(?:m|min|mins|minutes?))?\s*'
    r'(?:(?P<seconds>\d+)\s*(?:s|sec|secs|seconds?))?$',
    re.IGNORECASE
)

_SHORT_DURATION_REGEX = re.compile(
    r'^\+?(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$',
    re.IGNORECASE
)

_TIME_12H_REGEX = re.compile(
    r'^(?P<hour>0?[1-9]|1[0-2])(?::(?P<minute>[0-5]\d))?(?::(?P<second>[0-5]\d))?\s*(?P<period>am|pm)$',
    re.IGNORECASE
)

_TIME_24H_REGEX = re.compile(
    r'^(?P<hour>[01]?\d|2[0-3]):(?P<minute>[0-5]\d)(?::(?P<second>[0-5]\d))?$'
)


def parse_duration(text: str) -> timedelta:
    """
    Parse a duration string into a timedelta object.
    
    Supported formats:
    - '10s', '45sec', '30 seconds'
    - '15m', '10min', '25 minutes'
    - '1h', '2hours', '1h30m', '1h 15m 30s'
    - '+10m'
    
    Raises:
        TimeParseError: If text cannot be parsed as a valid non-zero duration.
    """
    cleaned = text.strip()
    if not cleaned:
        raise TimeParseError("Duration string cannot be empty.")

    # Strip conversational prefix like "in " (e.g. "in 15m", "in 10 minutes")
    if cleaned.lower().startswith("in "):
        cleaned = cleaned[3:].strip()

    match = _DURATION_REGEX.match(cleaned) or _SHORT_DURATION_REGEX.match(cleaned)
    if not match or not any(match.groupdict().values()):
        raise TimeParseError(
            f"Invalid duration format: '{text}'. "
            "Examples of valid durations: '30s', '15m', '1h30m', '2h'."
        )

    parts = match.groupdict()
    hours = int(parts.get("hours") or 0)
    minutes = int(parts.get("minutes") or 0)
    seconds = int(parts.get("seconds") or 0)

    total_seconds = hours * 3600 + minutes * 60 + seconds
    if total_seconds <= 0:
        raise TimeParseError("Duration must be greater than zero seconds.")

    return timedelta(seconds=total_seconds)


def parse_clock_time(text: str, now: Optional[datetime] = None) -> Tuple[datetime, bool]:
    """
    Parse a 12-hour, 24-hour, or named clock time into a target datetime.
    
    If the specified time is earlier than or equal to current time, it automatically
    rolls over to tomorrow (+1 day).
    
    Args:
        text: Time string like '14:30', '7:30am', '7pm', 'noon', 'midnight'.
        now: Reference datetime (defaults to datetime.now()).
        
    Returns:
        Tuple[datetime, bool]: (target_datetime, is_tomorrow)
        
    Raises:
        TimeParseError: If the format is invalid.
    """
    cleaned = text.strip()
    if not cleaned:
        raise TimeParseError("Time string cannot be empty.")

    if now is None:
        now = datetime.now()

    # Support natural named times
    lowered = cleaned.lower()
    if lowered == "noon":
        target = now.replace(hour=12, minute=0, second=0, microsecond=0)
        is_tomorrow = target <= now
        if is_tomorrow:
            target += timedelta(days=1)
        return target, is_tomorrow
    elif lowered == "midnight":
        target = now.replace(hour=0, minute=0, second=0, microsecond=0)
        is_tomorrow = target <= now
        if is_tomorrow:
            target += timedelta(days=1)
        return target, is_tomorrow

    hour: int
    minute: int
    second: int

    # Try 12-hour AM/PM format (e.g. 7am, 7:30pm, 11:45:00 AM)
    match_12h = _TIME_12H_REGEX.match(cleaned)
    if match_12h:
        data = match_12h.groupdict()
        hour = int(data["hour"])
        minute = int(data["minute"] or 0)
        second = int(data["second"] or 0)
        period = data["period"].lower()

        if period == "pm" and hour != 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0
    else:
        # Try 24-hour format (e.g. 14:30, 09:15, 23:59:59)
        match_24h = _TIME_24H_REGEX.match(cleaned)
        if match_24h:
            data = match_24h.groupdict()
            hour = int(data["hour"])
            minute = int(data["minute"])
            second = int(data["second"] or 0)
        else:
            raise TimeParseError(
                f"Invalid time format: '{text}'. "
                "Accepted formats: '07:30', '14:45', '7:30am', '7pm', '11:45 PM'."
            )

    # Construct target time today (zeroing out microseconds for clean seconds alignment)
    target = now.replace(hour=hour, minute=minute, second=second, microsecond=0)

    # Next-day rollover check
    is_tomorrow = False
    if target <= now:
        target += timedelta(days=1)
        is_tomorrow = True

    return target, is_tomorrow


def parse_alarm_target(input_str: str, now: Optional[datetime] = None) -> Tuple[datetime, str]:
    """
    Unified entry point to parse either a duration ('15m') or clock time ('7:30am').
    
    Returns:
        Tuple[datetime, str]: (target_datetime, human_friendly_description)
    """
    if now is None:
        now = datetime.now()

    cleaned = input_str.strip()
    if not cleaned:
        raise TimeParseError("Alarm input cannot be empty.")

    # 1. Try parsing as a duration first (if it contains 's', 'm', 'h', or starts with '+')
    if any(unit in cleaned.lower() for unit in ('s', 'm', 'h')) and not any(p in cleaned.lower() for p in ('am', 'pm')):
        try:
            duration = parse_duration(cleaned)
            target = (now + duration).replace(microsecond=0)
            mins, secs = divmod(int(duration.total_seconds()), 60)
            hrs, mins = divmod(mins, 60)
            
            parts = []
            if hrs > 0:
                parts.append(f"{hrs} hour{'s' if hrs > 1 else ''}")
            if mins > 0:
                parts.append(f"{mins} minute{'s' if mins > 1 else ''}")
            if secs > 0 or not parts:
                parts.append(f"{secs} second{'s' if secs > 1 else ''}")
            
            dur_text = ", ".join(parts)
            desc = f"in {dur_text} ({target.strftime('%I:%M:%S %p')})"
            return target, desc
        except TimeParseError:
            pass  # Fall through to clock time check

    # 2. Try parsing as clock time
    try:
        target, is_tomorrow = parse_clock_time(cleaned, now=now)
        time_display = target.strftime('%I:%M:%S %p')
        if is_tomorrow:
            desc = f"tomorrow at {time_display}"
        else:
            desc = f"today at {time_display}"
        return target, desc
    except TimeParseError as err:
        raise TimeParseError(
            f"Could not parse '{input_str}' as a duration or time.\n"
            "• Durations: '30s', '10m', '1h', '1h30m', '+15m'\n"
            "• Clock times: '07:30', '14:45', '7:30am', '7pm'"
        ) from err
