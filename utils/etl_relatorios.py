import pandas as pd
import re
import streamlit as st
import math

# from mimufs.processing import medico

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# load .env file
load_dotenv()

# key to know the local of the code being run
production = os.environ.get("PRODUCTION")

# Supabase configuration
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


# Function to insert data into Supabase
@st.cache_data()
def supabase_record(unidade, ano, mes, tipo):
    # Get current datetime
    date_time = datetime.now().isoformat()

    # Create the data in a format to be inserted into Supabase
    sb_insert = {
        "created_at": date_time,
        "unidade": unidade,
        "ano": ano,
        "mes": mes,
        "tipo": tipo,
        # "production": bool(environment),
    }

    # Insert data into Supabase
    supabase.table("ide_uploads").insert(sb_insert).execute()


# From mimufs
@st.cache_data()
def medico(df: pd.DataFrame, column="Médico Familia") -> pd.DataFrame:
    # convert the string to title case
    df.loc[:, column] = df.loc[:, column].str.title()

    # remove the double spaces in the string
    df.loc[:, column] = df.loc[:, column].str.replace("  ", " ")

    # remove the last space in the string
    df.loc[:, column] = df.loc[:, column].str.rstrip()

    return df


@st.cache_data()
def extrair_id(df, coluna):
    # remove columns with BA

    # drop rows that end in "FX", but keep "2020.435.01 FX"
    df = df[~(df[coluna].str.endswith("FX") & (df[coluna] != "2020.435.01 FX"))]

    # extrair o id que se econtra entre dois . (pontos) e transformar em int
    # exemplo de input: "2013.001.01 FL" output 1

    df[coluna] = (
        df[coluna].str.extract(r"\.(\d+)\.", expand=False).fillna(0).astype(int)
    )

    return df


@st.cache_data()
def etiqueta_ano_completo(df, ano, list_texto):
    list_etiquetas = []

    # ano = 2024

    for each in list_texto:
        etiqueta = f"{each} {ano}"
        if etiqueta not in df.columns:
            etiqueta = f"{each} 2024"
        list_etiquetas.append(etiqueta)

    return list_etiquetas


@st.cache_data()
def etiqueta_ano(df, ano):
    # cria as etiquetas para os intervalos aceitáveis e esperados com o ano correcto correspondente aos dados extraídos
    ano = 2024

    int_aceit = f"Intervalo Aceitável {ano}"
    int_esper = f"Intervalo Esperado {ano}"

    # caso não haja intervalos para o ano dos dados, por definição usa os intervalos de 2023
    if int_aceit not in df.columns or int_esper not in df.columns:
        int_aceit = "Intervalo Aceitável 2024"
        int_esper = "Intervalo Esperado 2024"

    return int_aceit, int_esper


@st.cache_data()
def calculate_score_mimuf(row):
    # Convert the values to floats
    valor = float(row["Valor"])
    min_aceitavel = float(row["Mínimo Aceitável"])
    min_esperado = float(row["Mínimo Esperado"])
    max_esperado = float(row["Máximo Esperado"])
    max_aceitavel = float(row["Máximo Aceitável"])
    # min_aceitavel = float(row["Mínimo Aceitável 2024"])
    # min_esperado = float(row["Mínimo Esperado 2024"])
    # max_esperado = float(row["Máximo Esperado 2024"])
    # max_aceitavel = float(row["Máximo Aceitável 2024"])

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
        return 0  # Return some value or raise an exception in case none of the conditions are met


