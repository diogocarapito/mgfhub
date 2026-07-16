"""Funções partilhadas de limpeza/normalização dos ficheiros exportados."""

import pandas as pd


def medico(df: pd.DataFrame, column="Médico Familia") -> pd.DataFrame:
    """Normaliza nomes de médicos: title case, sem espaços duplos/finais."""
    df.loc[:, column] = df.loc[:, column].str.title()

    # remove the double spaces in the string
    df.loc[:, column] = df.loc[:, column].str.replace("  ", " ")

    # remove the last space in the string
    df.loc[:, column] = df.loc[:, column].str.rstrip()

    return df


def extrair_id(df, coluna):
    """Extrai o id numérico do código do indicador (ex: "2013.001.01 FL" → 1).

    Linhas terminadas em "FX" são descartadas, exceto "2020.435.01 FX".
    """
    df = df[~(df[coluna].str.endswith("FX") & (df[coluna] != "2020.435.01 FX"))]

    df[coluna] = (
        df[coluna].str.extract(r"\.(\d+)\.", expand=False).fillna(0).astype(int)
    )

    return df
