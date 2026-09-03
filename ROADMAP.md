# Phased Implementation Roadmap & Git Commit Strategy

**Project:** Python CLI Alarm Clock  
**Development Strategy:** 12–15 Incremental, Test-Driven Commits with Validation Gates  

---

## Phase Breakdown & Commit Sequence

```mermaid
graph TD
    P1[Phase 1: Research & Specifications] --> P2[Phase 2: Project Architecture & Time Parser]
    P2 --> P3[Phase 3: Comprehensive Parser Test Suite]
    P3 --> P4[Phase 4: Cross-Platform Sound Engine]
    P4 --> P5[Phase 5: Sound Profiles & Test-Sound CLI]
    P5 --> P6[Phase 6: Drift-Free Core Clock & Sleep Detection]
    P6 --> P7[Phase 7: Live Dynamic Terminal Countdown UI]
    P7 --> P8[Phase 8: Multi-Threaded Ringer & Snooze Controller]
    P8 --> P9[Phase 9: Pre-Alarm Heads-up Notification]
    P9 --> P10[Phase 10: Preset Storage & Management Subcommands]
    P10 --> P11[Phase 11: Interactive Setup Wizard]
    P11 --> P12[Phase 12: Signal Handling, Defect Fixes & Edge Polish]
    P12 --> P13[Phase 13: End-to-End Test Suite & Verification]
    P13 --> P14[Phase 14: Documentation, README & Demo Walkthrough]
```

---

## Detailed Stages & Commit Plan

