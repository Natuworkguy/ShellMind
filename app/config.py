import os
from dataclasses import dataclass

from colorama import Fore, Style
from dotenv import load_dotenv

from .errors import ShellMindError

load_dotenv()


def int_env(name: str, default: int, *, minimum: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return max(int(value), minimum)
    except ValueError:
        return default


@dataclass(frozen=True)
class Config:
    api_key: str
    model: str
    max_history_messages: int
    max_history_chars: int
    max_tool_rounds: int
    max_tool_output_chars: int
    max_output_tokens: int
    prompt: str

    @classmethod
    def from_env(cls) -> "Config":
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise ShellMindError("API_KEY is not set.")

        model = os.getenv("MODEL")
        if not model:
            raise ShellMindError("MODEL is not set.")

        return cls(
            api_key=api_key,
            model=model,
            max_history_messages=int_env(
                "MAX_HISTORY_MESSAGES",
                6,
                minimum=2
            ),
            max_history_chars=int_env(
                "MAX_HISTORY_CHARS",
                3000,
                minimum=1000
            ),
            max_tool_rounds=int_env(
                "MAX_TOOL_ROUNDS",
                4,
                minimum=1
            ),
            max_tool_output_chars=int_env(
                "MAX_TOOL_OUTPUT_CHARS",
                1200,
                minimum=500
            ),
            max_output_tokens=int_env(
                "MAX_OUTPUT_TOKENS",
                512,
                minimum=128
            ),
            prompt=Fore.BLUE + "[SM]> " + Style.RESET_ALL,
        )
