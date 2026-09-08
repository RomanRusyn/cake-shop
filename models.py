from datetime import date, datetime
from sqlalchemy import CheckConstraint, ForeignKey, func, text, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    is_available: Mapped[bool] = mapped_column(
        default=True,
        server_default=text("1"),
    )
    internal_notes: Mapped[str | None] = mapped_column(Text)


class Order(Base):
    __tablename__ = "orders"

    __table_args__ = (
        CheckConstraint(
            "status IN "
            "('new', 'confirmed', 'in_preparation', "
            "'ready', 'completed', 'cancelled')",
            name="ck_orders_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str]
    customer_phone: Mapped[str]
    requested_date: Mapped[date]
    customer_note: Mapped[str | None]

    status: Mapped[str] = mapped_column(
        default="new",
        server_default="new",
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.current_timestamp(),
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        order_by="OrderItem.id",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity"),
        CheckConstraint(
            "unit_price_kopiyky > 0",
            name="ck_order_items_price",
        ),
        CheckConstraint(
            "weight_grams > 0",
            name="ck_order_items_weight",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        index=True,
    )
    cake_id: Mapped[int] = mapped_column(
        ForeignKey("cakes.id"),
        index=True,
    )

    cake_name: Mapped[str]
    unit_price_kopiyky: Mapped[int]
    weight_grams: Mapped[int]
    quantity: Mapped[int]

    order: Mapped["Order"] = relationship(back_populates="items")