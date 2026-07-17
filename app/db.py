"""Base de dados SQLite da v3 (contas, unidades, uploads guardados).

Um ficheiro único (env MGFHUB_DB; default var/mgfhub.db, e um volume
docker no VPS), WAL para leituras/escritas concorrentes e migrações
sequenciais controladas pelo PRAGMA user_version.
"""

import os
import sqlite3
import threading
from pathlib import Path

DB_PATH = Path(
    os.environ.get(
        "MGFHUB_DB", Path(__file__).resolve().parent.parent / "var" / "mgfhub.db"
    )
)

MIGRACOES = [
    # v1 — contas, unidades, membros, convites, sessões de login e uploads
    """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        email TEXT NOT NULL UNIQUE COLLATE NOCASE,
        nome TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        criado_em TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE unidades (
        id INTEGER PRIMARY KEY,
        nome TEXT NOT NULL UNIQUE,
        criado_em TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE membros (
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        unidade_id INTEGER NOT NULL REFERENCES unidades(id) ON DELETE CASCADE,
        papel TEXT NOT NULL CHECK (papel IN ('gestor', 'membro')),
        criado_em TEXT NOT NULL DEFAULT (datetime('now')),
        PRIMARY KEY (user_id, unidade_id)
    );

    CREATE TABLE convites (
        codigo TEXT PRIMARY KEY,
        unidade_id INTEGER NOT NULL REFERENCES unidades(id) ON DELETE CASCADE,
        criado_por INTEGER REFERENCES users(id) ON DELETE SET NULL,
        criado_em TEXT NOT NULL DEFAULT (datetime('now')),
        expira_em TEXT NOT NULL
    );

    CREATE TABLE sessoes (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        unidade_ativa INTEGER REFERENCES unidades(id) ON DELETE SET NULL,
        criado_em TEXT NOT NULL DEFAULT (datetime('now')),
        expira_em TEXT NOT NULL
    );

    CREATE TABLE uploads (
        id INTEGER PRIMARY KEY,
        unidade_id INTEGER NOT NULL REFERENCES unidades(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        tipo TEXT NOT NULL CHECK (tipo IN ('bicsp', 'mimuf')),
        nome TEXT NOT NULL,
        ano TEXT NOT NULL,
        mes TEXT NOT NULL,
        unidade_origem TEXT NOT NULL,
        dados BLOB NOT NULL,
        criado_em TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE (unidade_id, tipo, nome) ON CONFLICT REPLACE
    );
    """,
]

_migrado = False
_lock = threading.Lock()


def ligar() -> sqlite3.Connection:
    """Ligação nova (uma por operação; fechar com 'with closing(...)')."""
    _garantir_migracoes()
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def _garantir_migracoes():
    global _migrado  # pylint: disable=global-statement
    if _migrado:
        return
    with _lock:
        if _migrado:
            return
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(DB_PATH, timeout=10)
        try:
            con.execute("PRAGMA journal_mode = WAL")
            versao = con.execute("PRAGMA user_version").fetchone()[0]
            for i, migracao in enumerate(MIGRACOES[versao:], start=versao + 1):
                con.executescript(migracao)
                con.execute(f"PRAGMA user_version = {i}")
                con.commit()
        finally:
            con.close()
        _migrado = True
