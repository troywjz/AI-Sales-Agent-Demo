from __future__ import annotations

import json
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.core.time import beijing_now
from app.core.config import get_settings
from app.db.models import (
    ConversationFollowupJob,
    ConversationSession,
    ConversationSOPState,
    ConversationTurn,
    CustomerRecord,
    LLMCall,
    Message,
    NodeInvocation,
    SalesCaseRAGEvent,
    SalesRAGChunk,
    SalesRAGConversation,
    ScheduledMessageTask,
)
from app.db.session import SessionLocal
from app.repositories import ChatRepository


DEMO_SESSION_PREFIX = "demo-session-"


def seed_demo_environment() -> None:
    """校验目标库后，安全导入公开知识和演示业务数据。"""
    settings = get_settings()
    _assert_demo_database_target(settings)

    from app.knowledge.importer import import_knowledge_sources

    import_knowledge_sources(
        use_example_sources=True,
        include_safety_rules=False,
    )
    ensure_demo_data()


def ensure_demo_data() -> None:
    """幂等写入可公开展示的样例会话、案例和效果指标。"""
    settings = get_settings()
    _assert_demo_database_target(settings)
    with SessionLocal() as db:
        ChatRepository(db).ensure_default_sales_user()
        _seed_sales_cases(db)
        exists = db.scalar(
            select(ConversationSession.session_id).where(
                ConversationSession.session_id == f"{DEMO_SESSION_PREFIX}001"
            )
        )
        if not exists:
            _seed_dashboard_data(db)
        db.commit()


def _assert_demo_database_target(settings) -> None:
    database_name = (make_url(settings.database_url).database or "").lower()
    if "demo" not in database_name and not settings.demo_allow_unsafe_seed:
        raise RuntimeError(
            "拒绝向非 Demo 数据库写入演示数据。请使用名称包含 demo 的独立数据库。"
        )


def _seed_sales_cases(db) -> None:
    if db.get(SalesRAGConversation, "demo-rag-conversation") is None:
        db.add(
            SalesRAGConversation(
                conversation_hash="demo-rag-conversation",
                source_name="公开演示案例",
                source_path="built-in-demo",
                source_sheet="demo",
                raw_conversation_id="demo",
                message_count=8,
                text_message_count=8,
                usable_chunk_count=4,
                quality_score=0.93,
                metadata_json=json.dumps({"license": "demo"}, ensure_ascii=False),
            )
        )

    cases = [
        (
            "demo-rag-001",
            "我是零基础，担心课程太难跟不上。",
            "先不用急着判断难不难，可以从你每天最常用的一个场景开始，先看到一项具体改善。",
            "客户想提升办公效率，但担心学习门槛。",
            ["零基础", "顾虑处理", "单问题推进"],
        ),
        (
            "demo-rag-002",
            "价格有点高，我还要再考虑一下。",
            "预算确实需要认真考虑。先看这个方案能不能解决你现在最耗时间的问题，再决定是否值得投入。",
            "客户认可需求，但对价格敏感。",
            ["价格", "预算", "价值塑造"],
        ),
        (
            "demo-rag-003",
            "最近工作太忙，可能没有时间学。",
            "可以先按你的工作节奏拆成小任务，不需要集中投入。你一周大概能安排几次短时间练习？",
            "客户有兴趣，但担心时间投入。",
            ["时间", "没空", "探需"],
        ),
        (
            "demo-rag-004",
            "这个课程真的适合我的工作吗？",
            "是否适合要看你的实际任务。你最常处理文档、数据，还是沟通协作？先从使用频率最高的场景判断。",
            "客户正在判断课程和自身工作的匹配度。",
            ["适合", "课程", "办公", "场景诊断"],
        ),
    ]
    for index, (chunk_id, customer_text, sales_reply, context_before, tags) in enumerate(cases):
        if db.get(SalesRAGChunk, chunk_id) is not None:
            continue
        db.add(
            SalesRAGChunk(
                chunk_id=chunk_id,
                conversation_hash="demo-rag-conversation",
                chunk_index=index,
                source_name="公开演示案例",
                customer_text=customer_text,
                sales_reply=sales_reply,
                context_before=context_before,
                chunk_text=f"{context_before}\n客户：{customer_text}\n销售：{sales_reply}",
                quality_score=0.93 - index * 0.02,
                tags_json=json.dumps(tags, ensure_ascii=False),
                raw_json="{}",
            )
        )


