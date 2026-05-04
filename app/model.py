from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types

from .config import Config
from .tools import SYSTEM_PROMPT


@dataclass
class GenAIModel:
    client: Any
    model_name: str
    max_output_tokens: int

    def generate_content(self, messages: list[Any], tools=None):
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=self.max_output_tokens,
            tools=tools,
        )

        return self.client.models.generate_content(
            model=self.model_name,
            contents=messages,
            config=config
        )


def create_model(config: Config, client_factory=genai.Client) -> GenAIModel:
    client = client_factory(api_key=config.api_key)
    return GenAIModel(
        client=client,
        model_name=config.model,
        max_output_tokens=config.max_output_tokens
    )


def configure_client(api_key: str) -> None:
    """Backward-compatible hook for callers that expect explicit client setup."""
    # The google-genai SDK uses per-client API keys in `genai.Client(...)`.
    # We keep this function so older call sites continue to work.
    return None
