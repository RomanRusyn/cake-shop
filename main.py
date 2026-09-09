from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database import engine
from routers import admin_cakes, admin_orders, cakes, orders, pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    engine.dispose()


app = FastAPI(title="Cake Shop", lifespan=lifespan)

PROJECT_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=str(PROJECT_DIR / "static")),
    name="static",
)

app.include_router(pages.router)
app.include_router(cakes.router)
app.include_router(admin_cakes.router)
app.include_router(orders.router)
app.include_router(admin_orders.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}