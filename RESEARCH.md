# Technical Research & Feasibility Analysis

**Project:** Python CLI Alarm Clock  
**Author:** Sai Surla
**Date:** September 2026  

---

## 1. Executive Summary & Objective

The goal is to design and build a resilient, intuitive, and feature-rich Command Line Interface (CLI) alarm clock in Python. The challenge is balancing **instant simplicity** (setting a 10-minute timer in 2 seconds) with **rich customization** (recurring alarms, sound profiles, pre-alarm heads-up notifications, and presets), while navigating OS-level realities like power states, terminal rendering, and audio hardware without bloated dependencies.

---

## 2. Technical Feasibility & Scenario Analysis

We evaluated the user scenarios, edge cases, and OS constraints:

### Scenario A: Quick Alarm vs. Fully Customized Alarm
* **Feasibility:** **100% Feasible & Recommended.**
* **Architectural Approach: Dual-Mode UX**
  1. **Direct CLI / Quick Mode:** If arguments are provided (e.g. `alarm 10m` or `alarm 07:30`), it bypasses all menus and immediately starts the countdown using smart defaults (5m snooze, default chime, auto-calculated next-day rollover).
  2. **Interactive Wizard Mode:** If run with `alarm --interactive` (or with no arguments), it launches an interactive terminal wizard prompting for:
     - Target time or duration
     - Custom label / message
     - Sound pattern (Chime, Digital, Pulse, Custom WAV)
     - Pre-alarm heads-up (e.g. alert 2 mins before)
     - Snooze duration
* **Senior Decision:** Enables a 1-second quick command for developers while supporting deep configuration when desired.

---

### Scenario B: Laptop Sleep Mode, Wake Timers & Lock Screen
* **Question 1: Can the alarm ring when the laptop is asleep?**
  - *Technical Reality:* When an OS enters S3 Sleep or Modern Standby, CPU execution is suspended. Standard user-space Python threads stop executing.
  - *OS Capabilities:*
    - **Windows:** Supports `SetWaitableTimer` with `fResume = True` or Windows Task Scheduler with "Wake the computer to run this task".
    - **macOS:** Supports `pmset schedule wake` or `launchd`.
    - **Linux:** Supports `rtcwake` via `/sys/class/rtc/rtc0/wakealarm`.
  - *Trade-off & Recommendation:* Implementing low-level ACPI wake timers directly in a cross-platform Python CLI requires root/admin privileges and OS-specific C-bindings.
  - *Pragmatic Senior Solution:* Provide **Sleep Detection & Catch-up Handling**:
    - Continuously measure wall-clock delta `(target_time - datetime.now())`.
    - If the system was suspended and wakes up *past* the alarm time, detect that the delta is negative.
    - Trigger an immediate alert: `[MISSED ALARM] 'Morning Standup' was scheduled for 08:00:00 AM (System woke up at 08:15:22 AM)`.
    - Provide a `--no-catchup` flag if the user prefers stale alarms to be silently discarded.

* **Question 2: Can the user dismiss the alarm from the lock screen without logging in?**
  - *Technical Reality:* Modern OS security architectures (Windows Secure Desktop / Winlogon, macOS WindowServer) isolate the lock screen. Unauthenticated processes cannot receive keyboard/mouse input from the lock screen for security reasons.
  - *Pragmatic Senior Solution:* When the alarm fires, it rings continuously for a configurable timeout (e.g. 60 seconds) with repeat bursts, then enters an auto-snooze state or silence to prevent draining the battery, until the user unlocks the terminal and presses `[d]` to dismiss.

---

### Scenario C: Sound Library & Custom Sounds
* **Feasibility:** **100% Feasible.**
* **Architectural Approach:**
  1. **Built-in Synthetic Sound Library (Zero External Dependencies):**
     - Pattern 1: `chime` (gentle ascending frequency bursts)
     - Pattern 2: `digital` (rapid classic digital clock beeps)
     - Pattern 3: `pulse` (rhythmic alert beeps)
     - Pattern 4: `bell` (ASCII terminal bell `\a` fallback)
  2. **Custom Audio File Playback:**
     - Support `--sound path/to/custom.wav`.
     - Platform-native audio dispatch:
       - Windows: `winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)`
       - macOS: subprocess `afplay <path>`
       - Linux: subprocess `aplay` or `paplay <path>`
  3. **Sound Preview Mode:**
     - Flag `--test-sound` or `--preview <sound_name>` to verify speaker volume beforehand.

---

### Scenario D: Pre-Alarm Notification ("Heads-up" / Gentle Wake)
* **Feasibility:** **100% Feasible & High ROI.**
* **Description:** A subtle chime or visual banner 2–5 minutes before the main alarm (e.g. "Meeting starts in 2 minutes, wrap up your thought").
* **Implementation:**
  - Introduce an intermediate trigger threshold: `pre_alert_time = target_time - timedelta(minutes=N)`.
  - When `now >= pre_alert_time`, emit a gentle single beep and display a yellow status banner: `[HEADS-UP] Alarm 'Sprint Review' in 2 minutes`.
  - Continue counting down smoothly to the primary alarm.

---

### Scenario E: Multiple Alarms & Presets / Saved Alarms
* **Feasibility:** **100% Feasible.**
* **Architectural Approach:**
  - **Preset Storage:** Lightweight JSON file stored in user configuration directory (e.g., `~/.alarm_cli/presets.json` or local `alarms.json`).
  - **Preset Commands:**
    - `alarm save standup 09:30 -m "Team Standup" --sound chime`
    - `alarm run standup`
    - `alarm list`
    - `alarm delete standup`
  - **Multi-Alarm Execution:**
    - Foreground mode runs a single active countdown with live terminal UI.
    - Background / Daemon mode or Multi-Alarm schedule evaluates the earliest upcoming alarm from the preset queue.

---

## 3. Engineering Decisions & Trade-Off Matrix

| Feature | Complexity | Value / UX Impact | Verdict for 30-Min Scope | Strategy |
| :--- | :---: | :---: | :---: | :--- |
| **Dual-Mode (Quick CLI + Interactive)** | Medium | **Very High** | **Include** | Support positional time (`15m`, `7am`) + optional interactive prompt if no args. |
| **Drift-Free Scheduling** | Low | **Critical** | **Include** | Absolute wall-clock delta calculation (`target - now`). |
| **Zero-Dependency Audio Engine** | Medium | **Critical** | **Include** | Native OS sound dispatch (`winsound`, `afplay`, `aplay`, `\a`). |
| **Non-blocking Snooze / Dismiss** | Medium | **High** | **Include** | Alert loop in background daemon thread; main thread captures keypresses. |
| **Pre-Alarm Heads-up** | Low | **High** | **Include** | Intermediate threshold trigger with soft chime & banner. |
| **Saved Presets (`alarms.json`)** | Low | **High** | **Include** | JSON persistence for named alarms (`save`, `list`, `run`). |
| **ACPI Wake Timers (Hardware Wake)** | Very High | Low (Fragile) | **Defer & Document** | Requires OS root/admin & C-bindings; handle via sleep detection & catch-up instead. |
| **Lock Screen Key Interception** | Impossible | N/A (OS Security) | **Document** | Blocked by OS security kernel; handle via auto-timeout and unlock prompt. |

---

## 4. Key Takeaway

By choosing a modular, zero-dependency architecture with dual-mode interaction (Quick vs. Customized), we maximize flexibility and UX while guaranteeing that anyone cloning the repository can run it immediately without `pip install` failures.
