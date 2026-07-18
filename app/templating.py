"""Configuração partilhada dos templates Jinja2."""

import hashlib
from pathlib import Path

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _versao_estatica() -> str:
    """Hash do conteúdo dos assets próprios — muda a cada deploy que os
    altere, invalidando as caches (browser e edge da Cloudflare) via
    query param ?v= nos URLs."""
    digest = hashlib.sha256()
    for nome in ("styles.css", "app.js"):
        digest.update((BASE_DIR / "static" / nome).read_bytes())
    return digest.hexdigest()[:10]


templates.env.globals["v_estatica"] = _versao_estatica()
