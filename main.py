#!/usr/bin/env python3
"""
Python CLI Alarm Clock - Root Entry Point.

Usage:
  python main.py 10m
  python main.py 7:30am -m "Team Sync"
  python main.py --help
"""

import sys
from src.alarm_clock.main import main

if __name__ == "__main__":
    sys.exit(main())
