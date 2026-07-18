"""Testes de contas, unidades, pedidos de adesão e persistência por unidade."""

import re
from contextlib import closing
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# a unidade dos fixtures xlsx é "USF Fixture" — os testes de persistência
# usam um nome equivalente (a correspondência é normalizada)
UNIDADE_FIXTURE = "usf fixture"


@pytest.fixture(autouse=True)
def limpar_bd():
    yield
    with closing(db.ligar()) as con:
        for tabela in (
            "sessoes",
            "convites",
            "uploads",
            "membros",
            "unidades",
            "users",
        ):
            con.execute(f"DELETE FROM {tabela}")
        con.commit()


def _registar(nome, email):
    client = TestClient(app)
    resp = client.post(
        "/registar",
        data={"nome": nome, "email": email, "password": "segredo123"},
    )
    assert resp.status_code == 200
    return client


def _criar_unidade(client, nome):
    resp = client.post("/conta/unidades", data={"nome": nome})
    assert "és o gestor" in resp.text
    return resp


def _codigo_convite(texto_conta):
    match = re.search(r"<code>([^<]+)</code>", texto_conta)
    assert match, "código de convite não encontrado"
    return match.group(1)


def _id_por_email(email):
    with closing(db.ligar()) as con:
        return con.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()[
            "id"
        ]


def _juntar_e_aceitar(gestor, email_membro, unidade_id=1):
    """Fluxo completo: membro pede adesão com o código, gestor aceita."""
    codigo = _codigo_convite(gestor.post(f"/conta/unidades/{unidade_id}/convite").text)
    membro = _registar(email_membro.split("@")[0].title(), email_membro)
    resp = membro.post("/conta/unidades/juntar", data={"codigo": codigo})
    assert "Pedido enviado" in resp.text
    gestor.post(
        f"/conta/unidades/{unidade_id}/pedidos/{_id_por_email(email_membro)}/aceitar"
    )
    return membro


def _upload_bicsp(client):
    nome = "bicsp_com_cabecalho_2024_06.xlsx"
    return client.post(
        "/ide/upload",
        files=[("bicsp", (nome, (FIXTURES / nome).read_bytes(), XLSX))],
    )


def test_registo_e_conta():
    client = _registar("Ana Gestora", "ana@example.com")
    resp = client.get("/conta")
    assert "Ana Gestora" in resp.text
    assert "Sair" in resp.text


def test_login_password_errada():
    _registar("Ana Gestora", "ana@example.com")
    client = TestClient(app)
    resp = client.post(
        "/entrar", data={"email": "ana@example.com", "password": "errada123"}
    )
    assert "Email ou password incorretos" in resp.text


def test_login_correto():
    _registar("Ana Gestora", "ana@example.com")
    client = TestClient(app)
    resp = client.post(
        "/entrar", data={"email": "ana@example.com", "password": "segredo123"}
    )
    assert resp.status_code == 200
    assert "Ana Gestora" in client.get("/conta").text


def test_pedido_de_adesao_pendente_ate_aceitar():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, "USF Teste")
    codigo = _codigo_convite(gestora.post("/conta/unidades/1/convite").text)

    membro = _registar("Bruno Membro", "bruno@example.com")
    resp = membro.post("/conta/unidades/juntar", data={"codigo": codigo})
    assert "Pedido enviado" in resp.text
    # enquanto pendente: sem acesso aos dados nem à unidade
    assert "pendente" in membro.get("/conta").text
    assert "BI-CSP não carregados" in membro.get("/ide").text
    resp = membro.post("/conta/unidades/1/ativa")
    assert "Não és membro dessa unidade" in resp.text

    # gestora vê o pedido e aceita
    resp = gestora.get("/conta")
    assert "Pedidos de adesão" in resp.text
    assert "Bruno Membro" in resp.text
    resp = gestora.post(
        f"/conta/unidades/1/pedidos/{_id_por_email('bruno@example.com')}/aceitar"
    )
    assert "Pedido aceite" in resp.text

    # agora é membro
    resp = membro.get("/conta")
    assert "membro" in resp.text
    assert "Pedido de adesão" not in resp.text


