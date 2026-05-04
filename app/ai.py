import sys

from google.api_core.exceptions import ResourceExhausted \
    as ResourceExhaustedError
from rich.console import Console

from .config import Config
from .errors import ShellMindError
from .model import configure_client, create_model
from .rendering import banner, print_error, print_warning, render_markdown
from .session import ShellMindSession
from .tools import run_tool


def build_session(
    *,
    console: Console | None = None,
    input_func=input,
    output=print
) -> ShellMindSession:
    config = Config.from_env()
    configure_client(config.api_key)

    session_console = console or Console()

    try:
        model = create_model(config)
    except ResourceExhaustedError as exc:
        raise ShellMindError(
            "Model is currently overloaded. Please try again later."
        ) from exc

    if model is None:
        raise ShellMindError("Failed to initialize the generative model.")

    return ShellMindSession(
        config=config,
        model=model,
        console=session_console,
        render_markdown=render_markdown,
        run_tool=run_tool,
        input_func=input_func,
        output=output,
    )


def main() -> None:
    try:
        session = build_session()
    except ShellMindError as exc:
        print_error(print, str(exc))
        sys.exit(1)

    banner(session.console)

    try:
        session.run()
    except KeyboardInterrupt:
        print_warning(print, "\nSession interrupted.")


if __name__ == "__main__":
    main()
