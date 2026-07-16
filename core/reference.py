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
