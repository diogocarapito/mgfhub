"""Cálculo de scores IDE a partir dos intervalos aceitáveis/esperados.

Score por indicador (0-2):
- fora do intervalo aceitável → 0
- dentro do intervalo esperado → 2
- entre aceitável e esperado → interpolação linear entre 0 e 2
"""

import pandas as pd

from core.reference import load_intervalos, load_portaria_sunburst


def calculate_score_mimuf(row):
    valor = float(row["Valor"])
    min_aceitavel = float(row["Mínimo Aceitável"])
    min_esperado = float(row["Mínimo Esperado"])
    max_esperado = float(row["Máximo Esperado"])
    max_aceitavel = float(row["Máximo Aceitável"])

    if valor > max_aceitavel or valor < min_aceitavel:
        return 0
    elif min_aceitavel <= valor < min_esperado:
        score_min = 2 * (valor - min_aceitavel) / (min_esperado - min_aceitavel)
        return score_min
    elif max_esperado < valor <= max_aceitavel:
        score_max = 2 * (max_aceitavel - valor) / (max_aceitavel - max_esperado)
        return score_max
    elif min_esperado <= valor <= max_esperado:
        return 2
    else:
        return 0


def calculate_score_bicsp(row):
    if (
        row["Resultado"] > row["Máximo Aceitável"]
        or row["Resultado"] < row["Mínimo Aceitável"]
    ):
        return 0
    elif row["Mínimo Aceitável"] <= row["Resultado"] < row["Mínimo Esperado"]:
        score_min = (
            2
            * (row["Resultado"] - row["Mínimo Aceitável"])
            / (row["Mínimo Esperado"] - row["Mínimo Aceitável"])
        )
        return score_min
    elif row["Máximo Esperado"] < row["Resultado"] <= row["Máximo Aceitável"]:
        score_max = (
            2
            * (row["Máximo Aceitável"] - row["Resultado"])
            / (row["Máximo Aceitável"] - row["Máximo Esperado"])
        )
        return score_max
    elif row["Mínimo Esperado"] <= row["Resultado"] <= row["Máximo Esperado"]:
        return 2
    else:
        # linhas sem dados (merge com a portaria) ficam "Error" e são descartadas
        return "Error"


def merge_portaria_bicsp(df_bicsp, ano):
    """Junta os resultados BI-CSP à estrutura da portaria e agrega os
    scores por dimensão e para o IDE global (para o sunburst).

    Os intervalos apresentados vêm de data/intervalos_ide.csv para o ano
    dos dados (com fallback para o ano disponível mais próximo)."""
    df_portaria = load_portaria_sunburst()[
        ["id", "Nome", "Dimensão", "Ponderação", "Lable"]
    ]

    df = df_portaria.merge(load_intervalos(ano), on="id", how="left")

    df = df.merge(
        df_bicsp[
            [
                "id",
                "Resultado",
                "Score",
                "Mês Ind",
                "Hierarquia Contratual - Área",
                "Área clínica",
            ]
        ],
        on="id",
        how="left",
    )

    # dimensões (exclui vazias e a linha IDE); não depende da ordem do unique()
    list_dimensoes = [
        x for x in df["Dimensão"].unique().tolist() if pd.notna(x) and x != "IDE"
    ]

    # calculate the score for each dimension based on the average wheighed score
    df["contributo"] = df["Ponderação"] * df["Score"] / 2

    for dim in list_dimensoes:
        df.loc[df["Nome"] == dim, "Resultado"] = df[df["Dimensão"] == dim][
            "contributo"
        ].sum()

    df.loc[df["Dimensão"] == "IDE", "Score"] = (
        2
        * df.loc[df["Dimensão"] == "IDE", "Resultado"]
        / df.loc[df["Dimensão"] == "IDE", "Ponderação"]
    )

    # linhas sem intervalos próprios (dimensões, IDE) mostram "N/A"
    df["Intervalo Aceitável"] = df["Intervalo Aceitável"].fillna("N/A")
    df["Intervalo Esperado"] = df["Intervalo Esperado"].fillna("N/A")

    # IDE
    df.loc[df["Nome"] == "IDE", "Resultado"] = df.loc[
        df["Dimensão"] == "IDE", "Resultado"
    ].sum()
    df.loc[df["Nome"] == "IDE", "Score"] = (
        2
        * df.loc[df["Nome"] == "IDE", "Resultado"]
        / df.loc[df["Nome"] == "IDE", "Ponderação"]
    )

    # make score a float
    df["Score"] = df["Score"].astype(float)

    return df