@st.cache_data()
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
        return "Error"  # Return some value or raise an exception in case none of the conditions are met
    # if (
    #     row["Resultado"] > row["Máximo Aceitável 2024"]
    #     or row["Resultado"] < row["Mínimo Aceitável 2024"]
    # ):
    #     return 0
    # elif row["Mínimo Aceitável 2024"] <= row["Resultado"] < row["Mínimo Esperado 2024"]:
    #     score_min = (
    #         2
    #         * (row["Resultado"] - row["Mínimo Aceitável 2024"])
    #         / (row["Mínimo Esperado 2024"] - row["Mínimo Aceitável 2024"])
    #     )
    #     return score_min
    # elif row["Máximo Esperado 2024"] < row["Resultado"] <= row["Máximo Aceitável 2024"]:
    #     score_max = (
    #         2
    #         * (row["Máximo Aceitável 2024"] - row["Resultado"])
    #         / (row["Máximo Aceitável 2024"] - row["Máximo Esperado 2024"])
    #     )
    #     return score_max
    # elif row["Mínimo Esperado 2024"] <= row["Resultado"] <= row["Máximo Esperado 2024"]:
    #     return 2
    # else:
    #     return "Error"  # Return some value or raise an exception in case none of the conditions are met


@st.cache_data()
def etl_bicsp(list_of_files):
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

        # processamento se o ficherio tiver cabeçalho (summarized e underalying data)
        first_column_name = df.columns[0]

        # versão ENG
        if first_column_name.startswith("Applied"):
            # get the text int he header of the first column
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

        # make id the index
        # df.set_index("id", inplace=True)

        # sort by id
        df = df.sort_values("id")

        # check if df["Hierarquia Contratual - Área"] has "IDE - Desempenho" and keep only those rows
        if df["Hierarquia Contratual - Área"].str.contains("IDE - Desempenho").any():
            df = df[df["Hierarquia Contratual - Área"].str.contains("IDE - Desempenho")]

        # Eextração do mês e ano
        ano_mes = str(df["Mês Ind"].unique().max())
        # ano = "2024"
        ano = ano_mes[:4]
        mes = ano_mes[4:6]

        # nome = f"{unidade} {ano}/{mes}"
        nome = f"{unidade} {mes}/{ano}"

        # correção_vacina_gripe_435(df)

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

        df_portaria = pd.read_csv("./data/sunburst_portaria_411a_2023.csv")

        # ## print("sf_portaria.columns")
        # ## print(sf_portaria.columns)

        colunas_portaria = [
            "id",
            "Nome",
            "Dimensão",
            "Ponderação",
            "Lable",
            "Área clínica",
        ]

        # ## print("colunas_portaria")
        # ## print(colunas_portaria)

        # etiquetas_intervalos_ano = etiqueta_ano_completo(
        #     df,
        #     ano,
        #     [
        #         "Intervalo Aceitável",
        #         "Mínimo Aceitável",
        #         "Máximo Aceitável",
        #         "Intervalo Esperado",
        #         "Mínimo Esperado",
        #         "Máximo Esperado",
        #     ],
        # )

        # colunas_portaria.extend(etiquetas_intervalos_ano)

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

        # Update list_of_dfs with the new df
        if nome in dict_dfs:
            dict_dfs[nome]["df"] = pd.concat(
                [dict_dfs[nome]["df"], df], ignore_index=True
            )
        else:
            dict_dfs[nome] = {
                "data": df,
                "ano": ano,
                "mes": mes,
                "unidade": unidade,
                "nome": nome,
            }

        supabase_record(unidade, ano, mes, "bicsp")

    return dict_dfs


@st.cache_data()
def merge_portaria_bicsp(df_bicsp, ano):
    df_portaria = pd.read_csv("./data/sunburst_portaria_411a_2023.csv")

    # df_portaria.loc[df_portaria["Nome"]=="IDE", "Ponderação"] = 100

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

    # list of dimensions and drop empty obnes
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

    # df.loc[df["Nome"] != "IDE"] = df.loc[df["Nome"] != "IDE"].fillna(0)

    # make score a float
    df["Score"] = df["Score"].astype(float)

    # remove id column
    # df.drop(columns=["id"], inplace=True)

    # st.write(
    #     df[["id", "Nome", "Dimensão", "Ponderação", "Resultado", "Score", "contributo"]]
    # )

    # st.write(df[["Lable", "Score"]].dtypes)

    return df


