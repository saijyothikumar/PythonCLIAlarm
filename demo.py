#!/usr/bin/env python3
"""
Quick Demonstration Script for Reviewers.

Runs a fast 5-second demonstration alarm with:
- Custom message ('Coffee Break')
- Sound pattern ('digital')
- Pre-alert notification (at 2s remaining)
- Live countdown ticker
"""

import sys
from src.alarm_clock.main import main

if __name__ == "__main__":
    print("=" * 60)
    print("      Starting Python CLI Alarm 5-Second Demo Walkthrough   ")
    print("=" * 60)
    sys.exit(main(["5s", "-m", "Coffee Break", "-p", "digital", "--pre-alert", "2s"]))
