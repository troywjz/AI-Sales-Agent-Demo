from typing import Any

import httpx

from app.llm.base import (
    ChatMessage,
    LLMConfigurationError,
    LLMProviderError,
    LLMResponse,
)
from app.llm.providers import LLMProtocol, LLMProviderConfig


class HttpLLMClient:
    def __init__(self, config: LLMProviderConfig) -> None:
        self.config = config

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        self._validate_config()

        if self.config.protocol == LLMProtocol.anthropic_messages:
            return await self._chat_anthropic(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        return await self._chat_openai_compatible(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

    def _validate_config(self) -> None:
        missing: list[str] = []
        if not self.config.api_url:
            missing.append("api_url")
        if not self.config.api_key:
            missing.append("api_key")
        if not self.config.model:
            missing.append("model")

        if missing:
            missing_text = ", ".join(missing)
            raise LLMConfigurationError(
                f"LLM provider '{self.config.provider}' is missing: {missing_text}."
            )

    async def _chat_openai_compatible(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float,
        max_tokens: int | None,
        response_format: str | None,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in messages
            ],
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        # Many OpenAI-compatible gateways do not fully support response_format.
        # JSON-only behavior is enforced by prompts and validated after response.

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json; charset=utf-8",
        }

        raw = await self._post_json(self._openai_chat_url(), payload, headers)
        try:
            content = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(
                f"Unexpected response shape from provider '{self.config.provider}'."
            ) from exc

        return LLMResponse(
            content=content or "",
            provider=self.config.provider,
            model=self.config.model or "",
            raw_response=raw,
            usage=raw.get("usage") or {},
        )

    async def _chat_anthropic(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float,
        max_tokens: int | None,
    ) -> LLMResponse:
        system_parts = [
            message.content for message in messages if message.role == "system"
        ]
        conversation = [
            {"role": message.role, "content": message.content}
            for message in messages
            if message.role in {"user", "assistant"}
        ]

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": conversation,
            "temperature": temperature,
            "max_tokens": max_tokens or 1024,
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)

        headers = {
            "x-api-key": self.config.api_key or "",
            "anthropic-version": self.config.anthropic_version or "2023-06-01",
            "Content-Type": "application/json",
        }

        raw = await self._post_json(self.config.api_url or "", payload, headers)
        try:
            content_blocks = raw["content"]
        except KeyError as exc:
            raise LLMProviderError(
                f"Unexpected response shape from provider '{self.config.provider}'."
            ) from exc

        text = "".join(
            block.get("text", "")
            for block in content_blocks
            if isinstance(block, dict) and block.get("type") == "text"
        )
        return LLMResponse(
            content=text,
            provider=self.config.provider,
            model=self.config.model or "",
            raw_response=raw,
            usage=raw.get("usage") or {},
        )

    async def _post_json(
        self,
        api_url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(
                    api_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            text = exc.response.text[:1000]
            raise LLMProviderError(
                f"Provider '{self.config.provider}' returned "
                f"HTTP {exc.response.status_code}: {text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(
                f"Provider '{self.config.provider}' request failed: {exc}"
            ) from exc

    def _openai_chat_url(self) -> str:
        api_url = (self.config.api_url or "").rstrip("/")
        if api_url.endswith("/chat/completions"):
            return api_url
        return f"{api_url}/chat/completions"
