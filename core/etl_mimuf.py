"""ETL dos ficheiros xlsx exportados do MIM@UF.

Dois formatos: export da unidade inteira (tabela de 10 colunas) e export
por médico (bloco de metadados "P02.01.R03." seguido da tabela, com o
médico identificado nos metadados). O MIM@UF não traz intervalos — vêm
da portaria.
"""

import pandas as pd

from core.common import extrair_id, medico
from core.reference import load_intervalos, load_portaria_sunburst
from core.scoring import calculate_score_mimuf


def localizacao_coluna_medico(df):
    index = df.columns.get_loc("Médico Familia") - 3
    list_text = [
        "para_remover_2",
        "para_remover_3",
        "para_remover_4",
    ]

    list_text.insert(index, "Médico Familia")

    return list_text


def split_metadata_from_df(df, df_start):
    # look for the row that contains the string df_start. thats the column's
    # header for the df. what's before is the metadata

    i = None  # Initialize i

    for idx, row in df.iterrows():
        if idx == 20:
            raise ValueError(
                f"'{df_start}' not found in DataFrame. Maybe the keyword is wrong?"
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
        # look at this row and if there are duplicate column names, add
        # .1, .2, .3, etc to the duplicates

        counts = {}
        for idx, value in enumerate(row):
            if pd.isna(value):
                continue
            if value in counts:
                counts[value] += 1
                row.iloc[idx] = f"{value}.{counts[value]:01d}"
            else:
                counts[value] = 0

        # check if there are any NaN values in the row and replace them with
        # NaN1, NaN2, NaN3, etc
        nan_count = 1
        for idx, value in enumerate(row):
            if pd.isna(value):
                row.iloc[idx] = f"NaN{nan_count}"
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

            # add a new column titled Médico Familia and fill it with the value
            # of medico_familia except for row 0
            df.loc[1:, "Médico Familia"] = medico_familia
            cols = df.columns.tolist()
            cols.remove("Médico Familia")
            cols.insert(4, "Médico Familia")
            df = df[cols]

            break

    return df


def etl_mimuf(list_of_files, on_upload=None, on_warning=None):
    """Processa uma lista de ficheiros xlsx do MIM@UF.

    Devolve um dicionário {"<unidade> <mes>/<ano>": {"df", "ano", "mes",
    "unidade", "nome"}}. Ficheiros da mesma unidade+mês (ex: um export por
    médico) são concatenados. `on_upload(unidade, ano, mes, "mimuf")` é
    chamado por ficheiro (telemetria); `on_warning(mensagem)` quando o
    formato parece errado.
    """
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
            if on_warning:
                on_warning("O ficheiro não está correcto")

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

        # give name to columns
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

        # drop helper columns
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

        # estrutura da portaria + intervalos do ano dos dados
        # (com fallback para o ano disponível mais próximo)
        df_portaria = load_portaria_sunburst()

        colunas_portaria = [
            "id",
            "Nome",
            "Dimensão",
            "Ponderação",
            "Lable",
        ]

        # merge df with df_portaria
        df = df.merge(
            df_portaria[colunas_portaria],
            on="id",
            how="left",
        )

        df = df.merge(
            load_intervalos(ano),
            on="id",
            how="left",
        )

        df = df.reset_index(drop=True)

        # valores em formato PT ("1.234,5") chegam como string; floats ficam como estão
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

        # sort by id
        df = df.sort_values("id")

        # score calculado a partir do valor do indicador e dos intervalos
        # aceitável e esperado (ver core.scoring)
        df["Score"] = df.apply(calculate_score_mimuf, axis=1)

        # calculate the score for each dimension based on the average wheighed score
        df["contributo"] = df["Ponderação"] * df["Score"] / 2

        # list of dimensions and drop empty ones
        list_dimensoes = [x for x in df["Dimensão"].unique().tolist() if pd.notna(x)]

        # remove IDE
        list_dimensoes = list_dimensoes[1:]

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
        df.loc[df["Dimensão"] == "IDE", "Intervalo Aceitável"] = "N/A"
        df.loc[df["Dimensão"] == "IDE", "Intervalo Esperado"] = "N/A"
        df.loc[df["Nome"] == "IDE", "Intervalo Aceitável"] = "N/A"
        df.loc[df["Nome"] == "IDE", "Intervalo Esperado"] = "N/A"

        # IDE
        df.loc[df["Nome"] == "IDE", "Resultado"] = df.loc[
            df["Dimensão"] == "IDE", "Resultado"
        ].sum()
        df.loc[df["Nome"] == "IDE", "Score"] = (
            2
            * df.loc[df["Nome"] == "IDE", "Resultado"]
            / df.loc[df["Nome"] == "IDE", "Ponderação"]
        )

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

        if on_upload:
            on_upload(unidade, ano, mes, "mimuf")

    return dict_dfs
