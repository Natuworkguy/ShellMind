from types import SimpleNamespace

from google.genai import types


def blank_response():
    return _response(text="", function_calls=[], parts=[])


def text_response(*parts: str):
    return _response(text="".join(parts), function_calls=[], parts=[])


def function_call_response(name: str, args: dict):
    part = types.Part(function_call=types.FunctionCall(name=name, args=args))
    return _response(
        text="",
        function_calls=[types.FunctionCall(name=name, args=args)],
        parts=[part]
    )


class FakeModel:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def generate_content(self, messages, tools=None):
        self.calls.append({"messages": messages, "tools": tools})
        response = self._responses.pop(0)
        if isinstance(response, BaseException):
            raise response

        return response


def _response(*, text, function_calls, parts):
    content = types.Content(role="model", parts=parts)
    candidate = SimpleNamespace(content=content)
    return SimpleNamespace(
        text=text,
        function_calls=function_calls,
        candidates=[candidate]
    )
