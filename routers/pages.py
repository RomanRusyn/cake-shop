from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from dependencies import SessionDep
from models import Cake


PROJECT_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(PROJECT_DIR / "templates"),
)

router = APIRouter(tags=["Pages"])


def format_uah(kopiyky: int) -> str:
    hryvnias, remainder = divmod(kopiyky, 100)
    whole = f"{hryvnias:,}".replace(",", " ")
    return f"{whole},{remainder:02d} ₴"


templates.env.filters["uah"] = format_uah


@router.get("/", response_class=HTMLResponse, name="catalogue_page")
def catalogue_page(request: Request, session: SessionDep):
    statement = (
        select(Cake)
        .where(Cake.is_available.is_(True))
        .order_by(Cake.id)
    )
    cakes = session.scalars(statement).all()

    return templates.TemplateResponse(
        request=request,
        name="catalogue.html",
        context={"cakes": cakes},
    )


@router.get(
    "/catalogue/{cake_id}",
    response_class=HTMLResponse,
    name="cake_detail_page",
)
def cake_detail_page(
    cake_id: int,
    request: Request,
    session: SessionDep,
):
    cake = session.get(Cake, cake_id)

    if cake is None or not cake.is_available:
        return templates.TemplateResponse(
            request=request,
            name="not_found.html",
            context={},
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name="cake_detail.html",
        context={"cake": cake},
    )