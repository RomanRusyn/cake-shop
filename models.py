from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Cake(Base):
    __tablename__ = "cakes"

    __table_args__ = (
        CheckConstraint("price_kopiyky > 0"),
        CheckConstraint("weight_grams > 0"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str]
    price_kopiyky: Mapped[int]
    weight_grams: Mapped[int]