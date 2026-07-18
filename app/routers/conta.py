"""Contas e unidades: registo, login, workspace de unidade com um gestor,
pedidos de adesão por código com aprovação, e gestão de membros.

Modelo: contas individuais; os dados vivem ao nível da unidade; cada
unidade tem exatamente um gestor. Juntar-se por código cria um pedido
pendente que o gestor aceita/rejeita; um gestor não se pode juntar a
outra unidade (transfere primeiro a gestão), e não pode apagar a conta
enquanto a unidade tiver outros membros.
"""

import secrets
from contextlib import closing
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import auth, db, storage
from app.templating import templates

router = APIRouter()

CONVITE_DIAS = 14


# ---------------------------------------------------------------- helpers


def unidades_do_utilizador(user_id: int) -> list:
    """Unidades onde o utilizador é gestor ou membro (exclui pendentes)."""
    with closing(db.ligar()) as con:
        rows = con.execute(
            """
            SELECT un.id, un.nome, m.papel
            FROM membros m JOIN unidades un ON un.id = m.unidade_id
            WHERE m.user_id = ? AND m.papel != 'pendente'
            ORDER BY un.nome
            """,
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def papel_na_unidade(user_id: int, unidade_id: int):
    with closing(db.ligar()) as con:
        row = con.execute(
            "SELECT papel FROM membros WHERE user_id = ? AND unidade_id = ?",
            (user_id, unidade_id),
        ).fetchone()
    return row["papel"] if row else None


def _e_gestor_de_alguma(user_id: int) -> bool:
    with closing(db.ligar()) as con:
        row = con.execute(
            "SELECT 1 FROM membros WHERE user_id = ? AND papel = 'gestor' LIMIT 1",
            (user_id,),
        ).fetchone()
    return row is not None


def _pedidos_enviados(user_id: int) -> list:
    with closing(db.ligar()) as con:
        rows = con.execute(
            """
            SELECT un.id, un.nome
            FROM membros m JOIN unidades un ON un.id = m.unidade_id
            WHERE m.user_id = ? AND m.papel = 'pendente'
            ORDER BY un.nome
            """,
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def _membros_da_unidade(unidade_id: int) -> list:
    with closing(db.ligar()) as con:
        rows = con.execute(
            """
            SELECT u.id, u.nome, u.email, m.papel
            FROM membros m JOIN users u ON u.id = m.user_id
            WHERE m.unidade_id = ? AND m.papel != 'pendente'
            ORDER BY m.papel, u.nome
            """,
            (unidade_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def _pendentes_da_unidade(unidade_id: int) -> list:
    with closing(db.ligar()) as con:
        rows = con.execute(
            """
            SELECT u.id, u.nome, u.email
            FROM membros m JOIN users u ON u.id = m.user_id
            WHERE m.unidade_id = ? AND m.papel = 'pendente'
            ORDER BY m.criado_em
            """,
            (unidade_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def _convite_ativo(unidade_id: int):
    with closing(db.ligar()) as con:
        row = con.execute(
            "SELECT codigo, expira_em FROM convites "
            "WHERE unidade_id = ? AND expira_em > datetime('now') "
            "ORDER BY criado_em DESC LIMIT 1",
            (unidade_id,),
        ).fetchone()
    return dict(row) if row else None


def _uploads_por_mes(unidade_id: int) -> list:
    """Dados guardados agrupados por mês: uma linha por mês com as colunas
    BI-CSP e MIM@UF lado a lado."""
    por_mes = {}
    for doc in storage.listar_uploads(unidade_id):
        chave = f"{doc['ano']}-{doc['mes']}"
        por_mes.setdefault(chave, {"bicsp": [], "mimuf": []})
        por_mes[chave][doc["tipo"]].append(doc)
    # mais recente primeiro
    return [
        {"mes": mes, **tipos} for mes, tipos in sorted(por_mes.items(), reverse=True)
    ]


def _definir_unidade_ativa(token: str, unidade_id) -> None:
    with closing(db.ligar()) as con:
        con.execute(
            "UPDATE sessoes SET unidade_ativa = ? WHERE token = ?",
            (unidade_id, token),
        )
        con.commit()


def _render_conta(request, utilizador, mensagem=None, erro=None):
    # (a ativação automática da única unidade vive em auth.utilizador_atual)
    unidades = unidades_do_utilizador(utilizador["id"])

    detalhe = []
    for unidade in unidades:
        info = dict(unidade)
        info["ativa"] = unidade["id"] == utilizador["unidade_ativa"]
        if unidade["papel"] == "gestor":
            info["membros"] = _membros_da_unidade(unidade["id"])
            info["pendentes"] = _pendentes_da_unidade(unidade["id"])
            info["convite"] = _convite_ativo(unidade["id"])
            info["dados"] = _uploads_por_mes(unidade["id"])
        detalhe.append(info)

    return templates.TemplateResponse(
        request=request,
        name="conta.html",
        context={
            "utilizador": utilizador,
            "unidades": detalhe,
            "pedidos_enviados": _pedidos_enviados(utilizador["id"]),
            "e_gestor": _e_gestor_de_alguma(utilizador["id"]),
            "mensagem": mensagem,
            "erro": erro,
        },
    )


# ------------------------------------------------------------ registo/login


@router.get("/registar", response_class=HTMLResponse)
def registar_form(request: Request):
    return templates.TemplateResponse(
        request=request, name="registar.html", context={"erro": None}
    )


@router.post("/registar", response_class=HTMLResponse)
def registar(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    nome = nome.strip()
    email = email.strip().lower()
    if not nome or "@" not in email:
        return templates.TemplateResponse(
            request=request,
            name="registar.html",
            context={"erro": "Nome e email válidos são obrigatórios."},
        )
    if len(password) < 8:
        return templates.TemplateResponse(
            request=request,
            name="registar.html",
            context={"erro": "A password tem de ter pelo menos 8 caracteres."},
        )

    with closing(db.ligar()) as con:
        existe = con.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
        if existe:
            return templates.TemplateResponse(
                request=request,
                name="registar.html",
                context={"erro": "Já existe uma conta com esse email."},
            )
        cur = con.execute(
            "INSERT INTO users (email, nome, password_hash) VALUES (?, ?, ?)",
            (email, nome, auth.hash_password(password)),
        )
        con.commit()
        user_id = cur.lastrowid

    token = auth.criar_sessao(user_id)
    response = RedirectResponse("/conta", status_code=303)
    auth.anexar_cookie_login(response, token)
    return response


@router.get("/entrar", response_class=HTMLResponse)
def entrar_form(request: Request):
    return templates.TemplateResponse(
        request=request, name="entrar.html", context={"erro": None}
    )


@router.post("/entrar", response_class=HTMLResponse)
def entrar(request: Request, email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()
    with closing(db.ligar()) as con:
        user = con.execute(
            "SELECT id, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()

    if user is None or not auth.verificar_password(user["password_hash"], password):
        return templates.TemplateResponse(
            request=request,
            name="entrar.html",
            context={"erro": "Email ou password incorretos."},
        )

    unidades = unidades_do_utilizador(user["id"])
    unidade_ativa = unidades[0]["id"] if len(unidades) == 1 else None
    token = auth.criar_sessao(user["id"], unidade_ativa)
    response = RedirectResponse("/conta", status_code=303)
    auth.anexar_cookie_login(response, token)
    return response


@router.post("/sair")
def sair(request: Request):
    token = request.cookies.get(auth.LOGIN_COOKIE)
    if token:
        auth.terminar_sessao(token)
    response = RedirectResponse("/", status_code=303)
    auth.limpar_cookie_login(response)
    return response


# ----------------------------------------------------------------- conta


@router.get("/conta", response_class=HTMLResponse)
def conta(request: Request):
    utilizador = auth.utilizador_atual(request)
    if utilizador is None:
        return RedirectResponse("/entrar", status_code=303)
    return _render_conta(request, utilizador)


@router.post("/conta/unidades", response_class=HTMLResponse)
def criar_unidade(request: Request, nome: str = Form(...)):
    utilizador = auth.utilizador_atual(request)
    if utilizador is None:
        return RedirectResponse("/entrar", status_code=303)

    nome = nome.strip()
    if not nome:
        return _render_conta(
            request, utilizador, erro="O nome da unidade é obrigatório."
        )

    with closing(db.ligar()) as con:
        existe = con.execute(
            "SELECT 1 FROM unidades WHERE nome = ?", (nome,)
        ).fetchone()
        if existe:
            return _render_conta(
                request,
                utilizador,
                erro="Já existe uma unidade com esse nome — pede um código de convite ao gestor.",
            )
        cur = con.execute("INSERT INTO unidades (nome) VALUES (?)", (nome,))
        unidade_id = cur.lastrowid
        con.execute(
            "INSERT INTO membros (user_id, unidade_id, papel) VALUES (?, ?, 'gestor')",
            (utilizador["id"], unidade_id),
        )
        con.commit()

    _definir_unidade_ativa(utilizador["token"], unidade_id)
    utilizador["unidade_ativa"] = unidade_id
    return _render_conta(
        request,
        utilizador,
        mensagem=f"Unidade «{nome}» criada — és o gestor. "
        "Dica: usa o nome oficial da unidade tal como aparece nos ficheiros "
        "do BI-CSP/MIM@UF, para os uploads ficarem guardados.",
    )


@router.post("/conta/unidades/juntar", response_class=HTMLResponse)
def juntar_unidade(request: Request, codigo: str = Form(...)):
    utilizador = auth.utilizador_atual(request)
    if utilizador is None:
        return RedirectResponse("/entrar", status_code=303)

    if _e_gestor_de_alguma(utilizador["id"]):
        return _render_conta(
            request,
            utilizador,
            erro="Como gestor de uma unidade não te podes juntar a outra — "
            "transfere primeiro a gestão a um membro.",
        )

    codigo = codigo.strip()
    with closing(db.ligar()) as con:
        convite = con.execute(
            "SELECT unidade_id FROM convites "
            "WHERE codigo = ? AND expira_em > datetime('now')",
            (codigo,),
        ).fetchone()
        if convite is None:
            return _render_conta(
                request, utilizador, erro="Código de convite inválido ou expirado."
            )
        existente = con.execute(
            "SELECT papel FROM membros WHERE user_id = ? AND unidade_id = ?",
            (utilizador["id"], convite["unidade_id"]),
        ).fetchone()
        if existente is not None:
            erro = (
                "Já tens um pedido pendente nessa unidade."
                if existente["papel"] == "pendente"
                else "Já és membro dessa unidade."
            )
            return _render_conta(request, utilizador, erro=erro)
        con.execute(
            "INSERT INTO membros (user_id, unidade_id, papel) VALUES (?, ?, 'pendente')",
            (utilizador["id"], convite["unidade_id"]),
        )
        con.commit()

    return _render_conta(
        request,
        utilizador,
        mensagem="Pedido enviado — fica pendente até o gestor da unidade o aceitar.",
    )


@router.post(
    "/conta/unidades/{unidade_id}/pedidos/{user_id}/aceitar",
    response_class=HTMLResponse,
)
def aceitar_pedido(request: Request, unidade_id: int, user_id: int):
    utilizador = auth.utilizador_atual(request)
    if utilizador is None:
        return RedirectResponse("/entrar", status_code=303)
    if papel_na_unidade(utilizador["id"], unidade_id) != "gestor":
        return _render_conta(
            request, utilizador, erro="Só o gestor pode aceitar pedidos."
        )

    with closing(db.ligar()) as con:
        con.execute(
            "UPDATE membros SET papel = 'membro' "
            "WHERE user_id = ? AND unidade_id = ? AND papel = 'pendente'",
            (user_id, unidade_id),
        )
        con.commit()

    return _render_conta(request, utilizador, mensagem="Pedido aceite — novo membro.")


@router.post(
    "/conta/unidades/{unidade_id}/pedidos/{user_id}/rejeitar",
    response_class=HTMLResponse,
)
def rejeitar_pedido(request: Request, unidade_id: int, user_id: int):
    utilizador = auth.utilizador_atual(request)
    if utilizador is None:
        return RedirectResponse("/entrar", status_code=303)
    if papel_na_unidade(utilizador["id"], unidade_id) != "gestor":
        return _render_conta(
            request, utilizador, erro="Só o gestor pode rejeitar pedidos."
        )

    with closing(db.ligar()) as con:
        con.execute(
            "DELETE FROM membros "
            "WHERE user_id = ? AND unidade_id = ? AND papel = 'pendente'",
            (user_id, unidade_id),
        )
        con.commit()

    return _render_conta(request, utilizador, mensagem="Pedido rejeitado.")


@router.post(
    "/conta/unidades/{unidade_id}/pedidos/cancelar", response_class=HTMLResponse
)
def cancelar_pedido(request: Request, unidade_id: int):
    utilizador = auth.utilizador_atual(request)
    if utilizador is None:
        return RedirectResponse("/entrar", status_code=303)

    with closing(db.ligar()) as con:
        con.execute(
            "DELETE FROM membros "
            "WHERE user_id = ? AND unidade_id = ? AND papel = 'pendente'",
            (utilizador["id"], unidade_id),
        )
        con.commit()

    return _render_conta(request, utilizador, mensagem="Pedido cancelado.")


@router.post("/conta/unidades/{unidade_id}/ativa", response_class=HTMLResponse)
def ativar_unidade(request: Request, unidade_id: int):
    utilizador = auth.utilizador_atual(request)
    if utilizador is None:
        return RedirectResponse("/entrar", status_code=303)
    if papel_na_unidade(utilizador["id"], unidade_id) not in ("gestor", "membro"):
        return _render_conta(request, utilizador, erro="Não és membro dessa unidade.")
    _definir_unidade_ativa(utilizador["token"], unidade_id)
    utilizador["unidade_ativa"] = unidade_id
    return _render_conta(request, utilizador)


@router.post("/conta/unidades/{unidade_id}/convite", response_class=HTMLResponse)
def gerar_convite(request: Request, unidade_id: int):
    utilizador = auth.utilizador_atual(request)
    if utilizador is None:
        return RedirectResponse("/entrar", status_code=303)
    if papel_na_unidade(utilizador["id"], unidade_id) != "gestor":
        return _render_conta(
            request, utilizador, erro="Só o gestor da unidade pode gerar convites."
        )

    codigo = secrets.token_urlsafe(8)
    expira = (datetime.now(timezone.utc) + timedelta(days=CONVITE_DIAS)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    with closing(db.ligar()) as con:
        # um convite ativo de cada vez: os anteriores deixam de ser válidos
        con.execute("DELETE FROM convites WHERE unidade_id = ?", (unidade_id,))
        con.execute(
            "INSERT INTO convites (codigo, unidade_id, criado_por, expira_em) "
            "VALUES (?, ?, ?, ?)",
            (codigo, unidade_id, utilizador["id"], expira),
        )
        con.commit()

    return _render_conta(
        request,
        utilizador,
        mensagem=f"Convite criado (válido {CONVITE_DIAS} dias) — quem o usar fica "
        "pendente até aceitares o pedido.",
    )


@router.post(
    "/conta/unidades/{unidade_id}/transferir/{membro_id}",
    response_class=HTMLResponse,
)
def transferir_gestao(request: Request, unidade_id: int, membro_id: int):
    utilizador = auth.utilizador_atual(request)
    if utilizador is None:
        return RedirectResponse("/entrar", status_code=303)
    if papel_na_unidade(utilizador["id"], unidade_id) != "gestor":
        return _render_conta(
            request, utilizador, erro="Só o gestor pode transferir a gestão."
        )
    if papel_na_unidade(membro_id, unidade_id) != "membro":
        return _render_conta(
            request,
            utilizador,
            erro="A gestão só pode ser transferida para um membro da unidade.",
        )

    with closing(db.ligar()) as con:
        con.execute(
            "UPDATE membros SET papel = 'membro' "
            "WHERE user_id = ? AND unidade_id = ?",
            (utilizador["id"], unidade_id),
        )
        con.execute(
            "UPDATE membros SET papel = 'gestor' "
            "WHERE user_id = ? AND unidade_id = ?",
            (membro_id, unidade_id),
        )
        con.commit()

    return _render_conta(
        request, utilizador, mensagem="Gestão transferida — agora és membro da unidade."
    )


@router.post(
    "/conta/unidades/{unidade_id}/membros/{membro_id}/remover",
    response_class=HTMLResponse,
)
def remover_membro(request: Request, unidade_id: int, membro_id: int):
    utilizador = auth.utilizador_atual(request)
    if utilizador is None:
        return RedirectResponse("/entrar", status_code=303)
    if papel_na_unidade(utilizador["id"], unidade_id) != "gestor":
        return _render_conta(
            request, utilizador, erro="Só o gestor da unidade pode remover membros."
        )
    if papel_na_unidade(membro_id, unidade_id) != "membro":
        return _render_conta(
            request, utilizador, erro="O gestor não pode ser removido."
        )

    with closing(db.ligar()) as con:
        con.execute(
            "DELETE FROM membros WHERE user_id = ? AND unidade_id = ?",
            (membro_id, unidade_id),
        )
        con.execute(
            "UPDATE sessoes SET unidade_ativa = NULL "
            "WHERE user_id = ? AND unidade_ativa = ?",
            (membro_id, unidade_id),
        )
        con.commit()

    return _render_conta(request, utilizador, mensagem="Membro removido.")


@router.post("/conta/unidades/{unidade_id}/uploads/apagar", response_class=HTMLResponse)
def apagar_dados(
    request: Request,
    unidade_id: int,
    tipo: str = Form(...),
    nome: str = Form(...),
):
    utilizador = auth.utilizador_atual(request)
    if utilizador is None:
        return RedirectResponse("/entrar", status_code=303)
    # qualquer membro pode carregar dados, mas só o gestor pode apagar
    if papel_na_unidade(utilizador["id"], unidade_id) != "gestor":
        return _render_conta(
            request, utilizador, erro="Só o gestor da unidade pode apagar dados."
        )

    storage.apagar_upload(unidade_id, tipo, nome)
    return _render_conta(request, utilizador, mensagem="Dados apagados.")


@router.post("/conta/unidades/{unidade_id}/apagar", response_class=HTMLResponse)
def apagar_unidade(request: Request, unidade_id: int):
    utilizador = auth.utilizador_atual(request)
    if utilizador is None:
        return RedirectResponse("/entrar", status_code=303)
    if papel_na_unidade(utilizador["id"], unidade_id) != "gestor":
        return _render_conta(
            request, utilizador, erro="Só o gestor pode apagar a unidade."
        )

    with closing(db.ligar()) as con:
        # cascade: membros, convites e uploads da unidade
        con.execute("DELETE FROM unidades WHERE id = ?", (unidade_id,))
        con.commit()

    utilizador["unidade_ativa"] = None
    return _render_conta(
        request, utilizador, mensagem="Unidade apagada, incluindo os dados guardados."
    )


@router.post("/conta/apagar")
def apagar_conta(request: Request):
    utilizador = auth.utilizador_atual(request)
    if utilizador is None:
        return RedirectResponse("/entrar", status_code=303)

    with closing(db.ligar()) as con:
        # um gestor com outros membros tem de transferir a gestão primeiro,
        # senão a unidade ficava sem ninguém para aprovar pedidos/gerir dados
        bloqueio = con.execute(
            """
            SELECT un.nome FROM membros m JOIN unidades un ON un.id = m.unidade_id
            WHERE m.user_id = ? AND m.papel = 'gestor'
              AND EXISTS (SELECT 1 FROM membros m2
                          WHERE m2.unidade_id = m.unidade_id
                            AND m2.user_id != m.user_id
                            AND m2.papel != 'pendente')
            LIMIT 1
            """,
            (utilizador["id"],),
        ).fetchone()
        if bloqueio:
            return _render_conta(
                request,
                utilizador,
                erro=f"És gestor da unidade «{bloqueio['nome']}», que tem outros "
                "membros — transfere a gestão antes de apagar a conta.",
            )

        # apaga também as unidades onde este utilizador é o único membro real
        orfas = con.execute(
            """
            SELECT m.unidade_id FROM membros m
            WHERE m.user_id = ? AND m.papel = 'gestor'
            """,
            (utilizador["id"],),
        ).fetchall()
        for row in orfas:
            con.execute("DELETE FROM unidades WHERE id = ?", (row["unidade_id"],))
        con.execute("DELETE FROM users WHERE id = ?", (utilizador["id"],))
        con.commit()

    response = RedirectResponse("/", status_code=303)
    auth.limpar_cookie_login(response)
    return response
