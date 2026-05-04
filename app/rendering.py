from typing import Callable


def banner(console) -> None:
    console.print("ShellMind CLI")


def render_markdown(console, text: str, *, end: str = "\n") -> None:
    console.print(text, end=end)


def print_error(output: Callable[[str], None], message: str) -> None:
    output(message)


def print_info(output: Callable[[str], None], message: str) -> None:
    output(message)


def print_warning(output: Callable[[str], None], message: str) -> None:
    output(message)
