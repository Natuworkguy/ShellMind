from dataclasses import dataclass, field
from typing import Any, Callable

from google.genai import errors, types

from .commands import direct_shell_command, help_text
from .config import Config
from .messages import (
    ChatMessage,
    message,
    response_content,
    response_parts,
    tool_response_part,
    trim_history,
    trim_tool_output,
)
from .rendering import print_error, print_info, print_warning
from .tools import tools


@dataclass
class ShellMindSession:
    config: Config
    model: Any
    console: Any
    render_markdown: Callable[[Any, str], None]
    run_tool: Callable[[tuple[str, dict[str, Any]]], str]
    input_func: Callable[[str], str] = input
    output: Callable[[str], None] = print
    tool_schemas: list[Any] = field(default_factory=lambda: tools)
    messages: list[ChatMessage] = field(default_factory=list)

    def run(self) -> None:
        while True:
            user_input = self.input_func(self.config.prompt)
            if not self.process_input(user_input):
                return

    def process_input(self, user_input: str) -> bool:
        if user_input == "/bye":
            return False

        if user_input == "/model":
            print_info(self.output, self.config.model)
            return True

        if user_input == "/clear":
            self.messages.clear()
            print_info(self.output, "Context cleared.")
            return True

        if user_input in {"/help", "/?"}:
            self.output(help_text())
            return True

        command = direct_shell_command(user_input)
        if command:
            self.output(self.run_tool(("shell", {"command": command})))
            self.output("")
            return True

        self.messages.append(message("user", user_input))
        trim_history(
            self.messages,
            max_messages=self.config.max_history_messages,
            max_chars=self.config.max_history_chars
        )

        try:
            response = self._generate(self.messages, use_tools=True)
        except errors.APIError:
            self.messages.pop()
            print_error(
                self.output,
                "Model is currently overloaded. Please try again later."
            )
            return True

        final, tool_calls = response_parts(response)

        if not tool_calls:
            self._handle_non_tool_response(final)
            return True

        followup = self._handle_tool_response(
            response,
            tool_calls,
            original_request=user_input
        )
        self.render_markdown(self.console, followup)
        self.messages.append(message("model", followup))
        trim_history(
            self.messages,
            max_messages=self.config.max_history_messages,
            max_chars=self.config.max_history_chars
        )
        self.output("")
        return True

    def _generate(self, messages: list[Any], *, use_tools: bool) -> Any:
        if use_tools:
            return self.model.generate_content(
                messages,
                tools=self.tool_schemas
            )

        return self.model.generate_content(messages)

    def _handle_non_tool_response(self, final: str) -> None:
        if final:
            self.render_markdown(self.console, final)
            self.messages.append(message("model", final))
            trim_history(
                self.messages,
                max_messages=self.config.max_history_messages,
                max_chars=self.config.max_history_chars
            )
        else:
            self.messages.pop()
            print_warning(self.output, "The model returned no response.")

        self.output("")

    def _handle_tool_response(
        self,
        response: Any,
        tool_calls: list[Any],
        *,
        original_request: str
    ) -> str:
        tool_messages: list[Any] = self.messages.copy()
        tool_outputs: list[str] = []
        followup = ""
        active_response = response
        active_tool_calls = tool_calls

        try:
            followup = self._run_tool_rounds(
                active_response,
                active_tool_calls,
                tool_messages,
                tool_outputs
            )
        except errors.APIError:
            print_error(
                self.output,
                "While generating follow-up response, the model is "
                "currently overloaded. Please try again later."
            )
            return self._fallback_tool_output(tool_outputs)

        if followup.strip():
            return followup

        tool_messages.append(
            message(
                "user",
                "Using the tool results above, answer the original request: "
                f"{original_request}. Do not call more tools."
            )
        )

        try:
            followup, _ = response_parts(
                self._generate(tool_messages, use_tools=False)
            )
        except errors.APIError:
            print_error(
                self.output,
                "While generating final response, the model is currently "
                "overloaded. Please try again later."
            )
            return self._fallback_tool_output(tool_outputs)

        if followup.strip():
            return followup

        print_warning(
            self.output,
            "The model did not provide a final response after tools."
        )
        return self._fallback_tool_output(tool_outputs)

    def _run_tool_rounds(
        self,
        response: Any,
        tool_calls: list[Any],
        tool_messages: list[Any],
        tool_outputs: list[str]
    ) -> str:
        active_response = response
        active_tool_calls = tool_calls
        followup = ""

        for _ in range(self.config.max_tool_rounds):
            content = response_content(active_response)
            if content is not None:
                tool_messages.append(content)

            response_parts_list = self._execute_tool_calls(
                active_tool_calls,
                tool_outputs
            )
            tool_messages.append(
                types.Content(role="tool", parts=response_parts_list)
            )

            active_response = self._generate(tool_messages, use_tools=True)
            followup, active_tool_calls = response_parts(active_response)

            if not active_tool_calls:
                break

        return followup

    def _execute_tool_calls(
        self,
        tool_calls: list[Any],
        tool_outputs: list[str]
    ) -> list[types.Part]:
        response_parts_list = []

        for call in tool_calls:
            tool_result = self.run_tool((call.name, dict(call.args)))
            trimmed = trim_tool_output(
                tool_result,
                max_chars=self.config.max_tool_output_chars
            )
            tool_outputs.append(f"{call.name}:\n{trimmed}")
            response_parts_list.append(
                tool_response_part(call.name, trimmed)
            )

        return response_parts_list

    def _fallback_tool_output(self, tool_outputs: list[str]) -> str:
        if not tool_outputs:
            return "Tool output:\n\n```text\n(no output)\n```"

        return (
            "Tool output:\n\n```text\n"
            + "\n\n".join(tool_outputs)
            + "\n```"
        )
