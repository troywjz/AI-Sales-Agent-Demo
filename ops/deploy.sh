#!/usr/bin/env bash
set -Eeuo pipefail

# 统一解析项目根目录，保证从任意当前目录执行都使用本项目的文件。
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
VENV_DIR="$PROJECT_ROOT/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
ENV_FILE="$PROJECT_ROOT/.env"

die() {
    printf '部署失败：%s\n' "$1" >&2
    exit 1
}

cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || die "未找到 $PYTHON_BIN，请先安装 Python 3.11 或更高版本。"
"$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' \
    || die "Python 版本必须为 3.11 或更高版本。"

if [[ ! -x "$VENV_PYTHON" ]]; then
    printf '[1/7] 创建 Python 虚拟环境 ...\n'
    "$PYTHON_BIN" -m venv "$VENV_DIR" \
        || die "创建 Python 虚拟环境失败。"
fi

if [[ ! -f "$ENV_FILE" ]]; then
    cp "$PROJECT_ROOT/.env.example" "$ENV_FILE" \
        || die "无法从 .env.example 创建 .env。"
    printf '\n已创建 .env，请先填写数据库和模型配置，再重新运行本脚本。\n'
    printf '配置文件：%s\n' "$ENV_FILE"
    exit 2
fi

printf '[2/7] 安装 Python 依赖 ...\n'
"$VENV_PYTHON" -m pip install --disable-pip-version-check --upgrade pip \
    || die "pip 升级失败。"
"$VENV_PYTHON" -m pip install --disable-pip-version-check -r requirements.txt \
    || die "Python 依赖安装失败。"

printf '[3/7] 校验 Python 依赖 ...\n'
"$VENV_PYTHON" -m pip check \
    || die "Python 依赖一致性检查失败。"

printf '[4/7] 创建或确认 PostgreSQL 数据库 ...\n'
"$VENV_PYTHON" -X utf8 -m scripts.ensure_postgres_database \
    || die "PostgreSQL 数据库创建或连接失败，请检查 DATABASE_URL 和账号权限。"

printf '[5/7] 初始化 PostgreSQL 数据表 ...\n'
"$VENV_PYTHON" -X utf8 -c \
    'from app.db import init_db; init_db(); print("PostgreSQL schema is ready.")' \
    || die "PostgreSQL 连接或数据表初始化失败，请检查 .env 中的 DATABASE_URL。"

printf '[6/7] 按配置导入知识库和演示数据 ...\n'
demo_seed_enabled="$("$VENV_PYTHON" -X utf8 -c 'from app.core.config import get_settings; print("1" if get_settings().demo_seed_data else "0")')"
if [[ "$demo_seed_enabled" == "1" ]]; then
    "$VENV_PYTHON" -X utf8 -c \
        'from app.demo_data import seed_demo_environment; seed_demo_environment(); print("Demo data is ready.")' \
        || die "演示数据初始化失败；生产数据库请将 DEMO_SEED_DATA=false。"
fi

knowledge_auto_import="$("$VENV_PYTHON" -X utf8 -c 'from app.core.config import get_settings; print("1" if get_settings().knowledge_auto_import else "0")')"
if [[ "$knowledge_auto_import" == "1" ]]; then
    "$VENV_PYTHON" -X utf8 -c \
        'from app.knowledge.importer import import_knowledge_sources; print(import_knowledge_sources())' \
        || die "知识库导入失败，请检查 data/knowledge 和 data/safety_rules。"
fi

mkdir -p "$PROJECT_ROOT/logs/ops"
printf '[7/7] 部署初始化完成。\n'
printf '下一步启动：bash ops/start.sh\n'
printf '停止服务：bash ops/stop.sh\n'
