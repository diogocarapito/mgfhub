# mgfhub — comandos de desenvolvimento
#
# Primeira vez:   make venv     (cria .venv com python3.13 e instala dependências)
# Correr a app:   make run      (http://localhost:8501)
# Testes:         make test
# Antes de commit: make check   (format + lint + testes)
#
# Os targets usam .venv/bin/ se existir; caso contrário (ex: CI) usam o PATH.
BIN = $(wildcard .venv/bin/)

.DEFAULT_GOAL := help
.PHONY: help venv install run test test-cov lint format check clean \
	docker-build docker-run docker-test docker

help:  ## mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-13s\033[0m %s\n", $$1, $$2}'

venv:  ## primeira utilização: cria .venv (python3.13) e instala dependências
	python3.13 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

install:  ## instala dependências no ambiente ativo (usado no CI)
	pip install --upgrade pip
	pip install -r requirements.txt

run:  ## corre a app Streamlit em http://localhost:8501
	$(BIN)streamlit run mgfhub.py

test:  ## corre os testes
	$(BIN)pytest tests/

test-cov:  ## testes com relatório de cobertura detalhado
	$(BIN)pytest -vv --cov=mgfhub --cov=core --cov=utils --cov=pages tests/ --cov-report term-missing

lint:  ## pylint sobre todo o código
	$(BIN)pylint --disable=R,C,W0622 *.py core/*.py monitor/*.py ui/*.py scripts/*.py utils/*.py pages/*.py tests/*.py

format:  ## formata o código com black
	$(BIN)black .

check: format lint test  ## format + lint + testes (correr antes de cada commit)

clean:  ## remove caches (__pycache__, pytest, coverage)
	find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage

docker-build:  ## constrói a imagem docker
	docker build -t mgfhub .

docker-run:  ## corre a app em docker na porta 8501 (container mgfhub-local)
	docker run --rm -d --name mgfhub-local -p 8501:8501 mgfhub

docker-test:  ## health-check do container e paragem (remove-se ao parar)
	sleep 10
	curl --fail http://localhost:8501/_stcore/health
	docker stop mgfhub-local

docker: docker-build docker-run docker-test  ## build + run + health-check + stop
