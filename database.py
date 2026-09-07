from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

DATABASE_PATH = Path(__file__).resolve().parent / "cake_shop.db"

engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    connect_args={"check_same_thread": False},
)


class Base(DeclarativeBase):
    pass


def get_session():
    with Session(engine) as session:
        yield session