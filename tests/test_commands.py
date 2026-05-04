import unittest

from app.commands import direct_shell_command, help_text


class CommandTests(unittest.TestCase):
    def test_direct_shell_command_supports_bang_prefix(self):
        self.assertEqual(direct_shell_command("!ls"), "ls")

    def test_direct_shell_command_supports_run_prefix(self):
        self.assertEqual(direct_shell_command("/run pwd"), "pwd")

    def test_direct_shell_command_supports_shell_prefix(self):
        self.assertEqual(direct_shell_command("/shell dir"), "dir")

    def test_direct_shell_command_ignores_normal_text(self):
        self.assertIsNone(direct_shell_command("hello"))

    def test_help_text_mentions_supported_commands(self):
        text = help_text()
        self.assertIn("/help", text)
        self.assertIn("/model", text)
        self.assertIn("/clear", text)
        self.assertIn("/bye", text)
        self.assertIn("/run <command>", text)
        self.assertIn("/shell <command>", text)
