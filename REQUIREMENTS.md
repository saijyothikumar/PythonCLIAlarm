# System Requirements & Specifications

**Project:** Python CLI Alarm Clock  
**Author:** Senior Software Engineer Candidate  
**Date:** September 2026  

---

## 1. Product Vision

A versatile, high-precision, zero-dependency Python CLI Alarm Clock that empowers power users to set quick 5-second timers while offering rich customization (sound libraries, pre-alarm notifications, presets, and interactive wizards) for complex daily workflows.

---

## 2. Functional Requirements (FR)

### FR1: Dual-Mode Operation
* **FR1.1 (Quick CLI Mode):** If positional arguments are passed (e.g. `alarm 15m`, `alarm 07:30`), execute immediately using sensible defaults (5m snooze, default sound, auto-calculated rollover).
* **FR1.2 (Interactive Wizard Mode):** If invoked with `--interactive` or with zero arguments, guide the user step-by-step through setting time, label, sound, pre-alert, and snooze.

### FR2: Human-Friendly Time Parsing
* **FR2.1 (Relative Durations):** Support `10s`, `15m`, `1h`, `1h30m`, `+45m`.
* **FR2.2 (Absolute Clock Times):** Support 24-hour (`14:30`, `07:15:30`) and 12-hour AM/PM formats (`7:30am`, `7pm`, `11:45PM`).
* **FR2.3 (Next-Day Rollover Awareness):** If the specified time has already elapsed today (e.g., current time is 4:00 PM and user inputs `8:00 AM`), automatically schedule for tomorrow morning (+24h) and display clear notification.

### FR3: Drift-Free Scheduling Engine
* **FR3.1 (Wall-Clock Synchronization):** Time tracking must use wall-clock delta `(target_time - now)` rather than cumulative `time.sleep()`.
* **FR3.2 (Sleep / Wake-up Detection):** If the host system suspends and wakes up after the target time has passed, detect the negative delta and trigger a "Missed Alarm" alert immediately.

### FR4: Audio & Alert Notification System
* **FR4.1 (Zero External Dependencies):** Must operate out-of-the-box using the Python standard library.
  - Windows: `winsound.Beep()` and `winsound.PlaySound()`
  - macOS: `afplay` subprocess
  - Linux: `aplay` / `paplay` subprocess
  - Universal fallback: ASCII Bell `\a` + ANSI visual flash
* **FR4.2 (Sound Profile Library):** Include distinct sound styles (`chime`, `digital`, `pulse`, `bell`).
* **FR4.3 (Custom Audio Files & Slicing):**
  - Allow user-specified WAV/audio file via `--sound <path>`.
  - Support sound segment slicing via `--sound-duration <seconds>` (or `--sound-start` / `--sound-end`).
  - **Audio Validation & Error Handling:**
    - File existence check with descriptive error messages.
    - WAV metadata inspection (duration, channels, framerate via `wave` standard module).
    - Bounds checking: if requested start offset exceeds file duration, report error cleanly.
    - Clamping: if requested end offset exceeds file length, warn and clamp to file duration.
* **FR4.4 (Sound Preview):** Support `--test-sound` to verify audio volume before scheduling.

### FR8: Comprehensive CLI Help & Documentation
* **FR8.1 (Rich Help Display):** Running `--help` or `-h` provides structured documentation, usage examples for quick vs. custom modes, subcommands, and flag explanations.

### FR5: Pre-Alarm Heads-up Notification
* **FR5.1 (Gentle Warning):** Allow setting a pre-alarm notification (e.g. `--pre-alert 2m`).
* **FR5.2 (Heads-up Event):** Emit a single soft chime and display a yellow terminal banner 2 minutes before the main alarm without interrupting the countdown.

### FR6: Interactive Ringing & Snooze Lifecycle
* **FR6.1 (Non-Blocking Alert):** When the alarm triggers, sound loops in a background thread while the main thread accepts keyboard commands:
  - `[s]` or `s`: Snooze for configured minutes (default: 5 min).
  - `[d]` or `Enter`: Dismiss the alarm cleanly.
  - `[q]`: Quit application.
* **FR6.2 (Auto-Silence Timeout):** Ring for a maximum of 60 seconds before entering auto-snooze to prevent battery drain if user is away.

### FR7: Preset & Alarm Management
* **FR7.1 (Preset Storage):** Persist presets in local JSON (`~/.alarm_cli/alarms.json` or `./alarms.json`).
* **FR7.2 (Management Commands):**
  - `alarm save <name> <time> [-m message] [--sound sound]`
  - `alarm list`
  - `alarm run <name>`
  - `alarm delete <name>`

---

## 3. Non-Functional Requirements (NFR)

* **NFR1 (Portability):** Pure Python 3.8+ compatibility across Windows, macOS, and Linux without compiling C-extensions or external wheels.
* **NFR2 (User Experience):** Live in-place countdown display using carriage return (`\r`) with clean formatting:
  `[00:14:22 remaining]  Target: 07:30:00 AM  • Standup`
* **NFR3 (Graceful Termination):** Trap `SIGINT` (`Ctrl+C`) to restore terminal cursor visibility and exit cleanly without raw Python tracebacks.
* **NFR4 (Testability):** Modular architecture with decoupled time parsing, clock engine, and audio dispatcher covered by automated unit tests.
