"""Lógica de negócio do mgfhub, independente de framework.

Este package contém o ETL dos ficheiros BI-CSP/MIM@UF e o cálculo de
scores IDE (Portaria 411-A/2023) em pandas puro — sem streamlit, sem
supabase. É partilhado pela app Streamlit atual e pela futura app
FastAPI (v3). Efeitos laterais (telemetria, avisos ao utilizador) são
injetados por callbacks opcionais.
"""

from core.common import extrair_id, medico
from core.etl_bicsp import etl_bicsp
from core.etl_mimuf import etl_mimuf, localizacao_coluna_medico, split_metadata_from_df
from core.indicators import (
    extracao_areas_clinicas,
    process_filter_temporal,
    process_indicador,
)
from core.reference import DATA_DIR, load_intervalos, load_portaria_sunburst
from core.scoring import (
    calculate_score_bicsp,
    calculate_score_mimuf,
    merge_portaria_bicsp,
)

__all__ = [
    "DATA_DIR",
    "calculate_score_bicsp",
    "calculate_score_mimuf",
    "etl_bicsp",
    "etl_mimuf",
    "extracao_areas_clinicas",
    "extrair_id",
    "load_intervalos",
    "load_portaria_sunburst",
    "localizacao_coluna_medico",
    "medico",
    "merge_portaria_bicsp",
    "process_filter_temporal",
    "process_indicador",
    "split_metadata_from_df",
]
