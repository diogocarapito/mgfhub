"""Página inicial: texto introdutório sobre a ferramenta."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app import auth
from app.templating import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"utilizador": auth.utilizador_atual(request)},
    )
