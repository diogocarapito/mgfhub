"""Configuração dos testes: base de dados SQLite isolada por execução.

Tem de correr antes de qualquer import de app.* (o caminho da BD é lido
no import de app.db).
"""

import os
import tempfile
from pathlib import Path

os.environ.setdefault(
    "MGFHUB_DB", str(Path(tempfile.mkdtemp(prefix="mgfhub-tests-")) / "mgfhub.db")
)
