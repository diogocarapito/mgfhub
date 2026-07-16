"""Testes unitários das funções de scoring e limpeza do core/."""

import pandas as pd
import pytest

from core import (
    calculate_score_bicsp,
    calculate_score_mimuf,
    extrair_id,
    load_intervalos,
    medico,
    split_metadata_from_df,
)


def _row_mimuf(valor):
    return {
        "Valor": valor,
        "Mínimo Aceitável": 40.0,
        "Mínimo Esperado": 60.0,
        "Máximo Esperado": 90.0,
        "Máximo Aceitável": 100.0,
    }


@pytest.mark.parametrize(
    "valor,esperado",
    [
        (30.0, 0),  # abaixo do mínimo aceitável
        (40.0, 0.0),  # no mínimo aceitável (início da interpolação)
        (50.0, 1.0),  # a meio entre aceitável e esperado
        (60.0, 2),  # no mínimo esperado
        (75.0, 2),  # dentro do intervalo esperado
        (90.0, 2),  # no máximo esperado
        (95.0, 1.0),  # a meio entre esperado e aceitável (descendo)
        (100.0, 0.0),  # no máximo aceitável
        (110.0, 0),  # acima do máximo aceitável
    ],
)
def test_calculate_score_mimuf(valor, esperado):
    assert calculate_score_mimuf(_row_mimuf(valor)) == pytest.approx(esperado)


def test_calculate_score_bicsp_error_para_linhas_sem_dados():
    # linhas da portaria sem correspondência no ficheiro (NaN) → "Error"
    row = {
        "Resultado": float("nan"),
        "Mínimo Aceitável": float("nan"),
        "Mínimo Esperado": float("nan"),
        "Máximo Esperado": float("nan"),
        "Máximo Aceitável": float("nan"),
    }
    assert calculate_score_bicsp(row) == "Error"


def test_extrair_id():
    df = pd.DataFrame(
        {
            "cod": [
                "2013.008.01 FL",  # normal → 8
                "2019.999.01 FX",  # termina em FX → descartada
                "2020.435.01 FX",  # exceção mantida → 435
                "sem codigo",  # sem padrão → 0
            ]
        }
    )
    result = extrair_id(df, "cod")
    assert result["cod"].tolist() == [8, 435, 0]


def test_medico_normalizacao():
    df = pd.DataFrame({"Médico Familia": ["ANA  PRIMEIRA ", "bruno segundo"]})
    result = medico(df)
    assert result["Médico Familia"].tolist() == ["Ana Primeira", "Bruno Segundo"]


def test_split_metadata_keyword_em_falta():
    df = pd.DataFrame({0: [f"meta {i}" for i in range(25)], 1: [None] * 25})
    with pytest.raises(ValueError):
        split_metadata_from_df(df, "Unidade Funcional / Polo Hospitalar")


def _min_aceitavel_294(df):
    return df.loc[df["id"] == 294, "Mínimo Aceitável"].iloc[0]


def test_load_intervalos_por_ano():
    # o indicador 294 tem intervalos diferentes em 2023 e 2024
    assert _min_aceitavel_294(load_intervalos(2023)) == 300.0
    assert _min_aceitavel_294(load_intervalos(2024)) == 150.0


def test_load_intervalos_fallback():
    # ano futuro sem intervalos publicados → usa o mais recente disponível
    assert _min_aceitavel_294(load_intervalos(2025)) == 150.0
    # ano anterior a todos os disponíveis → usa o mais antigo
    assert _min_aceitavel_294(load_intervalos(2022)) == 300.0
    # o ETL passa o ano como string
    assert _min_aceitavel_294(load_intervalos("2025")) == 150.0
