from colorama import Fore, Style


def direct_shell_command(text: str) -> str | None:
    if text.startswith("!"):
        return text[1:].strip()

    for prefix in ("/shell ", "/run "):
        if text.startswith(prefix):
            return text[len(prefix):].strip()

    return None


def help_text() -> str:
    return (
        f"""
{Fore.CYAN}Console{Fore.YELLOW}
Type {Fore.BLUE}/model{Fore.YELLOW} to show active model.
Type {Fore.BLUE}/help{Fore.YELLOW} or {Fore.BLUE}/?{Fore.YELLOW} to see this.
Type {Fore.BLUE}/bye{Fore.YELLOW} to exit.
Type {Fore.BLUE}/clear{Fore.YELLOW} to clear saved context.
Type {Fore.BLUE}!<command>{Fore.YELLOW} to run shell directly.
Type {Fore.BLUE}/run <command>{Fore.YELLOW}
or {Fore.BLUE}/shell <command>{Fore.YELLOW} to run shell directly.
Type anything else to get a response from the AI.
"""
        + Style.RESET_ALL
    )
