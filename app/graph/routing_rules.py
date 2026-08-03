from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import PROJECT_ROOT


ROUTING_RULES_PATH = PROJECT_ROOT / "data" / "business" / "routing_rules.json"
ROUTING_RULES_EXAMPLE_PATH = PROJECT_ROOT / "data" / "business" / "routing_rules.example.json"


@dataclass(frozen=True)
class RoutingRules:
    """确定性路由规则配置。

    这里集中管理不需要 LLM 的关键词和枚举规则，方便单独修改。
    注意：这些规则只负责快速路由，不替代 SOPAgent / SafetyAgent 的业务判断。
    """

    strong_handover_keywords: tuple[str, ...] = (
        "投诉",
        "举报",
        "诈骗",
        "骗子",
        "退款",
        "退费",
        "拉黑",
        "报警",
        "律师",
        "起诉",
        "立刻报名",
        "现在付款",
        "马上买",
        "转人工",
        "人工",
    )
    extreme_emotion_keywords: tuple[str, ...] = (
        "气死",
        "崩溃",
        "烦死",
        "别烦我",
        "太差了",
        "垃圾",
        "滚",
    )
    knowledge_keywords: tuple[str, ...] = (
        "多少钱",
        "价格",
        "费用",
        "优惠",
        "折扣",
        "套餐",
        "产品",
        "课程",
        "服务",
        "包含",
        "区别",
        "对比",
        "适合",
        "报名",
        "退款",
        "协议",
        "合同",
        "发票",
        "证书",
        "上课",
        "交付",
        "时间",
    )
    profile_update_keywords: tuple[str, ...] = (
        "我是",
        "我在",
        "我想",
        "我希望",
        "我准备",
        "预算",
        "年龄",
        "学历",
        "工作",
        "目标",
        "基础",
        "经验",
        "急",
        "担心",
    )
    small_talk_keywords: tuple[str, ...] = (
        "你好",
        "您好",
        "在吗",
        "有人吗",
        "谢谢",
        "好的",
        "嗯",
        "行",
    )
    small_talk_max_chars: int = 20
    intent_handover_categories: tuple[str, ...] = ("high_intent",)
    intent_handover_purchase_intents: tuple[str, ...] = ("high",)
    intent_handover_emotions: tuple[str, ...] = ("impatient",)
    intent_direct_reply_categories: tuple[str, ...] = ("greeting", "off_topic")
    intent_context_categories: tuple[str, ...] = (
        "course_inquiry",
        "price_inquiry",
        "objection",
    )
    safety_max_review_count: int = 3
    knowledge_sufficient_values: tuple[str, ...] = (
        "sufficient",
        "enough",
        "true",
        "yes",
        "充足",
    )
    knowledge_insufficient_values: tuple[str, ...] = (
        "insufficient",
        "not_enough",
        "false",
        "no",
        "不足",
    )


def _tuple_setting(
    data: dict[str, Any],
    key: str,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    value = data.get(key)
    if value is None:
        return default
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list | tuple):
        raise TypeError(f"{key} 必须是字符串数组")
    return tuple(str(item).strip() for item in value if str(item).strip())


def _int_setting(data: dict[str, Any], key: str, default: int) -> int:
    value = data.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{key} 必须是整数") from exc


