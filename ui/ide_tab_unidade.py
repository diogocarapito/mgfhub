import streamlit as st
from utils.etl_relatorios import (
    # etl_bicsp,
    # etl_mimuf,
    extracao_areas_clinicas,
    merge_portaria_bicsp,
    # process_indicador,
)
from utils.vis_relatorios import (
    sunburst_bicsp,
    dumbbell_plot,
    tabela,
    # ide_bar,
    # horizontal_bar,
    # sunburst_mimuf,
)


def radio_opcao_visualizacao(df_bicsp):
    opções_visualizacao = (
        [
            "Sunburst",
            "Tabela",
            "Sunburst + Tabela",
            "Dumbbell",
            "Sunburst + Sunburst",
        ]
        if len(df_bicsp) > 1
        else ["Sunburst", "Tabela", "Sunburst + Tabela", "Dumbbell"]
    )

    # Dumbbell chart by default if more than one file uploaded
    index_visualizacao = 3 if len(df_bicsp) > 1 else 0

    # radio escolha visualização
    return st.radio(
        "Visualização",
        opções_visualizacao,
        horizontal=True,
        index=index_visualizacao,
        # label_visibility="collapsed",
        key="opcao_visualizacao_1",
    )


# @st.cache_data
def tab_visao_unidade(df_bicsp):
    st.session_state["opcao_visualizacao"] = radio_opcao_visualizacao(df_bicsp)

    # filtros
    (
        col_filter_1,
        col_filter_2,
        col_filter_2_1,
        col_filter_3,
        col_filter_4,
        col_filter_4_1,
    ) = st.columns([3, 1, 1, 3, 1, 1])

    # escolha do dataframe de analise
    with col_filter_1:
        escolha = st.selectbox("Escolha o dados para análise", df_bicsp)

    if st.session_state["opcao_visualizacao"] != "Dumbbell":
        # st.divider()
        col_2_filter_1, space_1, col_2_filter_2, space_2, col_2_filter_3 = st.columns(
            [8, 1, 4, 1, 4]
        )
        # filtro de areas clinicas
        with space_1:
            st.empty()
        with space_2:
            st.empty()
        # get the unique values of "Área clínica" from the dataframe
        areas_clinicas = extracao_areas_clinicas(df_bicsp[escolha]["df"])

        with col_2_filter_1:
            # selectbox for the "Área clínica"
            selected_areas = st.multiselect(
                "Área clínica", areas_clinicas, help="Filtrar por área clínica"
            )

        with col_2_filter_2:
            score_range = st.slider(
                "Score", 0.0, 2.0, (0.0, 2.0), 0.1, help="Filtrar por score (0-2)"
            )

        with col_2_filter_3:
            ponderacao_range = st.slider(
                "Peso",
                1.2,
                10.0,
                (1.2, 10.0),
                0.2,
                help="Filtrar por peso do indicador",
            )

        # if selected_areas is not empty, filter the dataframe and update df_bicsp

        for key, value in df_bicsp.items():
            # make Score None if score not in the range
            mask_range = (value["df"]["Score"] < score_range[0]) | (
                value["df"]["Score"] > score_range[1]
            )
            value["df"].loc[mask_range, "Score"] = None

            mask_poderacao = (value["df"]["Ponderação"] < ponderacao_range[0]) | (
                value["df"]["Ponderação"] > ponderacao_range[1]
            )
            value["df"].loc[mask_poderacao, "Score"] = None

            if selected_areas:
                # substitute the value in "Score" to None if the "Área clínica" is not in the selected_areas
                mask = value["df"]["Área clínica"].isin(selected_areas)
                value["df"].loc[~mask, "Score"] = None

            # update df_bicso with the new value
            df_bicsp[key] = value

    # processamento do dataframe
    df_sunburst = merge_portaria_bicsp(
        df_bicsp[escolha]["df"],
        df_bicsp[escolha]["ano"],
    )

    if st.session_state["opcao_visualizacao"] != "Dumbbell":
        # Change score to None if Ponderação is not in the ponderacao_range and Hierarquia is 'IDE- Desempenho'
        mask = (
            (df_sunburst["Ponderação"] < ponderacao_range[0])
            | (df_sunburst["Ponderação"] > ponderacao_range[1])
        ) & (df_sunburst["Hierarquia Contratual - Área"] == "IDE - Desempenho")
        df_sunburst.loc[mask, "Score"] = None

    # metrica IDE
    with col_filter_2:
        ide = (
            (
                df_sunburst.loc[
                    (df_sunburst["Nome"] == "IDE") & (df_sunburst["Score"].notnull()),
                    "Resultado",
                ]
                .values[0]
                .round(1)
            )
            if df_sunburst.loc[df_sunburst["Nome"] == "IDE", "Score"].notnull().any()
            else None
        )

        # sum of all "Poderação" if Score is not Null
        max_ide = df_sunburst.loc[
            ~df_sunburst["Dimensão"].isin(["IDE", None])
            & df_sunburst["Score"].notnull(),
            "Ponderação",
        ].sum()
        max_ide -= 100
        max_ide = max_ide.round(1)

        diference = (ide - max_ide).round(1)

        # diference_percentage =diference/max_ide

        st.metric("IDE", ide)

    with col_filter_2_1:
        st.metric(
            "IDE máximo",
            max_ide,
            -diference,
            help="IDE máximo teórico para os filtros selecionados em baixo. O número a verde representa o potencial ganho no IDE se se cumprir com score 2 todos os indicadores incluídos no mesmo filtro",
        )

    # SUNBURST
    if st.session_state["opcao_visualizacao"] == "Sunburst":
        # if len(df_bicsp) == 1:
        sunburst_bicsp(
            df_sunburst,
            df_bicsp[escolha]["ano"],
            df_bicsp[escolha]["mes"],
            df_bicsp[escolha]["unidade"],
            800,
        )

    # TABELA
    if st.session_state["opcao_visualizacao"] == "Tabela":
        # tabela
        if len(df_bicsp) >= 1:
            # st.write(df_sunburst[["Nome", "Resultado", "Score"]])
            tabela(
                df_sunburst,
                df_bicsp[escolha]["ano"],
                df_bicsp[escolha]["nome"],
            )

    # SUNBURST + TABELA
    if st.session_state["opcao_visualizacao"] == "Sunburst + Tabela":
        col_1, col_2 = st.columns([1, 1])
        with col_1:
            sunburst_bicsp(
                df_sunburst,
                df_bicsp[escolha]["ano"],
                df_bicsp[escolha]["mes"],
                df_bicsp[escolha]["unidade"],
                500,
            )
        with col_2:
            # tabela
            if len(df_bicsp) >= 1:
                # st.subheader(df_bicsp[escolha]["unidade"])
                tabela(
                    df_sunburst,
                    df_bicsp[escolha]["ano"],
                    df_bicsp[escolha]["nome"],
                )

    if st.session_state["opcao_visualizacao"] == "Sunburst + Sunburst":
        with col_filter_3:
            escolha_2 = st.selectbox(
                "Escolha o 2ºs dados para análise", df_bicsp, index=1
            )

        df_sunburst_2 = merge_portaria_bicsp(
            df_bicsp[escolha_2]["df"],
            df_bicsp[escolha_2]["ano"],
        )

        # metrica IDE 2
        with col_filter_4:
            st.metric(
                "IDE 2º",
                df_sunburst_2.loc[df_sunburst_2["Nome"] == "IDE", "Resultado"]
                .values[0]
                .round(1),
            )

        with col_filter_4_1:
            st.empty()
        #     max_ide_2 = df_sunburst_2.loc[df_sunburst_2["Nome"] == "IDE", "Peso"].values[0].round(1)

        #     st.metric("IDE max 2", max_ide_2)

        col_sun_1, col_sun_2 = st.columns(2)

        with col_sun_1:
            sunburst_bicsp(
                df_sunburst,
                df_bicsp[escolha]["ano"],
                df_bicsp[escolha]["mes"],
                df_bicsp[escolha]["unidade"],
                500,
            )

        with col_sun_2:
            sunburst_bicsp(
                df_sunburst_2,
                df_bicsp[escolha_2]["ano"],
                df_bicsp[escolha_2]["mes"],
                df_bicsp[escolha_2]["unidade"],
                500,
            )

    if st.session_state["opcao_visualizacao"] == "Dumbbell":
        if len(df_bicsp) == 1:
            dumbbell_plot(
                {df_bicsp[escolha]["nome"]: df_sunburst},
                df_bicsp[escolha]["ano"],
            )
        elif len(df_bicsp) > 1:
            with col_filter_3:
                escolha_2 = st.selectbox("Escolha o 2º gráfico", df_bicsp, index=1)

            df_sunburst_2 = merge_portaria_bicsp(
                df_bicsp[escolha_2]["df"],
                df_bicsp[escolha_2]["ano"],
            )

            # metrica IDE 2
            with col_filter_4:
                st.metric(
                    "IDE nº2",
                    df_sunburst_2.loc[df_sunburst_2["Nome"] == "IDE", "Resultado"]
                    .values[0]
                    .round(1),
                )

            dumbbell_plot(
                {
                    df_bicsp[escolha]["nome"]: df_sunburst,
                    df_bicsp[escolha_2]["nome"]: df_sunburst_2,
                },
                df_bicsp[escolha]["ano"],
            )
        st.write(
            """Interpretação/dicas:
- Se passares o rato por cima do círculo/quadrado mostra mais informação sobre o indicador.
- O tamanho do círculo/quadrado representa o peso do indicador - indicadores com mais impacto do IDE serão representados com um tamanho maior.
- A cor representa o score do indicador, entre 0-2 num gradiente vermelho -> amarelo -> verde.
- Quando é introduzido uma segundo ficheiro xlsx, é calculada a diferença entre os dois periodos para permitir avaliar a evolução temporal. Automaticamente o dados mais antigos serão círculos e o mais recente quadrados (mesmo que em cima fique trocado). Fica ordenado pelos dados antigos dos indicadores com pior para melhor score.
- A linha representa a variação do indicador entre os dois periodos, quando a diferença é significativa aparece a seta a indicar a direção da variação.
- Se o indicador se mantiver no mesmo valor, o circulo e o quadrado ficam sobrepostos.
- Para visualizar com mais detalhe, clica no botão de ecrã inteiro no canto superior direito do gráfico para aumentar o tamanho.
"""
        )
