"""
Unit tests for Alarm Presets persistence.
"""

import os
import tempfile
import unittest

from src.alarm_clock.presets import PresetManager


class TestPresetManager(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.manager = PresetManager(storage_path=self.temp_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_save_and_load_preset(self):
        self.manager.save_preset("standup", "09:30", message="Daily Standup", pattern="digital", snooze=10)
        preset = self.manager.get_preset("standup")
        
        self.assertIsNotNone(preset)
        self.assertEqual(preset["name"], "standup")
        self.assertEqual(preset["time"], "09:30")
        self.assertEqual(preset["message"], "Daily Standup")
        self.assertEqual(preset["pattern"], "digital")
        self.assertEqual(preset["snooze"], 10)

    def test_delete_preset(self):
        self.manager.save_preset("tea", "15m")
        deleted = self.manager.delete_preset("tea")
        self.assertTrue(deleted)
        self.assertIsNone(self.manager.get_preset("tea"))

    def test_list_presets(self):
        self.manager.save_preset("b_preset", "10m")
        self.manager.save_preset("a_preset", "20m")
        listed = self.manager.list_presets_formatted()
        
        self.assertEqual(len(listed), 2)
        self.assertEqual(listed[0]["name"], "a_preset")
        self.assertEqual(listed[1]["name"], "b_preset")


if __name__ == "__main__":
    unittest.main()
