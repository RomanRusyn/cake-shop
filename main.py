from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Cake Shop")


class Cake(BaseModel):
    id: int
    name: str
    description: str
    price_kopiyky: int = Field(gt=0)
    weight_grams: int = Field(gt=0)


cakes = [
    Cake(
        id=1,
        name="Штрудель вишневий",
        description="Штрудель із вишневою начинкою",
        price_kopiyky=120000,
        weight_grams=1500,
    ),
    Cake(
        id=2,
        name="Баник горіховий",
        description="Дріждьове тісто з горіховою начинкою",
        price_kopiyky=95000,
        weight_grams=1200,
    ),Cake(
        id=3,
        name="Штрудель горіхово-маковий",
        description="Штрудель із горіховою та маковою начинкою 50/50",
        price_kopiyky=95000,
        weight_grams=1200,
    ),
]


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/cakes")
def list_cakes() -> list[Cake]:
    return cakes


@app.get("/cakes/{cake_id}")
def get_cake(cake_id: int) -> Cake:
    for cake in cakes:
        if cake.id == cake_id:
            return cake

    raise HTTPException(status_code=404, detail="Cake not found")