import streamlit as st
from utils.etl_relatorios import (
    # etl_bicsp,
    # etl_mimuf,
    # extracao_areas_clinicas,
    # merge_portaria_bicsp,
    process_indicador,
    process_filter_temporal,
)
from utils.vis_relatorios import (
    # sunburst_bicsp,
    # dumbbell_plot,
    # tabela,
    ide_bar,
    horizontal_bar,
    # sunburst_mimuf,
    line_chart,
)


# @st.cache_data
def tab_visao_indicador(df_mimuf):
    # (
    #     col_indicador,
    #     col_visualizacao,
    # ) = st.columns([5, 2])

    with st.container(border=True):
        col_filter_1, col_filter_2 = st.columns([1, 1])
        with col_filter_1:
            dataframe_selected = st.selectbox(
                "Escolha o mês de analise",
                df_mimuf,
            )
        with col_filter_2:
            st.session_state["opcao_visualizacao_tab_indicador"] = st.radio(
                "Visualização",
                ["Equipa", "Evolução temporal"],
                horizontal=True,
                key="opcao_visualizacao_indicador",
            )

        # with col_indicador:
        list_dfs = list(df_mimuf.keys())

        lista_indicadores = df_mimuf[list_dfs[0]]["df"]["Nome"].unique()
        lista_indicadores = lista_indicadores[1:]

        # get just the characters before the first space in each element of the list
        lista_nun_indicadores = [i.split(" - ")[0] for i in lista_indicadores]

        filtro_indicador_id = st.pills(
            # filtro_indicador = st.selectbox(
            "Indicador",
            (lista_nun_indicadores),
            # horizontal=True,
            selection_mode="single",
            default=lista_nun_indicadores[0],
        )

        if filtro_indicador_id is None:
            filtro_indicador_id = lista_nun_indicadores[0]

        # get the index of the selected indicator
        selected_index = lista_nun_indicadores.index(filtro_indicador_id)
        # get the corresponinf name in the lista_indicadores
        filtro_indicador = lista_indicadores[selected_index]

        # with col_visualizacao:
        # radio escolha visualização

        (
            col_visualizacao,
            _,
        ) = st.columns([1, 1])

    #        with col_filtro_equipa_1:

    # with col_filtro_equipa_2:
    #     lista_indicadores = df_mimuf[dataframe_selected]["df"]["Nome"].unique()
    #     filtro_indicador = st.selectbox(
    #         "Indicador",
    #         (lista_indicadores[1:]),
    #     )

    # processar infomração por médico para unidade
    valores_indicador = process_indicador(
        df_mimuf[dataframe_selected]["df"].loc[
            df_mimuf[dataframe_selected]["df"]["Nome"] == filtro_indicador
        ]
    )

    filtro_indicador_id = filtro_indicador.split(" ")[0]
    link = f"https://sdm.min-saude.pt/BI.aspx?id={filtro_indicador_id}"
    # text = f"link SDM indicador {filtro_indicador_id}"

    # st.markdown(f"[{text}]({link})")

    # if valores_indicador["nome_indicador"] has "[" or "]" substitute for ( and )
    if "[" in valores_indicador["nome_indicador"]:
        valores_indicador["nome_indicador"] = valores_indicador[
            "nome_indicador"
        ].replace("[", "(")
    if "]" in valores_indicador["nome_indicador"]:
        valores_indicador["nome_indicador"] = valores_indicador[
            "nome_indicador"
        ].replace("]", ")")

    st.markdown(
        f'### [{valores_indicador["nome_indicador"]}]({link})',
        unsafe_allow_html=True,
    )

    if st.session_state["opcao_visualizacao_tab_indicador"] == "Equipa":
        # col_filtro_equipa_1, col_filtro_equipa_2, col_visualizacao = st.columns(
        #     [2, 4, 2]
        # )
        # with col_visualizacao:
        #     st.session_state["opcao_visualizacao_2"] = st.radio(
        #         "Ordenar por:",
        #         ["Valor", "Numerador", "Denominador"],
        #         index=1,
        #         horizontal=True,
        #     )

        list_indidacores_no_metric = [
            269,
            302,
            310,
            311,
            312,
            330,
            331,
            335,
            341,
            354,
            404,
            409,
            412,
            314,
            294,
        ]

        if valores_indicador["id_indicador"] in list_indidacores_no_metric:
            num_utentes_amarelo = "NA"
            num_utentes_verde = "NA"
            valores_indicador["quantos_faltam_aceitavel"] = 0
            valores_indicador["quantos_faltam_esperado"] = 0
        else:
            num_utentes_amarelo = 1 + int(
                valores_indicador["denominador"]
                * valores_indicador["min_aceitavel"]
                / 100,
            )
            num_utentes_verde = 1 + int(
                valores_indicador["denominador"]
                * valores_indicador["min_esperado"]
                / 100,
            )
        st.info(
            "Nota: É necessário colocar todos os médicos para as métricas serem calculadas para a unidade toda corretamente."
        )

        # visualização barra horizontal com os valores indicador
        (
            _,
            metric_col_1,
            metric_col_2,
            metric_col_3,
            metric_col_4,
            _,
        ) = st.columns(
            [1, 2, 2, 2, 2, 1]  # , vertical_alignment="center"
        )

        with metric_col_1:
            st.metric(
                "Denominador",
                value=int(valores_indicador["denominador"]),
                help="Número total de utentes relacionados com este indicador",
            )

        with metric_col_2:
            st.metric(
                "Numerador",
                value=int(valores_indicador["numerador"]),
                help="Número total de utentes cumpridores deste indicador",
            )

        with metric_col_3:
            st.metric(
                "Utentes p/ aceitável",
                value=num_utentes_amarelo,
                delta=int(valores_indicador["quantos_faltam_aceitavel"]),
                help="Numero de cumpridores necessários para atingir o valor aceitável para o indicador. Por baixo reflete o número actual acima ou abaixo do alvo mínimo aceitável (Amarelo)",
            )

        with metric_col_4:
            st.metric(
                "Utentes p/ esperado",
                value=num_utentes_verde,
                delta=int(valores_indicador["quantos_faltam_esperado"]),
                help="Numero de cumpridores necessários para atingir o valor aceitável para o indicador. Por baixo reflete o número actual acima ou abaixo do alvo mínimo esperado (Verde)",
            )

        _, ide_bar_col_2, ide_bar_col_3 = st.columns(
            [1, 15, 4], vertical_alignment="center"
        )

        with ide_bar_col_2:
            ide_bar(valores_indicador)

        with ide_bar_col_3:
            st.session_state["opcao_visualizacao_2"] = st.radio(
                "Ordenar por:",
                ["Valor", "Numerador", "Denominador"],
                index=1,
                horizontal=True,
            )

        col_graph_1, col_graph_2 = st.columns([5, 3])

        # link for sdm by using th id of the indicador selected
        # extract the initial numbers inside this string

        # with col_graph_empty:

        with col_graph_1:
            horizontal_bar(
                df_mimuf[dataframe_selected]["df"].loc[
                    df_mimuf[dataframe_selected]["df"]["Nome"] == filtro_indicador
                ],
                df_mimuf[dataframe_selected]["ano"],
                st.session_state["opcao_visualizacao_2"],
                int(filtro_indicador_id),
            )

        with col_graph_2:
            df_num_den_med = (
                df_mimuf[dataframe_selected]["df"]
                .loc[df_mimuf[dataframe_selected]["df"]["Nome"] == filtro_indicador][
                    ["Médico Familia", "Numerador", "Denominador", "Valor"]
                ]
                .sort_values(
                    by=st.session_state["opcao_visualizacao_2"], ascending=False
                )
            )

            if df_num_den_med.shape[0] > 0:
                row_height = int(310 / (df_num_den_med.shape[0]))
            else:
                row_height = 35  # default row height

            df_num_den_med["Valor"] = df_num_den_med["Valor"].apply(
                lambda x: f"{x:.1f}"
            )

            st.dataframe(
                df_num_den_med,
                hide_index=True,
                row_height=row_height,
                height=(df_num_den_med.shape[0]) * row_height + 35 + 3,
            )

    elif st.session_state["opcao_visualizacao_tab_indicador"] == "Evolução temporal":
        data_evolucao_temporal = process_filter_temporal(df_mimuf, filtro_indicador)

        with col_visualizacao:
            filtro_visualização = st.radio(
                "TIpo de visualização",
                ["Unidade", "Por profissional"],
                index=0,
                horizontal=True,
                # label_visibility="collapsed",
            )
        line_chart(data_evolucao_temporal, filtro_visualização)
