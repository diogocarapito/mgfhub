"""ETL dos ficheiros xlsx exportados do BI-CSP.

O export pode vir com uma linha de filtros no topo (versões PT e ENG) ou
diretamente com os cabeçalhos. Os intervalos aceitáveis/esperados vêm no
próprio ficheiro; a estrutura (dimensões, ponderações) vem da portaria.
"""

import re

import pandas as pd

from core.common import extrair_id
from core.reference import load_portaria_sunburst
from core.scoring import calculate_score_bicsp


def etl_bicsp(list_of_files, on_upload=None):
    """Processa uma lista de ficheiros xlsx do BI-CSP.

    Devolve um dicionário {"<unidade> <mes>/<ano>": {"df", "ano", "mes",
    "unidade", "nome"}}. Ficheiros da mesma unidade+mês são concatenados.
    `on_upload(unidade, ano, mes, "bicsp")` é chamado por ficheiro
    processado (telemetria).
    """
    if list_of_files is None:
        return None

    dict_dfs = {}

    dict_of_dfs = {
        xlsx_file.name: pd.read_excel(xlsx_file, engine="openpyxl")
        for xlsx_file in list_of_files
    }

    for file_name, df in dict_of_dfs.items():
        # get the file name
        unidade = file_name

        # processamento se o ficheiro tiver cabeçalho (summarized e underlying data)
        first_column_name = df.columns[0]

        # versão ENG
        if first_column_name.startswith("Applied"):
            # get the text in the header of the first column
            unidade = re.search(r"Nome UF is (.*)", first_column_name).group(1)

            # remove the first row
            df = df[1:]
            df.columns = df.iloc[0]
            df = df[1:]

            # reset index
            df = df.reset_index(drop=True)

        # versão PT
        elif first_column_name.startswith("Filtros"):
            unidade = re.search(r"Nome UF é (.*)", first_column_name).group(1)

            # remove the first row
            df = df[1:]
            df.columns = df.iloc[0]
            df = df[1:]

            # reset index
            df = df.reset_index(drop=True)

        # remove any row with "Designação Indicador (+ID)" None
        df = df[df["Designação Indicador (+ID)"].notnull()]

        # extrair o id do "Cód. Indicador"
        df = extrair_id(df, "Cód. Indicador")

        # rename "Cód. Indicador" to "id"
        df = df.rename(columns={"Cód. Indicador": "id"})

        # sort by id
        df = df.sort_values("id")

        # check if df["Hierarquia Contratual - Área"] has "IDE - Desempenho" and keep only those rows
        if df["Hierarquia Contratual - Área"].str.contains("IDE - Desempenho").any():
            df = df[df["Hierarquia Contratual - Área"].str.contains("IDE - Desempenho")]

        # extração do mês e ano
        ano_mes = str(df["Mês Ind"].unique().max())
        ano = ano_mes[:4]
        mes = ano_mes[4:6]

        nome = f"{unidade} {mes}/{ano}"

        df["Resultado"] = df["Resultado"].astype(float)

        df.rename(
            columns={
                "Min. Aceit": "Mínimo Aceitável",
                "Máx. Aceit": "Máximo Aceitável",
                " Min. Esper": "Mínimo Esperado",
                "Máx. Esper": "Máximo Esperado",
            },
            inplace=True,
        )

        df_portaria = load_portaria_sunburst()

        colunas_portaria = [
            "id",
            "Nome",
            "Dimensão",
            "Ponderação",
            "Lable",
            "Área clínica",
        ]

        df = df.merge(
            df_portaria[colunas_portaria],
            on="id",
            how="right",
        )

        df["Score"] = df.apply(calculate_score_bicsp, axis=1)

        # drop the rows with Score "Error"
        df = df[df["Score"] != "Error"]

        df["Score"] = df["Score"].astype(float)

        df["ano_mes"] = f"{ano}-{mes}"

        # update dict_dfs with the new df
        if nome in dict_dfs:
            dict_dfs[nome]["df"] = pd.concat(
                [dict_dfs[nome]["df"], df], ignore_index=True
            )
        else:
            dict_dfs[nome] = {
                "df": df,
                "ano": ano,
                "mes": mes,
                "unidade": unidade,
                "nome": nome,
            }

        if on_upload:
            on_upload(unidade, ano, mes, "bicsp")

    return dict_dfs