def load_routing_rules(path: Path | None = None) -> RoutingRules:
    """读取可手动维护的确定性路由规则。

    优先读取本地私有配置 ``data/business/routing_rules.json``；
    如果不存在，则读取可提交的示例配置 ``routing_rules.example.json``；
    示例也不存在时回退到代码默认值，保证测试和最小运行不被阻断。
    """
    defaults = RoutingRules()
    config_path = path
    if config_path is None:
        config_path = ROUTING_RULES_PATH if ROUTING_RULES_PATH.exists() else ROUTING_RULES_EXAMPLE_PATH
    if not config_path.exists():
        return defaults

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"读取路由规则配置失败：{config_path}") from exc

    if not isinstance(raw, dict):
        raise RuntimeError(f"路由规则配置必须是 JSON 对象：{config_path}")
    data = raw.get("routing_rules", raw)
    if not isinstance(data, dict):
        raise RuntimeError(f"routing_rules 必须是 JSON 对象：{config_path}")

    return RoutingRules(
        strong_handover_keywords=_tuple_setting(
            data,
            "strong_handover_keywords",
            defaults.strong_handover_keywords,
        ),
        extreme_emotion_keywords=_tuple_setting(
            data,
            "extreme_emotion_keywords",
            defaults.extreme_emotion_keywords,
        ),
        knowledge_keywords=_tuple_setting(
            data,
            "knowledge_keywords",
            defaults.knowledge_keywords,
        ),
        profile_update_keywords=_tuple_setting(
            data,
            "profile_update_keywords",
            defaults.profile_update_keywords,
        ),
        small_talk_keywords=_tuple_setting(
            data,
            "small_talk_keywords",
            defaults.small_talk_keywords,
        ),
        small_talk_max_chars=_int_setting(
            data,
            "small_talk_max_chars",
            defaults.small_talk_max_chars,
        ),
        intent_handover_categories=_tuple_setting(
            data,
            "intent_handover_categories",
            defaults.intent_handover_categories,
        ),
        intent_handover_purchase_intents=_tuple_setting(
            data,
            "intent_handover_purchase_intents",
            defaults.intent_handover_purchase_intents,
        ),
        intent_handover_emotions=_tuple_setting(
            data,
            "intent_handover_emotions",
            defaults.intent_handover_emotions,
        ),
        intent_direct_reply_categories=_tuple_setting(
            data,
            "intent_direct_reply_categories",
            defaults.intent_direct_reply_categories,
        ),
        intent_context_categories=_tuple_setting(
            data,
            "intent_context_categories",
            defaults.intent_context_categories,
        ),
        safety_max_review_count=_int_setting(
            data,
            "safety_max_review_count",
            defaults.safety_max_review_count,
        ),
        knowledge_sufficient_values=_tuple_setting(
            data,
            "knowledge_sufficient_values",
            defaults.knowledge_sufficient_values,
        ),
        knowledge_insufficient_values=_tuple_setting(
            data,
            "knowledge_insufficient_values",
            defaults.knowledge_insufficient_values,
        ),
    )


@lru_cache
def get_routing_rules() -> RoutingRules:
    return load_routing_rules()


DEFAULT_ROUTING_RULES = get_routing_rules()


def normalize_text(value: str) -> str:
    """转小写并移除空白，避免关键词被空格或换行拆开后无法命中。"""
    return "".join(str(value or "").lower().split())


def contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    """检查文本是否包含任一关键词。"""
    return any(keyword.lower() in text for keyword in keywords)


def has_strong_handover_keyword(
    message: str,
    rules: RoutingRules = DEFAULT_ROUTING_RULES,
) -> bool:
    return contains_any(normalize_text(message), rules.strong_handover_keywords)


def has_extreme_emotion_keyword(
    message: str,
    rules: RoutingRules = DEFAULT_ROUTING_RULES,
) -> bool:
    return contains_any(normalize_text(message), rules.extreme_emotion_keywords)


def looks_like_knowledge_request(
    message: str,
    rules: RoutingRules = DEFAULT_ROUTING_RULES,
) -> bool:
    return contains_any(normalize_text(message), rules.knowledge_keywords)


def has_profile_signal(
    message: str,
    rules: RoutingRules = DEFAULT_ROUTING_RULES,
) -> bool:
    return contains_any(normalize_text(message), rules.profile_update_keywords)


def is_small_talk(
    message: str,
    rules: RoutingRules = DEFAULT_ROUTING_RULES,
) -> bool:
    text = normalize_text(message)
    if len(text) > rules.small_talk_max_chars:
        return False
    return contains_any(text, rules.small_talk_keywords)


def intent_should_handover(
    intent: dict[str, Any],
    rules: RoutingRules = DEFAULT_ROUTING_RULES,
) -> bool:
    category = str(intent.get("intent_category") or "").lower()
    purchase_intent = str(intent.get("purchase_intent") or "").lower()
    emotion = str(intent.get("emotion") or "").lower()
    return (
        bool(intent.get("should_transfer"))
        or category in rules.intent_handover_categories
        or purchase_intent in rules.intent_handover_purchase_intents
        or emotion in rules.intent_handover_emotions
    )


def intent_should_direct_reply(
    intent: dict[str, Any],
    rules: RoutingRules = DEFAULT_ROUTING_RULES,
) -> bool:
    category = str(intent.get("intent_category") or "").lower()
    return category in rules.intent_direct_reply_categories


def intent_needs_context(
    intent: dict[str, Any],
    rules: RoutingRules = DEFAULT_ROUTING_RULES,
) -> bool:
    category = str(intent.get("intent_category") or "").lower()
    return category in rules.intent_context_categories


def safety_retry_exceeded(
    retry_count: int,
    rules: RoutingRules = DEFAULT_ROUTING_RULES,
) -> bool:
    return retry_count >= rules.safety_max_review_count


def explicit_knowledge_sufficiency(
    value: Any,
    rules: RoutingRules = DEFAULT_ROUTING_RULES,
) -> bool | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in rules.knowledge_sufficient_values:
            return True
        if normalized in rules.knowledge_insufficient_values:
            return False
    return bool(value)
