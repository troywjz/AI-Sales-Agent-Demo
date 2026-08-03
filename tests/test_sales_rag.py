import asyncio
import json
from types import SimpleNamespace

from app.core.config import Settings
from app.sales_rag.service import SalesCaseRAGService


class FakeResult:
    def __init__(self, rows) -> None:
        self.rows = rows

    def scalars(self):
        return self.rows


class FakeSession:
    def __init__(self, rows) -> None:
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, _statement):
        return FakeResult(self.rows)


def _settings(enabled: bool = True) -> Settings:
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+psycopg://user:pass@127.0.0.1:5432/sales_agent_demo",
        SALES_RAG_ENABLED=enabled,
    )


def test_local_sales_rag_prefers_matching_case() -> None:
    rows = [
        SimpleNamespace(
            chunk_id="price-case",
            conversation_hash="demo",
            customer_text="价格有点高，预算不够",
            sales_reply="先判断方案是否解决当前问题，再讨论投入。",
            context_before="客户认可需求但关注预算",
            quality_score=0.9,
            tags_json=json.dumps(["价格", "预算"], ensure_ascii=False),
        ),
        SimpleNamespace(
            chunk_id="time-case",
            conversation_hash="demo",
            customer_text="最近工作忙，没有时间",
            sales_reply="可以拆成小任务。",
            context_before="客户担心时间投入",
            quality_score=0.92,
            tags_json=json.dumps(["时间"], ensure_ascii=False),
        ),
    ]
    service = SalesCaseRAGService(
        settings=_settings(),
        session_factory=lambda: FakeSession(rows),
    )

    references = asyncio.run(
        service.retrieve(message="我觉得价格有点高，预算有限", current_stage="价值塑造")
    )

    assert references
    assert references[0].chunk_id == "price-case"
    assert references[0].similarity > 0


def test_disabled_sales_rag_does_not_open_database_session() -> None:
    def fail_session():
        raise AssertionError("disabled RAG should not access PostgreSQL")

    service = SalesCaseRAGService(
        settings=_settings(enabled=False),
        session_factory=fail_session,
    )

    assert asyncio.run(service.retrieve(message="价格是多少")) == []
