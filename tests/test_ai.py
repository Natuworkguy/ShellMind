import os
import unittest
from unittest.mock import patch

from app.ai import build_session
from app.config import Config


class AITests(unittest.TestCase):
    def test_build_session_constructs_session(self):
        config = Config(
            api_key="abc",
            model="gemini-test",
            max_history_messages=6,
            max_history_chars=3000,
            max_tool_rounds=4,
            max_tool_output_chars=1200,
            max_output_tokens=512,
            prompt="[SM]> ",
        )

        with patch("app.ai.Config.from_env", return_value=config), patch(
            "app.ai.create_model", return_value=object()
        ):
            session = build_session(output=lambda _: None)

        self.assertEqual(session.config.model, "gemini-test")
        self.assertEqual(session.config.prompt, "[SM]> ")

    def test_config_reads_dotenv(self):
        env_path = ".env"
        previous = None
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                previous = f.read()

        with open(env_path, "w", encoding="utf-8") as f:
            f.write("API_KEY=from_env_file\nMODEL=from_env_model\n")

        os.environ.pop("API_KEY", None)
        os.environ.pop("MODEL", None)

        from app import config as config_module

        config_module._load_dotenv(env_path)
        cfg = config_module.Config.from_env()

        self.assertEqual(cfg.api_key, "from_env_file")
        self.assertEqual(cfg.model, "from_env_model")

        if previous is None:
            os.remove(env_path)
        else:
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(previous)


if __name__ == "__main__":
    unittest.main()