@st.cache_data()
def localizacao_coluna_medico(df):
    index = df.columns.get_loc("Médico Familia") - 3
    list_text = [
        "para_remover_2",
        "para_remover_3",
        "para_remover_4",
    ]

    list_text.insert(index, "Médico Familia")

    return list_text

    # df["Médico Familia"] = "Sem informação"
    # # Insert "Médico Familia" at the desired position (e.g., index 4)
    # desired_position = 4
    # cols = df.columns.tolist()
    # if "Médico Familia" in cols:
    #     cols.remove("Médico Familia")
    # cols.insert(desired_position, "Médico Familia")
    # df = df.reindex(columns=cols)


def split_metadata_from_df(df, df_start):
    # look for the row that contains the string df_start. thats the column's header for the df. what's before is the metadata

    i = None  # Initialize i

    for idx, row in df.iterrows():
        if idx == 20:
            raise ValueError(
                f"'{df_start}' not found in DataFrame. Mayve the keyword is wrong?"
            )
        elif df_start in row.values:
            i = idx
            break

    if i is not None:
        metadata = df.iloc[:i, 0].dropna().tolist()
        df = df.iloc[i:]

    else:
        raise ValueError(f"'{df_start}' not found in DataFrame")

    # make row 0 index
    def prepare_row_to_column(row):

        # look at this row and if there are duplicate column names, add  .1, .2, .3, etc to the duplicates

        counts = {}
        for idx, value in enumerate(row):
            if pd.isna(value):
                continue
            if value in counts:
                counts[value] += 1
                row[idx] = f"{value}.{counts[value]:01d}"
            else:
                counts[value] = 0

        # check if there are any NaN values in the row and replace them with NaN1, NaN2, NaN3, etc
        nan_count = 1
        for idx, value in enumerate(row):
            if pd.isna(value):
                row[idx] = f"NaN{nan_count}"
                nan_count += 1

        return row

    df.columns = prepare_row_to_column(df.iloc[0])

    df = df[1:]

    # drop index
    df = df.reset_index(drop=True)

    # look for metadata that starts with "Médico Familia:"
    for each in metadata:
        if each.startswith("Médico Familia:"):
            medico_familia = each.split("Médico Familia: ")[1].strip()

            # add a new column titled Médico Familia and fill it with the value of medico_familia except for row 0

            df.loc[1:, "Médico Familia"] = medico_familia
            cols = df.columns.tolist()
            cols.remove("Médico Familia")
            cols.insert(
                4, "Médico Familia"
            )  # Change 1 to your desired position (0-based)
            df = df[cols]

            break

    return df


