"""LLM interface to Groq with tool-calling support.

This module wraps Groq's chat API and implements safe execution of
tool calls. The `ask_ai` function always returns a non-empty string
(explaining errors when they occur) so caller code doesn't receive
None.
"""
import os
import json
from typing import Any, Dict, List

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

try:
    from groq import Groq
except Exception:
    Groq = None

import tools

if load_dotenv is not None:
    load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY or Groq is None:
    # Keep client None but allow the module to be imported in environments
    # where the key is missing or Groq is unavailable.
    client = None
else:
    client = Groq(api_key=API_KEY)

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


# Define tools in an OpenAI-compatible schema that Groq understands.
TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a new empty file",
            "parameters": {
                "type": "object",
                "properties": {"filename": {"type": "string"}},
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file",
            "parameters": {
                "type": "object",
                "properties": {"filename": {"type": "string"}},
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rename_file",
            "description": "Rename a file",
            "parameters": {
                "type": "object",
                "properties": {"old_name": {"type": "string"}, "new_name": {"type": "string"}},
                "required": ["old_name", "new_name"],
            },
        },
    },
]


TOOL_MAP = {
    "create_file": tools.create_file,
    "delete_file": tools.delete_file,
    "rename_file": tools.rename_file,
}


def _get_attr(obj: Any, *names):
    """Helper to safely extract nested attributes or dict keys."""
    cur = obj
    for name in names:
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(name)
        else:
            cur = getattr(cur, name, None)
    return cur


def ask_ai(user_text: str) -> str:
    """Send `user_text` to the LLM and execute any tool calls.

    Always returns a string. If the Groq client is not configured or an
    error happens, the returned string describes the failure.
    """
    if not user_text:
        return ""
    if client is None:
        return "Error: GROQ_API_KEY is not configured. Set it in your environment."

    messages = [{"role": "user", "content": user_text}]

    try:
        resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOL_DEFINITIONS, tool_choice="auto")
    except Exception as e:
        return f"Error: LLM request failed: {e}"

    # Extract the assistant message
    choice0 = _get_attr(resp, "choices", 0) or (resp.choices[0] if hasattr(resp, 'choices') else None)
    message = _get_attr(choice0, "message") or (choice0.message if hasattr(choice0, 'message') else None)

    # Normalize tool calls list (may be attribute or dict)
    tool_calls = _get_attr(message, "tool_calls") or _get_attr(message, "toolCalls")

    if tool_calls:
        # Append assistant message to the conversation history so the final
        # pass can reference it.
        # message may be object-like or dict-like; convert to simple dict
        messages.append({"role": "assistant", "content": _get_attr(message, "content") or _get_attr(message, "text") or ""})

        for call in tool_calls:
            # Extract id, function name and arguments robustly
            call_id = _get_attr(call, "id") or _get_attr(call, "call_id")
            func_name = _get_attr(call, "function", "name") or _get_attr(call, "functionName")
            raw_args = _get_attr(call, "function", "arguments") or _get_attr(call, "arguments")

            # Groq sometimes returns JSON string for arguments
            args = {}
            if isinstance(raw_args, str):
                try:
                    args = json.loads(raw_args)
                except Exception:
                    args = {}
            elif isinstance(raw_args, dict):
                args = raw_args

            func = TOOL_MAP.get(func_name)
            if func is None:
                result = f"Error: unknown tool '{func_name}'"
            else:
                try:
                    result = func(**(args or {}))
                except Exception as e:
                    result = f"Error running {func_name}: {e}"

            # Append tool response to messages using the tool_call_id
            messages.append({"role": "tool", "tool_call_id": call_id, "content": str(result)})

        # Finalize with one more LLM call to produce a natural assistant reply
        try:
            final = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOL_DEFINITIONS)
        except Exception as e:
            return f"Error: LLM finalization failed: {e}"

        final_choice = _get_attr(final, "choices", 0) or (final.choices[0] if hasattr(final, 'choices') else None)
        final_message = _get_attr(final_choice, "message") or (final_choice.message if hasattr(final_choice, 'message') else None)
        return _get_attr(final_message, "content") or _get_attr(final_message, "text") or ""

    # No tool calls — return assistant content
    return _get_attr(message, "content") or _get_attr(message, "text") or ""