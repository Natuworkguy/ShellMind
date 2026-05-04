import unittest
from types import SimpleNamespace

from google.genai import types

from app.config import Config
from app.model import GenAIModel, create_model
from app.tools import tools


class ModelTests(unittest.TestCase):
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

    def test_create_model_builds_client_with_api_key(self):
        captured = {}

        def fake_client_factory(*, api_key):
            captured["api_key"] = api_key
            return SimpleNamespace(models=SimpleNamespace())

        model = create_model(self.config, client_factory=fake_client_factory)

        self.assertIsInstance(model, GenAIModel)
        self.assertEqual(captured["api_key"], "abc")

    def test_generate_content_uses_new_sdk_request_shape(self):
        captured = {}

        class FakeModels:
            def generate_content(self, *, model, contents, config):
                captured["model"] = model
                captured["contents"] = contents
                captured["config"] = config
                return "response"

        model = GenAIModel(
            client=SimpleNamespace(models=FakeModels()),
            model_name="gemini-test",
            max_output_tokens=512,
        )

        result = model.generate_content(["hello"], tools=tools)

        self.assertEqual(result, "response")
        self.assertEqual(captured["model"], "gemini-test")
        self.assertEqual(captured["contents"], ["hello"])
        self.assertIsInstance(captured["config"], types.GenerateContentConfig)
        self.assertEqual(captured["config"].max_output_tokens, 512)
        self.assertEqual(captured["config"].tools, tools)
