"""
Preset Storage & Management Module.

Allows users to:
- Save reusable alarm configurations (e.g., 'standup', 'pomodoro')
- List saved presets in a clean table format
- Run presets by name
- Delete presets
"""

import json
import os
from typing import Dict, List, Optional


DEFAULT_PRESETS_FILE = os.path.join(os.path.expanduser("~"), ".alarm_cli", "presets.json")


def _get_storage_path(custom_path: Optional[str] = None) -> str:
    path = custom_path or DEFAULT_PRESETS_FILE
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError:
            # Fallback to current directory
            return os.path.abspath("alarms.json")
    return path


class PresetManager:
    """Manages persistence and retrieval of alarm presets."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = _get_storage_path(storage_path)

    def load_presets(self) -> Dict[str, dict]:
        """Load all presets from JSON file."""
        if not os.path.exists(self.storage_path):
            return {}
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_preset(
        self,
        name: str,
        time_str: str,
        message: str = "Alarm!",
        pattern: str = "chime",
        snooze: int = 5,
        pre_alert: Optional[str] = None,
    ) -> None:
        """Save or update an alarm preset."""
        presets = self.load_presets()
        presets[name.lower()] = {
            "name": name.lower(),
            "time": time_str,
            "message": message,
            "pattern": pattern,
            "snooze": snooze,
            "pre_alert": pre_alert,
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2)

    def get_preset(self, name: str) -> Optional[dict]:
        """Retrieve a specific preset by name."""
        presets = self.load_presets()
        return presets.get(name.lower())

    def delete_preset(self, name: str) -> bool:
        """Delete a preset by name. Returns True if deleted, False if not found."""
        presets = self.load_presets()
        if name.lower() in presets:
            del presets[name.lower()]
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(presets, f, indent=2)
            return True
        return False

    def list_presets_formatted(self) -> List[dict]:
        """Return list of preset dictionaries sorted by name."""
        presets = self.load_presets()
        return [presets[k] for k in sorted(presets.keys())]
