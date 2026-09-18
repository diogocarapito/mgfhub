"""Transformações pós-ETL usadas nas vistas por indicador/profissional."""

import math

import pandas as pd

from core.reference import load_indicadores

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


# indicadores em que as métricas de utentes em falta não fazem sentido
# (índices, despesas, taxas por 1000, etc.)
LIST_INDICADORES_SEM_METRICA = [
    269,
    302,
    310,
    311,
    312,
    330,
    331,
    335,
    341,
    354,
    404,
    409,
    412,
    314,
    294,
]


def extracao_areas_clinicas(df):
    return df["Área clínica"].unique().tolist()


def mask_scores_bicsp(df, areas=None, score_range=(0.0, 2.0), peso_range=(1.2, 10.0)):
    """Anula o Score dos indicadores fora dos filtros (área clínica, score,
    peso) — os indicadores continuam no sunburst mas sem cor/contributo."""
    df = df.copy()

    mask_range = (df["Score"] < score_range[0]) | (df["Score"] > score_range[1])
    df.loc[mask_range, "Score"] = None

    mask_peso = (df["Ponderação"] < peso_range[0]) | (df["Ponderação"] > peso_range[1])
    df.loc[mask_peso, "Score"] = None

    if areas:
        df.loc[~df["Área clínica"].isin(areas), "Score"] = None

    return df


def metricas_ide(df_sunburst):
    """IDE atual, IDE máximo teórico para os filtros ativos e a diferença."""
    tem_ide = df_sunburst.loc[df_sunburst["Nome"] == "IDE", "Score"].notnull().any()
    ide = (
        df_sunburst.loc[
            (df_sunburst["Nome"] == "IDE") & (df_sunburst["Score"].notnull()),
            "Resultado",
        ]
        .values[0]
        .round(1)
        if tem_ide
        else None
    )

    # soma leaf + linha IDE (100) − 100 = máximo atingível com os filtros
    max_ide = df_sunburst.loc[
        ~df_sunburst["Dimensão"].isin(["IDE", None]) & df_sunburst["Score"].notnull(),
        "Ponderação",
    ].sum()
    max_ide -= 100
    max_ide = round(max_ide, 1)

    diferenca = round(ide - max_ide, 1) if ide is not None else None

    return {"ide": ide, "max_ide": max_ide, "diferenca": diferenca}


def resumo_indicador_equipa(valores_indicador):
    """Nº de utentes cumpridores necessários para os alvos aceitável/esperado
    (NA para os indicadores em que a métrica não faz sentido)."""
    if valores_indicador["id_indicador"] in LIST_INDICADORES_SEM_METRICA:
        return {
            "num_utentes_amarelo": "NA",
            "num_utentes_verde": "NA",
            "faltam_aceitavel": 0,
            "faltam_esperado": 0,
        }

    return {
        "num_utentes_amarelo": 1
        + int(
            valores_indicador["denominador"] * valores_indicador["min_aceitavel"] / 100
        ),
        "num_utentes_verde": 1
        + int(
            valores_indicador["denominador"] * valores_indicador["min_esperado"] / 100
        ),
        "faltam_aceitavel": int(valores_indicador["quantos_faltam_aceitavel"]),
        "faltam_esperado": int(valores_indicador["quantos_faltam_esperado"]),
    }


def prepara_tabela_unidade(df):
    """Prepara a tabela da visão de unidade: só indicadores com score,
    com link para o SDM."""
    df = df.loc[df["Dimensão"] != "IDE"]

    links = load_indicadores()[["id", "link_sdm"]]
    df = df.merge(links, on="id", how="left")

    df = df.set_index("id")
    df = df[df.index.notnull()]
    df = df.dropna(subset=["Score"])

    return df


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
        # .copy() — senão o "filtered_df[...] = ..." mexeria numa fatia do
        # dataframe guardado na sessão (SettingWithCopyWarning / corrupção)
        filtered_df = df_mimuf[each]["df"].loc[
            df_mimuf[each]["df"]["id"] == int(id_indicador_selected)
        ].copy()
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
