"""Uploads guardados por unidade: os dataframes processados pelo ETL são
persistidos como parquet na base de dados, para os membros da unidade os
reutilizarem sem voltar a carregar os xlsx (análise longitudinal)."""

import io
from contextlib import closing

import pandas as pd

from app import db


def guardar_uploads(unidade_id: int, user_id: int, tipo: str, dict_dfs: dict) -> None:
    """Persiste as entradas de um ETL (bicsp/mimuf); a mesma unidade+mês
    substitui a versão anterior."""
    with closing(db.ligar()) as con:
        for nome, entry in dict_dfs.items():
            buffer = io.BytesIO()
            entry["df"].to_parquet(buffer)
            con.execute(
                "INSERT INTO uploads "
                "(unidade_id, user_id, tipo, nome, ano, mes, unidade_origem, dados) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    unidade_id,
                    user_id,
                    tipo,
                    nome,
                    entry["ano"],
                    entry["mes"],
                    entry["unidade"],
                    buffer.getvalue(),
                ),
            )
        con.commit()


def carregar_uploads(unidade_id: int) -> dict:
    """Reconstrói {'bicsp': dict_dfs, 'mimuf': dict_dfs} com todos os
    uploads guardados da unidade, ordenados por período."""
    dados = {"bicsp": {}, "mimuf": {}}
    with closing(db.ligar()) as con:
        rows = con.execute(
            "SELECT tipo, nome, ano, mes, unidade_origem, dados FROM uploads "
            "WHERE unidade_id = ? ORDER BY ano, mes, nome",
            (unidade_id,),
        ).fetchall()
    for row in rows:
        dados[row["tipo"]][row["nome"]] = {
            "df": pd.read_parquet(io.BytesIO(row["dados"])),
            "ano": row["ano"],
            "mes": row["mes"],
            "unidade": row["unidade_origem"],
            "nome": row["nome"],
        }
    return dados


def listar_uploads(unidade_id: int) -> list:
    with closing(db.ligar()) as con:
        rows = con.execute(
            "SELECT tipo, nome, ano, mes, criado_em FROM uploads "
            "WHERE unidade_id = ? ORDER BY ano, mes, tipo, nome",
            (unidade_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def apagar_upload(unidade_id: int, tipo: str, nome: str) -> None:
    with closing(db.ligar()) as con:
        con.execute(
            "DELETE FROM uploads WHERE unidade_id = ? AND tipo = ? AND nome = ?",
            (unidade_id, tipo, nome),
        )
        con.commit()