def test_rejeitar_pedido():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, "USF Teste")
    codigo = _codigo_convite(gestora.post("/conta/unidades/1/convite").text)

    membro = _registar("Bruno Membro", "bruno@example.com")
    membro.post("/conta/unidades/juntar", data={"codigo": codigo})

    resp = gestora.post(
        f"/conta/unidades/1/pedidos/{_id_por_email('bruno@example.com')}/rejeitar"
    )
    assert "Pedido rejeitado" in resp.text
    assert "Ainda não pertences a nenhuma unidade" in membro.get("/conta").text


def test_gestor_nao_pode_pedir_adesao():
    gestora_a = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora_a, "USF A")
    codigo = _codigo_convite(gestora_a.post("/conta/unidades/1/convite").text)

    gestora_b = _registar("Berta Gestora", "berta@example.com")
    _criar_unidade(gestora_b, "USF B")

    resp = gestora_b.post("/conta/unidades/juntar", data={"codigo": codigo})
    assert "Como gestor" in resp.text
    # e a UI não lhe mostra a opção
    assert "Juntar-me a outra unidade" not in gestora_b.get("/conta").text


def test_membro_nao_gere_convites():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, "USF Teste")
    membro = _juntar_e_aceitar(gestora, "bruno@example.com")

    resp = membro.post("/conta/unidades/1/convite")
    assert "Só o gestor" in resp.text


def test_convite_invalido():
    client = _registar("Ana Gestora", "ana@example.com")
    resp = client.post("/conta/unidades/juntar", data={"codigo": "inexistente"})
    assert "inválido ou expirado" in resp.text


def test_transferir_gestao():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, "USF Teste")
    membro = _juntar_e_aceitar(gestora, "bruno@example.com")

    resp = gestora.post(
        f"/conta/unidades/1/transferir/{_id_por_email('bruno@example.com')}"
    )
    assert "Gestão transferida" in resp.text

    # papéis trocados: a antiga gestora perde os poderes, o novo ganha-os
    assert "Só o gestor" in gestora.post("/conta/unidades/1/convite").text
    assert "<code>" in membro.post("/conta/unidades/1/convite").text


def test_upload_persistente_entre_sessoes_e_membros():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, UNIDADE_FIXTURE)

    resp = _upload_bicsp(gestora)
    assert "guardados na unidade" in resp.text
    assert "USF Fixture 06/2024" in resp.text

    # nova sessão (novo login) vê os dados guardados — sem novo upload
    outra_sessao = TestClient(app)
    outra_sessao.post(
        "/entrar", data={"email": "ana@example.com", "password": "segredo123"}
    )
    resp = outra_sessao.get("/ide")
    assert "USF Fixture 06/2024" in resp.text
    assert "chart-sunburst" in resp.text

    # outro membro da unidade vê os mesmos dados
    membro = _juntar_e_aceitar(gestora, "bruno@example.com")
    resp = membro.get("/ide")
    assert "USF Fixture 06/2024" in resp.text


def test_upload_de_outra_unidade_nao_persiste():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, "USF Outra Qualquer")

    # o ficheiro pertence a «USF Fixture» → renderiza mas não fica guardado
    resp = _upload_bicsp(gestora)
    assert "não ficou" in resp.text and "guardado" in resp.text
    assert "Só nesta sessão" in resp.text
    assert "chart-" in resp.text  # a análise renderiza na mesma

    # nada na tabela de dados da unidade
    assert "2024-06" not in gestora.get("/conta").text

    # uma nova sessão não vê nada (não persistiu)
    outra_sessao = TestClient(app)
    outra_sessao.post(
        "/entrar", data={"email": "ana@example.com", "password": "segredo123"}
    )
    assert "BI-CSP não carregados" in outra_sessao.get("/ide").text


