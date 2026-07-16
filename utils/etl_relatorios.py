"""Adaptador Streamlit para o ETL em core/.

A lógica vive em core/ (pandas puro, testável, partilhável com a app
FastAPI v3). Aqui só se acrescenta o que é específico do Streamlit:
cache por sessão (st.cache_data) e efeitos laterais (telemetria,
st.warning) injetados por callback.

Os re-exports mantêm compatibilidade com os imports existentes
(ui/, utils/vis_relatorios.py, scripts/).
"""

import streamlit as st

from core import etl_bicsp as _etl_bicsp
from core import etl_mimuf as _etl_mimuf
from core import extracao_areas_clinicas as _extracao_areas_clinicas
from core import merge_portaria_bicsp as _merge_portaria_bicsp
from core import process_filter_temporal as _process_filter_temporal

# re-exports para compatibilidade com os imports existentes
# pylint: disable=unused-import
from core import (
    calculate_score_bicsp,
    calculate_score_mimuf,
    extrair_id,
    localizacao_coluna_medico,
    medico,
    process_indicador,
    split_metadata_from_df,
)

# pylint: enable=unused-import
from monitor.telemetry import record_upload


@st.cache_data()
def etl_bicsp(list_of_files):
    return _etl_bicsp(list_of_files, on_upload=record_upload)


@st.cache_data()
def etl_mimuf(list_of_files):
    return _etl_mimuf(
        list_of_files,
        on_upload=record_upload,
        on_warning=st.warning,
    )


@st.cache_data()
def merge_portaria_bicsp(df_bicsp, ano):
    return _merge_portaria_bicsp(df_bicsp, ano)


@st.cache_data()
def extracao_areas_clinicas(df):
    return _extracao_areas_clinicas(df)


@st.cache_data()
def process_filter_temporal(df_mimuf, filtro_indicador):
    return _process_filter_temporal(df_mimuf, filtro_indicador)
