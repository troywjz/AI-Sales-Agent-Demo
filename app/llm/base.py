from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMCallAttempt:
    """单次模型供应商调用尝试，用于追踪 fallback 前后的完整链路。"""

    provider: str
    model: str
    api_url: str
    protocol: str
    attempt_index: int
    success: bool
    elapsed_ms: int
    request_json: dict[str, Any] = field(default_factory=dict)
    response_json: dict[str, Any] = field(default_factory=dict)
    usage: dict[str, Any] = field(default_factory=dict)
    error_type: str = ""
    error_message: str = ""


@dataclass(frozen=True)
class LLMResponse:
    content: str
    provider: str
    model: str
    raw_response: dict[str, Any]
    usage: dict[str, Any] = field(default_factory=dict)
    call_attempts: list[LLMCallAttempt] = field(default_factory=list)


class LLMClient(Protocol):
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        ...


class LLMConfigurationError(RuntimeError):
    pass


class LLMProviderError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        call_attempts: list[LLMCallAttempt] | None = None,
    ) -> None:
        super().__init__(message)
        self.call_attempts = call_attempts or []
