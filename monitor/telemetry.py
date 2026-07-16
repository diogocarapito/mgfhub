"""Registo de utilização (telemetria) em Supabase.

Se SUPABASE_URL/SUPABASE_KEY não estiverem definidos, o registo é
silenciosamente ignorado — a telemetria nunca deve impedir a aplicação
de funcionar (dev local, testes, CI).
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

_URL = os.environ.get("SUPABASE_URL")
_KEY = os.environ.get("SUPABASE_KEY")

_client = create_client(_URL, _KEY) if _URL and _KEY else None


def _insert(table, data):
    if _client is None:
        return
    try:
        _client.table(table).insert(data).execute()
    except Exception:  # pylint: disable=broad-except
        pass


def record_upload(unidade, ano, mes, tipo):
    _insert(
        "ide_uploads",
        {
            "created_at": datetime.now().isoformat(),
            "unidade": unidade,
            "ano": ano,
            "mes": mes,
            "tipo": tipo,
        },
    )


def record_query(query, filtro, area_clinica):
    _insert(
        "mgfhub_queries",
        {
            "created_at": datetime.now().isoformat(),
            "query": query,
            "filter": filtro,
            "area_clinica": area_clinica,
        },
    )
