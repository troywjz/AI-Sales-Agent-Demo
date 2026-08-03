from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base


settings = get_settings()
database_url = settings.database_url
if not database_url.startswith("postgresql+"):
    raise RuntimeError("Windows Demo 继续使用 PostgreSQL，请检查 DATABASE_URL。")

engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@event.listens_for(engine, "connect")
def _configure_postgres_connection(dbapi_connection, _connection_record) -> None:
    """统一按北京时间展示 PostgreSQL 的时区字段。"""
    cursor = dbapi_connection.cursor()
    cursor.execute("SET TIME ZONE 'Asia/Shanghai'")
    cursor.close()


def init_db() -> None:
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
