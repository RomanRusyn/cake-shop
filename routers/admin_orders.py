from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from dependencies import SessionDep
from models import Order
from schemas import OrderRead
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