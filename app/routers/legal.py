"""Páginas legais: política de privacidade e termos de utilização.

Renderizam os mesmos ficheiros markdown de content/ que a app Streamlit
usa — uma única fonte de verdade para os dois deployments.
"""

import markdown as md
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app import auth
from app.templating import templates
from core.reference import DATA_DIR

router = APIRouter()

CONTENT_DIR = DATA_DIR.parent / "content"


def _render_markdown(request, ficheiro: str, titulo: str):
    texto = (CONTENT_DIR / ficheiro).read_text(encoding="utf-8")
    return templates.TemplateResponse(
        request=request,
        name="legal.html",
        context={
            "utilizador": auth.utilizador_atual(request),
            "titulo": titulo,
            "conteudo": md.markdown(texto),
        },
    )


@router.get("/privacidade", response_class=HTMLResponse)
def privacidade(request: Request):
    return _render_markdown(
        request, "politica_privacidade.md", "Política de Privacidade"
    )


@router.get("/termos", response_class=HTMLResponse)
def termos(request: Request):
    return _render_markdown(request, "termos_utilização.md", "Termos de Utilização")
