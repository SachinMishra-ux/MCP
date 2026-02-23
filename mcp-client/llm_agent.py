"""
llm_agent.py — LLM Agent that drives tool selection and execution

Supports:
  - Anthropic Claude (default)
  - OpenAI GPT models

The agent receives the user's message + all available MCP tools,
sends them to the LLM, and handles multi-turn tool call loops.
"""

import os
import json
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────

@dataclass
class AgentMessage:
    role: str        # "user" | "assistant" | "tool_result"
    content: str
    tool_calls: Optional[List[Dict]] = None   # list of {name, input}
    tool_results: Optional[List[Dict]] = None  # list of {name, result}


@dataclass
class StreamChunk:
    type: str        # "text" | "tool_call" | "tool_result" | "error" | "done"
    data: Any = None


# ─────────────────────────────────────────────────────────────
# Anthropic Agent
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful AI assistant with access to a set of MCP (Model Context Protocol) tools.
Each tool is prefixed with the server it belongs to, e.g. "filesystem__list_directory" belongs to the "filesystem" server.

When the user asks you to do something, choose the right tool(s) to accomplish the task.
Always relay tool results clearly and concisely to the user.
If a tool fails, explain what went wrong and suggest alternatives.
"""


class AnthropicAgent:
    """Drives Claude to use MCP tools in a multi-turn loop."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model

    def _get_client(self):
        import anthropic
        return anthropic.Anthropic(api_key=self.api_key)

    async def run(
        self,
        user_message: str,
        tools: List[Dict],
        history: List[Dict],
        tool_executor,          # async callable: (server, tool, args) -> ToolCallResult
    ) -> AsyncIterator[StreamChunk]:
        """
        Runs the agent loop, yielding StreamChunk events.

        tool_executor signature:
            async def executor(server_name: str, tool_name: str, args: dict) -> ToolCallResult
        """
        import anthropic

        client = self._get_client()
        messages = list(history) + [{"role": "user", "content": user_message}]

        # Agentic loop: keep calling until no more tool_use
        while True:
            response = client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=tools if tools else [],
                messages=messages,
            )

            # Collect assistant content blocks
            assistant_content = []
            text_parts = []

            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            # Emit any text from assistant
            if text_parts:
                yield StreamChunk(type="text", data="".join(text_parts))

            # Append assistant's turn to messages
            messages.append({"role": "assistant", "content": assistant_content})

            # If no tool calls → done
            if response.stop_reason != "tool_use":
                yield StreamChunk(type="done")
                break

            # Execute each tool_use block
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                namespaced_name: str = block.name
                tool_input: Dict = block.input

                # Yield tool call event for UI display
                yield StreamChunk(
                    type="tool_call",
                    data={"tool": namespaced_name, "input": tool_input},
                )

                # Parse server__tool_name
                if "__" in namespaced_name:
                    server_name, tool_name = namespaced_name.split("__", 1)
                else:
                    server_name, tool_name = None, namespaced_name

                # Execute
                tool_result = await tool_executor(server_name, tool_name, tool_input)

                result_text = (
                    tool_result.error_message
                    if tool_result.is_error
                    else str(tool_result.result)
                )

                yield StreamChunk(
                    type="tool_result",
                    data={
                        "tool": namespaced_name,
                        "result": result_text,
                        "is_error": tool_result.is_error,
                    },
                )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                })

            # Append all tool results in one user turn
            messages.append({"role": "user", "content": tool_results})


# ─────────────────────────────────────────────────────────────
# OpenAI Agent
# ─────────────────────────────────────────────────────────────

class OpenAIAgent:
    """Drives OpenAI GPT to use MCP tools in a multi-turn loop."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model

    def _get_client(self):
        from openai import OpenAI
        return OpenAI(api_key=self.api_key)

    def _convert_tools_to_openai(self, tools: List[Dict]) -> List[Dict]:
        """Convert Anthropic-style tool schema to OpenAI function calling format."""
        openai_tools = []
        for t in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
                },
            })
        return openai_tools

    async def run(
        self,
        user_message: str,
        tools: List[Dict],
        history: List[Dict],
        tool_executor,
    ) -> AsyncIterator[StreamChunk]:
        """Runs the OpenAI agent loop, yielding StreamChunk events."""
        from openai import OpenAI

        client = self._get_client()
        openai_tools = self._convert_tools_to_openai(tools)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        # Convert history
        for msg in history:
            if msg["role"] in ("user", "assistant"):
                content = msg.get("content", "")
                if isinstance(content, list):
                    text = " ".join(
                        b.get("text", "") for b in content if isinstance(b, dict)
                    )
                else:
                    text = str(content)
                messages.append({"role": msg["role"], "content": text})

        messages.append({"role": "user", "content": user_message})

        while True:
            kwargs = {
                "model": self.model,
                "messages": messages,
            }
            if openai_tools:
                kwargs["tools"] = openai_tools
                kwargs["tool_choice"] = "auto"

            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            msg = choice.message

            if msg.content:
                yield StreamChunk(type="text", data=msg.content)

            if not msg.tool_calls:
                yield StreamChunk(type="done")
                break

            # Add assistant message with tool calls
            messages.append(msg)

            for tc in msg.tool_calls:
                namespaced_name = tc.function.name
                try:
                    tool_input = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_input = {}

                yield StreamChunk(
                    type="tool_call",
                    data={"tool": namespaced_name, "input": tool_input},
                )

                if "__" in namespaced_name:
                    server_name, tool_name = namespaced_name.split("__", 1)
                else:
                    server_name, tool_name = None, namespaced_name

                tool_result = await tool_executor(server_name, tool_name, tool_input)
                result_text = (
                    tool_result.error_message
                    if tool_result.is_error
                    else str(tool_result.result)
                )

                yield StreamChunk(
                    type="tool_result",
                    data={
                        "tool": namespaced_name,
                        "result": result_text,
                        "is_error": tool_result.is_error,
                    },
                )

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text,
                })


# ─────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────

def get_agent(provider: str, api_key: str, model: str):
    """Return the right agent for the given provider."""
    if provider == "Anthropic Claude":
        return AnthropicAgent(api_key=api_key, model=model)
    elif provider == "OpenAI GPT":
        return OpenAIAgent(api_key=api_key, model=model)
    else:
        raise ValueError(f"Unknown provider: {provider}")
