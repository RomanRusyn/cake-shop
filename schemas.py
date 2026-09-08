from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
)

from order_status import OrderStatus

class CakeCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=250)
    description: str = Field(max_length=3000)
    price_kopiyky: int = Field(gt=0)
    weight_grams: int = Field(gt=0)
    is_available: bool = True
    internal_notes: str | None = None


class CakeRead(CakeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int

class OrderItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cake_id: int = Field(gt=0, strict=True)
    quantity: int = Field(gt=0, le=20, strict=True)


class OrderCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    customer_name: str = Field(min_length=1, max_length=150)
    customer_phone: str = Field(pattern=r"^\+380[0-9]{9}$")
    requested_date: date
    customer_note: str | None = Field(default=None, max_length=2000)
    items: list[OrderItemCreate] = Field(min_length=1, max_length=20)

    @field_validator("requested_date")
    @classmethod
    def validate_requested_date(cls, value: date) -> date:
        today = datetime.now(ZoneInfo("Europe/Kyiv")).date()

        if value <= today:
            raise ValueError("Requested date must be after today")

        return value

    @field_validator("items")
    @classmethod
    def validate_unique_cakes(
        cls,
        value: list[OrderItemCreate],
    ) -> list[OrderItemCreate]:
        cake_ids = [item.cake_id for item in value]

        if len(cake_ids) != len(set(cake_ids)):
            raise ValueError(
                "Each cake must appear once; use quantity for multiples"
            )

        return value


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cake_id: int
    cake_name: str
    unit_price_kopiyky: int
    weight_grams: int
    quantity: int

    @computed_field
    @property
    def subtotal_kopiyky(self) -> int:
        return self.unit_price_kopiyky * self.quantity


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    customer_phone: str
    requested_date: date
    customer_note: str | None
    status: OrderStatus
    created_at: datetime
    items: list[OrderItemRead]

    @field_validator("created_at")
    @classmethod
    def normalize_created_at(cls, value: datetime) -> datetime:
        # Our SQLite CURRENT_TIMESTAMP values are stored in UTC.
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    @computed_field
    @property
    def total_kopiyky(self) -> int:
        return sum(item.subtotal_kopiyky for item in self.items)


class OrderStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: OrderStatus