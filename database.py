from pathlib import Path
import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session

DATABASE_PATH = Path(__file__).resolve().parent / "cake_shop.db"

@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        previous_autocommit = dbapi_connection.autocommit
        dbapi_connection.autocommit = True

        try:
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()
        finally:
            dbapi_connection.autocommit = previous_autocommit

engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    connect_args={"check_same_thread": False},
)


class Base(DeclarativeBase):
    pass


def get_session():
    with Session(engine) as session:
        yield session