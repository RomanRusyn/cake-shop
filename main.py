from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import engine, get_session
from models import Cake
from schemas import CakeCreate, CakeRead


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    engine.dispose()


app = FastAPI(title="Cake Shop", lifespan=lifespan)

SessionDep = Annotated[Session, Depends(get_session)]


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/cakes", response_model=list[CakeRead])
def list_cakes(session: SessionDep):
    statement = select(Cake).where(Cake.is_available.is_(True)).order_by(Cake.id)
    return session.scalars(statement).all()


@app.get("/cakes/{cake_id}", response_model=CakeRead)
def get_cake(cake_id: int, session: SessionDep):
    cake = session.get(Cake, cake_id)

    if cake is None or not cake.is_available:
        raise HTTPException(status_code=404, detail="Cake not found")

    return cake


@app.post("/cakes", response_model=CakeRead, status_code=201)
def create_cake(cake_data: CakeCreate, session: SessionDep):
    cake = Cake(**cake_data.model_dump())

    session.add(cake)
    session.commit()
    session.refresh(cake)

    return cake

@app.put("/cakes/{cake_id}", response_model=CakeRead)
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