from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, engine, get_session
from models import Cake
from schemas import CakeCreate, CakeRead


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield
    engine.dispose()


app = FastAPI(title="Cake Shop", lifespan=lifespan)

SessionDep = Annotated[Session, Depends(get_session)]


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/cakes", response_model=list[CakeRead])
def list_cakes(session: SessionDep):
    statement = select(Cake).order_by(Cake.id)
    return session.scalars(statement).all()


@app.get("/cakes/{cake_id}", response_model=CakeRead)
def get_cake(cake_id: int, session: SessionDep):
    cake = session.get(Cake, cake_id)

    if cake is None:
        raise HTTPException(status_code=404, detail="Cake not found")

    return cake


@app.post("/cakes", response_model=CakeRead, status_code=201)
def create_cake(cake_data: CakeCreate, session: SessionDep):
    cake = Cake(**cake_data.model_dump())

    session.add(cake)
    session.commit()
    session.refresh(cake)

    return cake