from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from dependencies import SessionDep
from models import Order
from order_status import ALLOWED_TRANSITIONS, OrderStatus
from schemas import OrderRead, OrderStatusUpdate
from security import require_admin


router = APIRouter(
    prefix="/admin/orders",
    tags=["Admin orders"],
    dependencies=[Depends(require_admin)],
)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, session: SessionDep):
    statement = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
    )
    order = session.scalars(statement).one_or_none()

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderRead.model_validate(order)


@router.get("", response_model=list[OrderRead])
def list_orders(
    session: SessionDep,
    status: OrderStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.id.desc())
    )

    if status is not None:
        statement = statement.where(Order.status == status.value)

    statement = statement.limit(limit).offset(offset)
    orders = session.scalars(statement).all()

    return [OrderRead.model_validate(order) for order in orders]


@router.patch("/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    session: SessionDep,
):
    order = session.get(Order, order_id)

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    current_status = OrderStatus(order.status)
    requested_status = status_data.status

    if requested_status == current_status:
        return OrderRead.model_validate(order)

    if requested_status not in ALLOWED_TRANSITIONS[current_status]:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot change status from {current_status.value} "
                f"to {requested_status.value}"
            ),
        )

    statement = (
        update(Order)
        .where(
            Order.id == order_id,
            Order.status == current_status.value,
        )
        .values(status=requested_status.value)
        .execution_options(synchronize_session=False)
    )
    result = session.execute(statement)

    if result.rowcount != 1:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Order changed during this request; reload and try again",
        )

    session.commit()
    session.refresh(order)

    return OrderRead.model_validate(order)