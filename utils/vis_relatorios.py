# pylint: disable=W0613


import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from core import load_intervalos, load_portaria_sunburst

# nomes das colunas de intervalos (já resolvidas por ano em core.reference)
INT_ACEIT = "Intervalo Aceitável"
INT_ESPER = "Intervalo Esperado"


@st.cache_data()
def check_date(df):
    # check the date of the data
    return df["Mês Ind"].mode()[0]


@st.cache_data()
def remove_dimensao(df):
    # remove rows that have "Dimensão" == "IDE" and "Nome" == "IDE"
    return df.loc[(df["Dimensão"] != "IDE") & (df["Nome"] != "IDE")]


# @st.cache_data()
# def sunburst_size_change(df, ano, mes, unidade, size):

#     if not st.session_state["sunburst_size"]:
#         st.session_state["sunburst_size"] = size

#     if st.button("+"):
#         st.session_state["sunburst_size"] += 100
#         sunburst_bicsp(df, ano, mes, unidade, st.session_state["sunburst_size"])

#     if st.button("-"):
#         st.session_state["sunburst_size"] -= 100

#         sunburst_bicsp(df, ano, mes, unidade, st.session_state["sunburst_size"])


def id_table(df, event_click):
    if event_click:
        id_clicked = event_click[0]["pointNumber"]
        df_clicked = df.iloc[id_clicked]
        st.write(df_clicked["Lable"])
        # st.write(df_clicked)
    else:
        st.write("IDE")
        # st.write(df.iloc[48])


# @st.cache_data()
def sunburst_bicsp(df, ano, mes, unidade, size=800):
    int_aceit, int_esper = INT_ACEIT, INT_ESPER

    df["Impacto"] = df["Score"] * df["Ponderação"] / 2

    # sunburst
    fig = px.sunburst(
        df,
        names="Lable",
        parents="Dimensão",
        values="Ponderação",
        branchvalues="total",
        custom_data=["Nome", "Resultado", int_aceit, int_esper, "Impacto"],
        color="Score",
        # color_continuous_scale=["#FF7E79", "#FFD479", "#56BA39"], #3 color gradient
        color_continuous_scale=[
            "#FF7E79",
            "#F0A774",
            "#FFD479",
            "#E5CB72",
            "#56BA39",
        ],  # 5 color gradient
        range_color=[0, 2],
    )

    fig.update_traces(
        hovertemplate="""<b>%{customdata[0]}</b><br>Peso: <b>%{value}%</b><br>Score: <b>%{color:.2f}</b><br>Impacto: <b>%{customdata[4]:.2f}%</b><br>Resultado: <b>%{customdata[1]:.2f}</b><br>Intervalo Aceitável: <b>%{customdata[2]}</b><br>Intervalo Esperado: <b>%{customdata[3]}</b><extra></extra>""",
        # hovertemplate="""<b>%{customdata[0]}</b>""",
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
        title_font=dict(size=24, color="black"),
        width=size,
        height=size,
        showlegend=True,
        legend_title_font=dict(color="black"),
        legend_font=dict(color="black"),
    )

    # col_sunburst, col_id = st.columns([3, 1])

    # with col_sunburst:
    #     with st.container():
    #         event_click = plotly_events(fig, override_width="100%")
    #         # event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")

    # with col_id:
    #     # st.json(event)
    #     id_table(df, event_click)

    # sunburst_size_change(df, ano, mes, unidade, size)

    st.plotly_chart(fig, width="stretch")


