# Engineering Guidelines & Agent Rules

**Project:** Python CLI Alarm Clock  
**Standard:** Senior Software Engineer Clean Code & Best Practices  

---

## 1. Core Principles

1. **Zero External Dependencies:**
   - The application must strictly use the Python standard library (`datetime`, `time`, `threading`, `argparse`, `json`, `subprocess`, `platform`, `sys`, `os`, `winsound` where applicable).
   - Any evaluator cloning the repository must be able to run it immediately without `pip install` or wheel compilation.

2. **Decoupled Architecture:**
   - Logic must be cleanly separated:
     - `parser.py`: Pure parsing functions with zero I/O side-effects.
     - `sound.py`: Sound driver abstraction isolated from UI and scheduling.
     - `engine.py`: Clock and state machine logic decoupled from presentation.
     - `ui.py`: Terminal formatting, ANSI colors, and cursor management.
     - `presets.py`: Persistence and storage management.
     - `wizard.py`: Interactive user input collection.

3. **Incremental Test-Driven Progression:**
   - Commit code in clear, logical phases corresponding to the roadmap.
   - Do not dump the entire codebase in one commit. Each commit must represent a working, testable enhancement or fix.
   - Run validation tests before moving to the next phase.

4. **Terminal Hygiene & Ergonomics:**
   - Always restore the terminal cursor (`\033[?25h`) on exit, cancellation, or error.
   - Intercept `SIGINT` (`Ctrl+C`) cleanly—never expose raw Python `KeyboardInterrupt` tracebacks to the user.
   - Use in-place updates (`\r`) rather than spamming lines during countdown.

5. **Code Quality & Typing:**
   - Use Python type hints (`from typing import Optional, Dict, Tuple, List, Callable`).
   - Write clear docstrings for public classes and functions.
   - Keep functions focused and single-purpose (SRP).
