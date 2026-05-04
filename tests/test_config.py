import os
import unittest
from unittest.mock import patch

from app.config import Config, int_env
from app.errors import ShellMindError


class ConfigTests(unittest.TestCase):
    def test_int_env_uses_default_for_missing_value(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(int_env("MAX_TOOL_ROUNDS", 4, minimum=1), 4)

    def test_int_env_clamps_to_minimum(self):
        with patch.dict(os.environ, {"MAX_TOOL_ROUNDS": "0"}, clear=True):
            self.assertEqual(int_env("MAX_TOOL_ROUNDS", 4, minimum=1), 1)

    def test_from_env_requires_api_key(self):
        with patch.dict(os.environ, {"MODEL": "gemini-test"}, clear=True):
            with self.assertRaises(ShellMindError):
                Config.from_env()

    def test_from_env_requires_model(self):
        with patch.dict(os.environ, {"API_KEY": "abc"}, clear=True):
            with self.assertRaises(ShellMindError):
                Config.from_env()

    def test_from_env_reads_expected_values(self):
        env = {
            "API_KEY": "abc",
            "MODEL": "gemini-test",
            "MAX_HISTORY_MESSAGES": "8",
            "MAX_HISTORY_CHARS": "5000",
            "MAX_TOOL_ROUNDS": "3",
            "MAX_TOOL_OUTPUT_CHARS": "900",
            "MAX_OUTPUT_TOKENS": "256",
        }
        with patch.dict(os.environ, env, clear=True):
            config = Config.from_env()

        self.assertEqual(config.api_key, "abc")
        self.assertEqual(config.model, "gemini-test")
        self.assertEqual(config.max_history_messages, 8)
        self.assertEqual(config.max_history_chars, 5000)
        self.assertEqual(config.max_tool_rounds, 3)
        self.assertEqual(config.max_tool_output_chars, 900)
        self.assertEqual(config.max_output_tokens, 256)
        self.assertIn("[SM]>", config.prompt)
