from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = Field(default="Sales Agent Demo", alias="APP_NAME")
    app_env: str = Field(default="demo", alias="APP_ENV")
    demo_mode: bool = Field(default=True, alias="DEMO_MODE")
    demo_agent_delay_ms: int = Field(default=60, alias="DEMO_AGENT_DELAY_MS")
    demo_seed_data: bool = Field(default=True, alias="DEMO_SEED_DATA")
    demo_allow_unsafe_seed: bool = Field(default=False, alias="DEMO_ALLOW_UNSAFE_SEED")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_secret_key: str = Field(default="change-me", alias="APP_SECRET_KEY")
    auth_token_ttl_seconds: int = Field(default=43200, alias="AUTH_TOKEN_TTL_SECONDS")
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin123", alias="ADMIN_PASSWORD")
    admin_password_hash: str = Field(default="", alias="ADMIN_PASSWORD_HASH")

    # Windows Python 服务直连 PostgreSQL；数据库可继续由 Docker 或独立服务提供。
    database_url: str = Field(
        default="postgresql+psycopg://sales_agent:change-me@127.0.0.1:5432/sales_agent_demo",
        alias="DATABASE_URL",
    )
    llm_provider: str = Field(default="demo", alias="LLM_PROVIDER")
    llm_provider_fallback: str = Field(
        default="",
        alias="LLM_PROVIDER_FALLBACK",
    )
    llm_timeout_seconds: float = Field(default=30.0, alias="LLM_TIMEOUT_SECONDS")
    llm_max_attempts_per_request: int = Field(
        default=0,
        alias="LLM_MAX_ATTEMPTS_PER_REQUEST",
    )
    chat_request_timeout_seconds: float = Field(
        default=180.0,
        alias="CHAT_REQUEST_TIMEOUT_SECONDS",
    )
    chat_merge_max_messages: int = Field(
        default=3,
        alias="CHAT_MERGE_MAX_MESSAGES",
    )
    chat_turn_debounce_seconds: float = Field(
        default=0.15,
        alias="CHAT_TURN_DEBOUNCE_SECONDS",
    )
    ai_reply_chunk_delay_seconds: float = Field(
        default=0.2,
        alias="AI_REPLY_CHUNK_DELAY_SECONDS",
    )
    ai_reply_chunk_max_chars: int = Field(
        default=45,
        alias="AI_REPLY_CHUNK_MAX_CHARS",
    )
    knowledge_auto_import: bool = Field(
        default=False,
        alias="KNOWLEDGE_AUTO_IMPORT",
    )
    sop_followup_enabled: bool = Field(
        default=True,
        alias="SOP_FOLLOWUP_ENABLED",
    )
    sop_followup_poll_interval_seconds: float = Field(
        default=5.0,
        alias="SOP_FOLLOWUP_POLL_INTERVAL_SECONDS",
    )
    sop_followup_batch_size: int = Field(
        default=10,
        alias="SOP_FOLLOWUP_BATCH_SIZE",
    )
    new_customer_welcome_messages: str = Field(
        default=(
            "你好，我是你的专属方案顾问，很高兴认识你\n"
            "你目前更想提升日常办公效率，还是解决某个具体工作场景？"
        ),
        alias="NEW_CUSTOMER_WELCOME_MESSAGES",
    )
    sales_rag_enabled: bool = Field(default=True, alias="SALES_RAG_ENABLED")
    sales_rag_top_k: int = Field(default=3, alias="SALES_RAG_TOP_K")
    sales_rag_min_quality_score: float = Field(
        default=0.45,
        alias="SALES_RAG_MIN_QUALITY_SCORE",
    )
    sales_rag_max_references: int = Field(
        default=3,
        alias="SALES_RAG_MAX_REFERENCES",
    )
    sales_rag_max_reference_chars: int = Field(
        default=1200,
        alias="SALES_RAG_MAX_REFERENCE_CHARS",
    )

    baiduqianfan_api_url: str | None = Field(
        default="https://qianfan.baidubce.com/v2/coding",
        alias="BAIDUQIANFAN_API_URL",
    )
    baiduqianfan_api_key: str | None = Field(
        default=None,
        alias="BAIDUQIANFAN_API_KEY",
    )
    baiduqianfan_model: str | None = Field(
        default=None,
        alias="BAIDUQIANFAN_MODEL",
    )
    baiduqianfan_models: str | None = Field(
        default=None,
        alias="BAIDUQIANFAN_MODELS",
    )

    minimax_api_url: str | None = Field(
        default="https://api.minimaxi.com/v1",
        alias="MINIMAX_API_URL",
    )
    minimax_api_key: str | None = Field(default=None, alias="MINIMAX_API_KEY")
    minimax_model: str | None = Field(default=None, alias="MINIMAX_MODEL")
    minimax_models: str | None = Field(default=None, alias="MINIMAX_MODELS")

    xiaomimimo_api_url: str | None = Field(
        default="https://token-plan-cn.xiaomimimo.com/v1",
        alias="XIAOMIMIMO_API_URL",
    )
    xiaomimimo_api_key: str | None = Field(
        default=None,
        alias="XIAOMIMIMO_API_KEY",
    )
    xiaomimimo_model: str | None = Field(default=None, alias="XIAOMIMIMO_MODEL")
    xiaomimimo_models: str | None = Field(default=None, alias="XIAOMIMIMO_MODELS")

    aliyun_api_url: str | None = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="ALIYUN_API_URL",
    )
    aliyun_api_key: str | None = Field(default=None, alias="ALIYUN_API_KEY")
    aliyun_model: str | None = Field(default=None, alias="ALIYUN_MODEL")
    aliyun_models: str | None = Field(default=None, alias="ALIYUN_MODELS")

    siliconflow_api_url: str | None = Field(
        default="https://api.siliconflow.cn/v1",
        alias="SILICONFLOW_API_URL",
    )
    siliconflow_api_key: str | None = Field(default=None, alias="SILICONFLOW_API_KEY")
    siliconflow_model: str | None = Field(default=None, alias="SILICONFLOW_MODEL")
    siliconflow_models: str | None = Field(default=None, alias="SILICONFLOW_MODELS")

    glm_api_url: str | None = Field(
        default="https://open.bigmodel.cn/api/paas/v4/chat/completions",
        alias="GLM_API_URL",
    )
    zhipuai_api_key: str | None = Field(default=None, alias="ZHIPUAI_API_KEY")
    glm_model: str | None = Field(default=None, alias="GLM_MODEL")
    glm_models: str | None = Field(default=None, alias="GLM_MODELS")

    qwen_api_url: str | None = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        alias="QWEN_API_URL",
    )
    dashscope_api_key: str | None = Field(default=None, alias="DASHSCOPE_API_KEY")
    qwen_model: str | None = Field(default=None, alias="QWEN_MODEL")
    qwen_models: str | None = Field(default=None, alias="QWEN_MODELS")

    deepseek_api_url: str | None = Field(
        default="https://api.deepseek.com/chat/completions",
        alias="DEEPSEEK_API_URL",
    )
    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_model: str | None = Field(default=None, alias="DEEPSEEK_MODEL")
    deepseek_models: str | None = Field(default=None, alias="DEEPSEEK_MODELS")

    chatgpt_api_url: str | None = Field(
        default="https://api.openai.com/v1/chat/completions",
        alias="CHATGPT_API_URL",
    )
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    chatgpt_model: str | None = Field(default=None, alias="CHATGPT_MODEL")
    chatgpt_models: str | None = Field(default=None, alias="CHATGPT_MODELS")

    claude_api_url: str | None = Field(
        default="https://api.anthropic.com/v1/messages",
        alias="CLAUDE_API_URL",
    )
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    claude_model: str | None = Field(default=None, alias="CLAUDE_MODEL")
    claude_models: str | None = Field(default=None, alias="CLAUDE_MODELS")
    anthropic_version: str = Field(
        default="2023-06-01",
        alias="ANTHROPIC_VERSION",
    )

    @property
    def new_customer_welcome_message_lines(self) -> list[str]:
        return [
            line.strip()
            for line in self.new_customer_welcome_messages.splitlines()
            if line.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
