from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from dependencies import SessionDep
from models import Cake
from schemas import CakeRead


router = APIRouter(prefix="/cakes", tags=["Catalogue"])


@router.get("", response_model=list[CakeRead])
def list_cakes(session: SessionDep):
    statement = (
        select(Cake)
        .where(Cake.is_available.is_(True))
        .order_by(Cake.id)
    )
    return session.scalars(statement).all()


@router.get("/{cake_id}", response_model=CakeRead)
def get_cake(cake_id: int, session: SessionDep):
    cake = session.get(Cake, cake_id)

    if cake is None or not cake.is_available:
        raise HTTPException(status_code=404, detail="Cake not found")

    return cake