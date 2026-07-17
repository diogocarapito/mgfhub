"""Dashboard IDE: upload dos xlsx e as três vistas (unidade, indicador,
profissional), com os gráficos plotly servidos como JSON para o plotly.js.

Os dados carregados vivem na sessão em memória (app.session_store); cada
mudança de controlo re-renderiza a tab via htmx.
"""

import io

import pandas as pd
from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import HTMLResponse

from app import session_store
from app.templating import templates
from core.charts import (
    build_barra_alvo,
    build_barras_equipa,
    build_dumbbell,
    build_evolucao_temporal,
    build_sunburst_ide,
    build_sunburst_profissional,
)
from core.etl_bicsp import etl_bicsp
from core.etl_mimuf import etl_mimuf
from core.indicators import (
    extracao_areas_clinicas,
    mask_scores_bicsp,
    metricas_ide,
    prepara_tabela_unidade,
    process_filter_temporal,
    process_indicador,
    resumo_indicador_equipa,
)
from core.reference import DATA_DIR
from core.scoring import merge_portaria_bicsp
from monitor.telemetry import record_upload

router = APIRouter()

AVISO_BICSP = "Ficheiros do BI-CSP não carregados!"
AVISO_MIMUF = "Ficheiros do MIM@UF não carregados!"

VISTAS_UNIDADE = ["Sunburst", "Tabela", "Sunburst + Tabela", "Dumbbell"]


def _fig_json(fig):
    # </ escapado para o JSON poder viver dentro de <script type=application/json>
    return fig.to_json().replace("</", "<\\/")


class _FicheiroUpload(io.BytesIO):
    """Adaptador com .name, como o etl espera (à imagem do UploadedFile)."""

    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


async def _ler_uploads(uploads: list[UploadFile]):
    ficheiros = []
    for up in uploads:
        if not up.filename:
            continue
        ficheiros.append(_FicheiroUpload(await up.read(), up.filename))
    return ficheiros


def _demo_sunburst():
    df = pd.read_csv(DATA_DIR / "sunburst_score_1.csv", sep=";")
    return build_sunburst_ide(df, 2000, "Janeiro", "USF ?", 560)


# ---------------------------------------------------------------- contextos


def _ctx_unidade(dados, params):
    bicsp = dados.get("bicsp") or {}

    if not bicsp:
        return {
            "tab": "unidade",
            "aviso": AVISO_BICSP,
            "fig_demo": _fig_json(_demo_sunburst()),
        }

    datasets = list(bicsp.keys())
    escolha = params.get("dataset") or datasets[0]
    if escolha not in bicsp:
        escolha = datasets[0]

    vistas = VISTAS_UNIDADE + (["Sunburst + Sunburst"] if len(datasets) > 1 else [])
    vista_default = "Dumbbell" if len(datasets) > 1 else "Sunburst"
    vista = params.get("vista") or vista_default
    if vista not in vistas:
        vista = vista_default

    entry = bicsp[escolha]
    areas_clinicas = extracao_areas_clinicas(entry["df"])
    areas = [a for a in params.getlist("area") if a in areas_clinicas]

    def _float(nome, default):
        try:
            return float(params.get(nome, default))
        except (TypeError, ValueError):
            return default

    score_range = (_float("score_min", 0.0), _float("score_max", 2.0))
    peso_range = (_float("peso_min", 1.2), _float("peso_max", 10.0))

    def _merge(nome_dataset):
        e = bicsp[nome_dataset]
        masked = mask_scores_bicsp(e["df"], areas, score_range, peso_range)
        df = merge_portaria_bicsp(masked, e["ano"])
        if vista != "Dumbbell":
            # re-máscara pós-merge (linhas vindas da portaria)
            mask = (
                (df["Ponderação"] < peso_range[0]) | (df["Ponderação"] > peso_range[1])
            ) & (df["Hierarquia Contratual - Área"] == "IDE - Desempenho")
            df.loc[mask, "Score"] = None
        return df

    df_sunburst = _merge(escolha)

    ctx = {
        "tab": "unidade",
        "aviso": None,
        "datasets": datasets,
        "dataset": escolha,
        "vistas": vistas,
        "vista": vista,
        "areas_clinicas": areas_clinicas,
        "areas": areas,
        "score_range": score_range,
        "peso_range": peso_range,
        "metricas": metricas_ide(df_sunburst),
        "fig_sunburst": None,
        "fig_dumbbell": None,
        "tabela_rows": None,
        "dataset_2": None,
        "metricas_2": None,
        "fig_sunburst_2": None,
    }

    tamanho = 500 if vista in ("Sunburst + Tabela", "Sunburst + Sunburst") else 800

    if vista in ("Sunburst", "Sunburst + Tabela", "Sunburst + Sunburst"):
        ctx["fig_sunburst"] = _fig_json(
            build_sunburst_ide(
                df_sunburst, entry["ano"], entry["mes"], entry["unidade"], tamanho
            )
        )

    if vista in ("Tabela", "Sunburst + Tabela"):
        tabela = prepara_tabela_unidade(df_sunburst).reset_index()
        ctx["tabela_rows"] = tabela.to_dict("records")

    if vista in ("Sunburst + Sunburst", "Dumbbell") and len(datasets) > 1:
        escolha_2 = params.get("dataset2") or [d for d in datasets if d != escolha][0]
        if escolha_2 not in bicsp:
            escolha_2 = [d for d in datasets if d != escolha][0]
        ctx["dataset_2"] = escolha_2
        df_sunburst_2 = _merge(escolha_2)
        ctx["metricas_2"] = metricas_ide(df_sunburst_2)
        if vista == "Sunburst + Sunburst":
            e2 = bicsp[escolha_2]
            ctx["fig_sunburst_2"] = _fig_json(
                build_sunburst_ide(
                    df_sunburst_2, e2["ano"], e2["mes"], e2["unidade"], tamanho
                )
            )
        else:
            ctx["fig_dumbbell"] = _fig_json(
                build_dumbbell({escolha: df_sunburst, escolha_2: df_sunburst_2})
            )

    if vista == "Dumbbell" and len(datasets) == 1:
        ctx["fig_dumbbell"] = _fig_json(build_dumbbell({escolha: df_sunburst}))

    return ctx


