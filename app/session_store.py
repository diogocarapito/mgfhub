"""Sessões em memória para os dados carregados no IDE.

Os xlsx processados vivem apenas em memória, associados a um cookie de
sessão, e expiram por inatividade — mantém-se a promessa de privacidade
da versão Streamlit: nada fica guardado no servidor. (O armazenamento
persistente por unidade chega na fase de contas + GDPR, com SQLite.)

Assume um único processo uvicorn (como no Dockerfile.v3); os endpoints
sync do FastAPI correm em threadpool, daí o lock.
"""

import secrets
import threading
import time

SESSION_COOKIE = "mgfhub_sessao"
TTL_SEGUNDOS = 4 * 3600
MAX_SESSOES = 200

_lock = threading.Lock()
_sessions: dict[str, dict] = {}


def _sweep(agora):
    expirados = [
        token
        for token, sessao in _sessions.items()
        if agora - sessao["touched"] > TTL_SEGUNDOS
    ]
    for token in expirados:
        del _sessions[token]

    # guarda-costas de memória: descarta as sessões mais antigas
    while len(_sessions) > MAX_SESSOES:
        mais_antigo = min(_sessions, key=lambda t: _sessions[t]["touched"])
        del _sessions[mais_antigo]


def obter(request) -> dict:
    """Dados da sessão do pedido ({} se não existir ou tiver expirado)."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return {}
    agora = time.time()
    with _lock:
        _sweep(agora)
        sessao = _sessions.get(token)
        if sessao is None:
            return {}
        sessao["touched"] = agora
        return sessao["dados"]


def guardar(request, bicsp=None, mimuf=None):
    """Junta os novos uploads à sessão (substituindo o tipo respetivo).

    Devolve (token, dados) — anexar o token à resposta com anexar_cookie.
    """
    token = request.cookies.get(SESSION_COOKIE)
    agora = time.time()
    with _lock:
        _sweep(agora)
        if not token or token not in _sessions:
            token = secrets.token_urlsafe(32)
            _sessions[token] = {"touched": agora, "dados": {}}
        sessao = _sessions[token]
        sessao["touched"] = agora
        if bicsp is not None:
            sessao["dados"]["bicsp"] = bicsp
        if mimuf is not None:
            sessao["dados"]["mimuf"] = mimuf
        return token, sessao["dados"]


def anexar_cookie(response, token) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=TTL_SEGUNDOS,
        httponly=True,
        samesite="lax",
    )
