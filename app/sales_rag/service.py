from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.db.models import SalesRAGChunk
from app.db.session import SessionLocal


@dataclass(frozen=True)
class SalesCaseRAGReference:
    chunk_id: str
    conversation_hash: str
    customer_text: str
    sales_reply: str
    context_before: str
    quality_score: float
    similarity: float
    tags: list[str]

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "conversation_hash": self.conversation_hash,
            "customer_text": self.customer_text,
            "sales_reply": self.sales_reply,
            "context_before": self.context_before,
            "quality_score": round(self.quality_score, 4),
            "similarity": round(self.similarity, 4),
            "tags": self.tags,
        }


class SalesCaseRAGService:
    """从本地演示案例中召回话术策略，不依赖外部向量服务。"""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        session_factory=SessionLocal,
        **_: Any,
    ) -> None:
        self.settings = settings or get_settings()
        self.session_factory = session_factory

    async def retrieve(
        self,
        *,
        message: str,
        current_stage: str = "",
        intent: dict[str, Any] | None = None,
    ) -> list[SalesCaseRAGReference]:
        if not self.settings.sales_rag_enabled or not message.strip():
            return []
        query = self._query_text(
            message=message,
            current_stage=current_stage,
            intent=intent or {},
        )
        query_terms = _terms(query)
        with self.session_factory() as db:
            rows = list(
                db.execute(
                    select(SalesRAGChunk).where(
                        SalesRAGChunk.quality_score
                        >= self.settings.sales_rag_min_quality_score
                    )
                ).scalars()
            )

        matches: list[SalesCaseRAGReference] = []
        for row in rows:
            tags = _loads_list(row.tags_json)
            candidate = "\n".join(
                (row.customer_text, row.sales_reply, row.context_before, " ".join(tags))
            )
            similarity = _term_similarity(query_terms, _terms(candidate))
            if similarity <= 0:
                continue
            matches.append(
                SalesCaseRAGReference(
                    chunk_id=row.chunk_id,
                    conversation_hash=row.conversation_hash,
                    customer_text=row.customer_text,
                    sales_reply=row.sales_reply,
                    context_before=row.context_before,
                    quality_score=float(row.quality_score or 0.0),
                    similarity=similarity,
                    tags=tags,
                )
            )
        matches.sort(
            key=lambda item: (item.similarity, item.quality_score),
            reverse=True,
        )
        return matches[: max(1, self.settings.sales_rag_top_k)]

    @staticmethod
    def _query_text(
        *,
        message: str,
        current_stage: str,
        intent: dict[str, Any],
    ) -> str:
        return "\n".join(
            item
            for item in (
                current_stage,
                str(intent.get("intent_category") or ""),
                str(intent.get("purchase_intent") or ""),
                message,
            )
            if item
        )


def _terms(value: str) -> set[str]:
    normalized = re.sub(r"\s+", "", value.lower())
    terms = set(re.findall(r"[a-z0-9_]+", normalized))
    chinese = "".join(re.findall(r"[\u4e00-\u9fff]", normalized))
    terms.update(chinese[index : index + 2] for index in range(max(0, len(chinese) - 1)))
    keywords = (
        "零基础",
        "跟不上",
        "价格",
        "预算",
        "太贵",
        "优惠",
        "时间",
        "没空",
        "效果",
        "适合",
        "课程",
        "办公",
        "效率",
        "报名",
        "购买",
    )
    terms.update(keyword for keyword in keywords if keyword in normalized)
    return {term for term in terms if term}


def _term_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    overlap = len(left & right)
    if not overlap:
        return 0.0
    return round(min(0.99, overlap / math.sqrt(len(left) * len(right))), 4)


def _loads_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []
