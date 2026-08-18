#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
RUNTIME_DIR="$PROJECT_ROOT/logs/ops"
PID_FILE="$RUNTIME_DIR/sales-agent.pid"

printf '正在停止 Sales Agent ...\n'

app_pid=""
if [[ -f "$PID_FILE" ]]; then
    candidate="$(cat "$PID_FILE")"
    if [[ "$candidate" =~ ^[0-9]+$ ]] && kill -0 "$candidate" 2>/dev/null; then
        command_line="$(ps -p "$candidate" -o args= 2>/dev/null || true)"
        if [[ "$command_line" == *"$PROJECT_ROOT"* && "$command_line" == *"-m app.main"* ]]; then
            app_pid="$candidate"
        fi
    fi
fi

if [[ -z "$app_pid" ]]; then
    rm -f "$PID_FILE"
    printf 'Sales Agent 当前没有由本脚本管理的运行进程。\n'
    exit 0
fi

kill -TERM "$app_pid" 2>/dev/null || true
for _ in $(seq 1 30); do
    if ! kill -0 "$app_pid" 2>/dev/null; then
        rm -f "$PID_FILE"
        printf 'Sales Agent 已停止，数据库和日志均已保留。\n'
        exit 0
    fi
    sleep 1
done

printf '进程未在 30 秒内退出，发送强制终止信号。\n' >&2
kill -KILL "$app_pid" 2>/dev/null || true
rm -f "$PID_FILE"
printf 'Sales Agent 已停止，数据库和日志均已保留。\n'
