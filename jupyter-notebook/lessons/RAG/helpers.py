"""Shared helpers for the RAG lessons.

搬自 001_tools_multi-turn_conversation.ipynb,逻辑不变,只是集中到一处,
让每个 RAG notebook 用一行 import 就能拿到 client / chat / message helper。

用法:
    from helpers import chat, add_user_message, add_assistant_message, txt_from_message
"""

from typing import Any, Iterable

import httpx
from anthropic import Anthropic
from anthropic.types import Message, ToolParam
from dotenv import load_dotenv

load_dotenv()

model = "claude-sonnet-4-5"

# verify=False:内网 gateway 的 TLS certificate 不在本机 trust store 里。
# 这是 notebook 里已在用的写法,搬过来保持一致。
client = Anthropic(http_client=httpx.Client(verify=False))


def add_user_message(messages: list[dict[str, Any]], message: Message | Any) -> None:
    """把一条 user message append 到 messages list(原地修改)。

    message 可以是 str,也可以是一个 Message object(这时取它的 .content)。
    """
    messages.append(
        {
            "role": "user",
            "content": message.content if isinstance(message, Message) else message,
        }
    )


def add_assistant_message(messages: list[dict[str, Any]], message: Message | Any) -> None:
    """把一条 assistant message append 到 messages list(原地修改)。"""
    messages.append(
        {
            "role": "assistant",
            "content": message.content if isinstance(message, Message) else message,
        }
    )


def chat(
    messages: list[dict[str, Any]],
    system: str | None = None,
    temperature: float = 1.0,
    stop_sequence: list[str] | None = None,
    tools: Iterable[ToolParam] | None = None,
) -> Message:
    """调一次 Messages API,返回完整的 Message object。

    system / tools 只在传了值的时候才放进 params,因为 API 不接受 None。
    """
    params: dict[str, Any] = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "temperature": temperature,
        "stop_sequences": stop_sequence if stop_sequence else [],
    }

    if tools:
        params["tools"] = list(tools)

    if system:
        params["system"] = system

    return client.messages.create(**params)


def txt_from_message(message: Message) -> str:
    """只把 response 里的 TextBlock 拼成字符串,忽略 ToolUseBlock 等其他 block。"""
    return "\n".join(block.text for block in message.content if block.type == "text")