### Commit 1: `docs: initialize research, feasibility analysis, and system requirements`
* **Artifacts:** `RESEARCH.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `AGENT_RULES.md`
* **Scope:** Architectural feasibility, competitive review, trade-off matrix, and functional specifications.
* **Validation:** Peer review and requirement alignment.

---

### Commit 2: `feat(parser): implement robust human-time and duration parsing`
* **Artifacts:** `src/alarm_clock/parser.py`
* **Scope:**
  - Parsing relative durations: `10s`, `15m`, `1h`, `1h30m`.
  - Parsing absolute 24h (`14:30`, `07:15`) and 12h formats (`7:30am`, `7pm`).
  - Next-day rollover logic (if target time has elapsed today, advance to tomorrow).
* **Validation:** Scripted parser dry-run checks.

---

### Commit 3: `test(parser): add comprehensive unit tests for time parsing and edge cases`
* **Artifacts:** `tests/test_parser.py`
* **Scope:** Unit tests covering midnight (`00:00`), midday (`12:00pm`), tomorrow rollovers, compound durations (`1h 15m 30s`), and invalid format exceptions.
* **Validation:** Run unit tests (`python -m unittest tests/test_parser.py`). All tests pass.

---

### Commit 4: `feat(sound): implement zero-dependency cross-platform sound engine`
* **Artifacts:** `src/alarm_clock/sound.py`
* **Scope:**
  - Standard-library sound abstraction: Windows (`winsound`), macOS (`afplay`), Linux (`aplay`/`paplay`), universal fallback (`\a` + ANSI visual flash).
  - Built-in sound patterns: `chime`, `digital`, `pulse`, `bell`.
  - Custom audio file playback (`.wav`).
* **Validation:** Audio loop playback test across operating system layers.

---

### Commit 5: `feat(cli): add sound preview and audio diagnostic flag`
* **Artifacts:** `src/alarm_clock/cli.py`, `src/alarm_clock/sound.py`
* **Scope:** `--test-sound` and `--preview <pattern>` CLI flags allowing users to verify speaker volume and sound patterns before scheduling alarms.
* **Validation:** Run `python -m src.alarm_clock.cli --test-sound --pattern digital`.

---

### Commit 6: `feat(engine): build drift-free clock scheduler with sleep detection`
* **Artifacts:** `src/alarm_clock/engine.py`
* **Scope:**
  - Adaptive sleep loop calculating real wall-clock delta `(target - now)`.
  - Sleep/wake-up detection: identifies system sleep gaps and alerts if an alarm was missed during suspension.
* **Validation:** Simulated clock jump test to verify immediate triggering on wake-up.

---

### Commit 7: `feat(ui): implement dynamic in-place terminal countdown ticker`
* **Artifacts:** `src/alarm_clock/ui.py`
* **Scope:**
  - Clean `\r` line rewrites with formatted countdown `[00:14:22 remaining]  Target: 07:30:00 AM  • Standup`.
  - Terminal cursor management (`\033[?25l` to hide, `\033[?25h` to restore).
  - Visual color highlights for active, pre-alert, and ringing states.
* **Validation:** Visual terminal verification of real-time seconds ticking without screen tearing.

---

### Commit 8: `feat(controller): implement multi-threaded ringer with interactive snooze and dismiss`
* **Artifacts:** `src/alarm_clock/controller.py`
* **Scope:**
  - Non-blocking audio playback on daemon thread controlled by `threading.Event`.
  - Concurrent user key prompt: `[s]` to snooze (resets target by N minutes), `[d]/[Enter]` to dismiss, `[q]` to quit.
  - Auto-silence safety timeout after 60s.
* **Validation:** Trigger mock alarm, test snooze cycle (resumes countdown) and clean dismiss.

---

### Commit 9: `feat(alert): add pre-alarm heads-up notification option`
* **Artifacts:** `src/alarm_clock/engine.py`, `src/alarm_clock/ui.py`
* **Scope:**
  - `--pre-alert <duration>` (e.g. `2m`, `30s`).
  - Triggers a soft single chime and warning banner 2 minutes before the main alarm.
* **Validation:** Schedule a 1-minute alarm with `--pre-alert 30s` and verify two-stage alerting.

---

### Commit 10: `feat(presets): add persistent alarm presets and management commands`
* **Artifacts:** `src/alarm_clock/presets.py`
* **Scope:**
  - JSON-based preset storage (`alarms.json`).
  - Subcommands: `save <name>`, `list`, `run <name>`, `delete <name>`.
* **Validation:** Save preset `tea 10m`, list presets, and trigger via `alarm run tea`.

---

### Commit 11: `feat(wizard): add interactive configuration wizard for setup without flags`
* **Artifacts:** `src/alarm_clock/wizard.py`
* **Scope:**
  - Step-by-step interactive CLI prompt when launched with no arguments or `--interactive`.
  - Allows selecting quick timer, setting alarm, browsing presets, or customizing sounds.
* **Validation:** Run without arguments and walk through interactive setup prompts.

---

### Commit 12: `fix(signals): handle SIGINT gracefully and clean up terminal state`
* **Artifacts:** `src/alarm_clock/main.py`
* **Scope:**
  - Intercept `Ctrl+C` (`SIGINT`) to suppress Python stack trace and restore cursor.
  - Safe terminal teardown on unhandled exceptions.
  - Edge case bug fixes: negative duration handling, invalid time formats.
* **Validation:** Send `Ctrl+C` at various stages (countdown, wizard, ringing) and verify clean exit.

---

### Commit 13: `test: add end-to-end and integration test suite`
* **Artifacts:** `tests/test_engine.py`, `tests/test_presets.py`
* **Scope:** Automated test coverage for scheduler states, preset save/load cycles, and CLI option parsing.
* **Validation:** Run full test suite: `python -m unittest discover tests`.

---

### Commit 14: `docs: add comprehensive README with architecture, quickstart, and demo script`
* **Artifacts:** `README.md`, `demo.py`
* **Scope:**
  - Engineering architecture diagrams.
  - CLI usage examples (Quick mode, Wizard mode, Presets, Flags).
  - Senior design decisions and rationale.
  - Self-contained demo script for fast evaluator review.
* **Validation:** Verification of all documented commands against working code.
