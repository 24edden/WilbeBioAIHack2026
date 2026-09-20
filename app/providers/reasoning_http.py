"""OpenAI reasoning transport, independent of the scientific agent prompts.

Rosalind uses the Responses path. The existing chat-completions path remains
available for compatible gateways. No model or transport fallback is implicit.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from app.config import Settings
from app.providers.errors import ProviderError


def _response_body(response: httpx.Response) -> dict[str, Any]:
    if response.status_code >= 400:
        # Provider messages can echo prompts, secrets or uploaded records. Keep
        # public errors actionable without forwarding the upstream response body.
        hints = {
            401: "Check REASONING_API_KEY on the server.",
            403: "Check the project's permission to use the configured model; Rosalind requires approved access.",
            404: "Check the model ID, API route and project access; Rosalind requires approved access.",
            429: "The provider rate or usage limit was reached. Retry after checking the account limits.",
        }
        hint = hints.get(response.status_code, "Check the provider service and configured API route.")
        raise ProviderError(f"Reasoning API failed (HTTP {response.status_code}). {hint}")
    try:
        body = response.json()
    except ValueError as exc:
        raise ProviderError("Reasoning API returned invalid JSON.") from exc
    if not isinstance(body, dict):
        raise ProviderError("Reasoning API returned an unexpected response shape.")
    return body


def _responses_text(body: dict[str, Any]) -> str:
    if body.get("status") != "completed" or body.get("error"):
        if body.get("status") == "incomplete":
            raise ProviderError(
                "Reasoning response was incomplete. Check the output token budget and provider limits before retrying."
            )
        raise ProviderError("Reasoning response did not complete successfully.")
    output = body.get("output")
    if not isinstance(output, list):
        raise ProviderError("Reasoning response has no output list.")
    texts = []
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            # Reasoning items are not answers and must never enter the evidence.
            continue
        if item.get("role") != "assistant":
            continue
        if item.get("status") not in (None, "completed"):
            raise ProviderError("Reasoning message was incomplete.")
        content = item.get("content")
        if not isinstance(content, list):
            raise ProviderError("Reasoning message has an unexpected content shape.")
        for part in content:
            if not isinstance(part, dict):
                raise ProviderError("Reasoning message has an unexpected content shape.")
            if part.get("type") == "refusal":
                raise ProviderError("The reasoning model declined this request.")
            if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                texts.append(part["text"])
    text = "\n".join(texts).strip()
    if not text:
        raise ProviderError("Reasoning response contained no assistant text.")
    return text


def _chat_text(body: dict[str, Any]) -> str:
    try:
        choice = body["choices"][0]
        message = choice["message"]
        if choice.get("finish_reason") not in (None, "stop"):
            raise ProviderError("Reasoning response was incomplete or blocked.")
        if message.get("refusal"):
            raise ProviderError("The reasoning model declined this request.")
        text = message["content"]
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise ProviderError("Reasoning API returned an unexpected chat response shape.") from exc
    if not isinstance(text, str) or not text.strip():
        raise ProviderError("Reasoning response contained no assistant text.")
    return text


class ReasoningHTTP:
    def __init__(self, settings: Settings) -> None:
        if not settings.reasoning_api_key.strip():
            raise ProviderError("REASONING_API_KEY is unset. Set it, or run with RUN_MODE=mock.")
        self.settings = settings
        self.usage: list[dict[str, Any]] = []

    def _record_usage(self, body: dict[str, Any]) -> None:
        # Preserve provider measurements, including incomplete/refused responses
        # that consumed tokens. An absent usage object means unavailable, not 0.
        self.usage.append({
            "model": body.get("model", self.settings.reasoning_model),
            "api": self.settings.effective_reasoning_api,
            "response_id": body.get("id"),
            "usage": body.get("usage") if isinstance(body.get("usage"), dict) else None,
        })

    async def _request(self, path: str, payload: dict | None = None) -> dict:
        url = f"{self.settings.reasoning_base_url.rstrip('/')}/{path}"
        headers = {"Authorization": f"Bearer {self.settings.reasoning_api_key}"}
        timeout = httpx.Timeout(self.settings.reasoning_timeout_seconds, connect=10.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if payload is None:
                    response = await client.get(url, headers=headers)
                else:
                    response = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise ProviderError("Reasoning API timed out. Check REASONING_TIMEOUT_SECONDS before retrying.") from exc
        except httpx.RequestError as exc:
            raise ProviderError("Could not reach the reasoning API. Check the server connection and base URL.") from exc
        return _response_body(response)

    async def check_access(self) -> None:
        """A read-only model lookup, not proof that generation succeeds."""
        body = await self._request("models/" + quote(self.settings.reasoning_model, safe=""))
        if body.get("id") != self.settings.reasoning_model:
            raise ProviderError("Model lookup did not return the configured model ID.")

    async def complete(self, system: str, user: str) -> str:
        if self.settings.effective_reasoning_api == "responses":
            body = await self._request("responses", {
                "model": self.settings.reasoning_model,
                "instructions": system,
                "input": [{"role": "user", "content": user}],
                "max_output_tokens": self.settings.reasoning_max_output_tokens,
                "store": False,
            })
            self._record_usage(body)
            # No temperature, reasoning effort or structured-output parameter is
            # assumed for Rosalind. Prompts request JSON; the provider validates it.
            return _responses_text(body)
        body = await self._request("chat/completions", {
            "model": self.settings.reasoning_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_completion_tokens": self.settings.reasoning_max_output_tokens,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        })
        self._record_usage(body)
        return _chat_text(body)