@st.cache_data()
def sunburst_mimuf(df, ano, mes, unidade, size=800):
    int_aceit, int_esper = INT_ACEIT, INT_ESPER
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

    # list of dimensions and drop empty obnes
    list_dimensoes = [x for x in df["Dimensão"].unique().tolist() if pd.notna(x)]

    # remove IDE
    list_dimensoes = list_dimensoes[1:]

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
    df[int_aceit] = df[int_aceit].fillna("N/A")
    df[int_esper] = df[int_esper].fillna("N/A")

    # IDE
    df.loc[df["Nome"] == "IDE", "Resultado"] = df.loc[
        df["Dimensão"] == "IDE", "Resultado"
    ].sum()
    df.loc[df["Nome"] == "IDE", "Score"] = (
        2
        * df.loc[df["Nome"] == "IDE", "Resultado"]
        / df.loc[df["Nome"] == "IDE", "Ponderação"]
    )

    # df.loc[df["Nome"] != "IDE"] = df.loc[df["Nome"] != "IDE"].fillna(0)

    # make score a float
    df["Score"] = df["Score"].astype(float)

    # # Add a row with Score 0
    # df = df.append(
    #     {
    #         "Lable": "",
    #         "Dimensão": "",
    #         "Ponderação": 0,
    #         "Nome": "",
    #         "Valor": "",
    #         int_aceit: "",
    #         int_esper: "",
    #         "Score": 0,
    #     },
    #     ignore_index=True,
    # )

    # # Add a row with Score 2
    # df = df.append(
    #     {
    #         "Lable": "",
    #         "Dimensão": "",
    #         "Ponderação": 0,
    #         "Nome": "",
    #         "Valor": "",
    #         int_aceit: "",
    #         int_esper: "",
    #         "Score": 2,
    #     },
    #     ignore_index=True,
    # )

    # sunburst
    fig = px.sunburst(
        df,
        names="Lable",
        parents="Dimensão",
        values="Ponderação",
        branchvalues="total",
        custom_data=["Nome", "Valor", int_aceit, int_esper],
        color="Score",
        # color_continuous_scale=["#FF7E79", "#FFD479", "#56BA39"],
        color_continuous_scale=[
            "#FF7E79",
            "#F0A774",
            "#FFD479",
            "#E5CB72",
            "#56BA39",
        ],  # 5 color gradient
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

    # # gets the event data and displays the fig as well
    # event = plotly_events(fig, override_height=size, override_width=size)
    # # st.plotly_chart(fig, use_container_width=True)

    # if event:
    #     selected_id = event[0]["pointNumber"]
    #     st.write(selected_id)

    st.plotly_chart(fig, width="stretch")


@st.cache_data()
def dumbbell_plot(dict_dfs, ano):
    dict_figs = {}

    dfs = []
    for nome, each in dict_dfs.items():
        dfs.append(
            {
                "df": remove_dimensao(each),
                "nome": nome,
                "date": check_date(each),
            }
        )

    # order dfs by date
    dfs = sorted(dfs, key=lambda x: x["date"])

    if len(dict_dfs) == 2:
        # Ensure the dataframes are sorted by 'score' in ascending order from the latest date
        sort_order_2 = dfs[1]["df"]["Score"].argsort()
        dfs[0]["df"] = dfs[0]["df"].iloc[sort_order_2]
        dfs[1]["df"] = dfs[1]["df"].iloc[sort_order_2]

        # remove the columns that have Dimensão == "IDE"
        dfs[0]["df"] = dfs[0]["df"].loc[dfs[0]["df"]["Dimensão"] != "IDE"]
        dfs[1]["df"] = dfs[1]["df"].loc[dfs[1]["df"]["Dimensão"] != "IDE"]

        # remove the columns that have Nome ==_ "IDE"
        dfs[0]["df"] = dfs[0]["df"].loc[dfs[0]["df"]["Nome"] != "IDE"]
        dfs[1]["df"] = dfs[1]["df"].loc[dfs[1]["df"]["Nome"] != "IDE"]

        list_indicadores = dfs[0]["df"]["Nome"].tolist()

        # Iterate over the 'indicador' values in the first dataframe
        for indicador in list_indicadores:
            # Get the 'Score' values for the current 'indicador' in both dataframes
            score1 = dfs[0]["df"][dfs[0]["df"]["Nome"] == indicador]["Score"].values[0]
            score2 = dfs[1]["df"][dfs[1]["df"]["Nome"] == indicador]["Score"].values[0]

            if abs(score1 - score2) < 0.06:
                marker_info = None
                linecolor = "grey"

            elif score1 > score2:
                marker_info = dict(
                    symbol="arrow",
                    # color="#FF7E79",
                    color="grey",
                    size=18,
                    angleref="previous",
                    standoff=8,
                )
                # linecolor = "#FF7E79"
                linecolor = "grey"
            else:
                marker_info = dict(
                    symbol="arrow",
                    # color="#56BA39",
                    color="grey",
                    size=18,
                    angleref="previous",
                    standoff=8,
                )
                # linecolor = "#56BA39"
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

    # colors = ["#588EF9", "#BE1CF3"]

    i = 0

    for each in dfs:
        int_aceit, int_esper = INT_ACEIT, INT_ESPER

        # drop rows if "Score" is  None
        each["df"] = each["df"].dropna(subset=["Score"])

        each["df"]["Etiqueta"] = each["nome"]
        # remove the columns that have Nome ==_ "IDE"
        each["df"] = each["df"].loc[each["df"]["Nome"] != "IDE"]
        each["df"] = each["df"].loc[each["df"]["Dimensão"] != "IDE"]

        each["df"] = each["df"].sort_values(by="Score", ascending=True)

        dict_figs[each["nome"]] = go.Scatter(
            x=each["df"]["Score"],
            y=each["df"]["Nome"],
            mode="markers",
            name=each["nome"],
            marker=dict(
                # size=16,
                size=10 * np.sqrt(each["df"]["Ponderação"]),
                color=each["df"]["Score"],  # Set color to Score
                # colorscale=["#FF7E79", "#FFD479", "#56BA39"],
                colorscale=[
                    "#FF7E79",
                    "#F0A774",
                    "#FFD479",
                    "#E5CB72",
                    "#56BA39",
                ],  # 5 color gradient
                symbol=i + 0,  # Set symbol to i
            ),
            customdata=each["df"][
                ["Nome", "Resultado", int_aceit, int_esper, "Score", "Ponderação"]
            ].values,
            hovertemplate="<b>%{customdata[0]}</b><br>Peso: %{customdata[5]}%<br>Score: <b>%{customdata[4]:.3f}</b><br>Resultado: <b>%{customdata[1]:.1f}</b><br>Intervalo Aceitável: %{customdata[2]}<br>Intervalo Esperado: %{customdata[3]}<extra></extra>",
            hoverlabel=dict(font=dict(size=18)),
        )

        # iterador de cor
        i += 1

    traces = []
    for trace in dict_figs.values():
        traces.append(trace)

    fig = go.Figure(
        data=traces,
    )

    fig.update_layout(
        xaxis=dict(
            range=[-0.1, 2.1],  # minimum and maximum values for the x axis
            tickvals=[
                0,
                0.5,
                1,
                1.5,
                2,
            ],  # specify the values at which ticks should appear
            ticklen=10,  # length of the ticks
            showgrid=True,  # show grid lines
            gridcolor="#D3D3D3",  # set grid color to light grey
            gridwidth=1,  # set grid line width
            tickfont=dict(size=20),  # increase the size of the x axis labels
            side="bottom",  # position the x axis labels at the top
        ),
        yaxis=dict(
            autorange="reversed",  # reverse the order of the y axis
            tickfont=dict(size=18),  # increase the size of the y axis labels
        ),
        height=each["df"].shape[0] * 25 + 300,
        # showlegend=False,
        legend=dict(
            orientation="h",  # horizontal orientation
            yanchor="bottom",  # anchor the y position to the bottom
            y=1.02,  # position the y just above the top of the graph
            xanchor="right",  # anchor the x position to the right
            x=1,  # position the x at the far right of the graph
            font=dict(size=14),  # increase the size of the legend labels
        ),
    )

    st.plotly_chart(fig, width="stretch")


@st.cache_data()
def tabela(df, ano, nome):
    int_aceit, int_esper = INT_ACEIT, INT_ESPER

    df = df.loc[df["Dimensão"] != "IDE"]

    df_sdm = pd.read_csv(
        "./data/indicadores_sdm_complete.csv", usecols=["id", "link_sdm"]
    )

    df = df.merge(
        df_sdm,
        on="id",
        how="left",
    )

    # make id index
    df = df.set_index("id")

    # remove row without id
    df = df[df.index.notnull()]

    st.subheader(nome)

    # remove rows where Score is None
    df = df.dropna(subset=["Score"])

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
            # "Dimensão",
            "Ponderação",
            "Score",
            "Resultado",
            int_aceit,
            int_esper,
        ],
        hide_index=False,
    )
    return None


