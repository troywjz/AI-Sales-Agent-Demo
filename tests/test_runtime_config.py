import pytest

from app.core.config import Settings
from app.demo_data import _assert_demo_database_target
from app.llm import DemoLLMClient, create_llm_client


def test_windows_demo_defaults_to_postgresql() -> None:
    settings = Settings(_env_file=None)

    assert settings.database_url.startswith("postgresql+psycopg://")
    assert "sales_agent_demo" in settings.database_url
    assert settings.demo_seed_data is True


def test_demo_mode_uses_local_llm() -> None:
    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql+psycopg://user:pass@127.0.0.1:5432/sales_agent_demo",
        DEMO_MODE=True,
        LLM_PROVIDER="demo",
    )

    assert isinstance(create_llm_client(settings), DemoLLMClient)


def test_demo_seed_rejects_non_demo_database() -> None:
    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql+psycopg://user:pass@127.0.0.1:5432/sales_agent",
        DEMO_ALLOW_UNSAFE_SEED=False,
    )

    with pytest.raises(RuntimeError, match="非 Demo 数据库"):
        _assert_demo_database_target(settings)
