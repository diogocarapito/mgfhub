"""Testes da app FastAPI v3 (páginas e fragmentos htmx)."""

import re

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _num_indicadores(html):
    match = re.search(r"<strong>(\d+)</strong> indicadores", html)
    assert match, "contagem de indicadores não encontrada"
    return int(match.group(1))


def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_home():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "mgfhub" in resp.text
    assert "/indicadores" in resp.text


def test_indicadores_pagina_completa():
    resp = client.get("/indicadores")
    assert resp.status_code == 200
    assert resp.text.lstrip().startswith("<!doctype html>")
    assert 'id="pesquisa-form"' in resp.text
    assert 'id="resultados"' in resp.text
    # página completa não pode trazer o select out-of-band duplicado
    assert "hx-swap-oob" not in resp.text


def test_indicadores_fragmento_htmx():
    resp = client.get("/indicadores", headers={"HX-Request": "true"})
    assert resp.status_code == 200
    assert not resp.text.lstrip().startswith("<!doctype html>")
    assert 'id="resultados"' in resp.text
    # o fragmento atualiza o select de áreas out-of-band
    assert "hx-swap-oob" in resp.text


def test_filtro_contratualizacao_muda_resultados():
    num_ide = _num_indicadores(
        client.get("/indicadores", params={"filtros": "IDE"}).text
    )
    num_todos = _num_indicadores(
        client.get("/indicadores", params={"filtros": "Todos"}).text
    )
    assert 0 < num_ide < num_todos


def test_pesquisa_fuzzy():
    resp = client.get(
        "/indicadores", params={"pesquisa": "diabetes", "filtros": "Todos"}
    )
    assert resp.status_code == 200
    assert _num_indicadores(resp.text) > 0
    assert "Diabetes" in resp.text


def test_pesquisa_sem_resultados():
    resp = client.get(
        "/indicadores",
        params={"pesquisa": "xyzzy qwerty inexistente", "filtros": "IDE"},
    )
    assert resp.status_code == 200
    assert "Nenhum indicador encontrado" in resp.text


def test_vista_tabela():
    resp = client.get("/indicadores", params={"vista": "tabela"})
    assert resp.status_code == 200
    assert "<table>" in resp.text
    assert "SDM" in resp.text


def test_area_clinica_filtra():
    num_area = _num_indicadores(
        client.get(
            "/indicadores", params={"filtros": "IDE", "area": "Diabetes Mellitus"}
        ).text
    )
    num_sem = _num_indicadores(
        client.get("/indicadores", params={"filtros": "IDE"}).text
    )
    assert 0 < num_area < num_sem


def test_area_invalida_ignorada():
    # área que não existe no filtro atual é ignorada em vez de esvaziar tudo
    resp = client.get(
        "/indicadores", params={"filtros": "IDE", "area": "Área Inexistente"}
    )
    num_ide = _num_indicadores(
        client.get("/indicadores", params={"filtros": "IDE"}).text
    )
    assert _num_indicadores(resp.text) == num_ide


def test_parametros_invalidos_normalizados():
    resp = client.get("/indicadores", params={"filtros": "hack", "vista": "hack"})
    assert resp.status_code == 200
    assert _num_indicadores(resp.text) > 0
