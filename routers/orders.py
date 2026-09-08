from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from dependencies import SessionDep
from models import Cake, Order, OrderItem
from schemas import OrderCreate, OrderRead


router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderRead, status_code=201)
def create_order(order_data: OrderCreate, session: SessionDep):
    cake_ids = [item.cake_id for item in order_data.items]

    statement = select(Cake).where(
        Cake.id.in_(cake_ids),
        Cake.is_available.is_(True),
    )
    cakes = session.scalars(statement).all()
    cakes_by_id = {cake.id: cake for cake in cakes}

    # Reject the whole request before saving anything.
    for requested_item in order_data.items:
        if requested_item.cake_id not in cakes_by_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cake {requested_item.cake_id} "
                    "does not exist or is unavailable"
                ),
            )

    order = Order(
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        requested_date=order_data.requested_date,
        customer_note=order_data.customer_note,
        status="new",
    )

    for requested_item in order_data.items:
        cake = cakes_by_id[requested_item.cake_id]

        order.items.append(
            OrderItem(
                cake_id=cake.id,
                cake_name=cake.name,
                unit_price_kopiyky=cake.price_kopiyky,
                weight_grams=cake.weight_grams,
                quantity=requested_item.quantity,
            )
        )

    session.add(order)
    session.commit()
    session.refresh(order)

    return OrderRead.model_validate(order)