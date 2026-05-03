from .tools import tools, SYSTEM_PROMPT, run_tool

# ----Modules----

genai = None


try:
    import sys
    import os
    try:
        from colorama import Style, Fore
    except ModuleNotFoundError:
        print("Error loading the colorama package")
        print("Please install colorama package.")
        sys.exit()

    try:
        from pyfiglet import Figlet
    except ModuleNotFoundError:
        print("Error loading the pyfiglet package")
        print("Please install pyfiglet package.")
        sys.exit()

    try:
        from rich.console import Console
        from rich.markdown import Markdown
    except ModuleNotFoundError:
        print("Error loading the rich package")
        print("Please install rich package.")
        sys.exit()

    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        print("Error loading the dotenv package")
        print("Please install dotenv package.")
        sys.exit()

    print(Fore.GREEN + "Loading..." + Style.RESET_ALL)

    try:
        import google.generativeai as genai
    except ModuleNotFoundError:
        print(Fore.RED + "Error loading the google-generativeai package")
        print("Please install google-generativeai package."
              + Style.RESET_ALL)
        sys.exit()
    except FutureWarning:
        pass

except KeyboardInterrupt:
    sys.exit()

load_dotenv()


class ShellMindError(Exception):
    pass


class config:
    api_key = os.getenv("API_KEY")
    model = os.getenv("MODEL")
    prompt = Fore.BLUE + "[SM]> " + Style.RESET_ALL

    if __name__ == "__main__" and \
            genai is not None and \
            hasattr(genai, "configure"):
        f = genai.configure  # pyright: ignore[reportPrivateImportUsage]
        f(api_key=api_key)


def banner(c: Console) -> None:
    f = Figlet(font="slant")
    c.print(
        f.renderText("ShellMind CLI"),
        style="bold cyan"
    )


def main() -> None:
    console = Console()
    messages = [{"role": "system", "parts": [{"text": SYSTEM_PROMPT}]}]

    try:
        banner(console)
        while True:
            uin = input(config.prompt)
            if uin == "/bye":
                sys.exit()
            if uin == "/model":
                if config.model is None:
                    print(Fore.RED + "Model not set." + Style.RESET_ALL)
                else:
                    print(Fore.LIGHTBLACK_EX + config.model + Style.RESET_ALL)
                continue
            if uin == "/help" or uin == "/?":
                print(f"""
              {Fore.CYAN} Console{Fore.YELLOW}
Type {Fore.BLUE}/model{Fore.YELLOW} to show active model.
Type {Fore.BLUE}/help{Fore.YELLOW} or {Fore.BLUE}/?{Fore.YELLOW} to see this.
Type {Fore.BLUE}/bye{Fore.YELLOW} to exit.
Type anything else to get a response from the AI.
                           """ + Style.RESET_ALL)
                continue
            try:
                try:
                    messages.append(
                        {
                            "role": "user",
                            "parts": [{"text": uin}]
                        }
                    )

                    print(messages)

                    if genai is not None and hasattr(genai, "GenerativeModel")\
                            and config.model is not None:
                        res = genai.GenerativeModel(config.model).generate_content(messages, tools=tools)  # pyright: ignore[reportPrivateImportUsage] # noqa: E501

                        print()

                        final = ""
                        tool_calls = []

                        for part in res.candidates[0].content.parts:
                            if hasattr(part, "text") and part.text:
                                final += part.text
                                console.print(
                                    Markdown(
                                        part.text,
                                        code_theme="monokai",
                                        hyperlinks=True
                                    ),
                                    end=""
                                )

                            if hasattr(part, "function_call") and \
                                    part.function_call:
                                tool_calls.append(part.function_call)

                        messages.append(
                            {
                                "role": "assistant",
                                "parts": [{"text": final}]
                            }
                        )

                        if tool_calls:
                            for call in tool_calls:
                                name = call.name
                                args = dict(call.args)

                                tool_result = run_tool(
                                    (
                                        name,
                                        args
                                    ),
                                    Fore,
                                    Style
                                )

                                messages.append(
                                    {
                                        "role": "tool",
                                        "parts": [
                                            {
                                                "text": tool_result
                                            }
                                        ]
                                    }
                                )

                                followup = genai.GenerativeModel(config.model).generate_content(messages, tools=tools).text  # pyright: ignore[reportPrivateImportUsage] # noqa: E501

                                console.print(
                                    Markdown(
                                        followup,
                                        code_theme="monokai",
                                        hyperlinks=True
                                    )
                                )

                                messages.append(
                                    {
                                        "role": "assistant",
                                        "parts": [{"text": followup}]
                                    }
                                )

                        print()
                    else:
                        print(
                            Fore.RED,
                            f"{genai is None=}, {hasattr(genai, 'GenerativeModel')=}, {config.model=}",  # noqa: E501
                            Style.RESET_ALL
                        )

                except Exception as e:
                    print(
                        Fore.RED,
                        "An unexpected error occurred.",
                        "Error message: " + str(e) +
                        Style.RESET_ALL
                    )
            except NameError:
                print(
                    Fore.RED + "An unexpected error occurred" + Style.RESET_ALL
                )
                continue
    except KeyboardInterrupt:
        sys.exit()
