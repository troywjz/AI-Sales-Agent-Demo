# Sales Agent Demo

一个可直接在 Windows Python 环境运行的 AI 销售智能体演示项目。项目通过多 Agent 协作完成客户意图识别、SOP 推进、知识匹配、销售案例 RAG、回复生成、风控审核与客户记忆更新，并提供销售端、客户模拟端和管理员效果大屏。数据库使用 PostgreSQL。

## 快速启动

环境要求：Windows 10/11、Python 3.11 或更高版本，以及可通过 `127.0.0.1:5432` 访问的 PostgreSQL。PostgreSQL 可以运行在 Docker Desktop 中，FastAPI 服务本身直接运行在 Windows Python 环境。

首次使用时复制配置并填写 PostgreSQL 密码：

```powershell
Copy-Item .env.example .env
notepad .env
```

Windows Demo 始终只连接独立的 `sales_agent_demo` 数据库，不要把 `DATABASE_URL` 指向 Linux 项目的 `sales_agent`。数据库不会脱离 Docker 运行：可只启动 Docker Desktop 中的 PostgreSQL，再在 Windows Python 中运行 FastAPI。`DATABASE_CONNECT_TIMEOUT_SECONDS` 同时控制正式服务、启动脚本与评估回放的数据库首次连接等待，默认 5 秒。

双击根目录的 `start_demo.cmd`，或在 PowerShell 中运行：

```powershell
.\start_demo.cmd
```

首次启动会自动创建 `.venv`、安装依赖，并在目标库为 `sales_agent_demo` 时创建 PostgreSQL 演示库、数据表和公开样例数据。数据库账号需要具有建库权限；无建库权限时请先由管理员创建 `.env` 中指定的数据库。看到访问地址后，在浏览器打开：

- 销售端：<http://127.0.0.1:8000/sales>
- 客户模拟端：<http://127.0.0.1:8000/customer>
- 管理员端：<http://127.0.0.1:8000/admin>

演示账号：

| 入口 | 账号 | 密码 |
| --- | --- | --- |
| 销售端 | `wangjie@salesagent.com` | `123456` |
| 管理员端 | `admin` | `admin123` |

按 `Ctrl+C` 停止服务。

## CloudStudio / Ubuntu 云服务器快速运维

云服务器使用 `ops/` 下的三个 Bash 脚本完成部署、启动和停止；脚本均从项目根目录解析路径，可以在 CloudStudio 终端或阿里云 Ubuntu 中执行：

```bash
bash ops/deploy.sh
bash ops/start.sh
bash ops/stop.sh
```

首次运行 `deploy.sh` 会创建 `.venv`、安装 `requirements.txt`、从 `.env.example` 创建本地 `.env`（不会覆盖已有 `.env`），创建或确认 `.env` 中指定的 PostgreSQL 数据库，初始化表结构，并按 `DEMO_SEED_DATA`、`KNOWLEDGE_AUTO_IMPORT` 开关导入演示数据和知识库。数据库账号需要具备连接维护库和 `CREATEDB` 权限；没有权限时请先手动建库。启动后的 PID 和日志保存在 `logs/ops/`，停止服务只处理由 `ops/start.sh` 启动且路径匹配当前项目的进程，数据库和日志会保留。

云端部署前请在 `.env` 中填写 PostgreSQL 连接串、模型 API Key，并按环境设置 `APP_HOST`、`APP_PORT`、`DEMO_SEED_DATA`。部署账号需要能够连接 PostgreSQL 的 `postgres` 维护库并具备 `CREATEDB` 权限；如果使用托管 PostgreSQL、账号没有建库权限，请先手动创建 `.env` 中指定的数据库。`DEMO_SEED_DATA=true` 只适用于 `sales_agent_demo` 演示库，生产库应设置为 `false`。

## 推荐演示流程

1. 打开管理员端，查看会话趋势、SOP 转化漏斗、Agent 表现和销售案例 RAG 效果。
2. 打开客户端，新建一个客户会话并发送“我是零基础，担心跟不上，想提升办公效率”。
3. 同时打开销售端，观察多 Agent 节点状态、自动回复、客户画像和 SOP 阶段实时更新。
4. 在销售端切换人工接管，或创建一条定时发送任务，展示人机协作与运营能力。