def _ctx_indicador(dados, params):
    mimuf = dados.get("mimuf") or {}

    if not mimuf:
        return {"tab": "indicador", "aviso": AVISO_MIMUF}

    datasets = list(mimuf.keys())
    escolha = params.get("dataset") or datasets[0]
    if escolha not in mimuf:
        escolha = datasets[0]

    df = mimuf[escolha]["df"]

    # indicadores disponíveis (id, nome) — só os que existem na portaria
    opcoes = (
        df[["id", "Nome"]].dropna().drop_duplicates().sort_values("id")["Nome"].tolist()
    )

    indicador = params.get("indicador") or opcoes[0]
    if indicador not in opcoes:
        indicador = opcoes[0]

    vista = params.get("vista") or "Equipa"
    if vista not in ("Equipa", "Evolução temporal"):
        vista = "Equipa"

    df_indicador = df.loc[df["Nome"] == indicador]
    valores = process_indicador(df_indicador)

    ctx = {
        "tab": "indicador",
        "aviso": None,
        "datasets": datasets,
        "dataset": escolha,
        "opcoes_indicador": opcoes,
        "indicador": indicador,
        "vista": vista,
        "id_indicador": int(valores["id_indicador"]),
        "nome_indicador": valores["nome_indicador"],
        "link_sdm": f"https://sdm.min-saude.pt/BI.aspx?id={int(valores['id_indicador'])}",
    }

    if vista == "Equipa":
        ordenar = params.get("ordenar") or "Numerador"
        if ordenar not in ("Valor", "Numerador", "Denominador"):
            ordenar = "Numerador"

        resumo = resumo_indicador_equipa(valores)
        tabela = df_indicador[
            ["Médico Familia", "Numerador", "Denominador", "Valor"]
        ].sort_values(by=ordenar, ascending=False)

        ctx.update(
            {
                "ordenar": ordenar,
                "denominador": int(valores["denominador"]),
                "numerador": int(valores["numerador"]),
                "resumo": resumo,
                "fig_alvo": _fig_json(build_barra_alvo(valores)),
                "fig_equipa": _fig_json(
                    build_barras_equipa(
                        df_indicador, ordenar, int(valores["id_indicador"])
                    )
                ),
                "tabela_rows": tabela.to_dict("records"),
            }
        )
    else:
        temporal_vista = params.get("temporal") or "Unidade"
        if temporal_vista not in ("Unidade", "Por profissional"):
            temporal_vista = "Unidade"
        df_temporal = process_filter_temporal(mimuf, indicador)
        ctx.update(
            {
                "temporal_vista": temporal_vista,
                "fig_temporal": _fig_json(
                    build_evolucao_temporal(df_temporal, temporal_vista)
                ),
            }
        )

    return ctx