@st.cache_data()
def horizontal_bar(df, ano, ordenar_por, id_indicador):
    # ano = 2024
    print(df.columns)

    df = df.dropna(subset=["id"])

    df = df.sort_values(by=ordenar_por, ascending=True)

    freq = df["Valor"].round(2)

    med = df["Médico Familia"]

    nome = df["Nome"].unique()[0]

    min_aceitavel = df["Mínimo Aceitável"].unique()[0]
    min_esperado = df["Mínimo Esperado"].unique()[0]
    max_aceitavel = df["Máximo Aceitável"].unique()[0]
    max_esperado = df["Máximo Esperado"].unique()[0]
    # min_aceitavel = df[f"Mínimo Aceitável {ano}"].unique()[0]
    # min_esperado = df[f"Mínimo Esperado {ano}"].unique()[0]
    # max_aceitavel = df[f"Máximo Aceitável {ano}"].unique()[0]
    # max_esperado = df[f"Máximo Esperado {ano}"].unique()[0]
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
def stakced_barchart(df):
    med = df["Médico Familia"]
    # denominador = df["Denominador"]
    numerador = df["Numerador"].astype(int)

    df["falta"] = df["Denominador"].astype(int) - df["Numerador"].astype(int)
    falta = df["falta"].astype(int)

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.barh(med, numerador, color="green")
    ax.barh(med, falta, left=falta, color="red")

    ax.set_xlabel("Denominador")
    ax.set_ylabel("Médico Familia")
    ax.set_title("Denominador and Numerador by Médico Familia")

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

    # elif id_indicador == 294:

    # Define the ranges of the colors
    ranges = [
        (0, min_aceitavel),
        (min_aceitavel, min_esperado),
        (min_esperado, max_esperado),
        (max_esperado, max_aceitavel),
        (max_aceitavel, maximo),
    ]

    # Create the figure and axis
    # fig, ax = plt.subplots(figsize=(5, 0.75))
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

    # make it only 1 decimal if the width is greater than 2
    # if width == 100.0:
    #     width = int(100)
    # elif width <= 2:
    #     width = round(width, 2)
    # elif width <= 200:
    #     width = round(width, 1)
    # else:
    #     width = round(width, 0)

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
        # width,
        rect.get_y() + rect.get_height() / 2,
        f"{width}{percentage_sign}",
        ha="left",
        va="center",
    )

    st.pyplot(fig)


