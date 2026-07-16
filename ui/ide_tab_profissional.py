import streamlit as st

# from utils.etl_relatorios import (
#     etl_bicsp,
#     etl_mimuf,
#     extracao_areas_clinicas,
#     merge_portaria_bicsp,
#     process_indicador,
# )

from utils.vis_relatorios import (
    # sunburst_bicsp,
    # dumbbell_plot,
    # tabela,
    # ide_bar,
    # horizontal_bar,
    sunburst_mimuf,
)
from utils.style import em_desenvolvimento


# @st.cache_data
def tab_visao_profissional(df_mimuf):
    # radio escolha visualização
    st.session_state["opcao_visualizacao_tab_profissional"] = st.radio(
        "Visualização",
        ["Sunburst", "Comparaitivo"],
        horizontal=True,
        key="opcao_visualizacao_profissional",
    )

    st.divider()

    col_filtro_medico_1, col_filtro_medico_2 = st.columns(2)

    with col_filtro_medico_1:
        dataframe_selected = st.selectbox(
            "Escolha o dataframe",
            df_mimuf,
        )

    with col_filtro_medico_2:
        filtro_medico = st.selectbox(
            "Médico Familia",
            (df_mimuf[dataframe_selected]["df"]["Médico Familia"].unique()),
        )

    if st.session_state["opcao_visualizacao_tab_profissional"] == "Sunburst":
        sunburst_mimuf(
            df_mimuf[dataframe_selected]["df"][
                df_mimuf[dataframe_selected]["df"]["Médico Familia"] == filtro_medico
            ],
            df_mimuf[dataframe_selected]["ano"],
            df_mimuf[dataframe_selected]["mes"],
            df_mimuf[dataframe_selected]["unidade"],
            800,
        )

    elif st.session_state["opcao_visualizacao_tab_profissional"] == "Comparaitivo":
        col_sunburst_prof, col_sunburst_unidade = st.columns(2)

        with col_sunburst_prof:
            sunburst_mimuf(
                df_mimuf[dataframe_selected]["df"][
                    df_mimuf[dataframe_selected]["df"]["Médico Familia"]
                    == filtro_medico
                ],
                df_mimuf[dataframe_selected]["ano"],
                df_mimuf[dataframe_selected]["mes"],
                df_mimuf[dataframe_selected]["unidade"],
                400,
            )

        with col_sunburst_unidade:
            em_desenvolvimento()
            # sunburst_mimuf(
            #     df_mimuf[dataframe_selected]["df"],
            #     df_mimuf[dataframe_selected]["ano"],
            #     df_mimuf[dataframe_selected]["mes"],
            #     df_mimuf[dataframe_selected]["unidade"],
            #     400,
            # )
