import streamlit as st
from utils.style import page_config, main_title, bottom_suport_email, em_desenvolvimento

# from utils.grpd import consent_popup

from ui.ide_sidebar import ide_sidebar
from ui.ide_tab_unidade import tab_visao_unidade
from ui.ide_tab_indicador import tab_visao_indicador
from ui.ide_tab_profissional import tab_visao_profissional

# from ui.ide_tab_test import test_tab

import pandas as pd

from utils.vis_relatorios import sunburst_bicsp

page_config()

main_title("IDE")

# if "consent" not in st.session_state:
#     consent_popup()

# variaveis iniciais
# Dicinoários para guardar os dataframes carregados
st.session_state["df_bicsp"] = {}
st.session_state["df_mimuf"] = {}

# opções de visualização
st.session_state["opcao_visualizacao"] = "Sunburst"
st.session_state["opcao_visualizacao_2"] = "Barras + Tabela"
st.session_state["opcao_visualizacao_tab_indicador"] = "Equipa"

# mensagens de alerta de ficheiros não carregados
bicsp_nao_carregado = "Ficheiros do BI-CSP não carregados!"
mimuf_nao_carregado = "Ficheiros do MIM@UF não carregados!"

# Sidebar with uplods of xlsx files after etl
st.session_state["df_bicsp"], st.session_state["df_mimuf"] = ide_sidebar()


@st.cache_data
def load_data_sunburst():
    # load a dummy sunburst with score 1 in all parameters
    bicsp_score_1 = pd.read_csv("data/sunburst_score_1.csv", sep=";")

    return bicsp_score_1


# Tabs
# tab_test, tab_unidade, tab_indicador, tab_prof_geral, tab_nao_ide = st.tabs(
tab_unidade, tab_indicador, tab_prof_geral, tab_nao_ide = st.tabs(
    [
        # "test",
        "Visão de Unidade",
        "Visão por Indicador",
        "Visão por Profissional",
        "Indicadores não-IDE",
    ],
)

# with tab_test:
#     test_tab(st.session_state["df_bicsp"], st.session_state["df_mimuf"])

with tab_unidade:
    # mensagem se não houver ficheiros carregados
    if not st.session_state["df_bicsp"]:
        # warning message
        st.warning(bicsp_nao_carregado)

        st.divider()
        # Load and get a click return of which place was clicked
        sunburst_bicsp(load_data_sunburst(), 2000, "Janeiro", "USF ?", 560)

    else:
        tab_visao_unidade(st.session_state["df_bicsp"])


with tab_indicador:
    if not st.session_state["df_mimuf"]:
        st.warning(mimuf_nao_carregado)

    else:
        tab_visao_indicador(st.session_state["df_mimuf"])


with tab_prof_geral:
    # centered_title("Profissional - Visão Geral")

    if not st.session_state["df_mimuf"]:
        st.warning(mimuf_nao_carregado)

    elif len(st.session_state["df_mimuf"]) >= 1:
        tab_visao_profissional(st.session_state["df_mimuf"])


with tab_nao_ide:
    em_desenvolvimento()

    st.write("")
    st.write(
        "Futura visualização de indicadores que não contam para o IDE mas podem ser relevantes monitorizar para auditorias internas ou para preparar mudanças no IDE"
    )
    st.write("")


bottom_suport_email()
