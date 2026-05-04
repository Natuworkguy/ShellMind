def direct_shell_command(user_input: str) -> str | None:
    if user_input.startswith("!") and len(user_input) > 1:
        return user_input[1:].strip()

    for prefix in ("/run ", "/shell "):
        if user_input.startswith(prefix):
            return user_input[len(prefix):].strip()

    return None


def help_text() -> str:
    return (
        "\nConsole\n"
        "Type /model to show active model.\n"
        "Type /help or /? to see this.\n"
        "Type /bye to exit.\n"
        "Type /clear to clear saved context.\n"
        "Type !<command> to run shell directly.\n"
        "Type /run <command>\n"
        "or /shell <command> to run shell directly.\n"
        "Type anything else to get a response from the AI.\n"
    )
