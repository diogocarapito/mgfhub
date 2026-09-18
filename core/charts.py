"""Construção das figuras plotly do IDE, partilhada pelas duas apps.

Cada função devolve um plotly.graph_objects.Figure: a app Streamlit
mostra-o com st.plotly_chart e a app v3 serializa-o com fig.to_json()
para o plotly.js renderizar no browser.

build_barra_alvo e build_barras_equipa são ports plotly dos gráficos
matplotlib da versão Streamlit (que os mantém até ao cutover).
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.reference import load_intervalos, load_portaria_sunburst

INT_ACEIT = "Intervalo Aceitável"
INT_ESPER = "Intervalo Esperado"

# gradiente de 5 cores para o score 0-2
ESCALA_SCORE = ["#FF7E79", "#F0A774", "#FFD479", "#E5CB72", "#56BA39"]

# zonas alvo: fora aceitável / aceitável / esperado / aceitável / fora
CORES_ZONAS = ["red", "yellow", "green", "yellow", "red"]

# indicadores em € (despesa) — afeta o sufixo dos valores
INDICADORES_EURO = (341, 354)


def _data_do_df(df):
    # data (Mês Ind) mais frequente do dataframe
    return df["Mês Ind"].mode()[0]


def _remove_dimensao(df):
    # remove as linhas de dimensão e do IDE global
    return df.loc[(df["Dimensão"] != "IDE") & (df["Nome"] != "IDE")]


def build_sunburst_ide(df, ano, mes, unidade, size=800):
    """Sunburst da visão de unidade (dados BI-CSP já merged com a portaria)."""
    df["Impacto"] = df["Score"] * df["Ponderação"] / 2

    # o CSV demo (sunburst_score_1.csv) pode não trazer os intervalos da
    # portaria; linhas sem intervalos próprios (dimensões, IDE) mostram "N/A"
    for col in (INT_ACEIT, INT_ESPER):
        if col not in df.columns:
            df[col] = "N/A"
        else:
            df[col] = df[col].fillna("N/A")

    fig = px.sunburst(
        df,
        names="Lable",
        parents="Dimensão",
        values="Ponderação",
        branchvalues="total",
        custom_data=["Nome", "Resultado", INT_ACEIT, INT_ESPER, "Impacto"],
        color="Score",
        color_continuous_scale=ESCALA_SCORE,
        range_color=[0, 2],
    )

    fig.update_traces(
        hovertemplate="""<b>%{customdata[0]}</b><br>Peso: <b>%{value}%</b><br>Score: <b>%{color:.2f}</b><br>Impacto: <b>%{customdata[4]:.2f}%</b><br>Resultado: <b>%{customdata[1]:.2f}</b><br>Intervalo Aceitável: <b>%{customdata[2]}</b><br>Intervalo Esperado: <b>%{customdata[3]}</b><extra></extra>""",
        hoverlabel=dict(font=dict(size=16)),
        textinfo="label",
        insidetextfont=dict(size=20, color="black"),
        insidetextorientation="radial",
        textfont=dict(
            color="black",
        ),
    )

    fig.update_layout(
        title=f"{unidade} {mes}/{ano}",
        title_font=dict(size=24),
        width=size,
        height=size,
        showlegend=True,
    )

    return fig


def build_sunburst_profissional(df, ano, mes, unidade, size=800):
    """Sunburst da visão por profissional (dados MIM@UF de um médico)."""
    df = df[df["Score"] != "Error"]

    df_portaria = load_portaria_sunburst()[
        ["id", "Nome", "Dimensão", "Ponderação", "Lable"]
    ]
    df_portaria = df_portaria.merge(load_intervalos(ano), on="id", how="left")

    df = df_portaria.merge(
        df[["id", "Valor", "Score", "Denominador", "Numerador"]],
        on="id",
        how="left",
    )

    # dimensões (exclui vazias e a linha IDE); não depende da ordem do unique()
    list_dimensoes = [
        x for x in df["Dimensão"].unique().tolist() if pd.notna(x) and x != "IDE"
    ]

    # calculate the score for each dimension based on the average wheighed score
    df["contributo"] = df["Ponderação"] * df["Score"] / 2

    for dim in list_dimensoes:
        df.loc[df["Nome"] == dim, "Resultado"] = df[df["Dimensão"] == dim][
            "contributo"
        ].sum()

    df.loc[df["Dimensão"] == "IDE", "Score"] = (
        2
        * df.loc[df["Dimensão"] == "IDE", "Resultado"]
        / df.loc[df["Dimensão"] == "IDE", "Ponderação"]
    )

    # linhas sem intervalos próprios (dimensões, IDE) mostram "N/A"
    df[INT_ACEIT] = df[INT_ACEIT].fillna("N/A")
    df[INT_ESPER] = df[INT_ESPER].fillna("N/A")

    # IDE
    df.loc[df["Nome"] == "IDE", "Resultado"] = df.loc[
        df["Dimensão"] == "IDE", "Resultado"
    ].sum()
    df.loc[df["Nome"] == "IDE", "Score"] = (
        2
        * df.loc[df["Nome"] == "IDE", "Resultado"]
        / df.loc[df["Nome"] == "IDE", "Ponderação"]
    )

    # make score a float
    df["Score"] = df["Score"].astype(float)

    fig = px.sunburst(
        df,
        names="Lable",
        parents="Dimensão",
        values="Ponderação",
        branchvalues="total",
        custom_data=["Nome", "Valor", INT_ACEIT, INT_ESPER],
        color="Score",
        color_continuous_scale=ESCALA_SCORE,
        range_color=[0, 2],
    )
    fig.update_traces(
        hovertemplate="""<b>%{customdata[0]}</b><br>Peso: %{value}%<br>Score: <b>%{color:.3f}</b><br>Resultado: <b>%{customdata[1]:.3f}</b><br>Intervalo Aceitável: %{customdata[2]}<br>Intervalo Esperado: %{customdata[3]}<extra></extra>""",
        hoverlabel=dict(font=dict(size=18)),
        textinfo="label",
        insidetextfont=dict(size=24),
        insidetextorientation="radial",
    )

    fig.update_layout(
        title=f"{unidade} {mes}/{ano}",
        title_font=dict(size=24),
        width=size,
        height=size,
        showlegend=True,
    )

    return fig


def build_dumbbell(dict_dfs):
    """Dumbbell de comparação de períodos (1 ou 2 datasets BI-CSP merged)."""
    dict_figs = {}

    dfs = []
    for nome, each in dict_dfs.items():
        dfs.append(
            {
                "df": _remove_dimensao(each),
                "nome": nome,
                "date": _data_do_df(each),
            }
        )

    # order dfs by date
    dfs = sorted(dfs, key=lambda x: x["date"])

    if len(dict_dfs) == 2:
        # Ensure the dataframes are sorted by 'score' in ascending order from
        # the latest date
        sort_order_2 = dfs[1]["df"]["Score"].argsort()
        dfs[0]["df"] = dfs[0]["df"].iloc[sort_order_2]
        dfs[1]["df"] = dfs[1]["df"].iloc[sort_order_2]

        list_indicadores = dfs[0]["df"]["Nome"].tolist()

        # Iterate over the 'indicador' values in the first dataframe
        for indicador in list_indicadores:
            # Get the 'Score' values for the current 'indicador' in both dataframes
            score1 = dfs[0]["df"][dfs[0]["df"]["Nome"] == indicador]["Score"].values[0]
            score2 = dfs[1]["df"][dfs[1]["df"]["Nome"] == indicador]["Score"].values[0]

            if abs(score1 - score2) < 0.06:
                marker_info = None
                linecolor = "grey"
            else:
                marker_info = dict(
                    symbol="arrow",
                    color="grey",
                    size=18,
                    angleref="previous",
                    standoff=8,
                )
                linecolor = "grey"

            # Create a line from score1 to score2
            line = go.Scatter(
                x=[score1, score2],
                y=[indicador, indicador],
                mode="markers+lines",
                showlegend=False,
                marker=marker_info,
                line=dict(
                    color=linecolor,
                ),
                hoverinfo="none",  # disable hover
            )
            dict_figs[indicador] = line

    i = 0

    for each in dfs:
        # drop rows if "Score" is None
        each["df"] = each["df"].dropna(subset=["Score"])

        each["df"]["Etiqueta"] = each["nome"]
        each["df"] = each["df"].loc[each["df"]["Nome"] != "IDE"]
        each["df"] = each["df"].loc[each["df"]["Dimensão"] != "IDE"]

        each["df"] = each["df"].sort_values(by="Score", ascending=True)

        dict_figs[each["nome"]] = go.Scatter(
            x=each["df"]["Score"],
            y=each["df"]["Nome"],
            mode="markers",
            name=each["nome"],
            marker=dict(
                size=10 * np.sqrt(each["df"]["Ponderação"]),
                color=each["df"]["Score"],  # Set color to Score
                colorscale=ESCALA_SCORE,
                symbol=i + 0,  # Set symbol to i
            ),
            customdata=each["df"][
                ["Nome", "Resultado", INT_ACEIT, INT_ESPER, "Score", "Ponderação"]
            ].values,
            hovertemplate="<b>%{customdata[0]}</b><br>Peso: %{customdata[5]}%<br>Score: <b>%{customdata[4]:.3f}</b><br>Resultado: <b>%{customdata[1]:.1f}</b><br>Intervalo Aceitável: %{customdata[2]}<br>Intervalo Esperado: %{customdata[3]}<extra></extra>",
            hoverlabel=dict(font=dict(size=18)),
        )

        # iterador de cor
        i += 1

    fig = go.Figure(data=list(dict_figs.values()))

    fig.update_layout(
        xaxis=dict(
            range=[-0.1, 2.1],
            tickvals=[0, 0.5, 1, 1.5, 2],
            ticklen=10,
            showgrid=True,
            gridcolor="rgba(128, 128, 128, 0.25)",
            gridwidth=1,
            tickfont=dict(size=20),
            side="bottom",
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(size=12),
        ),
        height=each["df"].shape[0] * 25 + 300,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=14),
        ),
    )

    return fig


def build_evolucao_temporal(df, filtro_visualizacao):
    """Linha temporal de um indicador (output de process_filter_temporal)."""
    if filtro_visualizacao == "Unidade":
        df = df[df["Médico Familia"] == "Unidade"]
    else:
        df = df[df["Médico Familia"] != "Unidade"]

    min_aceitavel = df["min_aceitavel"].unique()[0]
    min_esperado = df["min_esperado"].unique()[0]
    max_esperado = df["max_esperado"].unique()[0]
    max_aceitavel = df["max_aceitavel"].unique()[0]

    titulo = df["Nome"].unique()[0]

    minimo = 0
    maximo = max(df["Valor"].max(), max_aceitavel, 100)
    if maximo > 1000:
        maximo = 300

    id_indicador = titulo.split(" - ")[0]

    if id_indicador in ("330", "331"):
        maximo = 1
    elif id_indicador == "341":
        maximo = max(df["Valor"].max(), 200)

    ranges = [
        (minimo, min_aceitavel),
        (min_aceitavel, min_esperado),
        (min_esperado, max_esperado),
        (max_esperado, max_aceitavel),
        (max_aceitavel, maximo),
    ]

    fig = go.Figure()

    fig.update_layout(
        shapes=[
            dict(
                type="rect",
                x0=0,
                x1=1,
                y0=0,
                y1=1,
                xref="paper",
                yref="paper",
                line=dict(color="rgba(128, 128, 128, 0.35)", width=1),
            )
        ]
    )

    # Add the background areas
    for color, (start, end) in zip(CORES_ZONAS, ranges):
        fig.add_shape(
            type="rect",
            x0=0,
            x1=1,
            y0=start,
            y1=end,
            xref="paper",
            yref="y",
            fillcolor=color,
            opacity=0.3,
            layer="below",
            line_width=0,
        )

    # uma linha por Médico Familia
    for medico_familia in df["Médico Familia"].unique():
        df_medico = df.loc[df["Médico Familia"] == medico_familia]
        fig.add_trace(
            go.Scatter(
                x=df_medico["ano_mes"],
                y=df_medico["Valor"],
                mode="lines+markers",
                name=medico_familia,
                text=[f"{val:.2f}" for val in df_medico["Valor"]],
                marker=dict(size=18),
            )
        )

    fig.update_layout(
        title=dict(
            text=titulo,
            x=0.5,
            xanchor="center",
            font=dict(size=26),
        ),
        xaxis_title="Mês",
        yaxis_title="Cumprimento",
        xaxis=dict(
            tickmode="array",
            tickvals=df["ano_mes"].unique(),
            ticktext=df["ano_mes"].unique(),
            title_font=dict(size=24),
            tickfont=dict(size=24),
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=[
                minimo,
                min_aceitavel,
                min_esperado,
                max_esperado,
                max_aceitavel,
                maximo,
            ],
            title_font=dict(size=24),
            tickfont=dict(size=24),
        ),
        legend_title="Médico Familia",
        hoverlabel=dict(font_size=20),
        margin=dict(l=20, r=20, t=50, b=20),
    )

    fig.update_yaxes(range=[0, maximo])

    return fig


def _sufixo_valor(id_indicador, maximo):
    if id_indicador in INDICADORES_EURO:
        return "€"
    if maximo >= 100 and id_indicador not in (404, 294):
        return "%"
    return ""


def build_barra_alvo(info_indicador):
    """Barra horizontal do valor agregado da unidade contra as zonas alvo
    (port plotly do ide_bar matplotlib da versão Streamlit)."""
    min_aceitavel = info_indicador["min_aceitavel"]
    min_esperado = info_indicador["min_esperado"]
    max_esperado = info_indicador["max_esperado"]
    max_aceitavel = info_indicador["max_aceitavel"]
    id_indicador = info_indicador["id_indicador"]

    valor = float(info_indicador["valor"])
    if valor < 2:
        valor = round(valor, 2)
    else:
        valor = round(valor, 1)

    maximo = max(valor, max_aceitavel, 100)
    if maximo > 1000 and id_indicador != 294:
        maximo = 300

    if id_indicador == 341:
        maximo = max(valor, 200)
    elif id_indicador == 354:
        maximo = max(valor, 100)
    elif id_indicador == 404:
        valor = valor * 10000
        maximo = max(valor, 100)
        max_esperado = max(valor, 100)
        max_aceitavel = max(valor, 100)
    elif id_indicador in (269, 310, 311, 312, 302):
        maximo = 1
    elif id_indicador in (330, 331):
        maximo = 2

    ranges = [
        (0, min_aceitavel),
        (min_aceitavel, min_esperado),
        (min_esperado, max_esperado),
        (max_esperado, max_aceitavel),
        (max_aceitavel, maximo),
    ]

    fig = go.Figure()

    for color, (start, end) in zip(CORES_ZONAS, ranges):
        fig.add_shape(
            type="rect",
            x0=start,
                x1=cccccccccccccccccccccccvvvvvvvvvvvbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbvb,ncv;
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
        fillcolor=color,:
            opacity=0.3,
            layer="below",
            line_width=0,
        )

    sufixo = _sufixo_valor(id_indicador, maximo)

    fig.add_trace(
        go.Bar(
            x=[valor],
            y=[""],
            orientation="h",
            width=0.8,
            marker_color="#0aa6b8",
            text=[f"{valor}{sufixo}"],
            textposition="outside",
            cliponaxis=False,
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        height=90,
        showlegend=False,
        xaxis=dict(
            range=[0, maximo],
            tickvals=[min_aceitavel, min_esperado, max_esperado, max_aceitavel],
            tickfont=dict(size=11),
        ),
        yaxis=dict(visible=False),
        margin=dict(l=10, r=40, t=10, b=30),
    )

    return fig


def build_barras_equipa(df, ordenar_por, id_indicador):
    """Barras horizontais do cumprimento por médico contra as zonas alvo
    (port plotly do horizontal_bar matplotlib da versão Streamlit)."""
    df = df.dropna(subset=["id"])
    df = df.sort_values(by=ordenar_por, ascending=True)

    valores = df["Valor"].round(2)
    medicos = df["Médico Familia"]
    nome = df["Nome"].unique()[0]

    min_aceitavel = df["Mínimo Aceitável"].unique()[0]
    min_esperado = df["Mínimo Esperado"].unique()[0]
    max_aceitavel = df["Máximo Aceitável"].unique()[0]
    max_esperado = df["Máximo Esperado"].unique()[0]
    minimo = 0

    maximo_medico = df.groupby("Médico Familia")["Valor"].max().max()

    # regras específicas de escala para indicadores mal desenhados na fonte
    if id_indicador in (314, 354):
        maximo = max(df["Valor"].max(), 100)
    elif id_indicador == 341:
        maximo = max(df["Valor"].max(), 200)
    elif id_indicador == 404:
        if maximo_medico > 100:
            maximo, max_esperado, max_aceitavel = (
                maximo_medico,
                maximo_medico,
                maximo_medico,
            )
        else:
            maximo, max_esperado, max_aceitavel = 100, 100, 100
    else:
        maximo = max(
            [
                min_aceitavel,
                min_esperado,
                max_esperado,
                max_aceitavel,
                df["Valor"].max(),
            ]
        )

    ranges = [
        (minimo, min_aceitavel),
        (min_aceitavel, min_esperado),
        (min_esperado, max_esperado),
        (max_esperado, max_aceitavel),
        (max_aceitavel, maximo),
    ]

    fig = go.Figure()

    for color, (start, end) in zip(CORES_ZONAS, ranges):
        fig.add_shape(
            type="rect",
            x0=start,
            x1=end,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            fillcolor=color,
            opacity=0.3,
            layer="below",
            line_width=0,
        )

    sufixo = _sufixo_valor(id_indicador, maximo)

    def _label(valor):
        if valor == 100.0:
            valor = int(100)
        elif valor <= 2:
            valor = round(valor, 2)
        elif valor <= 200:
            valor = round(valor, 1)
        else:
            valor = round(valor, 0)
        return f"{valor}{sufixo}"

    fig.add_trace(
        go.Bar(
            x=valores,
            y=medicos,
            orientation="h",
            marker_color="#0aa6b8",
            text=[_label(v) for v in valores],
            textposition="outside",
            cliponaxis=False,
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        title=dict(text=f"{nome} por MF", font=dict(size=15)),
        height=max(300, df.shape[0] * 35 + 150),
        showlegend=False,
        xaxis=dict(
            range=[minimo, maximo],
            tickvals=[
                minimo,
                min_aceitavel,
                min_esperado,
                max_esperado,
                max_aceitavel,
                maximo,
            ],
            tickfont=dict(size=11),
        ),
        margin=dict(l=10, r=50, t=50, b=30),
    )

    return fig
