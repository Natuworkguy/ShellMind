import unittest

from google.genai import types

from app.messages import (
    message,
    response_content,
    response_parts,
    tool_response_part,
    trim_history,
    trim_tool_output,
)
from tests.helpers import (
    blank_response,
    function_call_response,
    text_response,
)


class MessageTests(unittest.TestCase):
    def test_message_wraps_text(self):
        self.assertEqual(
            message("user", "hello"),
            {"role": "user", "parts": [{"text": "hello"}]}
        )

    def test_trim_history_limits_message_count(self):
        messages = [
            message("user", "1"),
            message("user", "2"),
            message("user", "3"),
        ]
        trim_history(messages, max_messages=2, max_chars=100)
        self.assertEqual(
            [entry["parts"][0]["text"] for entry in messages],
            ["2", "3"]
        )

    def test_trim_history_limits_character_budget(self):
        messages = [
            message("user", "abc"),
            message("user", "def"),
            message("user", "ghi"),
        ]
        trim_history(messages, max_messages=5, max_chars=6)
        self.assertEqual(
            [entry["parts"][0]["text"] for entry in messages],
            ["def", "ghi"]
        )

    def test_trim_tool_output_truncates_long_text(self):
        text = trim_tool_output("a" * 20, max_chars=10)
        self.assertIn("truncated", text)
        self.assertEqual(len(text) > 10, True)

    def test_response_parts_collects_text(self):
        final, tool_calls = response_parts(text_response("hi", " there"))
        self.assertEqual(final, "hi there")
        self.assertEqual(tool_calls, [])

    def test_response_parts_collects_tool_calls(self):
        final, tool_calls = response_parts(
            function_call_response("shell", {"command": "ls"})
        )
        self.assertEqual(final, "")
        self.assertEqual(tool_calls[0].name, "shell")
        self.assertEqual(dict(tool_calls[0].args), {"command": "ls"})

    def test_response_content_returns_first_candidate_content(self):
        content = response_content(blank_response())
        self.assertIsNotNone(content)
        self.assertEqual(content.parts, [])

    def test_tool_response_part_contains_result_payload(self):
        part = tool_response_part("shell", "ok")
        self.assertIsInstance(part, types.Part)
        self.assertEqual(part.function_response.name, "shell")
        self.assertEqual(
            dict(part.function_response.response),
            {"result": "ok"}
        )
