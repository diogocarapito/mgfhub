"""Testes golden-master: o package core/ tem de reproduzir exatamente os
outputs da implementação original (capturados em tests/goldens/ antes do
refactor — ver tests/goldens/capture_goldens.py)."""

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from core import (
    etl_bicsp,
    etl_mimuf,
    merge_portaria_bicsp,
    process_filter_temporal,
    process_indicador,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
GOLDENS = REPO_ROOT / "tests" / "goldens"


def _assert_matches_golden(df, golden_name, tmp_path):
    """Compara via roundtrip parquet para normalizar dtypes de ambos os lados
    da mesma forma (os goldens estão guardados em parquet)."""
    path = tmp_path / f"{golden_name}.result.parquet"
    df.to_parquet(path)
    result = pd.read_parquet(path)
    golden = pd.read_parquet(GOLDENS / f"{golden_name}.parquet")
    pd.testing.assert_frame_equal(result, golden)


@pytest.fixture(name="res_bicsp", scope="module")
def fixture_res_bicsp():
    return etl_bicsp(
        [
            FIXTURES / "bicsp_com_cabecalho_2024_06.xlsx",
            FIXTURES / "bicsp_sem_cabecalho_2024_07.xlsx",
        ]
    )


@pytest.fixture(name="res_mimuf", scope="module")
def fixture_res_mimuf():
    return etl_mimuf(
        [
            FIXTURES / "mimuf_unidade_2024_06.xlsx",
            FIXTURES / "mimuf_medico_2024_06.xlsx",
        ]
    )


def test_bicsp_com_cabecalho(res_bicsp, tmp_path):
    entry = res_bicsp["USF Fixture 06/2024"]
    assert entry["ano"] == "2024"
    assert entry["mes"] == "06"
    assert entry["unidade"] == "USF Fixture"
    _assert_matches_golden(entry["df"], "bicsp_usf_fixture_2024_06", tmp_path)


def test_bicsp_sem_cabecalho(res_bicsp, tmp_path):
    entry = res_bicsp["bicsp_sem_cabecalho_2024_07.xlsx 07/2024"]
    assert entry["unidade"] == "bicsp_sem_cabecalho_2024_07.xlsx"
    _assert_matches_golden(entry["df"], "bicsp_sem_cabecalho_2024_07", tmp_path)


def test_merge_portaria_bicsp(res_bicsp, tmp_path):
    entry = res_bicsp["USF Fixture 06/2024"]
    df = merge_portaria_bicsp(entry["df"], entry["ano"])
    _assert_matches_golden(df, "merge_portaria_usf_fixture_2024_06", tmp_path)


def test_mimuf_unidade(tmp_path):
    res = etl_mimuf([FIXTURES / "mimuf_unidade_2024_06.xlsx"])
    entry = res["USF Fixture 06/2024"]
    assert entry["ano"] == "2024"
    assert entry["mes"] == "06"
    _assert_matches_golden(entry["df"], "mimuf_unidade_2024_06", tmp_path)


def test_mimuf_concat_unidade_mais_medico(res_mimuf, tmp_path):
    # os dois ficheiros têm a mesma unidade+mês → concatenados numa entrada
    assert list(res_mimuf.keys()) == ["USF Fixture 06/2024"]
    _assert_matches_golden(
        res_mimuf["USF Fixture 06/2024"]["df"], "mimuf_concat_2024_06", tmp_path
    )


def _assert_matches_json_golden(info, golden_name):
    with open(GOLDENS / f"{golden_name}.json", encoding="utf-8") as f:
        golden = json.load(f)
    assert set(info.keys()) == set(golden.keys())
    for key, expected in golden.items():
        got = info[key]
        if isinstance(expected, float):
            assert got == pytest.approx(expected), key
        else:
            assert got == expected, key


def test_process_indicador(res_mimuf):
    df = res_mimuf["USF Fixture 06/2024"]["df"]
    nome_8 = df.loc[df["id"] == 8, "Nome"].iloc[0]
    _assert_matches_json_golden(
        process_indicador(df.loc[df["Nome"] == nome_8]), "indicador_8"
    )


def test_process_indicador_valor_10x(res_mimuf):
    # 341 pertence à lista de indicadores com valor a dividir por 100
    df = res_mimuf["USF Fixture 06/2024"]["df"]
    nome_341 = df.loc[df["id"] == 341, "Nome"].iloc[0]
    _assert_matches_json_golden(
        process_indicador(df.loc[df["Nome"] == nome_341]), "indicador_341"
    )


def test_process_filter_temporal(res_mimuf, tmp_path):
    df = res_mimuf["USF Fixture 06/2024"]["df"]
    nome_8 = df.loc[df["id"] == 8, "Nome"].iloc[0]
    result = process_filter_temporal(res_mimuf, nome_8)
    # mesma normalização usada na captura: a linha "Unidade" tem id str
    result["id"] = result["id"].astype(str)
    _assert_matches_golden(result, "filter_temporal_8", tmp_path)


def test_on_upload_callback():
    events = []
    etl_bicsp(
        [FIXTURES / "bicsp_com_cabecalho_2024_06.xlsx"],
        on_upload=lambda *args: events.append(args),
    )
    assert events == [("USF Fixture", "2024", "06", "bicsp")]


def test_core_nao_importa_frameworks():
    """core/ tem de continuar pandas puro: sem streamlit nem supabase."""
    code = (
        "import sys; import core; "
        "assert 'streamlit' not in sys.modules, 'core importou streamlit'; "
        "assert 'supabase' not in sys.modules, 'core importou supabase'"
    )
    subprocess.run(
        [sys.executable, "-c", code], check=True, cwd=REPO_ROOT, capture_output=True
    )
