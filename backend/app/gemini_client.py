"""Vertex AI client wrapper.

Provides:
  - generate_json(model, prompt, schema, thinking_level=None) -> dict
  - generate_text(model, prompt, system=None) -> str
  - embed(text) -> list[float]

All calls are async and use exponential backoff on transient errors.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from google import genai
from google.genai import types
from tenacity import (
    AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential,
)

from app.config import settings


_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
    return _client


def _retry():
    return AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )


async def generate_json(
    model: str,
    prompt: str,
    schema: dict[str, Any],
    *,
    system: str | None = None,
    thinking_level: str | None = None,
    temperature: float = 0.4,
) -> dict[str, Any]:
    """Call a Gemini model and parse JSON response. Schema enforced by responseSchema."""
    client = get_client()
    config_kwargs: dict[str, Any] = {
        "response_mime_type": "application/json",
        "response_schema": schema,
        "temperature": temperature,
    }
    if system:
        config_kwargs["system_instruction"] = system
    # Note: thinking_level is a Gemini 3.x parameter; on 2.5 Pro we let the model
    # use its default thinking budget (no explicit knob needed). The arg is
    # accepted to keep the plan's call sites unchanged.
    _ = thinking_level

    config = types.GenerateContentConfig(**config_kwargs)

    async for attempt in _retry():
        with attempt:
            resp = await client.aio.models.generate_content(
                model=model, contents=prompt, config=config,
            )
            text = resp.text
            return json.loads(text)
    raise RuntimeError("unreachable")


async def generate_text(
    model: str,
    prompt: str,
    *,
    system: str | None = None,
    temperature: float = 0.7,
) -> str:
    client = get_client()
    config_kwargs: dict[str, Any] = {"temperature": temperature}
    if system:
        config_kwargs["system_instruction"] = system
    config = types.GenerateContentConfig(**config_kwargs)

    async for attempt in _retry():
        with attempt:
            resp = await client.aio.models.generate_content(
                model=model, contents=prompt, config=config,
            )
            return resp.text or ""
    raise RuntimeError("unreachable")


async def embed(text: str) -> list[float]:
    client = get_client()
    async for attempt in _retry():
        with attempt:
            resp = await client.aio.models.embed_content(
                model=settings.model_embedding,
                contents=text,
            )
            return list(resp.embeddings[0].values)
    raise RuntimeError("unreachable")


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed many texts. The SDK supports batch input."""
    client = get_client()
    async for attempt in _retry():
        with attempt:
            resp = await client.aio.models.embed_content(
                model=settings.model_embedding,
                contents=texts,
            )
            return [list(e.values) for e in resp.embeddings]
    raise RuntimeError("unreachable")
