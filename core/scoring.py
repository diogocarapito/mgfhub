"""Cálculo de scores IDE a partir dos intervalos aceitáveis/esperados.

Score por indicador (0-2):
- fora do intervalo aceitável → 0
- dentro do intervalo esperado → 2
- entre aceitável e esperado → interpolação linear entre 0 e 2
"""

import pandas as pd

from core.reference import load_portaria_sunburst


def etiqueta_ano(df, ano):
    # cria as etiquetas para os intervalos aceitáveis e esperados com o ano
    # correcto correspondente aos dados extraídos
    # nota: hardcoded a 2024 desde a versão streamlit — passa a ser data-driven
    # quando os intervalos forem carregados de data/intervalos_ide.csv
    ano = 2024

    int_aceit = f"Intervalo Aceitável {ano}"
    int_esper = f"Intervalo Esperado {ano}"

    # caso não haja intervalos para o ano dos dados, por definição usa os de 2024
    if int_aceit not in df.columns or int_esper not in df.columns:
        int_aceit = "Intervalo Aceitável 2024"
        int_esper = "Intervalo Esperado 2024"

    return int_aceit, int_esper


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
    scores por dimensão e para o IDE global (para o sunburst)."""
    df_portaria = load_portaria_sunburst()

    df = df_portaria.merge(
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

    # list of dimensions and drop empty ones
    list_dimensoes = [x for x in df["Dimensão"].unique().tolist() if pd.notna(x)]

    # remove IDE
    list_dimensoes = list_dimensoes[1:]

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

    # apagar intervalos que não fazem sentido
    int_aceit, int_esper = etiqueta_ano(df, ano)
    df.loc[df["Dimensão"] == "IDE", int_aceit] = "N/A"
    df.loc[df["Dimensão"] == "IDE", int_esper] = "N/A"
    df.loc[df["Nome"] == "IDE", int_aceit] = "N/A"
    df.loc[df["Nome"] == "IDE", int_esper] = "N/A"

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
