"""Captura os outputs golden-master do ETL a partir dos fixtures sintéticos.

Os goldens foram capturados originalmente com a implementação pré-refactor
(utils/etl_relatorios.py, commit "Fix known bugs") e recapturados quando os
intervalos passaram a ser data-driven por ano (data/intervalos_ide.csv) —
ver a mensagem desse commit para o diff de comportamento.

Só deve ser re-executado quando uma mudança de comportamento é DELIBERADA;
nesse caso, rever o diff dos goldens e explicar a mudança no commit.

Executar a partir da raiz do repositório:
    python tests/goldens/capture_goldens.py
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDENS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"

sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from utils.etl_relatorios import (  # noqa: E402
    etl_bicsp,
    etl_mimuf,
    merge_portaria_bicsp,
    process_filter_temporal,
    process_indicador,
)


def _save_df(df, name):
    df.to_parquet(GOLDENS_DIR / f"{name}.parquet")
    print(f"wrote {name}.parquet ({df.shape[0]} rows)")


def _save_json(data, name):
    # normalizar tipos numpy para tipos python nativos
    clean = {k: (v.item() if hasattr(v, "item") else v) for k, v in data.items()}
    with open(GOLDENS_DIR / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)
    print(f"wrote {name}.json")


def main():
    # --- BICSP: as duas variantes num só upload ---
    res_bicsp = etl_bicsp(
        [
            FIXTURES_DIR / "bicsp_com_cabecalho_2024_06.xlsx",
            FIXTURES_DIR / "bicsp_sem_cabecalho_2024_07.xlsx",
        ]
    )
    _save_df(res_bicsp["USF Fixture 06/2024"]["df"], "bicsp_usf_fixture_2024_06")
    _save_df(
        res_bicsp["bicsp_sem_cabecalho_2024_07.xlsx 07/2024"]["df"],
        "bicsp_sem_cabecalho_2024_07",
    )

    # --- merge da portaria para o sunburst (visão de unidade) ---
    entry = res_bicsp["USF Fixture 06/2024"]
    _save_df(
        merge_portaria_bicsp(entry["df"], entry["ano"]),
        "merge_portaria_usf_fixture_2024_06",
    )

    # --- MIMUF: só unidade ---
    res_m1 = etl_mimuf([FIXTURES_DIR / "mimuf_unidade_2024_06.xlsx"])
    _save_df(res_m1["USF Fixture 06/2024"]["df"], "mimuf_unidade_2024_06")

    # --- MIMUF: unidade + por-médico (mesmo nome → ramo de concatenação) ---
    res_m2 = etl_mimuf(
        [
            FIXTURES_DIR / "mimuf_unidade_2024_06.xlsx",
            FIXTURES_DIR / "mimuf_medico_2024_06.xlsx",
        ]
    )
    _save_df(res_m2["USF Fixture 06/2024"]["df"], "mimuf_concat_2024_06")

    # --- transformações pós-ETL usadas na tab de indicador ---
    df_m = res_m2["USF Fixture 06/2024"]["df"]
    nome_8 = df_m.loc[df_m["id"] == 8, "Nome"].iloc[0]
    nome_341 = df_m.loc[df_m["id"] == 341, "Nome"].iloc[0]

    # indicador normal
    _save_json(process_indicador(df_m.loc[df_m["Nome"] == nome_8]), "indicador_8")
    # indicador da lista com valor a dividir por 100 (341)
    _save_json(process_indicador(df_m.loc[df_m["Nome"] == nome_341]), "indicador_341")

    # evolução temporal (inclui a linha agregada "Unidade")
    # nota: a linha "Unidade" tem id string e as restantes id int (quirk do
    # código atual); normalizamos para str só para o parquet — o teste aplica
    # a mesma normalização antes de comparar
    df_temporal = process_filter_temporal(res_m2, nome_8)
    df_temporal["id"] = df_temporal["id"].astype(str)
    _save_df(df_temporal, "filter_temporal_8")


if __name__ == "__main__":
    main()
