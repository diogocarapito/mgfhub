"""Pesquisa de indicadores: página completa e fragmento htmx.

A mesma rota serve as duas coisas: com o header HX-Request devolve só o
fragmento de resultados (+ select de áreas via hx-swap-oob); sem ele
devolve a página completa — o URL com query params é sempre partilhável
e recarregável.
"""

from functools import lru_cache
from typing import List

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from app.templating import templates
from core.reference import load_indicadores
from core.search import FILTROS_CONTRATUALIZACAO, filter_indicadores

router = APIRouter()

# colunas mostradas nos cartões e na tabela (NaN → "—")
COLUNAS_DISPLAY = [
    "Nome abreviado",
    "Designação",
    "Descrição do Indicador",
    "Área clínica",
    "Intervalo Aceitável",
    "Intervalo Esperado",
    "Intervalo Aceitável 2023",
    "Intervalo Esperado 2023",
    "Intervalo Aceitável 2024",
    "Intervalo Esperado 2024",
]


@lru_cache(maxsize=1)
def _dataset():
    return load_indicadores()


@lru_cache(maxsize=8)
def _opcoes_area(filtros: str):
    df = filter_indicadores(_dataset(), "", filtros, [])
    return sorted(a for a in df["Área clínica"].dropna().unique())


@router.get("/indicadores", response_class=HTMLResponse)
def indicadores(
    request: Request,
    pesquisa: str = "",
    filtros: str = "IDE",
    area: List[str] = Query(default=[]),
    vista: str = "cartoes",
):
    if filtros not in FILTROS_CONTRATUALIZACAO:
        filtros = "IDE"
    if vista not in ("cartoes", "tabela"):
        vista = "cartoes"

    opcoes_area = _opcoes_area(filtros)
    # ignora áreas selecionadas que deixaram de existir após mudar o filtro
    area = [a for a in area if a in opcoes_area]

    df = filter_indicadores(_dataset(), pesquisa, filtros, area)
    df = df.sort_values("id")
    df[COLUNAS_DISPLAY] = df[COLUNAS_DISPLAY].fillna("—")

    context = {
        "pesquisa": pesquisa,
        "filtros": filtros,
        "filtros_opcoes": FILTROS_CONTRATUALIZACAO,
        "area": area,
        "opcoes_area": opcoes_area,
        "vista": vista,
        "rows": df.to_dict("records"),
        "num": len(df),
    }

    if request.headers.get("HX-Request"):
        # fragmento: resultados + select de áreas atualizado out-of-band
        context["oob"] = True
        return templates.TemplateResponse(
            request=request,
            name="partials/indicadores_resultados.html",
            context=context,
        )

    context["oob"] = False
    return templates.TemplateResponse(
        request=request,
        name="indicadores.html",
        context=context,
    )
