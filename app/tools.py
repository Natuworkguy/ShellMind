import subprocess

SYSTEM_PROMPT = """
You can use tools.

When you want to use a tool, respond ONLY like this:

TOOL: tool_name | arg1=value1 | arg2=value2

Example:
TOOL: shell | command=dir

Otherwise respond normally.
You can only use 1 tool in each response.
"""


def shell_tool(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15
        )
        return result.stdout or result.stderr
    except Exception as e:
        return f"Error: {e}"


tools = {
    "shell": {
        "description": "Execute shell commands and return the output.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute."
                }
            },
            "required": ["command"]
        },
        "function": shell_tool
    }
}


def parse_tool_call(text: str):
    if not text.startswith("TOOL:"):
        return None

    try:
        body = text.replace("TOOL:", "").strip()
        parts = [p.strip() for p in body.split("|")]

        name = parts[0]
        args = {}

        for p in parts[1:]:
            k, v = p.split("=", 1)
            args[k.strip()] = v.strip()

        return name, args
    except Exception:
        return None


def run_tool(call, Fore, Style):
    name, args = call

    if name in tools:
        try:
            return tools[name]["function"](**args)
        except Exception as e:
            exc_as_text = f"{e.__class__.__name__}: {str(e)}"
            print(
                Fore.RED,
                "Error running tool:", exc_as_text,
                Style.RESET_ALL
            )
            return exc_as_text

    return "Unknown tool"
