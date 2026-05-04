from .tools import tools, SYSTEM_PROMPT, run_tool

import os
import sys

from colorama import Fore, Style
from dotenv import load_dotenv
from google import generativeai as genai
from google.api_core.exceptions import ResourceExhausted \
    as ResourceExhaustedError
from pyfiglet import Figlet
from rich.console import Console
from rich.markdown import Markdown

load_dotenv()


class ShellMindError(Exception):
    pass


def _int_env(name: str, default: int, *, minimum: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return max(int(value), minimum)
    except ValueError:
        return default


class config:
    api_key = os.getenv("API_KEY")
    model = os.getenv("MODEL")
    max_history_messages = _int_env("MAX_HISTORY_MESSAGES", 12, minimum=2)
    max_tool_output_chars = _int_env("MAX_TOOL_OUTPUT_CHARS", 4000, minimum=500)
    max_output_tokens = _int_env("MAX_OUTPUT_TOKENS", 1024, minimum=128)
    prompt = Fore.BLUE + "[SM]> " + Style.RESET_ALL


def banner(c: Console) -> None:
    f = Figlet(font="slant")
    c.print(f.renderText("ShellMind CLI"), style="bold cyan")


def _message(role: str, text: str) -> dict:
    return {"role": role, "parts": [{"text": text}]}


def _trim_history(messages: list[dict]) -> None:
    if len(messages) > config.max_history_messages:
        del messages[:-config.max_history_messages]


def _trim_tool_output(text: str) -> str:
    text = text.strip() or "(no output)"

    if len(text) <= config.max_tool_output_chars:
        return text

    head_len = config.max_tool_output_chars // 2
    tail_len = config.max_tool_output_chars - head_len
    omitted = len(text) - config.max_tool_output_chars

    return (
        text[:head_len]
        + f"\n\n... truncated {omitted} characters ...\n\n"
        + text[-tail_len:]
    )


def _response_parts(response) -> tuple[str, list]:
    final = ""
    tool_calls = []
    candidates = getattr(response, "candidates", None) or []

    if not candidates:
        return final, tool_calls

    content = getattr(candidates[0], "content", None)
    parts = getattr(content, "parts", None) or []

    for part in parts:
        if getattr(part, "text", None):
            final += part.text

        if getattr(part, "function_call", None):
            tool_calls.append(part.function_call)

    return final, tool_calls


def _render_markdown(console: Console, text: str, *, end: str = "\n") -> None:
    console.print(
        Markdown(
            text,
            code_theme="monokai",
            hyperlinks=True
        ),
        end=end
    )


def main() -> None:
    if not config.api_key:
        raise ShellMindError("API_KEY is not set.")

    if not config.model:
        raise ShellMindError("MODEL is not set.")

    if hasattr(genai, "configure"):
        genai.configure(api_key=config.api_key)  # type: ignore

    console = Console()
    messages = []

    model = None
    if hasattr(genai, "GenerativeModel"):
        try:
            model = genai.GenerativeModel(  # type: ignore
                config.model,
                generation_config={
                    "max_output_tokens": config.max_output_tokens,
                },
                system_instruction=SYSTEM_PROMPT
            )
        except ResourceExhaustedError:
            print(
                Fore.RED +
                "Model is currently overloaded.",
                "Please try again later."
                + Style.RESET_ALL
            )
            return

    if model is None:
        print(
            Fore.YELLOW +
            "Failed to initialize the generative model."
            + Style.RESET_ALL
        )
        return

    banner(console)

    try:
        while True:
            uin = input(config.prompt)

            if uin == "/bye":
                return

            if uin == "/model":
                print(Fore.LIGHTBLACK_EX + config.model + Style.RESET_ALL)
                continue

            if uin in {"/help", "/?"}:
                print(
                    f"""
{Fore.CYAN}Console{Fore.YELLOW}
Type {Fore.BLUE}/model{Fore.YELLOW} to show active model.
Type {Fore.BLUE}/help{Fore.YELLOW} or {Fore.BLUE}/?{Fore.YELLOW} to see this.
Type {Fore.BLUE}/bye{Fore.YELLOW} to exit.
Type anything else to get a response from the AI.
""" + Style.RESET_ALL
                )
                continue

            messages.append(_message("user", uin))
            _trim_history(messages)

            try:
                res = model.generate_content(messages, tools=tools)
            except ResourceExhaustedError:
                print(
                    Fore.RED +
                    "Model is currently overloaded.",
                    "Please try again later."
                    + Style.RESET_ALL
                )
                continue

            final, tool_calls = _response_parts(res)

            if not tool_calls:
                if final:
                    _render_markdown(console, final)
                    messages.append(_message("model", final))
                    _trim_history(messages)
                print()
                continue

            tool_messages = messages.copy()

            for call in tool_calls:
                tool_result = run_tool((call.name, dict(call.args)))
                trimmed = _trim_tool_output(tool_result)
                tool_messages.append(
                    _message("user", f"Tool result ({call.name}):\n{trimmed}")
                )

            _trim_history(tool_messages)

            try:
                followup, _ = _response_parts(
                    model.generate_content(tool_messages)
                )
            except ResourceExhaustedError:
                print(
                    Fore.RED +
                    "While generating follow-up response:",
                    "Model is currently overloaded.",
                    "Please try again later."
                    + Style.RESET_ALL
                )
                continue

            _render_markdown(console, followup)
            messages.append(_message("model", followup))
            _trim_history(messages)

            print()

    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    try:
        print(Fore.GREEN + "Loading..." + Style.RESET_ALL)
        main()
    except ShellMindError as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        sys.exit(1)
