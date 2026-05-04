from typing import Callable

from colorama import Fore, Style
from pyfiglet import Figlet
from rich.console import Console
from rich.markdown import Markdown


def banner(console: Console) -> None:
    figlet = Figlet(font="slant")
    console.print(figlet.renderText("ShellMind CLI"), style="bold cyan")


def render_markdown(console: Console, text: str, *, end: str = "\n") -> None:
    console.print(
        Markdown(
            text,
            code_theme="monokai",
            hyperlinks=True
        ),
        end=end
    )


def print_error(output: Callable[[str], None], message: str) -> None:
    output(Fore.RED + message + Style.RESET_ALL)


def print_info(output: Callable[[str], None], message: str) -> None:
    output(Fore.LIGHTBLACK_EX + message + Style.RESET_ALL)


def print_warning(output: Callable[[str], None], message: str) -> None:
    output(Fore.YELLOW + message + Style.RESET_ALL)
