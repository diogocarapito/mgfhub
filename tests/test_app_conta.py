"""Testes de contas, unidades e persistência de uploads por unidade."""

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
    # nav mostra o primeiro nome e o botão sair
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


def test_criar_unidade_convite_e_juntar():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, "USF Teste")

    resp = gestora.post("/conta/unidades/1/convite")
    codigo = _codigo_convite(resp.text)

    membro = _registar("Bruno Membro", "bruno@example.com")
    resp = membro.post("/conta/unidades/juntar", data={"codigo": codigo})
    assert "Juntaste-te à unidade" in resp.text

    # gestora vê os dois membros
    resp = gestora.get("/conta")
    assert "Bruno Membro" in resp.text


def test_membro_nao_gere_convites():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, "USF Teste")
    codigo = _codigo_convite(gestora.post("/conta/unidades/1/convite").text)

    membro = _registar("Bruno Membro", "bruno@example.com")
    membro.post("/conta/unidades/juntar", data={"codigo": codigo})

    resp = membro.post("/conta/unidades/1/convite")
    assert "Só o gestor" in resp.text


def test_convite_invalido():
    client = _registar("Ana Gestora", "ana@example.com")
    resp = client.post("/conta/unidades/juntar", data={"codigo": "inexistente"})
    assert "inválido ou expirado" in resp.text


def test_upload_persistente_entre_sessoes_e_membros():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, "USF Teste")

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
    codigo = _codigo_convite(gestora.post("/conta/unidades/1/convite").text)
    membro = _registar("Bruno Membro", "bruno@example.com")
    membro.post("/conta/unidades/juntar", data={"codigo": codigo})
    resp = membro.get("/ide")
    assert "USF Fixture 06/2024" in resp.text


def test_gestor_ve_tabela_de_dados_e_apaga():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, "USF Teste")
    _upload_bicsp(gestora)

    # tabela por mês na conta: linha 2024-06 com o documento na coluna BI-CSP
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
    _criar_unidade(gestora, "USF Teste")
    _upload_bicsp(gestora)
    codigo = _codigo_convite(gestora.post("/conta/unidades/1/convite").text)

    membro = _registar("Bruno Membro", "bruno@example.com")
    membro.post("/conta/unidades/juntar", data={"codigo": codigo})

    resp = membro.post(
        "/conta/unidades/1/uploads/apagar",
        data={"tipo": "bicsp", "nome": "USF Fixture 06/2024"},
    )
    assert "Só o gestor" in resp.text
    # os dados continuam lá
    assert "USF Fixture 06/2024" in membro.get("/ide").text


def test_criar_unidade_escondida_quando_ja_tem():
    client = _registar("Ana Gestora", "ana@example.com")
    # sem unidade: o formulário de criar aparece
    assert "Criar (fico gestor)" in client.get("/conta").text

    _criar_unidade(client, "USF Teste")
    resp = client.get("/conta")
    assert "Criar (fico gestor)" not in resp.text
    # juntar-se a outra unidade continua acessível (recolhido)
    assert "Juntar-me a outra unidade" in resp.text


def test_anonimo_continua_temporario():
    client = TestClient(app)
    resp = _upload_bicsp(client)
    assert "temporários" in resp.text
    assert "guardados na unidade" not in resp.text


def test_remover_membro_perde_acesso():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, "USF Teste")
    _upload_bicsp(gestora)
    codigo = _codigo_convite(gestora.post("/conta/unidades/1/convite").text)

    membro = _registar("Bruno Membro", "bruno@example.com")
    membro.post("/conta/unidades/juntar", data={"codigo": codigo})
    assert "USF Fixture 06/2024" in membro.get("/ide").text

    # obter o id do membro e removê-lo
    with closing(db.ligar()) as con:
        membro_id = con.execute(
            "SELECT id FROM users WHERE email = 'bruno@example.com'"
        ).fetchone()["id"]
    gestora.post(f"/conta/unidades/1/membros/{membro_id}/remover")

    assert "USF Fixture 06/2024" not in membro.get("/ide").text


def test_apagar_unidade_apaga_dados():
    gestora = _registar("Ana Gestora", "ana@example.com")
    _criar_unidade(gestora, "USF Teste")
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

    # unidade onde era o único membro foi apagada juntamente
    with closing(db.ligar()) as con:
        n_unidades = con.execute("SELECT COUNT(*) c FROM unidades").fetchone()["c"]
    assert n_unidades == 0


def test_paginas_legais():
    client = TestClient(app)
    resp = client.get("/privacidade")
    assert resp.status_code == 200
    assert "Política de Privacidade" in resp.text
    assert "unidade" in resp.text
    resp = client.get("/termos")
    assert resp.status_code == 200
    assert "Termos de Utilização" in resp.text
