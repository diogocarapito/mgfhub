import streamlit as st
from utils.utils import data_source, filter_df
from utils.style import page_config, main_title, cartao_indicador, bottom_suport_email

from monitor.telemetry import record_query

# Configuração da página
page_config()

# titulo principal estilizado com a função main_title
main_title("Indicadores")


# Variaveis iniciais
# carregar o dataframe com os indicadores
@st.cache_data()
def load_indicadores():
    return data_source("indicadores_sdm_complete.csv")


df = load_indicadores()

# opções de filtros para o radio
radio_optioins = ["IDE", "IDG", "BI-CSP", "Todos"]


def update_dataframes(dataframe, texto_pesquisa, filtro_contratualizacao, areas):
    # filtragem do dataframe com base na pesquisa e nos filtros
    filtered = (
        filter_df(
            dataframe,
            texto_pesquisa,
            filtro_contratualizacao,
            areas,
        )
        .set_index("id")
        .sort_index()
    )

    # dataframe com os indicadores para visualização, filtrando as colunas
    # que não são necessárias para a tabela
    showable = filtered.drop(columns=["ide", "idg", "Área | Subárea | Dimensão"])

    return filtered, showable


# user interface
col_pesquisa_1, col_pesquisa_2 = st.columns([11, 1])

with col_pesquisa_1:
    # campo de pesquisa
    pesquisa = st.text_input(
        label="Pesquisa de indicadores",
        value="",
        help="Pesquisa indicadores por nome, código ou conjunto de palavras",
    )

# coluna para o botão de pesquisa
with col_pesquisa_2:
    # espaço para alinhar o botão com o campo de pesquisa
    st.markdown("<div style='margin-top: 29px;'></div>", unsafe_allow_html=True)
    # botão de pesquisa (a pesquisa é aplicada automaticamente; o botão força um rerun)
    st.button("🔎")


# colunas de filtros para arrumar a interface
col_filtros_1, col_filtros_2, col_filtros_3 = st.columns([5, 5, 3])

# coluna com o radio de filtros
with col_filtros_1:
    # radio de filtros para afunilar a pesquisa
    filtros = st.radio(
        "Filtro por contratualização",
        options=radio_optioins,
        index=0,
        horizontal=True,
        help="Filtrar por tipo de indicadores (IDE - Indicadores actuais; IDG - Indicadores antes de 2024; BI-CSP - 128 Indicadores disponíveis no BICSP; Todos - Todos os indicadores existentes no SDM)",
    )

# as opções de área clínica dependem da pesquisa e do filtro de contratualização,
# mas não da própria seleção de áreas (senão as opções colapsavam ao selecionar)
opcoes_area_df, _ = update_dataframes(df, pesquisa, filtros, [])

with col_filtros_2:
    filtro_area_clinica = st.multiselect(
        "Filtro por área clínica",
        opcoes_area_df["Área clínica"].unique(),
        placeholder="Selecione uma ou mais áreas clínicas",
        help="Podes selecionar mais do que um filtro. Nota - algumas áreas clínicas estão erradamente classificadas na fonte dos dados (exemplo: Resporatório tem indicadores de Saúde Mental) ",
    )

# filtragem final com todos os filtros aplicados
filtered_df, showable_df = update_dataframes(df, pesquisa, filtros, filtro_area_clinica)

# telemetria: regista apenas quando a pesquisa/filtros mudam, não a cada rerun
query_sig = (pesquisa, filtros, tuple(filtro_area_clinica))
if st.session_state.get("last_query_sig") != query_sig:
    st.session_state["last_query_sig"] = query_sig
    record_query(pesquisa, filtros, filtro_area_clinica)

# Cálculo do numero de indicadores
with col_filtros_3:
    num_indicatores = len(filtered_df)
    st.metric("Nº de indicadores", num_indicatores)


# tab com 2 opções de visualização dos indicadores encontrados: tabela e cartões
# cartões default
cards, table = st.tabs(["Cartões", "Tabela"])

# se não houver indicadores encontrados, mensagem de aviso
if len(filtered_df) == 0:
    # mensagem de aviso
    st.warning("Nenhum indicador encontrado")

else:
    # tab com os cartões
    with cards:
        # loop entre todos os indicadores para criar os cartões para cada
        for index, row in filtered_df.iterrows():
            # função para criar os cartões predifinida
            cartao_indicador(index, row.to_dict())

    with table:
        # dataframe com os indicadores para visualização

        st.dataframe(
            # dataframe com os indicadores para visualização
            showable_df,
            # configuração da coluna link_sdm para ter o link para o sdm
            column_config={
                "link_sdm": st.column_config.LinkColumn(
                    label="Link",
                    display_text="SDM",
                )
            },
            width="stretch",
            # esconder o index
            hide_index=False,
            # ordem das colunas
            column_order=[
                "id",
                "link_sdm",
                "Nome abreviado",
                "Área clínica",
                "Intervalo Aceitável 2023",
                "Intervalo Esperado 2023",
                "Intervalo Aceitável 2024",
                "Intervalo Esperado 2024",
            ],
        )

bottom_suport_email()
