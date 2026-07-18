"""Testes end-to-end do dashboard IDE da app v3.

Usam os mesmos fixtures xlsx dos testes golden do core: o fluxo completo
upload → sessão → tabs → gráficos plotly (JSON) é exercitado por HTTP.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _upload_completo(client):
    files = []
    for nome in (
        "bicsp_com_cabecalho_2024_06.xlsx",
        "bicsp_sem_cabecalho_2024_07.xlsx",
    ):
        files.append(("bicsp", (nome, (FIXTURES / nome).read_bytes(), XLSX)))
    for nome in ("mimuf_unidade_2024_06.xlsx", "mimuf_medico_2024_06.xlsx"):
        files.append(("mimuf", (nome, (FIXTURES / nome).read_bytes(), XLSX)))
    return client.post("/ide/upload", files=files)


def test_pagina_ide_sem_dados():
    client = TestClient(app)
    resp = client.get("/ide")
    assert resp.status_code == 200
    assert 'id="upload-bicsp"' in resp.text
    assert "BI-CSP não carregados" in resp.text
    # estado vazio mostra o sunburst de demonstração
    assert "chart-demo" in resp.text
    assert "plotly.min.js" in resp.text


def test_tabs_sem_dados_mostram_aviso():
    client = TestClient(app)
    assert "MIM@UF não carregados" in client.get("/ide/indicador").text
    assert "MIM@UF não carregados" in client.get("/ide/profissional").text


def test_upload_e_visao_unidade():
    client = TestClient(app)
    resp = _upload_completo(client)
    assert resp.status_code == 200
    # resumo da sessão com os dois tipos carregados
    assert "USF Fixture 06/2024" in resp.text
    assert "bicsp_sem_cabecalho_2024_07.xlsx 07/2024" in resp.text
    # com 2 datasets BI-CSP a vista default é Dumbbell
    assert "chart-dumbbell" in resp.text
    # métrica IDE do golden (19.076 → 19.1)
    assert "19.1" in resp.text

    # vista Sunburst
    resp = client.get("/ide/unidade", params={"vista": "Sunburst"})
    assert "chart-sunburst" in resp.text
    assert '"sunburst"' in resp.text

    # vista Tabela com links SDM
    resp = client.get("/ide/unidade", params={"vista": "Tabela"})
    assert "SDM" in resp.text
    assert "8 - Taxa" in resp.text

    # filtro por área clínica anula scores fora da seleção mas mantém o IDE máximo coerente
    resp = client.get(
        "/ide/unidade",
        params={"vista": "Sunburst", "area": "Diabetes Mellitus"},
    )
    assert resp.status_code == 200
    assert "chart-sunburst" in resp.text


def test_visao_indicador_equipa():
    client = TestClient(app)
    _upload_completo(client)

    resp = client.get("/ide/indicador")
    assert resp.status_code == 200
    # indicador default = menor id (8) com os agregados dos 3 médicos
    assert "8 - Taxa" in resp.text
    assert "1200" in resp.text  # denominador 400+400+400
    assert "792" in resp.text  # numerador 302+180+310
    assert "chart-alvo" in resp.text
    assert "chart-equipa" in resp.text
    assert "Ana Primeira" in resp.text
    assert "Carla Terceira" in resp.text


def test_visao_indicador_temporal():
    client = TestClient(app)
    _upload_completo(client)

    resp = client.get(
        "/ide/indicador",
        params={"vista": "Evolução temporal", "temporal": "Unidade"},
    )
    assert resp.status_code == 200
    assert "chart-temporal" in resp.text
    assert "Unidade" in resp.text


def test_visao_profissional():
    client = TestClient(app)
    _upload_completo(client)

    resp = client.get("/ide/profissional")
    assert resp.status_code == 200
    assert "Ana Primeira" in resp.text
    assert "Bruno Segundo" in resp.text
    assert "Carla Terceira" in resp.text
    assert "chart-profissional" in resp.text
    assert '"sunburst"' in resp.text

    resp = client.get("/ide/profissional", params={"medico": "Carla Terceira"})
    assert resp.status_code == 200
    assert '"sunburst"' in resp.text


def test_sessoes_isoladas():
    client_a = TestClient(app)
    _upload_completo(client_a)
    assert "chart-dumbbell" in client_a.get("/ide/unidade").text

    client_b = TestClient(app)
    assert "BI-CSP não carregados" in client_b.get("/ide/unidade").text


def test_upload_invalido_mostra_erro_amigavel():
    client = TestClient(app)
    resp = client.post(
        "/ide/upload",
        files=[("bicsp", ("lixo.xlsx", b"isto nao e um xlsx", XLSX))],
    )
    assert resp.status_code == 200
    assert "Não foi possível processar os ficheiros do BI-CSP" in resp.text
