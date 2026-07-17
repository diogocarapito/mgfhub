# pylint: disable=W0613
"""Adaptador Streamlit das visualizações do IDE.

As figuras plotly são construídas em core/charts.py (partilhadas com a
app v3); aqui só se faz st.plotly_chart e a preparação específica do
st.dataframe. Os gráficos matplotlib (ide_bar, horizontal_bar) ficam
nesta camada até ao cutover — a v3 usa os equivalentes plotly do core.
"""

import streamlit as st
import matplotlib.pyplot as plt

from core.charts import (
    INT_ACEIT,
    INT_ESPER,
    build_dumbbell,
    build_evolucao_temporal,
    build_sunburst_ide,
    build_sunburst_profissional,
)
from core.indicators import prepara_tabela_unidade


def sunburst_bicsp(df, ano, mes, unidade, size=800):
    st.plotly_chart(build_sunburst_ide(df, ano, mes, unidade, size), width="stretch")


@st.cache_data()
def sunburst_mimuf(df, ano, mes, unidade, size=800):
    st.plotly_chart(
        build_sunburst_profissional(df, ano, mes, unidade, size), width="stretch"
    )


@st.cache_data()
def dumbbell_plot(dict_dfs, ano):
    st.plotly_chart(build_dumbbell(dict_dfs), width="stretch")


@st.cache_data()
def line_chart(df, filtro_visualização):
    st.plotly_chart(build_evolucao_temporal(df, filtro_visualização), width="stretch")


@st.cache_data()
def tabela(df, ano, nome):
    df = prepara_tabela_unidade(df)

    st.subheader(nome)

    st.dataframe(
        df,
        column_config={
            "link_sdm": st.column_config.LinkColumn(
                label="Link",
                display_text="SDM",
            )
        },
        column_order=[
            "link_sdm",
            "Nome",
            "Ponderação",
            "Score",
            "Resultado",
            INT_ACEIT,
            INT_ESPER,
        ],
        hide_index=False,
    )
    return None


@st.cache_data()
def horizontal_bar(df, ano, ordenar_por, id_indicador):
    df = df.dropna(subset=["id"])

    df = df.sort_values(by=ordenar_por, ascending=True)

    freq = df["Valor"].round(2)

    med = df["Médico Familia"]

    nome = df["Nome"].unique()[0]

    min_aceitavel = df["Mínimo Aceitável"].unique()[0]
    min_esperado = df["Mínimo Esperado"].unique()[0]
    max_aceitavel = df["Máximo Aceitável"].unique()[0]
    max_esperado = df["Máximo Esperado"].unique()[0]
    minimo = 0

    for each in [min_aceitavel, min_esperado, max_esperado, max_aceitavel]:
        if each < 10:
            each = round(each, 2)
        else:
            each = round(each, 0)

    maximo_medico = df.groupby("Médico Familia")["Valor"].max().max()

    # se é o indicador 314, defenir o máximo com 100
    # porque o 314 é um indicador que e está mal desenhado! or 354

    if df["id"].unique()[0] == 314 or df["id"].unique()[0] == 354:
        if df["Valor"].max() > 100:
            maximo = df["Valor"].max()
        else:
            maximo = 100
    elif df["id"].unique()[0] == 341:
        if df["Valor"].max() > 200:
            maximo = df["Valor"].max()
        else:
            maximo = 200

    elif df["id"].unique()[0] == 404:
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

    # Define the colors
    colors = ["red", "yellow", "green", "yellow", "red"]

    # Define the ranges of the colors
    ranges = [
        (minimo, min_aceitavel),
        (min_aceitavel, min_esperado),
        (min_esperado, max_esperado),
        (max_esperado, max_aceitavel),
        (max_aceitavel, maximo),
    ]

    fig, ax = plt.subplots(figsize=(8, 6))

    # Add the background areas
    for color, (start, end) in zip(colors, ranges):
        ax.axvspan(start, end, facecolor=color, alpha=0.3)

    bar = ax.barh(med, freq, color=(30 / 255, 75 / 255, 124 / 255, 1))

    # Set plot title and labels
    ax.set_title(f"{nome} por MF")
    ax.set_xlabel("Cumprimento")
    ax.set_ylabel("Médico Familia")

    ax.set_xlim(minimo, maximo)

    ax.set_xticks(
        [minimo, min_aceitavel, min_esperado, max_esperado, max_aceitavel, maximo]
    )

    for rect in bar:
        # Get the width of the bar
        width = rect.get_width()

        # make it only 1 decimal if the width is greater than 2
        if width == 100.0:
            width = int(100)
        elif width <= 2:
            width = round(width, 2)
        elif width <= 200:
            width = round(width, 1)
        else:
            width = round(width, 0)

        percentage_sign = (
            "%"
            if maximo >= 100
            and id_indicador != 341
            and id_indicador != 354
            and id_indicador != 404
            and id_indicador != 294
            else ""
        )
        percentage_sign = (
            "€" if id_indicador == 341 or id_indicador == 354 else percentage_sign
        )

        # Add a label to the right of the bar
        ax.text(
            width + (0.005 * maximo),
            rect.get_y() + rect.get_height() / 2,
            f"{width}{percentage_sign}",
            ha="left",
            va="center",
        )

    st.pyplot(fig)