def _ctx_profissional(dados, params):
    mimuf = dados.get("mimuf") or {}

    if not mimuf:
        return {"tab": "profissional", "aviso": AVISO_MIMUF}

    datasets = list(mimuf.keys())
    escolha = params.get("dataset") or datasets[0]
    if escolha not in mimuf:
        escolha = datasets[0]

    entry = mimuf[escolha]
    medicos = entry["df"]["Médico Familia"].unique().tolist()
    medico = params.get("medico") or medicos[0]
    if medico not in medicos:
        medico = medicos[0]

    fig = build_sunburst_profissional(
        entry["df"][entry["df"]["Médico Familia"] == medico],
        entry["ano"],
        entry["mes"],
        entry["unidade"],
        700,
    )

    return {
        "tab": "profissional",
        "aviso": None,
        "datasets": datasets,
        "dataset": escolha,
        "medicos": medicos,
        "medico": medico,
        "fig_profissional": _fig_json(fig),
    }


_CONTEXTOS = {
    "unidade": _ctx_unidade,
    "indicador": _ctx_indicador,
    "profissional": _ctx_profissional,
}


def _resumo_sessao(dados):
    return {
        "bicsp": list((dados.get("bicsp") or {}).keys()),
        "mimuf": list((dados.get("mimuf") or {}).keys()),
    }


# ------------------------------------------------------------------- rotas


@router.get("/ide", response_class=HTMLResponse)
def ide(request: Request):
    dados = session_store.obter(request)
    context = {
        "resumo": _resumo_sessao(dados),
        "erros": [],
        **_ctx_unidade(dados, request.query_params),
    }
    return templates.TemplateResponse(request=request, name="ide.html", context=context)


@router.get("/ide/{tab}", response_class=HTMLResponse)
def ide_tab(request: Request, tab: str):
    if tab not in _CONTEXTOS:
        tab = "unidade"
    dados = session_store.obter(request)
    context = _CONTEXTOS[tab](dados, request.query_params)
    return templates.TemplateResponse(
        request=request, name="partials/ide_tabs.html", context=context
    )


@router.post("/ide/upload", response_class=HTMLResponse)
async def ide_upload(
    request: Request,
    bicsp: list[UploadFile] = File(default=[]),
    mimuf: list[UploadFile] = File(default=[]),
):
    erros = []
    avisos = []

    novos_bicsp = None
    ficheiros_bicsp = await _ler_uploads(bicsp)
    if ficheiros_bicsp:
        try:
            novos_bicsp = etl_bicsp(ficheiros_bicsp, on_upload=record_upload)
        except Exception:  # pylint: disable=broad-except
            erros.append(
                "Não foi possível processar os ficheiros do BI-CSP — "
                "confirma que são os xlsx exportados do BI-CSP (ver FAQs)."
            )

    novos_mimuf = None
    ficheiros_mimuf = await _ler_uploads(mimuf)
    if ficheiros_mimuf:
        try:
            novos_mimuf = etl_mimuf(
                ficheiros_mimuf,
                on_upload=record_upload,
                on_warning=avisos.append,
            )
        except Exception:  # pylint: disable=broad-except
            erros.append(
                "Não foi possível processar os ficheiros do MIM@UF — "
                "confirma que são os xlsx exportados do MIM@UF (ver FAQs)."
            )

    token, dados = session_store.guardar(request, bicsp=novos_bicsp, mimuf=novos_mimuf)

    context = {
        "resumo": _resumo_sessao(dados),
        "erros": erros + avisos,
        **_ctx_unidade(dados, request.query_params),
    }
    response = templates.TemplateResponse(
        request=request,
        name="partials/ide_dashboard.html",
        context=context,
    )
    session_store.anexar_cookie(response, token)
    return response
