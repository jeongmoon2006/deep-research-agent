#!/usr/bin/env python3
"""LLM provider abstraction — supports OpenAI and Anthropic with streaming."""

from __future__ import annotations

from collections.abc import AsyncGenerator


async def stream_completion(
    provider: str,
    api_key: str,
    model: str,
    system: str,
    messages: list[dict],
    max_tokens: int = 8192,
) -> AsyncGenerator[str, None]:
    """Stream text chunks from the configured LLM provider.

    Args:
        provider: "openai" or "anthropic".
        api_key: Provider API key.
        model: Model name, e.g. "gpt-4o" or "claude-opus-4-5".
        system: System prompt.
        messages: Chat messages list (role/content dicts).
        max_tokens: Maximum tokens to generate.

    Yields:
        Text chunks as they arrive from the provider.

    Raises:
        ValueError: If provider is not recognized.
        RuntimeError: If the required package is not installed.
    """
    if provider == "openai":
        async for chunk in _openai_stream(api_key, model, system, messages, max_tokens):
            yield chunk
    elif provider == "anthropic":
        async for chunk in _anthropic_stream(api_key, model, system, messages, max_tokens):
            yield chunk
    else:
        raise ValueError(f"Unknown provider '{provider}'. Use 'openai' or 'anthropic'.")


async def complete(
    provider: str,
    api_key: str,
    model: str,
    system: str,
    messages: list[dict],
    max_tokens: int = 512,
) -> str:
    """Non-streaming completion — collects all chunks and returns the full text.

    Args:
        provider: "openai" or "anthropic".
        api_key: Provider API key.
        model: Model name.
        system: System prompt.
        messages: Chat messages list.
        max_tokens: Maximum tokens to generate.

    Returns:
        Complete response text as a single string.
    """
    parts: list[str] = []
    async for chunk in stream_completion(provider, api_key, model, system, messages, max_tokens):
        parts.append(chunk)
    return "".join(parts)


async def _openai_stream(
    api_key: str,
    model: str,
    system: str,
    messages: list[dict],
    max_tokens: int,
) -> AsyncGenerator[str, None]:
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise RuntimeError("openai package not installed. Run: pip install openai")

    client = AsyncOpenAI(api_key=api_key)
    full_messages = [{"role": "system", "content": system}, *messages]

    stream = await client.chat.completions.create(
        model=model,
        messages=full_messages,
        stream=True,
        max_tokens=max_tokens,
    )
    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content


async def _anthropic_stream(
    api_key: str,
    model: str,
    system: str,
    messages: list[dict],
    max_tokens: int,
) -> AsyncGenerator[str, None]:
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

    client = anthropic.AsyncAnthropic(api_key=api_key)

    async with client.messages.stream(
        model=model,
        system=system,
        messages=messages,
        max_tokens=max_tokens,
    ) as stream:
        async for text in stream.text_stream:
            yield text