## 核心能力

- LangGraph 多 Agent 编排与并行上下文检索
- 基于客户意图和画像的 SOP 阶段推进
- SKU、FAQ、SOP 本地知识库匹配
- 可选向量安全审核与销售案例 RAG；没有向量数据时自动跳过增强层
- 回复风控、转人工和客户长期记忆
- 销售端、客户模拟端、管理员效果大屏
- WebSocket 实时同步、定时发送与自动跟进
- PostgreSQL 持久化和真实模型优先、无真实配置时自动回落的 Demo 模型

## 演示数据

仓库只包含明确标注的通用演示夹具。它们只用于功能演示，不来自历史聊天，也不能作为效果评估证据。默认 `DEMO_SEED_DATA=true`，首次启动会自动把这些数据写入独立的 `sales_agent_demo` PostgreSQL 数据库。

销售案例 RAG 使用 PostgreSQL `sales_rag_chunks` 中的案例向量。公开示例会导入结构化的 `sales_cases.example.csv`，但默认 `SALES_RAG_ENABLED=false`，因此不会调用 Embedding 或执行案例检索；写入来源明确且获授权的 `data/knowledge/sales_cases.csv`、建立向量并开启开关后才会检索。它不读取真实聊天记录，也不读取 `data/chat`；`data/knowledge/*.example.csv` 仅用于公开的通用知识示例。

需要手动补齐或重复检查演示数据时，运行：

```powershell
.\scripts\seed_demo_data.ps1
```

程序会拒绝向任何不是 `sales_agent_demo` 的数据库写入演示数据，避免连接或污染 Linux 生产库。

## 模型与向量配置

默认优先尝试真实模型配置；如果所有真实供应商都缺少 API Key 或模型名，则自动使用本地 Demo 模型。编辑本地 `.env` 填写任意一组真实供应商配置：

```dotenv
DEMO_MODE=false
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的密钥
DEEPSEEK_MODEL=你的模型名
```

重新启动项目后生效。`.env` 已被 Git 忽略，请勿提交密钥。

安全向量审核和销售案例 RAG 都是可选增强层。它们只有在对应开关打开且 `knowledge_safety_rules` 或 `sales_rag_chunks` 存在向量数据时才会调用 Embedding；没有向量数据时，安全审核只使用 `SafetyAgent`，销售案例 RAG 不返回案例。

## 生产链路评估回放

`evaluation/` 使用当前 `.env` 的模型与运行配置，直接复用正式 `SalesGraphService` 回放脱敏对话轮次。它不启动前端，也不将会话或运行记录写入数据库；知识、SOP、风控和销售案例只读取 `evaluation/knowledge_snapshot/`，与正式 `data/` 和正式数据库隔离。结果写入本地 UTF-8 CSV。数据契约、评分方法和边界见 [evaluation/docs/README.md](evaluation/docs/README.md)。

## 项目结构

```text
app/        FastAPI、LangGraph、Agent、数据库和演示数据
data/       可公开的演示业务与知识样例
evaluation/ 并发评测入口、盲评计分工具和说明；本地数据集与运行结果不进入 Git
prompts/    各 Agent 的 UTF-8 提示词
scripts/    Windows 初始化、启动和演示数据脚本
tests/      核心流程测试
web/        销售端、客户模拟端和管理员端
```

项目文件统一使用 UTF-8。该目录是 Windows Python 功能演示版，不依赖 Redis 或企业微信；PostgreSQL 作为唯一数据库继续保留。

## 开源许可

本项目代码采用 [GNU Affero General Public License v3.0](LICENSE)（AGPL-3.0）开源。

- 可以自由使用、修改和分发本项目代码，但基于本项目的衍生作品——包括以 SaaS 或托管形式对外提供服务——必须同样以 AGPL-3.0 开源。
- 项目名称及相关商标归作者所有，未经书面授权不得用于商业宣传。
- 业务数据不包含在开源范围内：`data/` 与 `evaluation/private_datasets/` 中的真实业务数据、评测对话数据仅供本地演示参考，不授予任何使用许可。
