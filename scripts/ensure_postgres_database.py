from __future__ import annotations

import re

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings


def ensure_postgres_database() -> None:
    """确保 .env 指向的 PostgreSQL 数据库存在。

    目标库不存在时，使用同一连接账号连接 PostgreSQL 的 ``postgres``
    维护库并执行创建；因此部署账号需要具备连接维护库和 CREATEDB 权限。
    已存在的数据库不会被覆盖、删除或清空。
    """
    settings = get_settings()
    database_url = make_url(settings.database_url)
    if database_url.get_backend_name() != "postgresql":
        raise RuntimeError("当前服务仅支持 PostgreSQL。")

    database_name = database_url.database or ""
    if not database_name:
        raise RuntimeError("DATABASE_URL 缺少 PostgreSQL 数据库名。")

    connect_args = {"connect_timeout": settings.database_connect_timeout_seconds}
    target_engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    try:
        with target_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print(f"PostgreSQL database is ready: {database_name}")
        return
    except OperationalError:
        pass
    finally:
        target_engine.dispose()

    if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        raise RuntimeError("PostgreSQL 数据库名只能包含字母、数字和下划线。")

    admin_url = database_url.set(database="postgres")
    admin_engine = create_engine(
        admin_url,
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
        connect_args=connect_args,
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

    print(f"PostgreSQL database is ready: {database_name}")


if __name__ == "__main__":
    ensure_postgres_database()
