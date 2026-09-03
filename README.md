# Python CLI Alarm Clock

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-25%20passed-brightgreen.svg)]()
[![Dependencies](https://img.shields.io/badge/dependencies-zero%20(stdlib%20only)-success.svg)]()
[![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey.svg)]()

A resilient, drift-free, and intuitive Command Line Interface (CLI) alarm clock built with Python's standard library. Engineered with **zero external dependencies**, cross-platform audio fallbacks, dual-mode interaction (instant quick alarms vs. interactive wizards), pre-alarm heads-up alerts, and saved alarm presets.

---

## 📑 Table of Contents

- [Key Highlights](#-key-highlights)
- [Architecture & Design](#-architecture--design)
- [Installation & Quickstart](#-installation--quickstart)
- [Usage Examples](#-usage-examples)
  - [1. Quick Alarms (Instant Mode)](#1-quick-alarms-instant-mode)
  - [2. Interactive Setup Wizard](#2-interactive-setup-wizard)
  - [3. Pre-Alarm Heads-up Warning](#3-pre-alarm-heads-up-warning)
  - [4. Custom Audio Files & Slicing](#4-custom-audio-files--slicing)
  - [5. Preset Management](#5-preset-management)
- [Audio Engine & Patterns](#-audio-engine--patterns)
- [Technical Deep Dive: Sleep Mode & OS Realities](#-technical-deep-dive-sleep-mode--os-realities)
- [Running Automated Tests](#-running-automated-tests)
- [Project Layout](#-project-layout)

---

## 🌟 Key Highlights

1. **Zero External Dependencies:** No `pip install` required. Clone and run immediately on any system with Python 3.8+.
2. **Drift-Free Timing:** Calculates absolute wall-clock target deltas `(target - now)` instead of accumulating latency with naive `time.sleep()`.
3. **Dual-Mode UX:**
   - **Quick Mode:** `python main.py 15m` starts an alarm in 1 second.
   - **Interactive Mode:** `python main.py` or `-i` provides a guided numbered terminal wizard.
4. **Interactive Ringing & Non-Blocking Audio:** Audio loops on a daemon thread while user controls (`[s]` Snooze, `[d]` Dismiss, `[q]` Quit) remain immediately responsive.
5. **Pre-Alarm Heads-Up:** Emits a gentle tone and status banner before the main alarm (e.g. `--pre-alert 2m`).
6. **Smart Rollover:** Automatically advances times that have already passed today to tomorrow morning.
7. **Custom Sound Slicing & Validation:** Supports custom `.wav` tracks with bounds-checking and duration clamping.

---

## 🏗 Architecture & Design

The application follows a clean separation of concerns:

```
┌────────────────────────────────────────────────────────┐
│                        main.py                         │
│            (CLI Entry, Signals & Routing)              │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
       ┌────────▼────────┐      ┌────────▼────────┐
       │   cli/parser    │      │  presets.py     │
       │  (Time Parsing) │      │ (JSON Storage)  │
       └────────┬────────┘      └─────────────────┘
                │
       ┌────────▼────────┐
       │   engine.py     │◄────────────┐
       │  (State Machine │             │
       │  & Drift-Free)  │             │
       └────────┬────────┘             │
                │                      │
       ┌────────▼────────┐      ┌──────┴──────────┐
       │  controller.py  │──────►   sound.py      │
       │ (Threading & UI)│      │ (Winsound/Bell) │
       └────────┬────────┘      └─────────────────┘
                │
       ┌────────▼────────┐
       │      ui.py      │
       │ (In-Place \r)   │
       └─────────────────┘
```

### State Machine Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Scheduled: Parse target time
    Scheduled --> PreAlert: Remaining <= Pre-Alert Threshold
    PreAlert --> Ringing: Target time reached
    Scheduled --> Ringing: Target time reached
    Scheduled --> Missed: System was asleep past target
    
    state Ringing {
        [*] --> AudioLoop
        AudioLoop --> AwaitInput: User prompted [s/d/q]
    }
    
    Ringing --> Scheduled: [s] Snooze (target = now + snooze_mins)
    Ringing --> Dismissed: [d / Enter] Dismiss
    Dismissed --> [*]
    Scheduled --> Cancelled: Ctrl+C (SIGINT)
    Cancelled --> [*]
```

---

## 🚀 Installation & Quickstart

Clone the repository and run directly:

```bash
git clone https://github.com/saijyothikumar/PythonCLIAlarm.git
cd PythonCLIAlarm
python main.py --help
```

To run the automated 5-second test walkthrough:

```bash
python demo.py
```

---

## 💡 Usage Examples

### 1. Quick Alarms (Instant Mode)

```bash
# 10-minute timer
python main.py 10m

# 45-second timer with custom label
python main.py 45s -m "Tea Steeped"

# Clock time (24-hour format)
python main.py 14:30 -m "Team Sync"

# Clock time (12-hour AM/PM format, auto-rolls to tomorrow if time has passed)
python main.py 7:30am -m "Wake Up"
```

### 2. Interactive Setup Wizard

Run without arguments or with `--interactive`:

```bash
python main.py
```
```text
============================================================
              ⏰ Interactive Alarm Setup Wizard              
============================================================
  1. Set Quick Timer (e.g., 10m, 25m Pomodoro, 45s)
  2. Set Clock Alarm (e.g., 7:30am, 14:45)
  3. Run a Saved Preset
  4. Sound Preview & Audio Diagnostics
  5. Exit
------------------------------------------------------------
Select an option (1-5) [1]:
```

### 3. Pre-Alarm Heads-up Warning

Receive a gentle heads-up banner and single chime 2 minutes before the main alarm rings:

```bash
python main.py 25m -m "Pomodoro" --pre-alert 2m
```

### 4. Custom Audio Files & Slicing

Use a custom audio track with duration limits and bounds checking:

```bash
python main.py 10m --sound sample.wav --sound-duration 30s
```

* **Error Handling:** If the audio file does not exist, or if the requested duration exceeds the audio length, the CLI provides clear diagnostic feedback rather than crashing.

### 5. Preset Management

Save and run frequently used alarms:

```bash
# Save a preset
python main.py save standup 09:30 -m "Team Sync" --pattern digital --snooze 5

# List all saved presets
python main.py list

# Run a preset
python main.py run standup

# Delete a preset
python main.py delete standup
```

---

## 🔊 Audio Engine & Patterns

The built-in sound engine requires **no third-party dependencies**:

| Pattern | Description | Frequency Profile |
| :--- | :--- | :--- |
| `chime` *(default)* | Musical ascending triad | 523Hz (C5) → 659Hz (E5) → 784Hz (G5) → 1046Hz (C6) |
| `digital` | Classic digital alarm clock | Double-beep burst (850Hz) |
| `pulse` | High-urgency alert | Rapid pulsating bursts (1200Hz) |
| `bell` | Universal fallback | Standard ASCII bell (`\a`) |

Test and verify your speaker output:

```bash
# Test default sound
python main.py --test-sound

# Preview specific pattern
python main.py --preview pulse
```

---

## 🔬 Technical Deep Dive: Sleep Mode & OS Realities

During our architectural research, we evaluated hardware sleep states:

1. **CPU Sleep Suspends Processes:** When a laptop enters S3 Sleep or Modern Standby, CPU execution for user-space threads is paused.
2. **ACPI Wake Timers:** Waking hardware requires OS-specific administrative privileges (`SetWaitableTimer` with resume flag on Windows, `rtcwake` on Linux).
3. **Lock-Screen Security Isolation:** Modern OSs isolate the lock screen (Windows Secure Desktop) to prevent unauthenticated keystroke interception.

### Our Solution: Sleep Detection & Auto-Silence
- **Missed Alarm Catch-up:** When the system wakes up, the scheduler detects if wall-clock time jumped past the target time, immediately firing a highlighted `[MISSED ALARM]` alert.
- **Auto-Silence Safety:** The alarm ringer will loop for a maximum safety timeout (60s) before auto-snoozing to prevent draining laptop battery while unattended.

---

## 🧪 Running Automated Tests

Run the full automated test suite (25 tests covering parser, engine, presets, and CLI integration):

```bash
python -m unittest discover tests
```

Output:
```text
Ran 25 tests in 2.885s
OK
```

---

## 📁 Project Layout

```
PythonCLIAlarm/
├── .gitignore
├── AGENT_RULES.md          # Engineering standards & guidelines
├── README.md               # Production documentation
├── REQUIREMENTS.md         # Detailed system requirements
├── RESEARCH.md             # Technical feasibility & OS sleep deep dive
├── ROADMAP.md              # 14-phase commit history and validation gates
├── demo.py                 # 5-second walkthrough demo
├── main.py                 # Root CLI entry point
├── src/
│   └── alarm_clock/
│       ├── __init__.py
│       ├── cli.py          # Argparse parser, subcommands, help
│       ├── controller.py   # Multi-threaded ringer & snooze loop
│       ├── engine.py       # Drift-free scheduler & state machine
│       ├── main.py         # Main dispatch & signal handling
│       ├── parser.py       # Human time & duration parsing
│       ├── presets.py      # JSON preset storage manager
│       ├── sound.py        # Cross-platform sound engine
│       ├── ui.py           # Terminal UI, \r ticker & ANSI formatting
│       └── wizard.py       # Interactive setup wizard
└── tests/
    ├── test_engine.py      # Scheduler & pre-alert tests
    ├── test_integration.py # End-to-end CLI integration tests
    ├── test_parser.py      # Time and duration parser tests
    └── test_presets.py     # Preset save/load tests
```

---

## 📄 License

MIT License. Designed and engineered for clean, reliable command-line productivity.