@st.cache_data()
def line_chart(df, filtro_visualização):
    # print(df.columns)
    if filtro_visualização == "Unidade":
        df = df[df["Médico Familia"] == "Unidade"]
    else:
        df = df[df["Médico Familia"] != "Unidade"]

    min_aceitavel = df["min_aceitavel"].unique()[0]
    min_esperado = df["min_esperado"].unique()[0]
    max_esperado = df["max_esperado"].unique()[0]
    max_aceitavel = df["max_aceitavel"].unique()[0]

    titulo = df["Nome"].unique()[0]

    # Define the colors
    colors = ["red", "yellow", "green", "yellow", "red"]

    minimo = 0
    maximo = max(df["Valor"].max(), max_aceitavel, 100)
    if maximo > 1000:
        maximo = 300

    id_indicador = titulo.split(" - ")[0]

    if id_indicador == "330" or id_indicador == "331":
        maximo = 1
    elif id_indicador == "341":
        maximo = max(df["Valor"].max(), 200)

    # Define the ranges of the colors
    ranges = [
        (minimo, min_aceitavel),
        (min_aceitavel, min_esperado),
        (min_esperado, max_esperado),
        (max_esperado, max_aceitavel),
        (max_aceitavel, maximo),
    ]

    # Create a Plotly figure
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
                line=dict(color="black", width=1.5),
            )
        ]
    )

    # Add the background areas
    for color, (start, end) in zip(colors, ranges):
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
            line_width=0,
        )

    # Plot a line chart with the values for each "Médico Familia", where each "Médico Familia" has a line
    for medico in df["Médico Familia"].unique():
        df_medico = df.loc[df["Médico Familia"] == medico]
        fig.add_trace(
            go.Scatter(
                x=df_medico["ano_mes"],
                y=df_medico["Valor"],
                mode="lines+markers",
                name=medico,
                text=[
                    f"{val:.2f}" for val in df_medico["Valor"]
                ],  # Format values to 2 decimal placess
                marker=dict(size=18),
            )
        )

    # Set plot title and labels
    fig.update_layout(
        title=dict(
            text=titulo,
            x=0.5,  # Center the title
            xanchor="center",  # Anchor the title at the center
            font=dict(size=26),  # Set font size to 30
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
        # add a line arround the graph
        margin=dict(l=20, r=20, t=50, b=20),
    )

    # Add a fine black border around the graph

    # # Annotate the points
    # for medico in df['Médico Familia'].unique():
    #     df_medico = df.loc[df['Médico Familia'] == medico]
    #     for i, row in df_medico.iterrows():
    #         fig.add_annotation(
    #             x=row['Mês'],
    #             y=row['Valor'],
    #             text=f"{row['Valor']:.0f}%".replace('.', ','),
    #             showarrow=True,
    #             arrowhead=2,
    #             ax=0,
    #             ay=-10,
    #             font=dict(size=10),
    #             align="center"
    #         )

    # # Set y-axis limit to exactly 100
    fig.update_yaxes(range=[0, maximo])
    # if filtro_visualização == "Por Profissional":

    #     max_val = df_medico["Valor"].max()
    #     min_val = df_medico["Valor"].min()

    #     # Add a 10% margin to the max and min values
    #     y_max = 1.1 * max_val
    #     y_min = 0.9 * max_val  # Use max_val for consistent scaling

    #     # Ensure y_min is not negative
    #     y_min = max(0, y_min)

    #     print(y_min, y_max)

    #     # Update the y-axis range dynamically
    #     fig.update_yaxes(range=[y_min, y_max])

    # Display the plot in Streamlit
    st.plotly_chart(fig, width="stretch")