def _seed_dashboard_data(db) -> None:
    now = beijing_now()
    stages = ["开场", "破冰", "探需扩需A", "探需扩需B", "价值塑造", "方案引导", "报价", "报价", "方案引导", "探需扩需C"]
    customers = [
        ("林晓", "提升日常文档效率", "medium", "零基础，担心跟不上"),
        ("陈思远", "自动整理经营数据", "high", "关注方案价格"),
        ("周宁", "优化团队协作", "medium", "时间安排紧张"),
        ("何然", "减少重复录入", "low", "仍在了解"),
        ("宋琪", "提升汇报效率", "medium", "希望看到实际案例"),
        ("赵峰", "搭建部门工作流", "high", "需要确认交付范围"),
        ("杜悦", "提高表格处理效率", "medium", "预算待确认"),
        ("许宁", "学习 AI 办公方法", "high", "准备报名"),
        ("顾晨", "优化客户沟通", "medium", "对比多个方案"),
        ("唐可", "形成个人自动化流程", "low", "暂无明确时间"),
    ]
    for index, (name, goal, intent, concern) in enumerate(customers, start=1):
        session_id = f"{DEMO_SESSION_PREFIX}{index:03d}"
        customer_id = f"demo-customer-{index:03d}"
        created_at = now - timedelta(hours=index * 7 if index < 4 else index * 14)
        transfer = index == 8
        session = ConversationSession(
            session_id=session_id,
            customer_id=customer_id,
            sales_id="sales-wangjie",
            sales_name="王杰",
            current_stage=stages[index - 1],
            message_count=2 + index % 4,
            transfer_flag=transfer,
            transfer_reason="客户已进入交易确认阶段" if transfer else "",
            history_summary=f"客户希望{goal}，当前顾虑：{concern}。",
            latest_turn_id=f"demo-turn-{index:03d}",
            created_at=created_at,
            updated_at=created_at + timedelta(minutes=18),
        )
        db.add(session)
        db.add(
            CustomerRecord(
                customer_id=customer_id,
                session_id=session_id,
                name=name,
                education="零基础" if index in {1, 4, 7} else "有基础",
                work_status="在职",
                learning_goal=goal,
                budget="待确认" if index % 3 else "2000元以内",
                urgency="近期" if intent == "high" else "一般",
                concerns_json=json.dumps([concern], ensure_ascii=False),
                purchase_intent=intent,
                created_at=created_at,
                updated_at=created_at + timedelta(minutes=18),
            )
        )
        db.add(
            ConversationSOPState(
                session_id=session_id,
                customer_id=customer_id,
                sales_id="sales-wangjie",
                sales_name="王杰",
                current_stage=stages[index - 1],
                followup_count=1 if index in {3, 6} else 0,
                status="handover" if transfer else "active",
                last_customer_message_at=created_at + timedelta(minutes=4),
                last_sales_message_at=created_at + timedelta(minutes=5),
                created_at=created_at,
                updated_at=created_at + timedelta(minutes=18),
            )
        )
        turn_id = f"demo-turn-{index:03d}"
        db.add(
            ConversationTurn(
                turn_id=turn_id,
                session_id=session_id,
                customer_id=customer_id,
                sales_id="sales-wangjie",
                sales_name="王杰",
                turn_index=1,
                trigger_type="customer_message",
                status="sent" if not transfer else "handover",
                input_message_ids_json=json.dumps([f"demo-message-{index:03d}-u"]),
                client_message_ids_json="[]",
                input_text=concern,
                reply_text="我先结合你的实际场景帮你判断，再给出更匹配的建议。" if not transfer else "",
                started_at=created_at + timedelta(minutes=4),
                completed_at=created_at + timedelta(minutes=4, milliseconds=420 + index * 35),
                created_at=created_at + timedelta(minutes=4),
                updated_at=created_at + timedelta(minutes=5),
            )
        )
        db.add(
            Message(
                message_id=f"demo-message-{index:03d}-u",
                session_id=session_id,
                turn_id=turn_id,
                customer_id=customer_id,
                sales_id="sales-wangjie",
                sales_name="王杰",
                role="user",
                sender_type="customer",
                content=concern,
                created_at=created_at + timedelta(minutes=4),
            )
        )
        if not transfer:
            db.add(
                Message(
                    message_id=f"demo-message-{index:03d}-a",
                    session_id=session_id,
                    turn_id=turn_id,
                    customer_id=customer_id,
                    sales_id="sales-wangjie",
                    sales_name="王杰",
                    role="assistant",
                    sender_type="salesagent",
                    content="我先结合你的实际场景帮你判断，再给出更匹配的建议。",
                    created_at=created_at + timedelta(minutes=5),
                )
            )
        _seed_agent_metrics(db, index, session_id, turn_id, created_at)

    db.add(
        ConversationFollowupJob(
            job_id="demo-followup-sent",
            session_id=f"{DEMO_SESSION_PREFIX}003",
            customer_id="demo-customer-003",
            sales_id="sales-wangjie",
            sales_name="王杰",
            stage="探需扩需A",
            status="sent",
            reference_script="你目前更关注投入时间，还是实际使用效果？",
            timeout_action="next",
            scheduled_at=now - timedelta(hours=1),
            sent_message_id="demo-followup-message",
            sent_at=now - timedelta(minutes=55),
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(minutes=55),
        )
    )
    db.add(
        ScheduledMessageTask(
            task_id="demo-scheduled-sent",
            name="演示回访任务",
            status="sent",
            enabled=True,
            scheduled_at=now - timedelta(hours=2),
            target_mode="manual",
            selected_session_ids_json=json.dumps([f"{DEMO_SESSION_PREFIX}001"]),
            message_text="你好，之前提到的办公提效场景还有需要我补充的吗？",
            sent_session_ids_json=json.dumps([f"{DEMO_SESSION_PREFIX}001"]),
            created_by_sales_id="sales-wangjie",
            created_by_sales_name="王杰",
            sent_at=now - timedelta(hours=2),
            created_at=now - timedelta(hours=3),
            updated_at=now - timedelta(hours=2),
        )
    )


