from typing import Any, TypedDict

from google.genai import types


class MessagePart(TypedDict):
    text: str


class ChatMessage(TypedDict):
    role: str
    parts: list[MessagePart]


def message(role: str, text: str) -> ChatMessage:
    return {"role": role, "parts": [{"text": text}]}


def message_text(entry: ChatMessage) -> str:
    parts = entry.get("parts", [])
    text_parts = []

    for part in parts:
        text = part.get("text")
        if text:
            text_parts.append(text)

    return "\n".join(text_parts)


def trim_history(
    messages: list[ChatMessage],
    *,
    max_messages: int,
    max_chars: int
) -> None:
    if len(messages) > max_messages:
        del messages[:-max_messages]

    while (
        len(messages) > 1
        and sum(len(message_text(entry)) for entry in messages) > max_chars
    ):
        del messages[0]


def trim_tool_output(text: str, *, max_chars: int) -> str:
    text = text.strip() or "(no output)"

    if len(text) <= max_chars:
        return text

    head_len = max_chars // 2
    tail_len = max_chars - head_len
    omitted = len(text) - max_chars

    return (
        text[:head_len]
        + f"\n\n... truncated {omitted} characters ...\n\n"
        + text[-tail_len:]
    )


def response_parts(response: Any) -> tuple[str, list[Any]]:
    final = getattr(response, "text", None) or ""
    tool_calls = list(getattr(response, "function_calls", None) or [])
    return final, tool_calls


def response_content(response: Any) -> Any:
    candidates = getattr(response, "candidates", None) or []

    if not candidates:
        return None

    return getattr(candidates[0], "content", None)


def tool_response_part(name: str, result: str) -> types.Part:
    return types.Part.from_function_response(
        name=name,
        response={"result": result}
    )