@st.cache_data()
def ide_bar(info_indicador=None):
    min_aceitavel, min_esperado, max_esperado, max_aceitavel = (
        info_indicador["min_aceitavel"],
        info_indicador["min_esperado"],
        info_indicador["max_esperado"],
        info_indicador["max_aceitavel"],
    )
    id_indicador = info_indicador["id_indicador"]
    nome_indicador = info_indicador["nome_indicador"]
    valor = float(info_indicador["valor"])
    if valor < 2:
        valor = round(valor, 2)
    else:
        valor = round(valor, 1)

    # Define the colors
    colors = ["red", "yellow", "green", "yellow", "red"]

    maximo = max(valor, info_indicador["max_aceitavel"], 100)
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

    elif (
        id_indicador == 269
        or id_indicador == 310
        or id_indicador == 311
        or id_indicador == 312
        or id_indicador == 302
    ):
        maximo = 1
    elif id_indicador == 330 or id_indicador == 331:
        maximo = 2

    # Define the ranges of the colors
    ranges = [
        (0, min_aceitavel),
        (min_aceitavel, min_esperado),
        (min_esperado, max_esperado),
        (max_esperado, max_aceitavel),
        (max_aceitavel, maximo),
    ]

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(5, 0.6))
    # Add the background areas
    for color, (start, end) in zip(colors, ranges):
        ax.axvspan(start, end, facecolor=color, alpha=0.3)

    # Plot the indicator value
    bar = ax.barh(
        id_indicador, valor, height=0.6, color=(46 / 255, 80 / 255, 140 / 255, 1)
    )

    # Convert the indicator ID to float for ylimit and yticks
    id_float = float(id_indicador)

    # Set the plot limits and ticks
    ax.set_xlim(0, maximo)
    ax.set_ylim(id_float - 0.5, id_float + 0.5)
    ax.set_yticks([])
    ax.set_xticks([min_aceitavel, min_esperado, max_esperado, max_aceitavel])
    ax.tick_params(axis="x", labelsize=8)

    # Set the y-label and title
    ax.set_title(f"{nome_indicador}", fontsize=9)

    # Add the value label
    rect = bar[0]
    width = rect.get_width()

    percentage_sign = (
        "%"
        if maximo >= 100
        and id_indicador != 341
        and id_indicador != 354
        and id_indicador != 404
        and id_indicador != 294
        else ""
    )
    percentage_sign = (
        "€" if id_indicador == 341 or id_indicador == 354 else percentage_sign
    )

    ax.text(
        width + (0.01 * maximo),
        rect.get_y() + rect.get_height() / 2,
        f"{width}{percentage_sign}",
        ha="left",
        va="center",
    )

    st.pyplot(fig)
