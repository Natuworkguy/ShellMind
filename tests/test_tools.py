import unittest
from types import SimpleNamespace

from app.tools import run_shell_command, run_tool, shell_command_args


class ToolTests(unittest.TestCase):
    def test_shell_command_args_for_windows(self):
        args = shell_command_args("ls", os_name="nt")
        self.assertEqual(args[0], "powershell")
        self.assertEqual(args[-1], "ls")

    def test_shell_command_args_for_posix(self):
        self.assertEqual(shell_command_args("ls", os_name="posix"), "ls")

    def test_run_shell_command_uses_shell_on_posix(self):
        captured = {}

        def fake_runner(args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return SimpleNamespace(stdout="ok\n", stderr="", returncode=0)

        lines = []
        result = run_shell_command(
            "ls",
            os_name="posix",
            process_runner=fake_runner,
            output=lines.append
        )

        self.assertEqual(result, "ok")
        self.assertEqual(captured["args"], "ls")
        self.assertTrue(captured["kwargs"]["shell"])
        self.assertEqual(len(lines), 1)

    def test_run_shell_command_uses_powershell_on_windows(self):
        captured = {}

        def fake_runner(args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return SimpleNamespace(stdout="ok\n", stderr="", returncode=0)

        result = run_shell_command(
            "ls",
            os_name="nt",
            process_runner=fake_runner,
            output=lambda _: None
        )

        self.assertEqual(result, "ok")
        self.assertEqual(captured["args"][0], "powershell")
        self.assertNotIn("shell", captured["kwargs"])

    def test_run_tool_returns_unknown_message(self):
        result = run_tool(("nope", {}), functions={})
        self.assertEqual(result, "Unknown tool: nope")

    def test_run_tool_calls_provided_function_map(self):
        result = run_tool(
            ("shell", {"command": "ls"}),
            functions={"shell": lambda command: f"ran {command}"}
        )
        self.assertEqual(result, "ran ls")
