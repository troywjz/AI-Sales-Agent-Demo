from app.core.config import Settings
from app.llm.base import ChatMessage, LLMProviderError, LLMResponse
from app.llm.fallback_client import FallbackLLMClient
from app.llm.http_client import HttpLLMClient
from app.llm.providers import LLMProtocol, LLMProviderConfig, build_llm_fallback_configs
import pytest


def test_baiduqianfan_provider_is_available_first() -> None:
    settings = Settings(
        LLM_PROVIDER="baiduqianfan",
        LLM_PROVIDER_FALLBACK="minimax",
        BAIDUQIANFAN_API_URL="https://qianfan.baidubce.com/v2/coding",
        BAIDUQIANFAN_API_KEY="test-key",
        BAIDUQIANFAN_MODEL="deepseek-v4-flash",
        MINIMAX_API_URL="https://api.minimaxi.com/v1",
        MINIMAX_API_KEY="test-key",
        MINIMAX_MODEL="MiniMax-M2.7",
    )

    configs = build_llm_fallback_configs(settings)

    assert [config.provider for config in configs[:2]] == ["baiduqianfan", "minimax"]
    assert configs[0].api_url == "https://qianfan.baidubce.com/v2/coding"
    assert configs[0].model == "deepseek-v4-flash"


class FailingClient:
    def __init__(self) -> None:
        self.called = False

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        self.called = True
        raise LLMProviderError("failed")


class SuccessClient:
    def __init__(self) -> None:
        self.called = False

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        self.called = True
        return LLMResponse(
            content="ok",
            provider="success",
            model="success-model",
            raw_response={"choices": [{"message": {"content": "ok"}}]},
            usage={"total_tokens": 1},
        )


class InvalidJsonClient:
    def __init__(self) -> None:
        self.called = False

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        self.called = True
        return LLMResponse(
            content='{"matched_skus": [',
            provider="invalid-json",
            model="invalid-json-model",
            raw_response={"choices": [{"message": {"content": '{"matched_skus": ['}}]},
            usage={"total_tokens": 10},
        )


class ValidJsonClient:
    def __init__(self) -> None:
        self.called = False

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        self.called = True
        return LLMResponse(
            content='{"matched_skus":[],"facts":[],"policy_notes":[],"missing_info":[]}',
            provider="valid-json",
            model="valid-json-model",
            raw_response={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"matched_skus":[],"facts":[],"policy_notes":[],'
                                '"missing_info":[]}'
                            )
                        }
                    }
                ]
            },
            usage={"total_tokens": 20},
        )


def test_fallback_client_respects_max_attempts() -> None:
    settings = Settings(
        LLM_PROVIDER="baiduqianfan",
        LLM_PROVIDER_FALLBACK="minimax,siliconflow",
        BAIDUQIANFAN_API_URL="https://qianfan.baidubce.com/v2/coding",
        BAIDUQIANFAN_API_KEY="test-key",
        BAIDUQIANFAN_MODEL="deepseek-v4-flash",
        MINIMAX_API_URL="https://api.minimaxi.com/v1",
        MINIMAX_API_KEY="test-key",
        MINIMAX_MODEL="MiniMax-M2.7",
        SILICONFLOW_API_URL="https://api.siliconflow.cn/v1",
        SILICONFLOW_API_KEY="test-key",
        SILICONFLOW_MODEL="deepseek-ai/DeepSeek-V4-Flash",
    )
    client = FallbackLLMClient(build_llm_fallback_configs(settings), max_attempts=2)
    fake_clients = [FailingClient(), FailingClient(), FailingClient()]
    client.clients = fake_clients

    import pytest

    async def run_case() -> None:
        await client.chat([ChatMessage(role="user", content="test")])

    with pytest.raises(LLMProviderError, match="Skipped 1 fallback configs"):
        import asyncio

        asyncio.run(run_case())

    assert [fake.called for fake in fake_clients] == [True, True, False]


def test_fallback_client_returns_attempt_records() -> None:
    settings = Settings(
        LLM_PROVIDER="baiduqianfan",
        LLM_PROVIDER_FALLBACK="minimax",
        BAIDUQIANFAN_API_URL="https://qianfan.baidubce.com/v2/coding",
        BAIDUQIANFAN_API_KEY="test-key",
        BAIDUQIANFAN_MODEL="deepseek-v4-flash",
        MINIMAX_API_URL="https://api.minimaxi.com/v1",
        MINIMAX_API_KEY="test-key",
        MINIMAX_MODEL="MiniMax-M2.7",
    )
    client = FallbackLLMClient(build_llm_fallback_configs(settings))
    client.clients = [FailingClient(), SuccessClient()]

    async def run_case() -> LLMResponse:
        return await client.chat([ChatMessage(role="user", content="test")])

    import asyncio

    response = asyncio.run(run_case())

    assert response.content == "ok"
    assert [attempt.provider for attempt in response.call_attempts] == [
        "baiduqianfan",
        "minimax",
    ]
    assert [attempt.success for attempt in response.call_attempts] == [False, True]
    assert response.call_attempts[0].error_type == "LLMProviderError"
    assert response.call_attempts[0].error_message == "failed"
    assert response.call_attempts[1].usage == {"total_tokens": 1}


def test_fallback_client_treats_invalid_json_as_failed_attempt() -> None:
    settings = Settings(
        LLM_PROVIDER="baiduqianfan",
        LLM_PROVIDER_FALLBACK="minimax",
        BAIDUQIANFAN_API_URL="https://qianfan.baidubce.com/v2/coding",
        BAIDUQIANFAN_API_KEY="test-key",
        BAIDUQIANFAN_MODEL="deepseek-v4-flash",
        MINIMAX_API_URL="https://api.minimaxi.com/v1",
        MINIMAX_API_KEY="test-key",
        MINIMAX_MODEL="MiniMax-M2.7",
    )
    client = FallbackLLMClient(build_llm_fallback_configs(settings))
    fake_clients = [InvalidJsonClient(), ValidJsonClient()]
    client.clients = fake_clients

    async def run_case() -> LLMResponse:
        return await client.chat(
            [ChatMessage(role="user", content="test")],
            response_format="json",
        )

    import asyncio

    response = asyncio.run(run_case())

    assert response.provider == "valid-json"
    assert [fake.called for fake in fake_clients] == [True, True]
    assert [attempt.success for attempt in response.call_attempts] == [False, True]
    assert response.call_attempts[0].error_type == "JSONDecodeError"
    assert "Invalid JSON response" in response.call_attempts[0].error_message


def test_http_client_rejects_reasoning_only_response_for_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = LLMProviderConfig(
        provider="test-provider",
        api_url="https://example.invalid/v1",
        api_key="test-key",
        model="test-model",
        protocol=LLMProtocol.openai_chat,
        timeout_seconds=1,
    )
    client = HttpLLMClient(config)

    async def reasoning_only_response(*_args, **_kwargs):
        return {
            "choices": [
                {
                    "finish_reason": "length",
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "reasoning_content": "internal reasoning",
                    },
                }
            ]
        }

    monkeypatch.setattr(client, "_post_json", reasoning_only_response)

    import asyncio

    with pytest.raises(LLMProviderError, match="reasoning-only response"):
        asyncio.run(client.chat([ChatMessage(role="user", content="test")]))
