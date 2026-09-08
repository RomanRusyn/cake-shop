from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from dependencies import SessionDep
from models import Cake
from schemas import CakeCreate, CakeRead
from security import require_admin


router = APIRouter(prefix="/admin/cakes", tags=["Admin cakes"], dependencies=[Depends(require_admin)],)


@router.get("", response_model=list[CakeRead])
def list_cakes(session: SessionDep):
    statement = select(Cake).order_by(Cake.id)
    return session.scalars(statement).all()


@router.get("/{cake_id}", response_model=CakeRead)
def get_cake(cake_id: int, session: SessionDep):
    cake = session.get(Cake, cake_id)

    if cake is None:
        raise HTTPException(status_code=404, detail="Cake not found")

    return cake


@router.post("", response_model=CakeRead, status_code=201)
def create_cake(cake_data: CakeCreate, session: SessionDep):
    cake = Cake(**cake_data.model_dump())

    session.add(cake)
    session.commit()
    session.refresh(cake)

    return cake


@router.put("/{cake_id}", response_model=CakeRead)
def update_cake(
    cake_id: int,
    cake_data: CakeCreate,
    session: SessionDep,
):
    cake = session.get(Cake, cake_id)

    if cake is None:
        raise HTTPException(status_code=404, detail="Cake not found")

    cake.name = cake_data.name
    cake.description = cake_data.description
    cake.price_kopiyky = cake_data.price_kopiyky
    cake.weight_grams = cake_data.weight_grams
    cake.is_available = cake_data.is_available
    cake.internal_notes = cake_data.internal_notes

    session.commit()
    session.refresh(cake)

    return cake