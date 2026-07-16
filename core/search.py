"""Pesquisa fuzzy de indicadores sobre o dataset SDM.

Filtra por contratualização (IDE/IDG/BI-CSP/Todos) e área clínica, e
pesquisa por texto livre com fuzzy matching sobre a coluna
search_indexes (id + nome + designação + área, sem acentos).
"""

from rapidfuzz import fuzz, process
from unidecode import unidecode

FILTROS_CONTRATUALIZACAO = ["IDE", "IDG", "BI-CSP", "Todos"]


def filter_indicadores(df, pesquisa, filtros, area_clinica):
    if filtros == "IDE":
        df = df[df["ide"] == 1]

    elif filtros == "IDG":
        df = df[df["idg"] == 1]

    elif filtros == "BI-CSP":
        df = df[df["bicsp"] == 1]

    else:
        pass

    if area_clinica:
        df = df[df["Área clínica"].isin(area_clinica)]

    pesquisa = unidecode(pesquisa.lower())

    if pesquisa == "":
        return df

    # fuzzy search com score cutoff de 59, comparando com indexing
    search_list = process.extract(
        pesquisa,
        df["search_indexes"],
        scorer=fuzz.WRatio,
        score_cutoff=59,
        limit=50,
    )
    return df.filter([item[2] for item in search_list], axis=0)
