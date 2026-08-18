#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
ENV_FILE="$PROJECT_ROOT/.env"
RUNTIME_DIR="$PROJECT_ROOT/logs/ops"
PID_FILE="$RUNTIME_DIR/sales-agent.pid"
LOG_FILE="$RUNTIME_DIR/sales-agent.log"

die() {
    printf '启动失败：%s\n' "$1" >&2
    exit 1
}

read_env_value() {
    local key="$1"
    awk -F= -v key="$key" '
        $0 ~ "^" key "=" {
            value = substr($0, index($0, "=") + 1)
            gsub(/^"|"$/, "", value)
            print value
            exit
        }
    ' "$ENV_FILE"
}

cd "$PROJECT_ROOT"
[[ -f "$ENV_FILE" ]] || die "缺少 .env，请先运行 bash ops/deploy.sh。"
[[ -x "$VENV_PYTHON" ]] || die "缺少 .venv，请先运行 bash ops/deploy.sh。"
command -v curl >/dev/null 2>&1 || die "启动健康检查需要 curl。"

APP_PORT="$(read_env_value APP_PORT)"
APP_PORT="${APP_PORT:-8000}"
[[ "$APP_PORT" =~ ^[0-9]+$ ]] || die ".env 中的 APP_PORT 不是有效端口。"

mkdir -p "$RUNTIME_DIR"

if [[ -f "$PID_FILE" ]]; then
    existing_pid="$(cat "$PID_FILE")"
    if [[ "$existing_pid" =~ ^[0-9]+$ ]] && kill -0 "$existing_pid" 2>/dev/null; then
        existing_command="$(ps -p "$existing_pid" -o args= 2>/dev/null || true)"
        if [[ "$existing_command" == *"$PROJECT_ROOT"* && "$existing_command" == *"-m app.main"* ]]; then
            printf 'Sales Agent 已在运行，PID=%s，端口=%s。\n' "$existing_pid" "$APP_PORT"
            exit 0
        fi
    fi
    rm -f "$PID_FILE"
fi

printf '正在启动 Sales Agent ...\n'
(
    cd "$PROJECT_ROOT"
    export PYTHONUTF8=1
    export PYTHONIOENCODING=utf-8
    exec "$VENV_PYTHON" -X utf8 -m app.main
) >>"$LOG_FILE" 2>&1 &
app_pid=$!
printf '%s\n' "$app_pid" >"$PID_FILE"

for _ in $(seq 1 90); do
    if ! kill -0 "$app_pid" 2>/dev/null; then
        tail -n 60 "$LOG_FILE" >&2 || true
        rm -f "$PID_FILE"
        die "进程已退出，请查看 $LOG_FILE。"
    fi
    if curl --silent --show-error --fail --max-time 3 "http://127.0.0.1:$APP_PORT/health" >/dev/null 2>&1; then
        printf 'Sales Agent 已启动，PID=%s，端口=%s。\n' "$app_pid" "$APP_PORT"
        printf '日志：%s\n' "$LOG_FILE"
        exit 0
    fi
    sleep 1
done

tail -n 60 "$LOG_FILE" >&2 || true
die "健康检查在 90 秒内未通过，请查看 $LOG_FILE。"