@st.cache_data()
def etl_mimuf(list_of_files):
    if list_of_files is None:
        return None

    dict_dfs = {}

    dict_of_dfs = {
        xlsx_file.name: pd.read_excel(xlsx_file, engine="openpyxl")
        for xlsx_file in list_of_files
    }

    # for loop to process each file
    for df in dict_of_dfs.values():
        # if first cell starts as "P02.01.R03." then it is a mimuf file with header
        if str(df.columns[0]).startswith("P02.01.R03."):
            df = split_metadata_from_df(df, "Unidade Funcional / Polo Hospitalar")

        # main ETL

        if df.columns.shape[0] != 10:
            st.warning("O ficheiro não está correcto")

        ano_mes = df.columns[7]
        ano = ano_mes[:4]
        mes = ano_mes[5:7]

        # remove the first row
        df = df[1:]
        df = df.reset_index(drop=True)

        if "Médico Familia" not in df.columns:
            df["Médico Familia"] = "Sem informação"
            # Insert "Médico Familia" at the desired position (e.g., index 4)
            desired_position = 4
            cols = df.columns.tolist()
            if "Médico Familia" in cols:
                cols.remove("Médico Familia")
            cols.insert(desired_position, "Médico Familia")
            df = df.reindex(columns=cols)

        nome_colunas = localizacao_coluna_medico(df)

        # #give name to columns
        df.columns = (
            ["Unidade", "para_remover_1", "id"]
            + nome_colunas
            + [
                "Numerador",
                "Denominador",
                "Valor",
            ]
        )

        unidade = df["Unidade"].unique()[0]
        nome = f"{unidade} {mes}/{ano}"

        # drop column "Mês"
        df = df.drop(
            columns=[
                "Unidade",
                "para_remover_1",
                "para_remover_2",
                "para_remover_3",
                "para_remover_4",
            ]
        )

        # Uniformizar nomes de médicos
        df = medico(df, column="Médico Familia")

        # drop rows where "id" is Nan
        df = df.dropna(subset=["id"])

        # extrair id indicador
        df = extrair_id(df, "id")

        # remove lines that are exact duplicates and keep only one
        df = df.drop_duplicates()

        # make id the index
        df = df.set_index("id")

        # print(df.columns)
        # print(df)

        # etiquetas_intervalos_ano = etiqueta_ano_completo(
        #     df,
        #     ano,
        #     [
        #         "Intervalo Aceitável",
        #         "Mínimo Aceitável",
        #         "Máximo Aceitável",
        #         "Intervalo Esperado",
        #         "Mínimo Esperado",
        #         "Máximo Esperado",
        #     ],
        # )

        # get sunburst_portaria csv
        df_portaria = pd.read_csv("./data/sunburst_portaria_411a_2023.csv")
        # st.write(df_portaria)

        colunas_portaria = [
            "id",
            "Nome",
            "Dimensão",
            "Ponderação",
            "Lable",
            "Intervalo Esperado 2024",
            "Intervalo Aceitável 2024",
            "Mínimo Aceitável 2024",
            "Máximo Aceitável 2024",
            "Mínimo Esperado 2024",
            "Máximo Esperado 2024",
        ]

        # colunas_portaria.extend(etiquetas_intervalos_ano)

        # merge df with df_portaria
        df = df.merge(
            df_portaria[colunas_portaria],
            on="id",
            how="left",
        )

        df.rename(
            columns={
                "Intervalo Aceitável 2024": "Intervalo Aceitável",
                "Mínimo Aceitável 2024": "Mínimo Aceitável",
                "Máximo Aceitável 2024": "Máximo Aceitável",
                "Intervalo Esperado 2024": "Intervalo Esperado",
                "Mínimo Esperado 2024": "Mínimo Esperado",
                "Máximo Esperado 2024": "Máximo Esperado",
            },
            inplace=True,
        )

        # drop rows with NaN
        # df.dropna(subset=["id"], inplace=True)

        df = df.reset_index(drop=True)

        # fill NA
        # df["Valor"] = df["Valor"].fillna(0)
        # df["Denominador"] = df["Denominador"].fillna(0)
        # df["Numerador"] = df["Numerador"].fillna(0)

        df["Valor"] = (
            df["Valor"]
            .apply(
                lambda x: (
                    x.replace(".", "").replace(",", ".") if isinstance(x, str) else x
                )
            )
            .astype(float)
        )
        df["Numerador"] = (
            df["Numerador"]
            .apply(
                lambda x: (
                    x.replace(".", "").replace(",", ".") if isinstance(x, str) else x
                )
            )
            .astype(float)
        )
        df["Denominador"] = (
            df["Denominador"]
            .apply(
                lambda x: (
                    x.replace(".", "").replace(",", ".") if isinstance(x, str) else x
                )
            )
            .astype(float)
        )

        # drop lines were "Médico Familia" is Sem Médico
        # df = df[df["Médico Familia"] != "Sem Médico"]

        # sort by id
        df = df.sort_values("id")

        # score calculado a partir do valor do indicador e dos intervalos aceitável e esperado
        # se acima do máximo aceitave ou abaixo do mínimo aceitavel, score = 0
        # se entre o minimo e maxio esperado, score = 2
        # se entre minimo aceitabel e minimo esperado ou entre maximo esperado e maximo aceitavel, score = 1
        # se acima do maximo esperado mas abaico do maximo aceitavel, score = 1
        # valores aceitáveis e esperados estão noutra coluna e deve ser usados o da mesma linha

        # st.write(df)

        df["Score"] = df.apply(calculate_score_mimuf, axis=1)

        # calculate the score for each dimension based on the average wheighed score
        df["contributo"] = df["Ponderação"] * df["Score"] / 2

        # list of dimensions and drop empty ones
        list_dimensoes = [x for x in df["Dimensão"].unique().tolist() if pd.notna(x)]

        # remove IDE
        list_dimensoes = list_dimensoes[1:]

        # st.write(list_dimensoes)

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

        # df.loc[df["Nome"] != "IDE"] = df.loc[df["Nome"] != "IDE"].fillna(0)

        # rename columns to remove year
        # df.rename(columns=lambda x: re.sub(r" 2023", "", x), inplace=True)

        df["Denominador"] = df["Denominador"].astype(float)
        df["Numerador"] = df["Numerador"].astype(float)

        df["ano_mes"] = f"{ano}-{mes}"

        # save as a dictionary name:df
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

        supabase_record(unidade, ano, mes, "mimuf")

    return dict_dfs


