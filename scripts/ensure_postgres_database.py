from __future__ import annotations

import re

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings


def ensure_postgres_database() -> None:
    """确保演示数据库存在，但绝不自动创建非 Demo 名称的数据库。"""
    database_url = make_url(get_settings().database_url)
    if database_url.get_backend_name() != "postgresql":
        raise RuntimeError("Windows Demo 仅支持 PostgreSQL。")

    database_name = database_url.database or ""
    if not database_name:
        raise RuntimeError("DATABASE_URL 缺少 PostgreSQL 数据库名。")

    target_engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with target_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print(f"PostgreSQL database is ready: {database_name}")
        return
    except OperationalError:
        pass
    finally:
        target_engine.dispose()

    if "demo" not in database_name.lower():
        raise RuntimeError(
            "目标 PostgreSQL 数据库不存在；仅允许自动创建名称包含 demo 的演示库。"
        )
    if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        raise RuntimeError("演示数据库名只能包含字母、数字和下划线。")

    admin_url = database_url.set(database="postgres")
    admin_engine = create_engine(
        admin_url,
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
    )
    try:
        with admin_engine.connect() as connection:
            exists = connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": database_name},
            )
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    finally:
        admin_engine.dispose()

    print(f"PostgreSQL demo database is ready: {database_name}")


if __name__ == "__main__":
    ensure_postgres_database()
