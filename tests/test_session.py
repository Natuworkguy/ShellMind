import unittest
from types import SimpleNamespace

from google.genai import errors

from app.config import Config
from app.messages import message
from app.session import ShellMindSession
from tests.helpers import (
    FakeModel,
    blank_response,
    function_call_response,
    text_response,
)


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.config = Config(
            api_key="abc",
            model="gemini-test",
            max_history_messages=6,
            max_history_chars=3000,
            max_tool_rounds=4,
            max_tool_output_chars=1200,
            max_output_tokens=512,
            prompt="[SM]> ",
        )
        self.console = SimpleNamespace()

    def test_bye_returns_false(self):
        session = self.make_session(model=FakeModel([]))
        self.assertFalse(session.process_input("/bye"))

    def test_model_command_prints_model_name(self):
        output = []
        session = self.make_session(model=FakeModel([]), output=output.append)
        self.assertTrue(session.process_input("/model"))
        self.assertEqual(len(output), 1)
        self.assertIn("gemini-test", output[0])

    def test_clear_command_resets_messages(self):
        output = []
        session = self.make_session(model=FakeModel([]), output=output.append)
        session.messages = [message("user", "hello")]
        session.process_input("/clear")
        self.assertEqual(session.messages, [])
        self.assertIn("Context cleared.", output[0])

    def test_help_command_prints_help(self):
        output = []
        session = self.make_session(model=FakeModel([]), output=output.append)
        session.process_input("/help")
        self.assertIn("/shell <command>", output[0])

    def test_direct_shell_command_bypasses_model(self):
        output = []
        model = FakeModel([])
        run_tool_calls = []

        def fake_run_tool(call):
            run_tool_calls.append(call)
            return "command output"

        session = self.make_session(
            model=model,
            output=output.append,
            run_tool=fake_run_tool
        )

        session.process_input("!ls")

        self.assertEqual(model.calls, [])
        self.assertEqual(
            run_tool_calls,
            [("shell", {"command": "ls"})]
        )
        self.assertEqual(output, ["command output", ""])

    def test_text_response_is_rendered_and_saved(self):
        rendered = []
        session = self.make_session(
            model=FakeModel([text_response("Hello")]),
            render_markdown=lambda console, text: rendered.append(text),
            output=lambda _: None
        )

        session.process_input("Hi")

        self.assertEqual(rendered, ["Hello"])
        self.assertEqual(len(session.messages), 2)
        self.assertEqual(session.messages[1]["parts"][0]["text"], "Hello")

    def test_empty_response_warns_and_discards_user_message(self):
        output = []
        session = self.make_session(
            model=FakeModel([blank_response()]),
            output=output.append
        )

        session.process_input("Hi")

        self.assertEqual(session.messages, [])
        self.assertIn("The model returned no response.", output[0])

    def test_initial_overload_prints_error_and_discards_user_message(self):
        output = []
        session = self.make_session(
            model=FakeModel([errors.ServerError(429, {"message": "busy"})]),
            output=output.append
        )

        session.process_input("Hi")

        self.assertEqual(session.messages, [])
        self.assertIn("overloaded", output[0])

    def test_single_round_tool_flow_renders_followup(self):
        rendered = []
        run_tool_calls = []

        def fake_run_tool(call):
            run_tool_calls.append(call)
            return "listing"

        model = FakeModel([
            function_call_response("shell", {"command": "ls"}),
            text_response("Summary"),
        ])
        session = self.make_session(
            model=model,
            render_markdown=lambda console, text: rendered.append(text),
            run_tool=fake_run_tool,
            output=lambda _: None
        )

        session.process_input("Summarize my project")

        self.assertEqual(rendered, ["Summary"])
        self.assertEqual(
            run_tool_calls,
            [("shell", {"command": "ls"})]
        )
        self.assertIsNotNone(model.calls[0]["tools"])
        self.assertIsNotNone(model.calls[1]["tools"])
        self.assertEqual(model.calls[1]["messages"][-1].role, "tool")

    def test_multi_round_tool_flow_executes_every_call(self):
        rendered = []
        run_tool_calls = []

        def fake_run_tool(call):
            run_tool_calls.append(call)
            return "ok"

        model = FakeModel([
            function_call_response("shell", {"command": "ls"}),
            function_call_response("shell", {"command": "cat app/ai.py"}),
            text_response("Project summary"),
        ])
        session = self.make_session(
            model=model,
            render_markdown=lambda console, text: rendered.append(text),
            run_tool=fake_run_tool,
            output=lambda _: None
        )

        session.process_input("Summarize my project")

        self.assertEqual(rendered, ["Project summary"])
        self.assertEqual(
            run_tool_calls,
            [
                ("shell", {"command": "ls"}),
                ("shell", {"command": "cat app/ai.py"}),
            ]
        )

    def test_blank_tool_followup_requests_final_answer_without_tools(self):
        rendered = []
        model = FakeModel([
            function_call_response("shell", {"command": "ls"}),
            blank_response(),
            text_response("Final answer"),
        ])
        session = self.make_session(
            model=model,
            render_markdown=lambda console, text: rendered.append(text),
            run_tool=lambda call: "listing",
            output=lambda _: None
        )

        session.process_input("Summarize my project")

        self.assertEqual(rendered, ["Final answer"])
        self.assertIsNone(model.calls[2]["tools"])

    def test_tool_fallback_renders_output_when_model_stays_blank(self):
        rendered = []
        output = []
        model = FakeModel([
            function_call_response("shell", {"command": "ls"}),
            blank_response(),
            blank_response(),
        ])
        session = self.make_session(
            model=model,
            render_markdown=lambda console, text: rendered.append(text),
            run_tool=lambda call: "listing",
            output=output.append
        )

        session.process_input("Summarize my project")

        self.assertIn("Tool output:", rendered[0])
        self.assertIn("shell:\nlisting", rendered[0])
        self.assertTrue(
            any("did not provide a final response" in line for line in output)
        )

    def make_session(
        self,
        *,
        model,
        render_markdown=None,
        run_tool=None,
        output=None
    ):
        return ShellMindSession(
            config=self.config,
            model=model,
            console=self.console,
            render_markdown=render_markdown or (lambda console, text: None),
            run_tool=run_tool or (lambda call: "ok"),
            output=output or (lambda _: None),
        )
