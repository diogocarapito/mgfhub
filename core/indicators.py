"""Transformações pós-ETL usadas nas vistas por indicador/profissional."""

import math

import pandas as pd

# indicadores cujo valor vem multiplicado por 100 na fonte (índices 0-2,
# despesas, etc.) e é preciso dividir para apresentar
LIST_INDICADORES_VALOR_10X = [
    269,
    302,
    310,
    311,
    312,
    330,
    331,
    341,
    354,
    404,
]


def extracao_areas_clinicas(df):
    return df["Área clínica"].unique().tolist()


def process_indicador(df):
    """Agrega numerador/denominador de um indicador (todas as linhas do df)
    e calcula quantos cumpridores faltam para os alvos aceitável/esperado."""
    numerador = df["Numerador"].sum()
    denominador = df["Denominador"].sum()
    valor = numerador / denominador * 100
    min_esperado = df["Mínimo Esperado"].unique()[0]
    min_acetavel = df["Mínimo Aceitável"].unique()[0]
    # round up to the nearest integer
    quantos_faltam_aceitavel = -math.ceil(denominador * min_acetavel / 100 - numerador)
    quantos_faltam_esperado = -math.ceil(denominador * min_esperado / 100 - numerador)

    info_indicador = {
        "id_indicador": df["id"].unique()[0],
        "nome_indicador": df["Nome"].unique()[0],
        "min_aceitavel": min_acetavel,
        "min_esperado": min_esperado,
        "max_esperado": df["Máximo Esperado"].unique()[0],
        "max_aceitavel": df["Máximo Aceitável"].unique()[0],
        "numerador": numerador,
        "denominador": denominador,
        "valor": valor,
        "quantos_faltam_aceitavel": quantos_faltam_aceitavel,
        "quantos_faltam_esperado": quantos_faltam_esperado,
    }

    if info_indicador["id_indicador"] in LIST_INDICADORES_VALOR_10X:
        info_indicador["valor"] = info_indicador["valor"] / 100

    # 294 é por 1000 habitantes
    if info_indicador["id_indicador"] == 294:
        info_indicador["quantos_faltam_aceitavel"] = (
            info_indicador["denominador"] * min_acetavel / 1000 - numerador
        )
        info_indicador["quantos_faltam_esperado"] = (
            info_indicador["denominador"] * min_esperado / 1000 - numerador
        )

    return info_indicador


def process_filter_temporal(df_mimuf, filtro_indicador):
    """Prepara a evolução temporal de um indicador ao longo dos meses
    carregados, acrescentando por mês uma linha agregada "Unidade"."""
    id_indicador_selected = filtro_indicador.split(" - ")[0]

    list_dfs = list(df_mimuf.keys())

    filtered_dfs = []

    for each in list_dfs:
        filtered_df = df_mimuf[each]["df"].loc[
            df_mimuf[each]["df"]["id"] == int(id_indicador_selected)
        ]
        filtered_df["Mês"] = df_mimuf[each]["mes"]
        filtered_df["Ano"] = df_mimuf[each]["ano"]

        # linha agregada da unidade: média para os índices/despesas, senão
        # numerador/denominador agregados
        if (
            id_indicador_selected == "354"
            or id_indicador_selected == "341"
            or id_indicador_selected == "330"
            or id_indicador_selected == "331"
        ):
            valor = [round(filtered_df["Valor"].mean(), 2)]
        else:
            valor = [
                round(
                    filtered_df["Numerador"].sum()
                    / filtered_df["Denominador"].sum()
                    * 100,
                    1,
                )
            ]
        new_row = pd.DataFrame(
            {
                "id": [id_indicador_selected],
                "Mês": [df_mimuf[each]["mes"]],
                "Ano": [df_mimuf[each]["ano"]],
                "ano_mes": [f"{df_mimuf[each]['ano']}-{df_mimuf[each]['mes']}"],
                "Nome": [filtro_indicador],
                "Médico Familia": ["Unidade"],
                "Numerador": [filtered_df["Numerador"].sum()],
                "Denominador": [filtered_df["Denominador"].sum()],
                "Valor": valor,
                "Score": [0],
                "Mínimo Aceitável": [filtered_df["Mínimo Aceitável"].iloc[0]],
                "Mínimo Esperado": [filtered_df["Mínimo Esperado"].iloc[0]],
                "Máximo Esperado": [filtered_df["Máximo Esperado"].iloc[0]],
                "Máximo Aceitável": [filtered_df["Máximo Aceitável"].iloc[0]],
            }
        )

        filtered_df = pd.concat([new_row, filtered_df], ignore_index=True)

        filtered_dfs.append(
            filtered_df[
                [
                    "id",
                    "Mês",
                    "Ano",
                    "ano_mes",
                    "Nome",
                    "Médico Familia",
                    "Numerador",
                    "Denominador",
                    "Valor",
                    "Score",
                    "Mínimo Aceitável",
                    "Mínimo Esperado",
                    "Máximo Esperado",
                    "Máximo Aceitável",
                ]
            ]
        )

    # Concatenate all filtered DataFrames
    concatenated_df = pd.concat(filtered_dfs, ignore_index=True)

    # change the name of the columns
    concatenated_df = concatenated_df.rename(
        {
            "Mínimo Aceitável": "min_aceitavel",
            "Mínimo Esperado": "min_esperado",
            "Máximo Esperado": "max_esperado",
            "Máximo Aceitável": "max_aceitavel",
        },
        axis=1,
    )

    # order by ano and mes
    concatenated_df = concatenated_df.sort_values(by=["Ano", "Mês", "Médico Familia"])

    return concatenated_df
