"""Acesso aos dados de referência em data/ (portaria, indicadores).

Os caminhos são resolvidos a partir da raiz do repositório para que o
código funcione independentemente do diretório de trabalho (streamlit,
pytest, fastapi).
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_portaria_sunburst() -> pd.DataFrame:
    """Estrutura da Portaria 411-A/2023: indicadores, dimensões,
    ponderações e intervalos, no formato usado pelo sunburst."""
    return pd.read_csv(DATA_DIR / "sunburst_portaria_411a_2023.csv")


def load_indicadores() -> pd.DataFrame:
    """Dataset SDM completo dos indicadores (pesquisa, cartões, tabela)."""
    return pd.read_csv(DATA_DIR / "indicadores_sdm_complete.csv", index_col=0)


def load_intervalos(ano) -> pd.DataFrame:
    """Intervalos aceitáveis/esperados dos indicadores IDE para um ano.

    Fonte: data/intervalos_ide.csv (formato longo; um novo ano contratual
    é acrescentar linhas a esse CSV). Se o ano pedido não existir, usa o
    ano mais recente disponível anterior a ele (ex: dados de 2025 usam os
    intervalos de 2024 enquanto os de 2025 não forem publicados); se for
    anterior a todos, usa o mais antigo.

    Devolve colunas com os nomes de apresentação: id, Intervalo Esperado,
    Intervalo Aceitável, Mínimo/Máximo Aceitável, Mínimo/Máximo Esperado.
    """
    df = pd.read_csv(DATA_DIR / "intervalos_ide.csv")

    anos = sorted(df["ano"].unique())
    anteriores = [a for a in anos if a <= int(ano)]
    ano_escolhido = anteriores[-1] if anteriores else anos[0]

    df = df[df["ano"] == ano_escolhido].drop(columns=["ano"])
    df = df.rename(
        columns={
            "intervalo_esperado": "Intervalo Esperado",
            "intervalo_aceitavel": "Intervalo Aceitável",
            "min_aceitavel": "Mínimo Aceitável",
            "max_aceitavel": "Máximo Aceitável",
            "min_esperado": "Mínimo Esperado",
            "max_esperado": "Máximo Esperado",
        }
    )

    return df.reset_index(drop=True)
