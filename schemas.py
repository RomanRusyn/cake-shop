from pydantic import BaseModel, ConfigDict, Field


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