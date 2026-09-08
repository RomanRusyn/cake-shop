from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import engine
from routers import admin_cakes, cakes


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    engine.dispose()


app = FastAPI(title="Cake Shop", lifespan=lifespan)

app.include_router(cakes.router)
app.include_router(admin_cakes.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}