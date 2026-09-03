"""
Unit tests for Interactive Wizard and Input Validation Recovery.
"""

import unittest
from unittest.mock import patch

from src.alarm_clock.wizard import run_interactive_wizard, _select_sound_pattern, _prompt_snooze


class TestWizardValidation(unittest.TestCase):

    @patch("builtins.input", side_effect=["6", "99", "5"])
    def test_wizard_rejects_out_of_range_menu_option(self, mock_input):
        """Verify that option 6 and 99 are rejected and menu recovers until 5 (exit)."""
        result = run_interactive_wizard()
        self.assertIsNone(result)

    @patch("builtins.input", side_effect=["pusle", "9", "chime"])
    def test_select_sound_pattern_rejects_typo_and_invalid_number(self, mock_input):
        """Verify that 'pusle' and '9' are rejected and prompt loops until valid."""
        pattern = _select_sound_pattern()
        self.assertEqual(pattern, "chime")

    @patch("builtins.input", side_effect=["-5", "0", "abc", "10"])
    def test_prompt_snooze_rejects_non_positive_and_non_numeric(self, mock_input):
        """Verify that -5, 0, and abc are rejected and prompt loops until positive integer."""
        snooze_min = _prompt_snooze()
        self.assertEqual(snooze_min, 10)

    @patch("builtins.input", side_effect=["1", "10m", "Test Alarm", "2", "", "5"])
    def test_full_wizard_timer_flow(self, mock_input):
        """Verify full wizard execution with valid inputs."""
        config, desc = run_interactive_wizard()
        self.assertIsNotNone(config)
        self.assertEqual(config.message, "Test Alarm")
        self.assertEqual(config.pattern, "digital")
        self.assertEqual(config.snooze_minutes, 5)
        self.assertIn("10 minutes", desc)


if __name__ == "__main__":
    unittest.main()
