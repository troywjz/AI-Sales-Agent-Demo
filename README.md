# Sales Agent Demo

一个可直接在 Windows Python 环境运行的 AI 销售智能体演示项目。项目通过多 Agent 协作完成客户意图识别、SOP 推进、知识匹配、销售案例 RAG、回复生成、风控审核与客户记忆更新，并提供销售端、客户模拟端和管理员效果大屏。数据库使用 PostgreSQL。

## 快速启动

环境要求：Windows 10/11、Python 3.11 或更高版本，以及可通过 `127.0.0.1:5432` 访问的 PostgreSQL。PostgreSQL 可以运行在 Docker Desktop 中，FastAPI 服务本身直接运行在 Windows Python 环境。

首次使用时复制配置并填写 PostgreSQL 密码：

```powershell
Copy-Item .env.example .env
notepad .env
```

已有完整项目数据库时，可将 `DATABASE_URL` 指向现有 `sales_agent` 数据库，并保持 `DEMO_SEED_DATA=false`、`KNOWLEDGE_AUTO_IMPORT=false`，避免写入演示数据。

双击根目录的 `start_demo.cmd`，或在 PowerShell 中运行：

```powershell
.\start_demo.cmd
```

首次启动会自动创建 `.venv`、安装依赖，并在目标名称包含 `demo` 时创建 PostgreSQL 演示库、数据表和公开样例数据。数据库账号需要具有建库权限；无建库权限时请先由管理员创建 `.env` 中指定的数据库。看到访问地址后，在浏览器打开：

- 销售端：<http://127.0.0.1:8000/sales>
- 客户模拟端：<http://127.0.0.1:8000/customer>
- 管理员端：<http://127.0.0.1:8000/admin>

演示账号：

| 入口 | 账号 | 密码 |
| --- | --- | --- |
| 销售端 | `wangjie@salesagent.com` | `123456` |
| 管理员端 | `admin` | `admin123` |

按 `Ctrl+C` 停止服务。

## 推荐演示流程

1. 打开管理员端，查看会话趋势、SOP 转化漏斗、Agent 表现和销售案例 RAG 效果。
2. 打开客户端，新建一个客户会话并发送“我是零基础，担心跟不上，想提升办公效率”。
3. 同时打开销售端，观察多 Agent 节点状态、自动回复、客户画像和 SOP 阶段实时更新。
4. 在销售端切换人工接管，或创建一条定时发送任务，展示人机协作与运营能力。

## 核心能力

- LangGraph 多 Agent 编排与并行上下文检索
- 基于客户意图和画像的 SOP 阶段推进
- SKU、FAQ、SOP 本地知识库匹配
- 本地销售案例 RAG 与注入效果统计
- 回复风控、转人工和客户长期记忆
- 销售端、客户模拟端、管理员效果大屏
- WebSocket 实时同步、定时发送与自动跟进
- PostgreSQL 持久化和无密钥本地演示模型

## 演示数据

仓库只包含可公开的通用示例数据。默认 `DEMO_SEED_DATA=true`，首次启动会自动把这些数据写入名称包含 `demo` 的 PostgreSQL 数据库。

销售案例 RAG 使用 `app/demo_data.py` 内置的 4 条通用演示案例，启动时写入 PostgreSQL 的 `sales_rag_chunks` 表，再由本地检索逻辑提供话术参考。它不读取真实聊天记录，也不读取 `data/chat`；`data/knowledge/*.example.*` 仅用于公开的通用知识示例。

需要手动补齐或重复检查演示数据时，运行：

```powershell
.\scripts\seed_demo_data.ps1
```

程序会拒绝向名称不包含 `demo` 的数据库写入演示数据，避免污染现有业务库。

## 接入真实模型

默认 `DEMO_MODE=true`，不调用外部模型，也不需要 API Key。需要体验真实模型时，编辑本地 `.env`：

```dotenv
DEMO_MODE=false
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的密钥
DEEPSEEK_MODEL=你的模型名
```

重新启动项目后生效。`.env` 已被 Git 忽略，请勿提交密钥。

## 项目结构

```text
app/        FastAPI、LangGraph、Agent、数据库和演示数据
data/       可公开的业务、知识库与评估样例
prompts/    各 Agent 的 UTF-8 提示词
scripts/    Windows 初始化、启动和演示数据脚本
tests/      核心流程测试
web/        销售端、客户模拟端和管理员端
```

项目文件统一使用 UTF-8。该目录是 Windows Python 功能演示版，不依赖 Redis 或企业微信；PostgreSQL 作为唯一数据库继续保留。
