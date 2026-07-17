"""Página inicial: intro + cartões das ferramentas (de content/cartoes_home.csv)."""

from functools import lru_cache

import pandas as pd
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.templating import templates
from core.reference import DATA_DIR

router = APIRouter()

CONTENT_DIR = DATA_DIR.parent / "content"

# mapeamento das páginas streamlit para as rotas v3 já disponíveis
ROTAS_V3 = {
    "pages/2_Indicadores.py": "/indicadores",
    "pages/3_IDE.py": "/ide",
}


@lru_cache(maxsize=1)
def _cartoes():
    df = pd.read_csv(CONTENT_DIR / "cartoes_home.csv")
    cartoes = []
    for row in df.to_dict("records"):
        cartoes.append(
            {
                "titulo": row["title"],
                "texto": row["text"],
                "icon": row["icon"] if pd.notna(row["icon"]) else "",
                "rota": ROTAS_V3.get(row["link"]),
                "em_construcao": bool(row["em_construcao"]),
            }
        )
    return cartoes


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"cartoes": _cartoes()},
    )
