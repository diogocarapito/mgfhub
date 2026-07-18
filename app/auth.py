"""Autenticação: passwords com scrypt (stdlib, sem dependências novas)
e sessões de login guardadas na base de dados (revogáveis)."""

import hashlib
import hmac
import secrets
from contextlib import closing
from datetime import datetime, timedelta, timezone

from app import db

LOGIN_COOKIE = "mgfhub_login"
SESSAO_DIAS = 30

# parâmetros scrypt (16 MiB por hash — resistente a brute-force offline)
_N, _R, _P = 16384, 8, 1


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${digest.hex()}"


def verificar_password(password_hash: str, password: str) -> bool:
    try:
        _, n, r, p, salt_hex, digest_hex = password_hash.split("$")
        digest = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=32,
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def _agora():
    return datetime.now(timezone.utc)


def criar_sessao(user_id: int, unidade_ativa=None) -> str:
    token = secrets.token_urlsafe(32)
    expira = (_agora() + timedelta(days=SESSAO_DIAS)).isoformat()
    with closing(db.ligar()) as con:
        con.execute(
            "INSERT INTO sessoes (token, user_id, unidade_ativa, expira_em) "
            "VALUES (?, ?, ?, ?)",
            (token, user_id, unidade_ativa, expira),
        )
        con.commit()
    return token


def terminar_sessao(token: str) -> None:
    with closing(db.ligar()) as con:
        con.execute("DELETE FROM sessoes WHERE token = ?", (token,))
        con.commit()


def utilizador_atual(request):
    """Utilizador autenticado do pedido (dict com unidade_ativa) ou None."""
    token = request.cookies.get(LOGIN_COOKIE)
    if not token:
        return None
    with closing(db.ligar()) as con:
        row = con.execute(
            """
            SELECT u.id, u.email, u.nome, s.token, s.unidade_ativa, s.expira_em
            FROM sessoes s JOIN users u ON u.id = s.user_id
            WHERE s.token = ?
            """,
            (token,),
        ).fetchone()
        if row is None:
            return None
        if datetime.fromisoformat(row["expira_em"]) < _agora():
            con.execute("DELETE FROM sessoes WHERE token = ?", (token,))
            con.commit()
            return None

        utilizador = dict(row)

        # sessão sem unidade ativa mas o utilizador pertence exatamente a uma
        # (ex: pedido de adesão aceite entretanto) → ativa automaticamente
        if utilizador["unidade_ativa"] is None:
            unidades = con.execute(
                "SELECT unidade_id FROM membros "
                "WHERE user_id = ? AND papel != 'pendente'",
                (utilizador["id"],),
            ).fetchall()
            if len(unidades) == 1:
                utilizador["unidade_ativa"] = unidades[0]["unidade_id"]
                con.execute(
                    "UPDATE sessoes SET unidade_ativa = ? WHERE token = ?",
                    (utilizador["unidade_ativa"], token),
                )
                con.commit()

        return utilizador


def anexar_cookie_login(response, token: str) -> None:
    response.set_cookie(
        LOGIN_COOKIE,
        token,
        max_age=SESSAO_DIAS * 24 * 3600,
        httponly=True,
        samesite="lax",
    )


def limpar_cookie_login(response) -> None:
    response.delete_cookie(LOGIN_COOKIE)
