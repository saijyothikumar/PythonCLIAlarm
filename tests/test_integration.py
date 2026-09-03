"""
End-to-End Integration Tests for Alarm CLI.
"""

from io import StringIO
import os
import sys
import unittest
from unittest.mock import patch

from src.alarm_clock.main import main
from src.alarm_clock.presets import PresetManager


class TestAlarmCLIIntegration(unittest.TestCase):
    def setUp(self):
        # Use isolated presets file for integration tests
        self.test_presets_path = os.path.abspath("test_presets.json")
        self.original_storage = PresetManager(self.test_presets_path)

    def tearDown(self):
        if os.path.exists(self.test_presets_path):
            os.remove(self.test_presets_path)

    @patch("src.alarm_clock.sound.SoundPlayer.emit_tone")
    def test_diagnostic_sound_run(self, mock_emit):
        mock_emit.return_value = None
        code = main(["--test-sound"])
        self.assertEqual(code, 0)

    @patch("sys.stdout", new_callable=StringIO)
    def test_invalid_time_cli(self, mock_stdout):
        code = main(["invalid_format_xyz"])
        self.assertEqual(code, 1)
        self.assertIn("Error:", mock_stdout.getvalue())

    @patch("sys.stdout", new_callable=StringIO)
    def test_invalid_sound_file_cli(self, mock_stdout):
        code = main(["10m", "--sound", "non_existent_audio_file.wav"])
        self.assertEqual(code, 1)
        self.assertIn("Audio Error:", mock_stdout.getvalue())

    def test_preset_management_cli_flow(self):
        # Save
        code_save = main(["save", "focus", "25m", "-m", "Pomodoro", "--pattern", "pulse"])
        self.assertEqual(code_save, 0)

        # List
        code_list = main(["list"])
        self.assertEqual(code_list, 0)

        # Delete
        code_del = main(["delete", "focus"])
        self.assertEqual(code_del, 0)


if __name__ == "__main__":
    unittest.main()
