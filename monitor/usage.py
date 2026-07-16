# i want to create a streamlit app to draw a graph of the usage by interpreting the data from supabase

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import os
from dotenv import load_dotenv
from supabase import create_client, Client


def fetch_all_rows(table_name, chunk_size=1000):
    # load .env file
    load_dotenv()

    # Supabase configuration
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    offset = 0
    all_data = []

    while True:
        # Fetch a chunk of data
        response = (
            supabase.table(table_name)
            .select("*")
            .range(offset, offset + chunk_size - 1)
            .execute()
        )
        data_chunk = response.data

        # Break the loop if no more data is returned
        if not data_chunk:
            break

        # Append the chunk to the all_data list
        all_data.extend(data_chunk)

        # Update the offset
        offset += chunk_size

    return all_data


def get_data(table_name):
    # get the data from supabase

    # data = supabase.table("ide_uploads").select("*").execute()
    data = fetch_all_rows(table_name)
    return data


st.title("mgfhub IDE Usage")

data = get_data("ide_uploads")
df = pd.DataFrame(data)

# create a column that gets the year and month of the created_at column
df["created_at"] = pd.to_datetime(df["created_at"])
df["year"] = df["created_at"].dt.year
df["month"] = df["created_at"].dt.month
df["yearmonth"] = df["year"].astype(str) + "-" + df["month"].astype(str)
df["day"] = df["created_at"].dt.day

# if month is less than 10, add a 0 before the month
df["yearmonth"] = np.where(
    df["month"] < 10,
    df["year"].astype(str) + "-0" + df["month"].astype(str),
    df["yearmonth"],
)

# get a frequency count of the unidade by yearmonth
df_unidades = df.groupby(["yearmonth", "unidade"]).size().reset_index(name="count")

# make each unidade a column and fill the NaN with 0
df_unidades = df_unidades.pivot(
    index="unidade", columns="yearmonth", values="count"
).fillna(0)

# make a new row with the total of each row
df_unidades.loc["Total"] = df_unidades.sum()
# make a new column with the total of each column
df_unidades["Total"] = df_unidades.sum(axis=1)
st.write(df_unidades)

# get frequency count of yearmonth
df_yearmonth = df.groupby(["yearmonth"]).size().reset_index(name="count")

# create a bar chart from the frequency count of yearmonth
bar_chart = (
    alt.Chart(df_yearmonth)
    .mark_bar()
    .encode(x="yearmonth", y="count")
    .properties(width=600, height=300)
)
st.write(bar_chart)

# get the usage of the last 6 months from df_unidades
df_last_6_months = df_unidades.iloc[:, -10:]

# remove total an recalculate total
df_last_6_months = df_last_6_months.drop("Total", axis=1)
df_last_6_months["Total"] = df_last_6_months.sum(axis=1)
# drop rows with all 0s
df_last_6_months = df_last_6_months.loc[~(df_last_6_months == 0).all(axis=1)]

# total acesses in the last 6 months
total_acesses = df_last_6_months["Total"].sum() / 2
st.metric("Nº de acessos nos últimos 6 meses", total_acesses)

# number of different unidade that accessed the platform in the last 6 months
n_unidades = df_last_6_months.shape[0] - 1
st.metric("Nº de unidades que acederam nos últimos 9 meses", n_unidades)

# n_unidades que acederam pelo menos 3 meses diferentes
df_last_6_months["n_months"] = df_last_6_months.apply(
    lambda x: x[x > 0].count() - 1, axis=1
)
n_unidades_3_months = df_last_6_months[df_last_6_months["n_months"] >= 2].shape[0] - 1
st.metric(
    "Nº de unidades que acederam pelo menos 3 meses diferentes", n_unidades_3_months
)


# median number of acesses per unidade in the last 6 months
median_acesses = df_last_6_months["Total"].median()
st.metric("Mediana de acessos por unidade nos últimos 6 meses", median_acesses)

st.write(df_last_6_months)


###

df_queries = get_data("mgfhub_queries")

df_queries = pd.DataFrame(df_queries)

df_queries["created_at"] = pd.to_datetime(df_queries["created_at"])
df_queries["year"] = df_queries["created_at"].dt.year
df_queries["month"] = df_queries["created_at"].dt.month
df_queries["yearmonth"] = (
    df_queries["year"].astype(str) + "-" + df_queries["month"].astype(str)
)
df_queries["day"] = df_queries["created_at"].dt.day

df_queries_last_6_months = df_queries[df_queries["year"] >= 2024]


# drop any row with area_clinica = []
# df_queries_last_6_months = df_queries_last_6_months[df_queries_last_6_months["area_clinica"] != []]


st.write(df_queries_last_6_months)
