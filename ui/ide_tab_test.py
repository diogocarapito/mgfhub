import streamlit as st

from ui.ui_utils import warning_if_empty

# from ui.components import visualization_options_ui

# from utils.etl_relatorios import (
#     etl_bicsp,
#     etl_mimuf,
#     extracao_areas_clinicas,
#     merge_portaria_bicsp,
#     process_indicador,
# )
# from utils.vis_relatorios import (
#     sunburst_bicsp,
#     dumbbell_plot,
#     tabela,
#     ide_bar,
#     horizontal_bar,
#     sunburst_mimuf,
# )


@st.cache_data(experimental_allow_widgets=True)
def test_tab(df_bicsp=None, df_mimuf=None):
    warning_if_empty(df_bicsp, df_mimuf)

    # visual_options = visualization_options_ui(df_bicsp)

    st.write(df_bicsp)
    st.write(df_mimuf)
    # st.write(visual_options)