@st.cache_data()
def extracao_areas_clinicas(df):
    return df["Área clínica"].unique().tolist()


def process_indicador(df):
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

    list_indicadores_valor_10x = [
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

    if info_indicador["id_indicador"] in list_indicadores_valor_10x:
        info_indicador["valor"] = info_indicador["valor"] / 100

    if info_indicador["id_indicador"] == 294:
        info_indicador["quantos_faltam_aceitavel"] = (
            info_indicador["denominador"] * min_acetavel / 1000 - numerador
        )
        info_indicador["quantos_faltam_esperado"] = (
            info_indicador["denominador"] * min_esperado / 1000 - numerador
        )

    return info_indicador


@st.cache_data()
def process_filter_temporal(df_mimuf, filtro_indicador):
    id_indicador_selected = filtro_indicador.split(" - ")[0]

    list_dfs = list(df_mimuf.keys())

    filtered_dfs = []

    for each in list_dfs:
        filtered_df = df_mimuf[each]["df"].loc[
            df_mimuf[each]["df"]["id"] == int(id_indicador_selected)
        ]
        filtered_df["Mês"] = df_mimuf[each]["mes"]
        filtered_df["Ano"] = df_mimuf[each]["ano"]

        # create a new row with the sum and average of the values of the unidade
        # add new row to the filtered_df

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
                # "Mínimo Aceitável 2024": [filtered_df["Mínimo Aceitável 2024"].iloc[0]],
                # "Mínimo Esperado 2024": [filtered_df["Mínimo Esperado 2024"].iloc[0]],
                # "Máximo Esperado 2024": [filtered_df["Máximo Esperado 2024"].iloc[0]],
                # "Máximo Aceitável 2024": [filtered_df["Máximo Aceitável 2024"].iloc[0]],
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
                    # "Mínimo Aceitável 2024",
                    # "Mínimo Esperado 2024",
                    # "Máximo Esperado 2024",
                    # "Máximo Aceitável 2024",
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
            # "Mínimo Aceitável 2024": "min_aceitavel",
            # "Mínimo Esperado 2024": "min_esperado",
            # "Máximo Esperado 2024": "max_esperado",
            # "Máximo Aceitável 2024": "max_aceitavel",
        },
        axis=1,
    )

    # order by ano and mes
    concatenated_df = concatenated_df.sort_values(by=["Ano", "Mês", "Médico Familia"])

    return concatenated_df

    # data_evolucao_temporal = []

    # for each in df_mimuf:
    #     # st.write(each)
    #     # st.write(df_mimuf[each]["df"])
    #     # st.write(df_mimuf[each]["ano"])
    #     # st.write(df_mimuf[each]["mes"])

    #     df = df_mimuf[each]["df"]

    #     df_num_den_med = (
    #         df.loc[df["Nome"] == filtro_indicador][
    #             ["Médico Familia", "Numerador", "Denominador", "Valor"]
    #         ]
    #         .sort_values(by="Valor", ascending=False)
    #     )

    #     data_evolucao_temporal.append(df_num_den_med)

    # return data_evolucao_temporal