def _seed_agent_metrics(db, index: int, session_id: str, turn_id: str, created_at) -> None:
    agents = ("intent_agent", "sop_agent", "knowledge_agent", "sales_case_rag", "conversation_agent", "safety_agent")
    rag_hit = index not in {4, 9}
    for agent_index, agent_name in enumerate(agents, start=1):
        invocation_id = f"demo-invocation-{index:03d}-{agent_index}"
        output: dict[str, object] = {"status": "ok"}
        provider = "demo"
        model = "sales-agent-demo"
        if agent_name == "sales_case_rag":
            provider = "local"
            model = "keyword-rag"
            output = {
                "sales_case_references": (
                    [{"chunk_id": f"demo-rag-00{(index % 4) + 1}", "similarity": 0.62 + index * 0.01}]
                    if rag_hit
                    else []
                )
            }
        db.add(
            NodeInvocation(
                invocation_id=invocation_id,
                session_id=session_id,
                turn_id=turn_id,
                node_name=agent_name,
                model_provider=provider,
                model_name=model,
                elapsed_ms=18 + agent_index * 11 + index,
                success=1,
                input_json=json.dumps({"message": "演示客户消息"}, ensure_ascii=False),
                output_json=json.dumps(output, ensure_ascii=False),
                raw_output=json.dumps(output, ensure_ascii=False),
                created_at=created_at + timedelta(minutes=4, milliseconds=agent_index * 40),
            )
        )
        if agent_name != "sales_case_rag":
            db.add(
                LLMCall(
                    call_id=f"demo-llm-{index:03d}-{agent_index}",
                    session_id=session_id,
                    turn_id=turn_id,
                    node_invocation_id=invocation_id,
                    node_name=agent_name,
                    provider="demo",
                    model_name="sales-agent-demo",
                    api_url="local://demo",
                    protocol="local_demo",
                    attempt_index=1,
                    elapsed_ms=18 + agent_index * 11 + index,
                    success=1,
                    request_json="{}",
                    response_json=json.dumps(output, ensure_ascii=False),
                    usage_json="{}",
                    created_at=created_at + timedelta(minutes=4, milliseconds=agent_index * 40),
                )
            )
    scores = [round(0.62 + index * 0.01, 4)] if rag_hit else []
    db.add(
        SalesCaseRAGEvent(
            event_id=f"demo-rag-event-{index:03d}",
            session_id=session_id,
            turn_id=turn_id,
            enabled=True,
            hit_count=1 if rag_hit else 0,
            used=rag_hit and index % 3 != 0,
            query_text="演示客户消息",
            reference_ids_json=json.dumps([f"demo-rag-00{(index % 4) + 1}"] if rag_hit else []),
            scores_json=json.dumps(scores),
            max_score=max(scores) if scores else 0.0,
            avg_score=sum(scores) / len(scores) if scores else 0.0,
            used_reference_ids_json=json.dumps([f"demo-rag-00{(index % 4) + 1}"] if rag_hit and index % 3 != 0 else []),
            used_strategy="注入回复生成" if rag_hit and index % 3 != 0 else "",
            elapsed_ms=24 + index,
            created_at=created_at + timedelta(minutes=4, milliseconds=180),
        )
    )


if __name__ == "__main__":
    from app.db import init_db

    init_db()
    seed_demo_environment()
    print("Windows Demo 数据已就绪。")