def test_gestor_ve_tabela_de_dados_e_apaga():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, UNIDADE_FIXTURE)
    _upload_bicsp(gestora)

    resp = gestora.get("/conta")
    assert "Dados guardados" in resp.text
    assert "2024-06" in resp.text
    assert "USF Fixture 06/2024" in resp.text

    resp = gestora.post(
        "/conta/unidades/1/uploads/apagar",
        data={"tipo": "bicsp", "nome": "USF Fixture 06/2024"},
    )
    assert "Dados apagados" in resp.text
    assert "BI-CSP não carregados" in gestora.get("/ide").text


def test_membro_nao_apaga_dados():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, UNIDADE_FIXTURE)
    _upload_bicsp(gestora)
    membro = _juntar_e_aceitar(gestora, "bruno@example.com")

    resp = membro.post(
        "/conta/unidades/1/uploads/apagar",
        data={"tipo": "bicsp", "nome": "USF Fixture 06/2024"},
    )
    assert "Só o gestor" in resp.text
    assert "USF Fixture 06/2024" in membro.get("/ide").text


def test_membro_pode_carregar_dados():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, UNIDADE_FIXTURE)
    membro = _juntar_e_aceitar(gestora, "bruno@example.com")

    resp = _upload_bicsp(membro)
    assert "guardados na unidade" in resp.text
    # a gestora vê os dados carregados pelo membro
    assert "USF Fixture 06/2024" in gestora.get("/ide").text


def test_anonimo_continua_temporario():
    client = TestClient(app)
    resp = _upload_bicsp(client)
    assert "temporários" in resp.text
    assert "guardados na unidade" not in resp.text


def test_remover_membro_perde_acesso():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, UNIDADE_FIXTURE)
    _upload_bicsp(gestora)
    membro = _juntar_e_aceitar(gestora, "bruno@example.com")
    assert "USF Fixture 06/2024" in membro.get("/ide").text

    gestora.post(
        f"/conta/unidades/1/membros/{_id_por_email('bruno@example.com')}/remover"
    )

    assert "USF Fixture 06/2024" not in membro.get("/ide").text


def test_apagar_unidade_apaga_dados():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, UNIDADE_FIXTURE)
    _upload_bicsp(gestora)

    gestora.post("/conta/unidades/1/apagar")

    with closing(db.ligar()) as con:
        n_uploads = con.execute("SELECT COUNT(*) c FROM uploads").fetchone()["c"]
    assert n_uploads == 0
    assert "BI-CSP não carregados" in gestora.get("/ide").text


def test_apagar_conta():
    client = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(client, "USF Teste")
    client.post("/conta/apagar")

    resp = TestClient(app).post(
        "/entrar", data={"email": "ana@example.com", "password": "segredo123"}
    )
    assert "Email ou password incorretos" in resp.text

    with closing(db.ligar()) as con:
        n_unidades = con.execute("SELECT COUNT(*) c FROM unidades").fetchone()["c"]
    assert n_unidades == 0


def test_gestor_com_membros_nao_apaga_conta():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, "USF Teste")
    _juntar_e_aceitar(gestora, "bruno@example.com")

    resp = gestora.post("/conta/apagar")
    assert "transfere a gestão" in resp.text.lower()
    # a conta continua a existir
    assert "Ana Gestora" in gestora.get("/conta").text


def test_criar_unidade_escondida_quando_ja_tem():
    client = _registar("Ana Gestora", "ana@example.com")
    assert "Criar (fico gestor)" in client.get("/conta").text

    _criar_unidade(client, "USF Teste")
    resp = client.get("/conta")
    assert "Criar (fico gestor)" not in resp.text
    # gestora não vê a opção de se juntar a outra unidade
    assert "Juntar-me a outra unidade" not in resp.text


def test_paginas_legais():
    client = TestClient(app)
    resp = client.get("/privacidade")
    assert resp.status_code == 200
    assert "Política de Privacidade" in resp.text
    assert "unidade" in resp.text
    resp = client.get("/termos")
    assert resp.status_code == 200
    assert "Termos de Utilização" in resp.text
