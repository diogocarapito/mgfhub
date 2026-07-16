import pandas as pd
import os
import streamlit as st

from core.search import filter_indicadores


def func():
    return None


@st.cache_data
def data_source(source):
    # check if source is in ./data folder
    # if not, download from github
    data_files_list = os.listdir("./data")

    if source in data_files_list:
        return pd.read_csv("./data/" + source, index_col=0)

    else:
        url = "https://github.com/DiogoCarapito/datasets_indicadores/raw/main/datasets/indicadores_sdm.csv"

        df = pd.read_csv(url, index_col=0)

        return df


@st.cache_data
def filter_df(df, pesquisa, filtros, area_clinica):
    # a lógica de pesquisa vive em core.search (partilhada com a app v3)
    return filter_indicadores(df, pesquisa, filtros, area_clinica)


@st.cache_data
def num_denom_paragraph(text):
    try:
        text_after_split = text.split("Numerador: ")
        text_after_split_2 = text_after_split[1].split("Denominador: ")
        text = [text_after_split[0], text_after_split_2[0], text_after_split_2[1]]
        return text
    except IndexError:
        return [text, "", ""]
